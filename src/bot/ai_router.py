"""
AI-based routing using LLM for intelligent agent selection.
"""

from typing import Literal
from pydantic import BaseModel, Field

from src.llm import OpenRouterClient
from src.utils import get_logger

logger = get_logger(__name__)


class AgentRoute(BaseModel):
    """Schema for AI routing decision."""
    
    agent: Literal["expert_agent", "general_agent"] = Field(
        description="The agent to route the query to"
    )
    reasoning: str = Field(
        description="Brief explanation of why this agent was chosen"
    )
    confidence: float = Field(
        description="Confidence score between 0.0 and 1.0",
        ge=0.0,
        le=1.0
    )


class AIRouter:
    """
    AI-powered router that uses LLM to intelligently route queries to agents.
    
    This is more accurate than keyword-based routing as it understands
    context, semantics, and subtle nuances in user queries.
    """
    
    ROUTING_PROMPT = """You are an intelligent routing system for a Discord bot.

Available Agent:

**general_agent** (Luma)
   - Handles ALL queries (unified agent system)
   - Casual chat: jokes, banter, community vibes
   - Serious mode: Liquid platform questions (trading, vaults, fees, APY)
   - Automatically switches tone based on query type
   - Context-aware: understands when to be funny vs helpful

Routing Logic:
- ALL queries go to general_agent (it's the only agent)
- This router exists for future expansion but currently always returns general_agent

Analyze the user's query and route to general_agent."""

    def __init__(self, llm_client: OpenRouterClient):
        """Initialize AI router with LLM client."""
        self.llm_client = llm_client
        logger.info("ai_router_initialized")
    
    async def route(self, query: str, channel_name: str = None) -> AgentRoute:
        """
        Route query to appropriate agent using LLM.
        
        Args:
            query: User's query text
            channel_name: Optional channel name for context
            
        Returns:
            AgentRoute with agent selection and reasoning
        """
        # Build context with channel info if available
        context = f"User query: {query}"
        if channel_name:
            context += f"\nChannel: #{channel_name}"
        
        # Create routing prompt
        messages = [
            {"role": "system", "content": self.ROUTING_PROMPT},
            {"role": "user", "content": context}
        ]
        
        try:
            # Use structured output for routing decision
            response = await self.llm_client.generate_structured(
                messages=messages,
                response_model=AgentRoute,
                temperature=0.1,  # Low temperature for consistent routing
            )
            
            logger.info(
                "ai_routing_decision",
                query=query[:50],
                agent=response.agent,
                confidence=response.confidence,
                reasoning=response.reasoning[:50],
            )
            
            return response
            
        except Exception as e:
            logger.error("ai_routing_error", error=str(e))
            # Fallback to general agent on error
            return AgentRoute(
                agent="general_agent",
                reasoning="Fallback due to routing error",
                confidence=0.5
            )
