"""
RAG Agent - Retrieval Augmented Generation
Searches through the Hindu scriptures knowledge base using Pinecone
"""

from agents.base_agent import BaseAgent
from typing import Optional

from typing import Dict, Any, List
from pinecone import Pinecone
from config.config import settings
import google.generativeai as genai
from loguru import logger


class RAGAgent(BaseAgent):
    """
    RAG Agent searches the vector database for relevant scripture passages.
    Uses Gemini embeddings for semantic search.
    """
    
    def __init__(self):
        super().__init__(name="RAG_Scripture_Agent")
        
                             
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)
        
                                          
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        
        logger.info(f"[{self.name}] Initialized with Pinecone index: {settings.PINECONE_INDEX_NAME}")
    
    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Search for relevant scripture passages using semantic search.
        
        Args:
            query: User's question
            context: Additional context (not used for RAG search currently)
            
        Returns:
            Dictionary with relevant scripture passages and citations
        """
                                                       
        embedding = genai.embed_content(
            model=settings.GEMINI_EMBEDDING_MODEL,
            content=query,
            task_type="retrieval_query"
        )
        
        query_embedding = embedding['embedding']
        
                                              
        results = self.index.query(
            vector=query_embedding,
            top_k=5,                                    
            include_metadata=True
        )
        
                         
        passages = []
        sources = []
        
        for match in results.matches:
            if match.score > 0.7:                                        
                metadata = match.metadata
                
                passage = {
                    "text": metadata.get("text", ""),
                    "source": metadata.get("source", ""),
                    "book": metadata.get("book", ""),
                    "chapter": metadata.get("chapter"),
                    "verse": metadata.get("verse"),
                    "score": match.score
                }
                
                passages.append(passage)
                sources.append(metadata.get("source", "Unknown"))
        
                         
        if passages:
            response = self._format_response(passages)
            confidence = int(passages[0]["score"] * 100)                                 
        else:
            response = "No relevant scripture passages found for this query."
            confidence = 0
        
        return {
            "response": response,
            "confidence": confidence,
            "sources": sources,
            "metadata": {
                "num_passages": len(passages),
                "passages": passages
            }
        }
    
    def _format_response(self, passages: List[Dict[str, Any]]) -> str:
        """Format scripture passages into a readable response"""
        formatted = []
        
        for passage in passages:
            source = passage["source"]
            text = passage["text"]
            
            formatted.append(f"{source}:\n{text}")
        
        return "\n\n".join(formatted)
    
    async def search_specific_scripture(
        self, 
        book: str, 
        chapter: Optional[int] = None, 
        verse: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search for a specific scripture reference.
        
        Args:
            book: Name of the scripture (e.g., "Bhagavad Gita")
            chapter: Chapter number (optional)
            verse: Verse number (optional)
            
        Returns:
            The specific scripture passage if found
        """
                                          
        filter_dict = {"book": {"$eq": book}}
        
        if chapter is not None:
            filter_dict["chapter"] = {"$eq": chapter}
        
        if verse is not None:
            filter_dict["verse"] = {"$eq": verse}
        
                                                                                      
        results = self.index.query(
            vector=[0.0] * 768,                
            filter=filter_dict,
            top_k=1,
            include_metadata=True
        )
        
        if results.matches:
            match = results.matches[0]
            metadata = match.metadata
            
            return {
                "found": True,
                "text": metadata.get("text", ""),
                "source": metadata.get("source", ""),
                "book": metadata.get("book", ""),
                "chapter": metadata.get("chapter"),
                "verse": metadata.get("verse")
            }
        
        return {"found": False}