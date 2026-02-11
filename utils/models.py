"""
Database models for WhatsApp Hindu Agent
Handles conversation history, user preferences, and message tracking
"""

from sqlalchemy import (
    Column, String, Integer, DateTime, Text, Boolean, JSON, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    """User/Subscriber model for tracking WhatsApp users"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscriber_id = Column(String(100), unique=True, nullable=False, index=True)
    phone_number = Column(String(20), nullable=True)
    name = Column(String(100), nullable=True)
    
                 
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")
    daily_quote_enabled = Column(Boolean, default=True)
    daily_quote_time = Column(String(5), default="08:00")                
    
              
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_interaction = Column(DateTime, default=datetime.utcnow)
    
                   
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.subscriber_id}>"


class Conversation(Base):
    """Conversation session model"""
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
                           
    started_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow)
    message_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
                                                  
    summary = Column(Text, nullable=True)
    topics = Column(JSON, nullable=True)                            
    
                   
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation {self.id} for User {self.user_id}>"


class Message(Base):
    """Individual message model"""
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
                     
    role = Column(String(20), nullable=False)                         
    content = Column(Text, nullable=False)
    
                      
    message_type = Column(String(20), default="text")                            
    media_url = Column(String(500), nullable=True)
    
                     
    processed = Column(Boolean, default=False)
    agents_used = Column(JSON, nullable=True)                             
    citations = Column(JSON, nullable=True)                                
    
                
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
                   
    user = relationship("User", back_populates="messages")
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message {self.id} by {self.role}>"


class ScriptureCitation(Base):
    """Track which scriptures are cited most often"""
    __tablename__ = "scripture_citations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
                      
    book = Column(String(100), nullable=False)
    chapter = Column(Integer, nullable=True)
    verse = Column(Integer, nullable=True)
    text = Column(Text, nullable=False)
    
              
    citation_count = Column(Integer, default=1)
    last_cited = Column(DateTime, default=datetime.utcnow)
    
                           
    source = Column(String(200), nullable=False, index=True)
    
    def __repr__(self):
        return f"<Citation {self.source}>"


class ProactiveMessage(Base):
    """Track proactive messages sent to users"""
    __tablename__ = "proactive_messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
                  
    message_type = Column(String(50), nullable=False)                                             
    content = Column(Text, nullable=False)
    
                
    scheduled_for = Column(DateTime, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="pending")                         
    
              
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ProactiveMessage {self.message_type} for User {self.user_id}>"


class AgentPerformance(Base):
    """Track performance metrics of different agents"""
    __tablename__ = "agent_performance"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
                
    agent_name = Column(String(50), nullable=False, index=True)                                 
    query = Column(Text, nullable=False)
    
                         
    response_time_ms = Column(Integer, nullable=False)
    success = Column(Boolean, default=True)
    confidence_score = Column(Integer, nullable=True)         
    
            
    result_length = Column(Integer, nullable=True)
    was_used_in_final_answer = Column(Boolean, default=False)
    
               
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<AgentPerformance {self.agent_name}>"