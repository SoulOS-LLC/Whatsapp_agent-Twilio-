
"""
Twilio Service
Handles interactions with Twilio API for WhatsApp
"""

from twilio.rest import Client
from typing import Dict, Any, List
from config.config import settings
from loguru import logger
import asyncio

class TwilioService:
    """Service for interacting with Twilio WhatsApp API"""
    
    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_number = settings.TWILIO_FROM_NUMBER
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("[TwilioService] Initialized")
        else:
            self.client = None
            logger.warning("[TwilioService] Missing credentials - functionality disabled")
    
    async def send_message(self, to_number: str, body: str) -> bool:
        """
        Send a WhatsApp message via Twilio.
        
        Args:
            to_number: Recipient's WhatsApp number (e.g., "whatsapp:+1234567890")
            body: Message content
            
        Returns:
            Success status
        """
        if not self.client:
            logger.error("[TwilioService] Cannot send message: Client not initialized")
            return False
            
        try:
                                                                        
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    from_=self.from_number,
                    body=body,
                    to=to_number
                )
            )
            logger.info(f"[TwilioService] Sent message to {to_number}")
            return True
            
        except Exception as e:
            logger.error(f"[TwilioService] Failed to send message: {e}")
            return False

    def _split_message(self, message: str, max_length: int = 1500) -> List[str]:
        """
        Split a message into chunks of max_length.
        Tries to split at newlines or spaces to keep text readable.
        """
        if len(message) <= max_length:
            return [message]
            
        chunks = []
        while len(message) > max_length:
            # Find the last space or newline within the limit
            split_idx = message.rfind(' ', 0, max_length)
            newline_idx = message.rfind('\n', 0, max_length)
            
            # Prefer splitting at newline if available and reasonably close to the end
            if newline_idx > max_length * 0.5:
                split_idx = newline_idx
            
            # If no suitable split point found, hard split
            if split_idx == -1:
                split_idx = max_length
                
            chunks.append(message[:split_idx])
            message = message[split_idx:].lstrip()
            
        if message:
            chunks.append(message)
            
        return chunks

    async def send_messages(self, to_number: str, messages: List[str]) -> bool:
        """
        Send multiple messages sequentially.
        Handles splitting of long messages and adds human-like delays.
        """
        # Flatten and split all messages
        final_messages = []
        for msg in messages:
            final_messages.extend(self._split_message(msg))
            
        for msg in final_messages:
            # Calculate a human-like typing delay
            # Average typing speed is about 200-300 characters per minute
            # Let's say 5 characters per second + some base reaction time
            typing_delay = min(len(msg) * 0.05, 3.0) # max 3 seconds delay
            if typing_delay > 0.5:
                logger.info(f"[TwilioService] Simulating typing for {typing_delay:.2f}s...")
                await asyncio.sleep(typing_delay)
            
            success = await self.send_message(to_number, msg)
            if not success:
                return False
            
            # Small fixed delay after sending to ensure order and readability
            await asyncio.sleep(0.8)
            
        return True
