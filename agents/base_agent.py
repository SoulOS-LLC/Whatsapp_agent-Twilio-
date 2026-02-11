"""
Base Agent class
All specialized agents inherit from this base class
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from loguru import logger
import time


class BaseAgent(ABC):
    """Base class for all agents in the multi-agent system"""
    
    def __init__(self, name: str):
        self.name = name
        self.response_time_ms: Optional[int] = None
        self.success: bool = False
        self.error: Optional[str] = None
        
    @abstractmethod
    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a query and return results.
        
        Args:
            query: The user's question/input
            context: Additional context (conversation history, user data, etc.)
            
        Returns:
            Dictionary containing:
                - response: The agent's response
                - confidence: Confidence score (0-100)
                - sources: List of sources used
                - metadata: Additional metadata
        """
        pass
    
    async def execute(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the agent with timing and error handling.
        Wraps the process() method.
        """
        start_time = time.time()
        
        try:
            logger.info(f"[{self.name}] Starting processing...")
            result = await self.process(query, context or {})
            
            self.response_time_ms = int((time.time() - start_time) * 1000)
            self.success = True
            
            logger.success(f"[{self.name}] Completed in {self.response_time_ms}ms")
            
            return {
                "agent": self.name,
                "success": True,
                "response": result.get("response", ""),
                "confidence": result.get("confidence", 50),
                "sources": result.get("sources", []),
                "metadata": result.get("metadata", {}),
                "response_time_ms": self.response_time_ms,
                "error": None
            }
            
        except Exception as e:
            self.response_time_ms = int((time.time() - start_time) * 1000)
            self.success = False
            self.error = str(e)
            
            logger.error(f"[{self.name}] Failed: {e}")
            
            return {
                "agent": self.name,
                "success": False,
                "response": "",
                "confidence": 0,
                "sources": [],
                "metadata": {},
                "response_time_ms": self.response_time_ms,
                "error": str(e)
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for this agent"""
        return {
            "agent": self.name,
            "response_time_ms": self.response_time_ms,
            "success": self.success,
            "error": self.error
        }