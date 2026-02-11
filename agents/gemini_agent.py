"""
Gemini Agent
Uses Google's Gemini API directly for general knowledge and reasoning
"""

from agents.base_agent import BaseAgent
from typing import Dict, Any
import google.generativeai as genai
from config.config import settings
from loguru import logger


class GeminiAgent(BaseAgent):
    """
    Gemini Agent queries Google's Gemini model directly.
    Used for general knowledge, reasoning, and backup responses.
    """
    
    def __init__(self):
        super().__init__(name="Gemini_AI_Agent")
        
                          
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        
                          
        self.model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
        )
        
        logger.info(f"[{self.name}] Initialized with model: {settings.GEMINI_MODEL}")
    
    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Query Gemini for an answer.
        
        Args:
            query: User's question
            context: Additional context including conversation history
            
        Returns:
            Dictionary with Gemini's response
        """
                                   
        prompt = self._build_prompt(query, context)
        
                                  
        try:
            response = self.model.generate_content(prompt)
            
            if not response.text:
                raise ValueError("Empty response from Gemini")
            
            answer = response.text.strip()
            
                                                                                
            confidence = self._estimate_confidence(answer)
            
            return {
                "response": answer,
                "confidence": confidence,
                "sources": ["Gemini AI"],
                "metadata": {
                    "model": settings.GEMINI_MODEL,
                    "prompt_length": len(prompt)
                }
            }
            
        except Exception as e:
            logger.error(f"[{self.name}] Generation failed: {e}")
            raise
    
    def _build_prompt(self, query: str, context: Dict[str, Any] = None) -> str:
        """
        Build a comprehensive prompt for Gemini.
        Includes system instructions and conversation context.
        """
                                  
        prompt_parts = [
            "You are a knowledgeable Hindu spiritual guide. Answer questions about Hindu philosophy, scriptures, and practices.",
            "",
            "Guidelines:",
            "- Provide accurate information based on Hindu scriptures",
            "- Be respectful and balanced in your responses",
            "- Cite specific scriptures when relevant",
            "- Acknowledge if you're uncertain about something",
            "",
        ]
        
                                               
        if context and "conversation_history" in context:
            history = context["conversation_history"]
            if history:
                prompt_parts.append("Previous conversation:")
                for msg in history[-5:]:                   
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    prompt_parts.append(f"{role.capitalize()}: {content}")
                prompt_parts.append("")
        
                               
        prompt_parts.append(f"User: {query}")
        prompt_parts.append("")
        prompt_parts.append("Assistant:")
        
        return "\n".join(prompt_parts)
    
    def _estimate_confidence(self, response: str) -> int:
        """
        Estimate confidence based on response characteristics.
        This is a heuristic since Gemini doesn't provide confidence scores.
        """
                         
        confidence = 70
        
                                       
        uncertainty_words = ["might", "maybe", "perhaps", "possibly", "i think", 
                            "i believe", "not sure", "unclear"]
        
        response_lower = response.lower()
        
        for word in uncertainty_words:
            if word in response_lower:
                confidence -= 10
        
                                      
        definitive_words = ["according to", "as mentioned in", "specifically", 
                           "definitely", "clearly"]
        
        for word in definitive_words:
            if word in response_lower:
                confidence += 10
        
                                 
        confidence = max(0, min(100, confidence))
        
        return confidence
    
    async def generate_with_context(
        self,
        query: str,
        scripture_context: str = None,
        web_context: str = None
    ) -> Dict[str, Any]:
        """
        Generate response with additional context from other agents.
        
        Args:
            query: User's question
            scripture_context: Context from RAG agent
            web_context: Context from web search agent
            
        Returns:
            Enhanced response considering all context
        """
        prompt_parts = [
            "You are answering a question about Hinduism. Use the provided context to give an accurate answer.",
            "",
        ]
        
        if scripture_context:
            prompt_parts.append("Scripture Context:")
            prompt_parts.append(scripture_context)
            prompt_parts.append("")
        
        if web_context:
            prompt_parts.append("Current Information:")
            prompt_parts.append(web_context)
            prompt_parts.append("")
        
        prompt_parts.append(f"Question: {query}")
        prompt_parts.append("")
        prompt_parts.append("Answer (cite sources when relevant):")
        
        prompt = "\n".join(prompt_parts)
        
        try:
            response = self.model.generate_content(prompt)
            answer = response.text.strip()
            
            return {
                "response": answer,
                "confidence": self._estimate_confidence(answer),
                "sources": ["Gemini AI with Context"],
                "metadata": {
                    "used_scripture_context": bool(scripture_context),
                    "used_web_context": bool(web_context)
                }
            }
            
        except Exception as e:
            logger.error(f"[{self.name}] Context-based generation failed: {e}")
            raise