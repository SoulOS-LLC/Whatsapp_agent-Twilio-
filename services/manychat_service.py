"""
ManyChat Service
Handles all interactions with ManyChat API
"""

import httpx
from typing import Dict, Any, List
from config.config import settings
from loguru import logger


class ManyChatService:
    """Service for interacting with ManyChat API"""
    
    def __init__(self):
        self.api_url = "https://api.manychat.com/fb"
        self.api_token = settings.MANYCHAT_API_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        logger.info("[ManyChatService] Initialized")
    
    async def set_custom_fields(
        self,
        subscriber_id: str,
        fields: Dict[str, str]
    ) -> bool:
        """
        Set custom fields for a subscriber.
        
        Args:
            subscriber_id: ManyChat subscriber ID
            fields: Dictionary of field names and values
            
        Returns:
            Success status
        """
        url = f"{self.api_url}/subscriber/setCustomFields"
        
        payload = {
            "subscriber_id": subscriber_id,
            "fields": [
                {"field_name": key, "field_value": value}
                for key, value in fields.items()
            ]
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                
                logger.info(f"[ManyChatService] Set custom fields for {subscriber_id}")
                return True
                
        except Exception as e:
            logger.error(f"[ManyChatService] Failed to set custom fields: {e}")
            return False
    
    async def send_flow(self, subscriber_id: str, flow_ns: str) -> bool:
        """
        Trigger a ManyChat flow for a subscriber.
        
        Args:
            subscriber_id: ManyChat subscriber ID
            flow_ns: Flow namespace/ID
            
        Returns:
            Success status
        """
        url = f"{self.api_url}/subscriber/sendFlow"
        
        payload = {
            "subscriber_id": subscriber_id,
            "flow_ns": flow_ns
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                
                logger.info(f"[ManyChatService] Triggered flow {flow_ns} for {subscriber_id}")
                return True
                
        except Exception as e:
            logger.error(f"[ManyChatService] Failed to send flow: {e}")
            return False
    
    async def send_content(
        self,
        subscriber_id: str,
        messages: List[Dict[str, Any]]
    ) -> bool:
        """
        Send content directly to a subscriber.
        
        Args:
            subscriber_id: ManyChat subscriber ID
            messages: List of message objects
            
        Returns:
            Success status
        """
        url = f"{self.api_url}/subscriber/sendContent"
        
        payload = {
            "subscriber_id": subscriber_id,
            "data": {
                "version": "v2",
                "content": {
                    "messages": messages
                }
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                
                logger.info(f"[ManyChatService] Sent content to {subscriber_id}")
                return True
                
        except Exception as e:
            logger.error(f"[ManyChatService] Failed to send content: {e}")
            return False
    
    async def get_subscriber_info(self, subscriber_id: str) -> Dict[str, Any]:
        """
        Get subscriber information.
        
        Args:
            subscriber_id: ManyChat subscriber ID
            
        Returns:
            Subscriber information
        """
        url = f"{self.api_url}/subscriber/getInfo"
        
        params = {"subscriber_id": subscriber_id}
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=self.headers
                )
                response.raise_for_status()
                
                data = response.json()
                
                logger.info(f"[ManyChatService] Retrieved info for {subscriber_id}")
                return data.get("data", {})
                
        except Exception as e:
            logger.error(f"[ManyChatService] Failed to get subscriber info: {e}")
            return {}
    
    async def set_answers(
        self,
        subscriber_id: str,
        answers: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Set multiple answer fields at once.
        This is the main method used for sending agent responses.
        
        Args:
            subscriber_id: ManyChat subscriber ID
            answers: Dictionary with AI_answer_1 through AI_answer_6
            
        Returns:
            Response from API
        """
                                          
        fields = {}
        for key, value in answers.items():
            if value:                                 
                fields[key] = value
        
        return await self.set_custom_fields(subscriber_id, fields)
    
    async def clear_fields(
        self,
        subscriber_id: str,
        field_names: List[str]
    ) -> bool:
        """
        Clear specific custom fields.
        
        Args:
            subscriber_id: ManyChat subscriber ID
            field_names: List of field names to clear
            
        Returns:
            Success status
        """
                                        
        fields = {name: "" for name in field_names}
        
        return await self.set_custom_fields(subscriber_id, fields)