"""
OpenRouter API client with prompt caching and usage tracking.

Features:
- Automatic prompt caching (Grok)
- Usage metrics logging
- Retry logic with exponential backoff
- Async support
- Structured output support
"""

import json
import time
from typing import Any, Dict, List, Optional, Type, TypeVar

import httpx
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.utils import get_logger, log_llm_request

logger = get_logger(__name__)

T = TypeVar('T', bound=BaseModel)

class Usage(BaseModel):
    """Token usage metrics."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0
    
    # Cost metrics (from OpenRouter)
    prompt_cost: float = 0.0
    completion_cost: float = 0.0
    total_cost: float = 0.0
    cache_discount: float = 0.0


class ChatResponse(BaseModel):
    """Chat completion response."""
    content: str
    model: str
    usage: Usage
    latency_ms: float = 0.0
    finish_reason: Optional[str] = None


class OpenRouterClient:
    """
    OpenRouter API client with prompt caching and usage tracking.
    
    Grok automatically caches system prompts - no configuration needed.
    Cache reads are charged at 0.25x of input price for cost savings.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "x-ai/grok-beta",
        base_url: str = "https://openrouter.ai/api/v1",
        timeout: int = 30,
    ):
        """
        Initialize OpenRouter client.
        
        Args:
            api_key: OpenRouter API key
            model: Model identifier (default: x-ai/grok-beta)
            base_url: API base URL
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/liquid-discord-bot",
                "X-Title": "Liquid Discord Multimodal Bot",
            },
            timeout=timeout,
        )
        
        logger.info(
            "openrouter_client_initialized",
            model=model,
            base_url=base_url,
        )
    
    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def chat_completion(
        self,
        messages: List[Dict[str, any]],  # Changed to 'any' to support multimodal content
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
        **kwargs
    ) -> ChatResponse:
        """
        Chat completion with usage tracking and prompt caching.
        
        System prompts are automatically cached by Grok for cost optimization.
        Cache reads cost 0.25x of input price.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt (will be cached)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Enable streaming (not yet implemented)
            **kwargs: Additional model parameters
        
        Returns:
            ChatResponse with content and usage metrics
        """
        start_time = time.time()
        
        # Prepend system prompt if provided (automatically cached)
        if system_prompt:
            messages = [
                {"role": "system", "content": system_prompt},
                *messages
            ]
        
        # Build request payload with usage tracking
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "usage": {
                "include": True  # Enable detailed usage tracking
            },
            **kwargs
        }
        
        # Removed verbose request logging
        
        try:
            # Make API request
            url = "https://openrouter.ai/api/v1/chat/completions"
            response = await self.client.post(
                url,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            
            # Parse response
            choice = data["choices"][0]
            content = choice["message"]["content"]
            finish_reason = choice.get("finish_reason")
            
            # Parse usage metrics from OpenRouter
            usage_data = data.get("usage", {})
            prompt_details = usage_data.get("prompt_tokens_details", {})
            completion_details = usage_data.get("completion_tokens_details", {})
            cost_details = usage_data.get("cost_details", {})
            
            usage = Usage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
                cached_tokens=prompt_details.get("cached_tokens", 0),
            )
            
            # Parse cost information (OpenRouter provides cost in credits)
            # 1 credit = $0.000001 USD
            cost_in_credits = usage_data.get("cost")
            if cost_in_credits is not None:
                usage.total_cost = cost_in_credits / 1_000_000  # Convert to USD
            
            # Upstream cost (for BYOK)
            upstream_cost = cost_details.get("upstream_inference_cost")
            if upstream_cost is not None:
                usage.prompt_cost = upstream_cost / 1_000_000  # Convert to USD
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Create response object
            chat_response = ChatResponse(
                content=content,
                model=self.model,
                usage=usage,
                latency_ms=latency_ms,
                finish_reason=finish_reason,
            )
            
            # Log usage metrics
            self._log_usage(chat_response)
            
            return chat_response
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            try:
                error_json = e.response.json()
                error_detail = error_json.get("error", {}).get("message", error_detail)
            except:
                pass
            
            logger.error(
                "openrouter_http_error",
                error=error_detail,
            )
            raise
        
        except Exception as e:
            logger.error(
                "openrouter_error",
                error=str(e),
                exc_info=True,
            )
            raise
    
    def _log_usage(self, response: ChatResponse) -> None:
        """Log token usage and costs with structured logging."""
        log_llm_request(
            logger=logger,
            model=response.model,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            cached_tokens=response.usage.cached_tokens,
            total_tokens=response.usage.total_tokens,
            cost_usd=response.usage.total_cost,
            cache_discount_usd=response.usage.cache_discount,
            latency_ms=response.latency_ms,  # Fixed: latency_ms is in ChatResponse, not Usage
        )
        
        # Track usage statistics (lazy import to avoid circular dependency)
        try:
            from src.analytics.usage_tracker import get_usage_tracker
            tracker = get_usage_tracker()
            tracker.track_request(
                model=response.model,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                cached_tokens=response.usage.cached_tokens,
                cost_usd=response.usage.total_cost,
            )
        except ImportError:
            pass  # Usage tracker not available yet (circular import)
    
    async def generate_structured(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        temperature: float = 0.3,
        max_tokens: int = 1000,
        **kwargs
    ) -> T:
        """
        Generate structured output using Pydantic model.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            response_model: Pydantic model class for structured output
            temperature: Sampling temperature (default lower for consistent structured output)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model parameters
            
        Returns:
            Instance of response_model with parsed structured data
        """
        # Get JSON schema from Pydantic model
        schema = response_model.model_json_schema()
        
        # Add instruction to generate JSON matching the schema
        instruction = f"\n\nYou must respond with valid JSON that matches this schema:\n```json\n{json.dumps(schema, indent=2)}\n```"
        
        # Append instruction to last user message
        enhanced_messages = messages.copy()
        if enhanced_messages and enhanced_messages[-1]["role"] == "user":
            enhanced_messages[-1]["content"] += instruction
        
        try:
            # Get completion
            response = await self.chat_completion(
                messages=enhanced_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Parse JSON response
            content = response.content.strip()
            
            # Try to extract JSON if wrapped in markdown code block
            if content.startswith("```"):
                # Remove markdown code fences
                lines = content.split("\n")
                content = "\n".join(lines[1:-1] if len(lines) > 2 else lines)
                content = content.replace("```json", "").replace("```", "").strip()
            
            # Parse and validate with Pydantic
            parsed = response_model.model_validate_json(content)
            
            logger.debug(
                "structured_output_generated",
                model=response_model.__name__,
            )
            
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(
                "structured_output_json_error",
                error=str(e),
                content=content[:200],
            )
            raise ValueError(f"Failed to parse JSON response: {e}")
        
        except Exception as e:
            logger.error(
                "structured_output_error",
                error=str(e),
                exc_info=True,
            )
            raise
    
    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
        logger.info("openrouter_client_closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
