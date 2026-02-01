"""
Web search tool using DuckDuckGo for agent searches.
"""

from typing import Any, Dict, List, Optional

import httpx

from src.utils import get_logger

logger = get_logger(__name__)


class WebSearchTool:
    """
    Tool for performing web searches using DuckDuckGo API.
    """
    
    def __init__(self):
        """Initialize web search tool."""
        self.base_url = "https://api.duckduckgo.com/"
        self.timeout = 10.0
        logger.info("web_search_tool_initialized")
    
    async def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Perform web search.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results
        """
        logger.info("web_search_executing", query=query[:50])
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # DuckDuckGo Instant Answer API
                params = {
                    "q": query,
                    "format": "json",
                    "no_html": 1,
                    "skip_disambig": 1,
                }
                
                response = await client.get(
                    self.base_url,
                    params=params,
                )
                response.raise_for_status()
                data = response.json()
                
                results = []
                
                # Extract instant answer
                if data.get("Abstract"):
                    results.append({
                        "title": data.get("Heading", "Quick Answer"),
                        "snippet": data.get("Abstract", ""),
                        "url": data.get("AbstractURL", ""),
                        "source": data.get("AbstractSource", "DuckDuckGo"),
                    })
                
                # Extract related topics
                for topic in data.get("RelatedTopics", [])[:max_results - 1]:
                    if isinstance(topic, dict) and "Text" in topic:
                        results.append({
                            "title": topic.get("Text", "")[:100],
                            "snippet": topic.get("Text", ""),
                            "url": topic.get("FirstURL", ""),
                            "source": "DuckDuckGo",
                        })
                
                logger.info(
                    "web_search_completed",
                    query=query[:50],
                    results_count=len(results),
                )
                
                return results[:max_results]
                
        except httpx.TimeoutException:
            logger.error("web_search_timeout", query=query[:50])
            return [{
                "title": "Search Timeout",
                "snippet": "The search request timed out. Please try again.",
                "url": "",
                "source": "Error",
            }]
        except Exception as e:
            logger.error(
                "web_search_error",
                query=query[:50],
                error=str(e),
            )
            return [{
                "title": "Search Error",
                "snippet": f"An error occurred during search: {str(e)}",
                "url": "",
                "source": "Error",
            }]
    
    def format_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Format search results for display.
        
        Args:
            results: List of search results
            
        Returns:
            Formatted string
        """
        if not results:
            return "No search results found."
        
        formatted = "🔍 **Web Search Results:**\n\n"
        
        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            snippet = result.get("snippet", "")
            url = result.get("url", "")
            source = result.get("source", "Unknown")
            
            formatted += f"**{i}. {title}**\n"
            if snippet:
                formatted += f"{snippet[:200]}{'...' if len(snippet) > 200 else ''}\n"
            if url:
                formatted += f"🔗 [{source}]({url})\n"
            formatted += "\n"
        
        return formatted.strip()
