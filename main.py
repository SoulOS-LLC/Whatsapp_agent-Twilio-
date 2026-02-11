"""
Main FastAPI Application
WhatsApp Hindu Spiritual Agent
"""

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio

from config.config import settings
from utils.database import init_db, check_db_health
from agents.orchestrator import MultiAgentOrchestrator
from services.image_service import ImageProcessor
from services.voice_service import VoiceProcessor
from services.manychat_service import ManyChatService
from services.twilio_service import TwilioService
from loguru import logger
from fastapi import Form

                   
logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="10 days",
    level=settings.LOG_LEVEL
)

                        
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-agent WhatsApp bot for Hindu spiritual guidance"
)

                     
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

                                               
orchestrator: Optional[MultiAgentOrchestrator] = None
image_processor: Optional[ImageProcessor] = None
voice_processor: Optional[VoiceProcessor] = None
manychat_service: Optional[ManyChatService] = None
twilio_service: Optional[TwilioService] = None


                                      
class WebhookData(BaseModel):
    """ManyChat webhook data model"""
    subscriber_id: str
    user_messages: Optional[str] = ""
    last_text_input: Optional[str] = ""
    
    class Config:
        extra = "allow"                           


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global orchestrator, image_processor, voice_processor, manychat_service, twilio_service
    
    logger.info("Starting WhatsApp Hindu Agent...")
    
                         
    try:
        init_db()
        logger.success("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
                         
    try:
        orchestrator = MultiAgentOrchestrator()
        image_processor = ImageProcessor()
        voice_processor = VoiceProcessor()
        manychat_service = ManyChatService()
        twilio_service = TwilioService()
        
        logger.success("All services initialized successfully")
    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        raise


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "connected" if check_db_health() else "disconnected"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    db_healthy = check_db_health()
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "services": {
            "database": db_healthy,
            "orchestrator": orchestrator is not None,
            "image_processor": image_processor is not None,
            "voice_processor": voice_processor is not None,
            "manychat": manychat_service is not None,
            "twilio": twilio_service is not None
        }
    }


@app.post("/webhook/twilio")
async def twilio_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Webhook endpoint for Twilio WhatsApp.
    Receives message, processes it, and replies.
    """
    try:
        logger.info(f"Received Twilio message from {From}: {Body}")
        
                                                                  
        background_tasks.add_task(
            process_and_respond_twilio,
            from_number=From,
            message_body=Body
        )
        
        return {"status": "processing"}
        
    except Exception as e:
        logger.error(f"Twilio webhook error: {e}")
                                                            
        return {"status": "error", "message": str(e)}


async def process_and_respond_twilio(from_number: str, message_body: str):
    """
    Process Twilio message and send response.
    """
    try:
                                                           
        subscriber_id = from_number.replace("whatsapp:", "")
        
                                                  
        result = await orchestrator.process_query(
            query=message_body,
            subscriber_id=subscriber_id
        )
        
        messages = result["messages"]
        
                                        
        await twilio_service.send_messages(
            to_number=from_number,
            messages=messages
        )
        
    except Exception as e:
        logger.error(f"Error processing Twilio message: {e}")


@app.post("/webhook/manychat")
async def manychat_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Main webhook endpoint for ManyChat.
    This is called by Make.com after it processes images/voice.
    
    Flow:
    1. Receive message from ManyChat (via Make.com)
    2. Process with multi-agent orchestrator
    3. Send responses back to ManyChat
    """
    try:
                               
        data = await request.json()
        logger.info(f"Received webhook data: {data.keys()}")
        
                            
        subscriber_id = data.get("subscriber_id")
        user_messages = data.get("user_messages", data.get("AI_user_messages", ""))
        
        if not subscriber_id:
            raise HTTPException(status_code=400, detail="Missing subscriber_id")
        
        if not user_messages:
            raise HTTPException(status_code=400, detail="Missing user_messages")
        
        logger.info(f"Processing query from {subscriber_id}: {user_messages[:100]}...")
        
                                                                 
        background_tasks.add_task(
            process_and_respond,
            subscriber_id=subscriber_id,
            user_messages=user_messages
        )
        
        return {"status": "processing"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_and_respond(subscriber_id: str, user_messages: str):
    """
    Process user message and send response.
    Runs in background.
    """
    try:
                                                  
        result = await orchestrator.process_query(
            query=user_messages,
            subscriber_id=subscriber_id
        )
        
        messages = result["messages"]
        
                                      
        answers = {}
        for i, msg in enumerate(messages[:settings.MAX_MESSAGES_PER_RESPONSE], 1):
            answers[f"AI_answer_{i}"] = msg
        
                          
        success = await manychat_service.set_answers(
            subscriber_id=subscriber_id,
            answers=answers
        )
        
        if success:
                                                     
                                                          
                                     
            logger.success(f"Sent {len(messages)} messages to {subscriber_id}")
        else:
            logger.error(f"Failed to send messages to {subscriber_id}")
        
    except Exception as e:
        logger.error(f"Error processing and responding: {e}")


@app.post("/webhook/process-image")
async def process_image(request: Request):
    """
    Endpoint for processing images.
    Called by Make.com when an image is detected.
    """
    try:
        data = await request.json()
        
        image_url = data.get("image_url")
        context = data.get("context", "")
        
        if not image_url:
            raise HTTPException(status_code=400, detail="Missing image_url")
        
                        
        description = await image_processor.describe_image(image_url, context)
        
        return {
            "description": description,
            "formatted": f"[Image: {description}]"
        }
        
    except Exception as e:
        logger.error(f"Image processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook/process-voice")
async def process_voice(request: Request):
    """
    Endpoint for processing voice memos.
    Called by Make.com when a voice memo is detected.
    """
    try:
        data = await request.json()
        
        audio_url = data.get("audio_url")
        language = data.get("language", "en")
        
        if not audio_url:
            raise HTTPException(status_code=400, detail="Missing audio_url")
        
                               
        if language and language != "en":
            transcription = await voice_processor.transcribe_with_language(
                audio_url,
                language
            )
        else:
            transcription = await voice_processor.transcribe_voice_memo(audio_url)
        
        return {
            "transcription": transcription,
            "formatted": f"[Voice: {transcription}]"
        }
        
    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query")
async def direct_query(
    query: str,
    subscriber_id: str,
    quick: bool = False
):
    """
    Direct query endpoint for testing.
    Bypasses ManyChat and returns response directly.
    """
    try:
        if quick:
            result = await orchestrator.quick_response(query, subscriber_id)
        else:
            result = await orchestrator.process_query(query, subscriber_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Direct query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversation-history/{subscriber_id}")
async def get_conversation_history(subscriber_id: str, limit: int = 10):
    """Get conversation history for a user"""
    try:
        from agents.context_agent import ContextAgent
        
        context_agent = ContextAgent()
        history = await context_agent._get_conversation_history(subscriber_id, limit)
        
        return {
            "subscriber_id": subscriber_id,
            "history": history,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )