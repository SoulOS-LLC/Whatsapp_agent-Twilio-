"""
Voice Processing Service
Uses OpenAI Whisper API to transcribe voice memos
"""

from openai import AsyncOpenAI
from config.config import settings
from loguru import logger
import httpx
import tempfile
import os


class VoiceProcessor:
    """Processes and transcribes voice memos using OpenAI Whisper"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_AUDIO_MODEL
        logger.info(f"[VoiceProcessor] Initialized with model: {self.model}")
    
    async def transcribe_voice_memo(self, audio_url: str) -> str:
        """
        Transcribe a voice memo to text.
        
        Args:
            audio_url: URL of the audio file
            
        Returns:
            Transcription text
        """
        try:
                                     
            audio_file = await self._download_audio(audio_url)
            
            if not audio_file:
                return "Error: Could not download audio file"
            
                                      
            with open(audio_file, "rb") as f:
                response = await self.client.audio.transcriptions.create(
                    model=self.model,
                    file=f,
                    response_format="text"
                )
            
            transcription = response.strip() if isinstance(response, str) else response.text.strip()
            
                                
            os.remove(audio_file)
            
            logger.info(f"[VoiceProcessor] Transcribed audio successfully")
            
            return transcription
            
        except Exception as e:
            logger.error(f"[VoiceProcessor] Failed to transcribe audio: {e}")
            return "Error: Could not transcribe audio"
    
    async def _download_audio(self, url: str) -> str:
        """
        Download audio file to temporary location.
        
        Args:
            url: URL of audio file
            
        Returns:
            Path to temporary file
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                                                                   
                ext = self._get_audio_extension(url, response.headers.get("content-type"))
                
                                       
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                    tmp_file.write(response.content)
                    return tmp_file.name
                    
        except Exception as e:
            logger.error(f"[VoiceProcessor] Failed to download audio: {e}")
            return None
    
    def _get_audio_extension(self, url: str, content_type: str = None) -> str:
        """Determine audio file extension"""
                            
        if ".mp3" in url:
            return ".mp3"
        elif ".m4a" in url:
            return ".m4a"
        elif ".ogg" in url:
            return ".ogg"
        elif ".oga" in url:
            return ".oga"
        elif ".wav" in url:
            return ".wav"
        
                               
        if content_type:
            if "mp3" in content_type:
                return ".mp3"
            elif "m4a" in content_type or "mp4" in content_type:
                return ".m4a"
            elif "ogg" in content_type:
                return ".ogg"
            elif "wav" in content_type:
                return ".wav"
        
                        
        return ".mp3"
    
    async def transcribe_with_language(self, audio_url: str, language: str = "en") -> str:
        """
        Transcribe audio with specific language hint.
        
        Args:
            audio_url: URL of audio file
            language: Language code (e.g., 'en', 'hi', 'sa')
            
        Returns:
            Transcription text
        """
        try:
            audio_file = await self._download_audio(audio_url)
            
            if not audio_file:
                return "Error: Could not download audio file"
            
            with open(audio_file, "rb") as f:
                response = await self.client.audio.transcriptions.create(
                    model=self.model,
                    file=f,
                    language=language,
                    response_format="text"
                )
            
            transcription = response.strip() if isinstance(response, str) else response.text.strip()
            
            os.remove(audio_file)
            
            logger.info(f"[VoiceProcessor] Transcribed audio with language: {language}")
            
            return transcription
            
        except Exception as e:
            logger.error(f"[VoiceProcessor] Failed to transcribe with language: {e}")
            return "Error: Could not transcribe audio"