"""
Expert agent for Liquid platform knowledge.
"""

from typing import Optional

import discord

from src.agents.base_agent import AgentConfig, BaseAgent
from src.llm import OpenRouterClient
from src.rag import HybridRetriever
from src.tools.web_search_tool import WebSearchTool
from src.utils import get_logger

logger = get_logger(__name__)


class ExpertAgent(BaseAgent):
    """
    Luma Expert Agent - specialized in Liquid platform knowledge.
    
    Features:
    - Deep Liquid documentation knowledge via RAG
    - Technical expertise on platform features
    - Citation of official sources
    - Vision support for diagrams
    - Web search for latest information
    """
    
    def __init__(
        self,
        config: AgentConfig,
        llm_client: OpenRouterClient,
        retriever: Optional[HybridRetriever] = None,
    ):
        """Initialize expert agent."""
        super().__init__(config, llm_client, retriever)
        
        # Initialize web search tool
        self.web_search = WebSearchTool()
        
        logger.info("expert_agent_initialized", web_search_enabled=True)
    
    async def _execute_tools(
        self,
        query: str,
        message: discord.Message,
    ) -> Optional[str]:
        """Execute web search tool if needed."""
        query_lower = query.lower()
        
        # Check if web search is needed
        search_keywords = [
            "search", "find", "look up", "latest", "news", "recent",
            "поиск", "найди", "найти", "последние", "новости"
        ]
        
        if any(keyword in query_lower for keyword in search_keywords):
            logger.info("expert_agent_web_search", query=query[:50])
            
            # Perform web search
            results = await self.web_search.search(query, max_results=3)
            
            if results:
                formatted = self.web_search.format_results(results)
                return formatted
        
        return None
    
    async def _format_response(
        self,
        response: str,
        context: str,
    ) -> str:
        """Format response with enhanced citations."""
        # Fix markdown
        formatted = response.replace("####", "###")
        
        # Add expert disclaimer
        if self.config.response.get("include_citations"):
            formatted += (
                "\n\n-# 🎓 **Luma Expert** | AI-generated response based on official documentation. "
                "Verify critical information in Liquid docs."
            )
        
        return formatted
    
    def get_name(self) -> str:
        """Get agent name."""
        return "Luma Expert"
    
    def get_description(self) -> str:
        """Get agent description."""
        return "Expert on Liquid platform features and documentation"
