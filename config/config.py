"""
Configuration management for WhatsApp Hindu Agent
Handles all environment variables and settings
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
              
    APP_NAME: str = "WhatsApp Hindu Agent"
    APP_VERSION: str = "1.0.0"
    
                           
    GOOGLE_API_KEY: str
    GOOGLE_PROJECT_ID: str
    GOOGLE_REGION: str = "us-central1"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    
            
    OPENAI_API_KEY: str
    
              
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str = "gcp-starter"
    PINECONE_INDEX_NAME: str = "hindu-scriptures"
    
              
    DATABASE_URL: str = "sqlite:///./hindu_agent.db"
    
           
    REDIS_URL: str = "redis://localhost:6379/0"
    
                                                    
    MANYCHAT_API_TOKEN: Optional[str] = None
    MANYCHAT_WEBHOOK_SECRET: Optional[str] = None
    
                                                         
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_NUMBER: str = "whatsapp:+14155238886"                          
    
                         
    SERPER_API_KEY: str
    
                  
    RELEVANCE_API_KEY: Optional[str] = None
    RELEVANCE_PROJECT_ID: Optional[str] = None
    RELEVANCE_REGION: str = "us-east-1"
    
            
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
                         
    MAX_CONVERSATION_HISTORY: int = 15
    MESSAGE_DELAY_SECONDS: int = 3
    MAX_MESSAGES_PER_RESPONSE: int = 6
    RESPONSE_TIMEOUT_SECONDS: int = 30
    
                        
    DAILY_QUOTE_TIME: str = "08:00"
    DAILY_QUOTE_ENABLED: bool = True
    FOLLOW_UP_ENABLED: bool = True
    
                    
    OPENAI_VISION_MODEL: str = "gpt-4-vision-preview"
    OPENAI_AUDIO_MODEL: str = "whisper-1"
    
             
    SYSTEM_PROMPT_PATH: str = "config/prompts/system_prompt.txt"
    VERIFICATION_PROMPT_PATH: str = "config/prompts/verification_prompt.txt"
    CONVERSATIONAL_PROMPT_PATH: str = "config/prompts/conversational_prompt.txt"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to avoid reading env file multiple times.
    """
    return Settings()

                     
settings = get_settings()
