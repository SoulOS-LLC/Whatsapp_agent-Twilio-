"""
Image Processing Service
Uses OpenAI Vision API to describe images sent via WhatsApp
"""

from openai import AsyncOpenAI
from config.config import settings
from loguru import logger
from typing import Dict, Any
import httpx


class ImageProcessor:
    """Processes and describes images using OpenAI Vision"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_VISION_MODEL
        logger.info(f"[ImageProcessor] Initialized with model: {self.model}")
    
    async def describe_image(self, image_url: str, context: str = None) -> str:
        """
        Generate a description of an image.
        
        Args:
            image_url: URL of the image to describe
            context: Optional context about why the image was sent
            
        Returns:
            Description of the image
        """
        try:
                          
            prompt = "Generate a detailed description of this image."
            
            if context:
                prompt += f" Context: {context}"
            
                                
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            
            description = response.choices[0].message.content.strip()
            
            logger.info(f"[ImageProcessor] Described image successfully")
            
            return description
            
        except Exception as e:
            logger.error(f"[ImageProcessor] Failed to describe image: {e}")
            return "Error: Could not process image"
    
    async def check_if_hindu_related(self, image_url: str) -> Dict[str, Any]:
        """
        Check if an image is related to Hinduism.
        Useful for filtering relevant images.
        
        Args:
            image_url: URL of the image
            
        Returns:
            Dictionary with is_hindu_related flag and confidence
        """
        try:
            prompt = """
            Is this image related to Hinduism? 
            Answer with YES or NO, followed by a brief reason.
            
            Examples of Hindu-related images:
            - Deities (Krishna, Rama, Shiva, Ganesha, etc.)
            - Temples and religious sites
            - Religious texts and scriptures
            - Religious symbols (Om, Swastika, etc.)
            - Religious practices and rituals
            """
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            }
                        ]
                    }
                ],
                max_tokens=150
            )
            
            result = response.choices[0].message.content.strip()
            is_related = result.upper().startswith("YES")
            
            return {
                "is_hindu_related": is_related,
                "explanation": result,
                "confidence": 80 if is_related else 70
            }
            
        except Exception as e:
            logger.error(f"[ImageProcessor] Failed to check if Hindu-related: {e}")
            return {
                "is_hindu_related": False,
                "explanation": "Error checking image",
                "confidence": 0
            }
    
    async def extract_text_from_image(self, image_url: str) -> str:
        """
        Extract text from an image (OCR).
        Useful for images of scripture pages.
        
        Args:
            image_url: URL of the image
            
        Returns:
            Extracted text
        """
        try:
            prompt = """
            Extract all visible text from this image.
            If there is no text, say "No text found".
            If the text is in Sanskrit or Hindi, transcribe it as accurately as possible.
            """
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            text = response.choices[0].message.content.strip()
            
            logger.info(f"[ImageProcessor] Extracted text from image")
            
            return text
            
        except Exception as e:
            logger.error(f"[ImageProcessor] Failed to extract text: {e}")
            return "Error: Could not extract text from image"