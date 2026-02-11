"""
Context Agent
Manages conversation history and context retrieval
"""

from agents.base_agent import BaseAgent
from typing import Dict, Any, List
from utils.database import get_db
from utils.models import Message, Conversation, User
from config.config import settings
from loguru import logger
from datetime import datetime, timedelta


class ContextAgent(BaseAgent):
    """
    Context Agent retrieves and manages conversation history.
    Provides context for maintaining continuity in conversations.
    """
    
    def __init__(self):
        super().__init__(name="Context_Memory_Agent")
        logger.info(f"[{self.name}] Initialized")
    
    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Retrieve conversation context for the user.
        
        Args:
            query: Current user query (not directly used, but kept for interface consistency)
            context: Must include 'subscriber_id' to retrieve user's history
            
        Returns:
            Dictionary with conversation history and context
        """
        if not context or "subscriber_id" not in context:
            return {
                "response": "No conversation history available.",
                "confidence": 0,
                "sources": [],
                "metadata": {}
            }
        
        subscriber_id = context["subscriber_id"]
        
                                       
        history = await self._get_conversation_history(subscriber_id)
        
                        
        formatted_history = self._format_history(history)
        
                              
        user_info = await self._get_user_info(subscriber_id)
        
        confidence = 90 if history else 0
        
        return {
            "response": formatted_history,
            "confidence": confidence,
            "sources": ["Conversation History"],
            "metadata": {
                "num_messages": len(history),
                "user_info": user_info,
                "history": history
            }
        }
    
    async def _get_conversation_history(
        self, 
        subscriber_id: str, 
        limit: int = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent conversation history for a user.
        
        Args:
            subscriber_id: ManyChat subscriber ID
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of message dictionaries
        """
        if limit is None:
            limit = settings.MAX_CONVERSATION_HISTORY
        
        try:
            with get_db() as db:
                          
                user = db.query(User).filter(
                    User.subscriber_id == subscriber_id
                ).first()
                
                if not user:
                    return []
                
                                     
                messages = db.query(Message).filter(
                    Message.user_id == user.id
                ).order_by(
                    Message.created_at.desc()
                ).limit(limit).all()
                
                                                    
                messages.reverse()
                
                                         
                history = []
                for msg in messages:
                    history.append({
                        "role": msg.role,
                        "content": msg.content,
                        "message_type": msg.message_type,
                        "created_at": msg.created_at.isoformat(),
                        "citations": msg.citations
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"[{self.name}] Failed to retrieve history: {e}")
            return []
    
    async def _get_user_info(self, subscriber_id: str) -> Dict[str, Any]:
        """Get user information and preferences"""
        try:
            with get_db() as db:
                user = db.query(User).filter(
                    User.subscriber_id == subscriber_id
                ).first()
                
                if not user:
                    return {}
                
                return {
                    "name": user.name,
                    "timezone": user.timezone,
                    "language": user.language,
                    "last_interaction": user.last_interaction.isoformat() if user.last_interaction else None
                }
                
        except Exception as e:
            logger.error(f"[{self.name}] Failed to retrieve user info: {e}")
            return {}
    
    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        """Format conversation history into readable text"""
        if not history:
            return "No previous conversation."
        
        formatted = []
        
        for msg in history:
            role = msg["role"].capitalize()
            content = msg["content"]
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    async def save_message(
        self,
        subscriber_id: str,
        role: str,
        content: str,
        message_type: str = "text",
        agents_used: List[str] = None,
        citations: List[Dict[str, Any]] = None
    ) -> bool:
        """
        Save a message to the database.
        
        Args:
            subscriber_id: ManyChat subscriber ID
            role: 'user' or 'assistant'
            content: Message content
            message_type: Type of message (text, image, voice)
            agents_used: List of agents that were used
            citations: Scripture citations included
            
        Returns:
            Success status
        """
        try:
            with get_db() as db:
                                    
                user = db.query(User).filter(
                    User.subscriber_id == subscriber_id
                ).first()
                
                if not user:
                    user = User(subscriber_id=subscriber_id)
                    db.add(user)
                    db.flush()
                
                                         
                user.last_interaction = datetime.utcnow()
                
                                                   
                conversation = db.query(Conversation).filter(
                    Conversation.user_id == user.id,
                    Conversation.is_active == True
                ).first()
                
                if not conversation:
                    conversation = Conversation(user_id=user.id)
                    db.add(conversation)
                    db.flush()
                
                                
                message = Message(
                    conversation_id=conversation.id,
                    user_id=user.id,
                    role=role,
                    content=content,
                    message_type=message_type,
                    agents_used=agents_used,
                    citations=citations,
                    processed=True
                )
                
                db.add(message)
                
                                              
                conversation.last_message_at = datetime.utcnow()
                conversation.message_count += 1
                
                db.commit()
                
                logger.info(f"[{self.name}] Saved message for {subscriber_id}")
                return True
                
        except Exception as e:
            logger.error(f"[{self.name}] Failed to save message: {e}")
            return False
    
    async def get_recent_topics(self, subscriber_id: str, days: int = 7) -> List[str]:
        """
        Get topics discussed in recent conversations.
        Useful for proactive follow-ups.
        
        Args:
            subscriber_id: User's subscriber ID
            days: Number of days to look back
            
        Returns:
            List of topics/keywords
        """
        try:
            with get_db() as db:
                user = db.query(User).filter(
                    User.subscriber_id == subscriber_id
                ).first()
                
                if not user:
                    return []
                
                                                    
                since_date = datetime.utcnow() - timedelta(days=days)
                
                conversations = db.query(Conversation).filter(
                    Conversation.user_id == user.id,
                    Conversation.last_message_at >= since_date
                ).all()
                
                                                            
                topics = []
                for conv in conversations:
                    if conv.topics:
                        topics.extend(conv.topics)
                
                return list(set(topics))                     
                
        except Exception as e:
            logger.error(f"[{self.name}] Failed to get recent topics: {e}")
            return []