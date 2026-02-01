"""
AI-powered scam detection using LLM.
"""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass

from src.llm import OpenRouterClient
from src.utils import get_logger

logger = get_logger(__name__)


@dataclass
class AIAnalysisResult:
    """Result of AI analysis."""
    is_scam: bool
    confidence: float
    risk_level: str
    primary_reason: str
    all_reasons: List[str]
    recommended_action: str


class AIAnalyzer:
    """
    AI-powered scam detection using LLM.
    
    Uses language model to analyze suspicious messages
    and determine if they are scams.
    """
    
    def __init__(
        self,
        llm_client: OpenRouterClient,
        confidence_threshold: float = 0.7,
    ):
        """
        Initialize AI analyzer.
        
        Args:
            llm_client: LLM client for analysis
            confidence_threshold: Minimum confidence to flag as scam
        """
        self.llm_client = llm_client
        self.confidence_threshold = confidence_threshold
        
        logger.info(
            "ai_analyzer_initialized",
            confidence_threshold=confidence_threshold,
        )
    
    async def analyze_message(
        self,
        content: str,
        author_name: str,
        channel_name: str,
        has_links: bool,
        has_mentions: bool,
        matched_patterns: List[str],
        matched_keywords: List[str],
    ) -> AIAnalysisResult:
        """
        Analyze message using AI to detect scams.
        
        Args:
            content: Message content
            author_name: Message author name
            channel_name: Channel name
            has_links: Whether message contains links
            has_mentions: Whether message contains mass mentions
            matched_patterns: Regex patterns that matched
            matched_keywords: Keywords that matched
        
        Returns:
            AIAnalysisResult with detection results
        """
        logger.info(
            "ai_analysis_started",
            content_length=len(content),
            has_links=has_links,
            patterns_matched=len(matched_patterns),
        )
        
        # Build prompt
        prompt = self._build_analysis_prompt(
            content=content,
            author_name=author_name,
            channel_name=channel_name,
            has_links=has_links,
            has_mentions=has_mentions,
            matched_patterns=matched_patterns,
            matched_keywords=matched_keywords,
        )
        
        try:
            # Get AI response
            response = await self.llm_client.chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                system_prompt="You are an expert Discord moderator specializing in scam detection. Analyze messages carefully and provide accurate assessments.",
                max_tokens=500,
                temperature=0.1,  # Low temperature for consistent results
            )
            
            # Parse JSON response
            result = self._parse_response(response.content)
            
            logger.info(
                "ai_analysis_completed",
                is_scam=result.is_scam,
                confidence=result.confidence,
                risk_level=result.risk_level,
            )
            
            return result
        
        except Exception as e:
            logger.error(
                "ai_analysis_failed",
                error=str(e),
                exc_info=True,
            )
            
            # Default to high-risk if AI fails but patterns matched
            return AIAnalysisResult(
                is_scam=True,
                confidence=0.5,
                risk_level="medium",
                primary_reason="AI analysis failed, flagged based on patterns",
                all_reasons=["AI analysis error", "Pattern matches detected"],
                recommended_action="delete",
            )
    
    def _build_analysis_prompt(
        self,
        content: str,
        author_name: str,
        channel_name: str,
        has_links: bool,
        has_mentions: bool,
        matched_patterns: List[str],
        matched_keywords: List[str],
    ) -> str:
        """Build analysis prompt for LLM."""
        
        context_info = []
        if has_links:
            context_info.append("contains links")
        if has_mentions:
            context_info.append("has @everyone/@here mentions")
        if matched_patterns:
            context_info.append(f"matched {len(matched_patterns)} regex patterns")
        if matched_keywords:
            context_info.append(f"matched keywords: {', '.join(matched_keywords[:3])}")
        
        context = ", ".join(context_info) if context_info else "no special indicators"
        
        prompt = f"""Analyze this Discord message for scam/phishing indicators.

MESSAGE: "{content}"
AUTHOR: {author_name}
CHANNEL: #{channel_name}
CONTEXT: {context}

⚠️ THIS IS A CRYPTO/TRADING COMMUNITY - users regularly discuss wallets, trading, transfers etc.

ACTUAL SCAM INDICATORS (flag these):
1. Offering unsolicited help: "DM me", "I can help", "contact support @..." 
2. Fake airdrops/giveaways: "claim free tokens", "you won", "congratulations"
3. Phishing: asking for private keys, seed phrases, passwords
4. Impersonation: claiming to be official/admin/support/team
5. Investment schemes: "guaranteed profit", "double your crypto"
6. Suspicious links: URL shorteners, unknown domains with suspicious paths

NOT SCAMS (allow these):
- Users ASKING for help with their own wallet/trading issues
- Genuine questions about how to use the platform
- Discussing trading strategies or market conditions
- Reporting their own problems ("my wallet doesn't work", "I can't trade")
- Casual conversation mentioning crypto terms

KEY DISTINCTION:
- "DM me for help" = SCAM (offering unsolicited help)
- "Can someone help me?" = NOT SCAM (asking for help)
- "My wallet won't enable" = NOT SCAM (reporting personal issue)
- "Send me your keys" = SCAM (phishing attempt)

Respond ONLY with valid JSON (no markdown, no code blocks):
{{
  "is_scam": true or false,
  "confidence": 0.0 to 1.0,
  "risk_level": "low" or "medium" or "high",
  "primary_reason": "main reason for flagging",
  "all_reasons": ["reason1", "reason2", "reason3"],
  "recommended_action": "allow" or "warn" or "delete"
}}

IMPORTANT: This is a TRADING community. Don't flag legitimate questions about wallets/trading.
Only flag messages where someone is ACTIVELY trying to scam others.
Respond ONLY with the JSON object, nothing else."""
        
        return prompt
    
    def _parse_response(self, response_text: str) -> AIAnalysisResult:
        """Parse LLM response into structured result."""
        try:
            # Remove markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith("```"):
                # Extract JSON from code block
                lines = response_text.split("\n")
                json_lines = []
                in_json = False
                for line in lines:
                    if line.startswith("```"):
                        in_json = not in_json
                        continue
                    if in_json or (not line.startswith("```") and "{" in line):
                        json_lines.append(line)
                response_text = "\n".join(json_lines)
            
            # Parse JSON
            data = json.loads(response_text)
            
            return AIAnalysisResult(
                is_scam=data.get("is_scam", False),
                confidence=float(data.get("confidence", 0.0)),
                risk_level=data.get("risk_level", "low"),
                primary_reason=data.get("primary_reason", "Unknown"),
                all_reasons=data.get("all_reasons", []),
                recommended_action=data.get("recommended_action", "allow"),
            )
        
        except json.JSONDecodeError as e:
            logger.error(
                "json_parse_error",
                response=response_text,
                error=str(e),
            )
            
            # Fallback: parse from text
            is_scam = "true" in response_text.lower() and "is_scam" in response_text.lower()
            
            return AIAnalysisResult(
                is_scam=is_scam,
                confidence=0.6,
                risk_level="medium",
                primary_reason="Response parsing failed",
                all_reasons=["Could not parse AI response"],
                recommended_action="delete" if is_scam else "allow",
            )
