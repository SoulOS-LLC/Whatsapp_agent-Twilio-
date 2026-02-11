"""
Web Search Agent
Searches the web for current information using Serper API
"""

from agents.base_agent import BaseAgent
from typing import Dict, Any, List
import httpx
from config.config import settings
from loguru import logger


class WebSearchAgent(BaseAgent):
    """
    Web Search Agent uses Serper API to search the web for:
    - Current events related to Hinduism
    - Festival dates and information
    - Temple information
    - Fact verification
    """
    
    def __init__(self):
        super().__init__(name="Web_Search_Agent")
        self.api_url = "https://google.serper.dev/search"
        self.api_key = settings.SERPER_API_KEY
        
        logger.info(f"[{self.name}] Initialized with Serper API")
    
    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Search the web for information related to the query.
        
        Args:
            query: User's question or search terms
            context: Additional context (can include search filters)
            
        Returns:
            Dictionary with search results and sources
        """
                                                  
        enhanced_query = self._enhance_query(query, context)
        
                        
        search_results = await self._search(enhanced_query)
        
        if not search_results:
            return {
                "response": "No web results found for this query.",
                "confidence": 0,
                "sources": [],
                "metadata": {}
            }
        
                                    
        response = self._format_results(search_results)
        sources = self._extract_sources(search_results)
        
                                                         
        confidence = min(len(search_results) * 20, 100)
        
        return {
            "response": response,
            "confidence": confidence,
            "sources": sources,
            "metadata": {
                "num_results": len(search_results),
                "query_used": enhanced_query,
                "raw_results": search_results[:3]                            
            }
        }
    
    def _enhance_query(self, query: str, context: Dict[str, Any] = None) -> str:
        """
        Enhance the search query for better results.
        Add relevant keywords for Hindu-related searches.
        """
                                                        
        query_lower = query.lower()
        
        hindu_keywords = ["hindu", "hinduism", "vedic", "sanskrit", "bhagavad", "gita", 
                         "veda", "upanishad", "purana", "ramayana", "mahabharata"]
        
        has_hindu_keyword = any(keyword in query_lower for keyword in hindu_keywords)
        
                                           
        if not has_hindu_keyword:
            enhanced = f"{query} hinduism"
        else:
            enhanced = query
        
        return enhanced
    
    async def _search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Perform the actual web search using Serper API"""
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": query,
            "num": num_results
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                
                data = response.json()
                
                                         
                results = []
                
                                            
                if "organic" in data:
                    for item in data["organic"]:
                        results.append({
                            "title": item.get("title", ""),
                            "snippet": item.get("snippet", ""),
                            "link": item.get("link", ""),
                            "position": item.get("position", 0)
                        })
                
                                                
                if "knowledgeGraph" in data:
                    kg = data["knowledgeGraph"]
                    results.insert(0, {
                        "title": kg.get("title", ""),
                        "snippet": kg.get("description", ""),
                        "link": kg.get("website", ""),
                        "position": 0,
                        "type": "knowledge_graph"
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"[{self.name}] Search failed: {e}")
            return []
    
    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format search results into readable text"""
        if not results:
            return "No results found."
        
        formatted = []
        
        for i, result in enumerate(results[:5], 1):                 
            title = result.get("title", "No title")
            snippet = result.get("snippet", "No description")
            
            formatted.append(f"{i}. {title}\n{snippet}")
        
        return "\n\n".join(formatted)
    
    def _extract_sources(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract source URLs from results"""
        sources = []
        
        for result in results[:5]:
            link = result.get("link", "")
            if link:
                sources.append(link)
        
        return sources
    
    async def search_specific(
        self, 
        query: str, 
        site: str = None, 
        date_range: str = None
    ) -> Dict[str, Any]:
        """
        Perform a specific search with filters.
        
        Args:
            query: Search query
            site: Specific site to search (e.g., "wikipedia.org")
            date_range: Date range filter (e.g., "past_month", "past_year")
            
        Returns:
            Search results
        """
        enhanced_query = query
        
        if site:
            enhanced_query = f"site:{site} {query}"
        
        results = await self._search(enhanced_query)
        
        return {
            "response": self._format_results(results),
            "confidence": min(len(results) * 20, 100),
            "sources": self._extract_sources(results),
            "metadata": {
                "num_results": len(results),
                "query_used": enhanced_query
            }
        }