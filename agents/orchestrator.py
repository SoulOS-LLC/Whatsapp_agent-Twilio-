"""
Multi-Agent Orchestrator
Coordinates all agents and performs verification
"""

from typing import Dict, Any, List
import asyncio
from loguru import logger
from openai import AsyncOpenAI

from agents.rag_agent import RAGAgent
from agents.web_search_agent import WebSearchAgent
from agents.gemini_agent import GeminiAgent
from agents.context_agent import ContextAgent
from config.config import settings


class MultiAgentOrchestrator:
    """
    Orchestrates multiple agents to provide verified, accurate responses.
    
    Flow:
    1. Query all agents in parallel
    2. Collect all responses
    3. Verification agent cross-checks all responses
    4. Response generator makes it conversational
    """
    
    def __init__(self):
                               
        self.rag_agent = RAGAgent()
        self.web_agent = WebSearchAgent()
        self.gemini_agent = GeminiAgent()
        self.context_agent = ContextAgent()
        
                                                                    
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
                      
        self.verification_prompt = self._load_prompt("verification_prompt.txt")
        self.conversational_prompt = self._load_prompt("conversational_prompt.txt")
        
        logger.info("[Orchestrator] Multi-agent system initialized")
    
    def _load_prompt(self, filename: str) -> str:
        """Load prompt from file"""
        try:
            with open(f"config/prompts/{filename}", "r") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load prompt {filename}: {e}")
            return ""
    
    async def process_query(
        self,
        query: str,
        subscriber_id: str,
        use_all_agents: bool = True
    ) -> Dict[str, Any]:
        """
        Process a user query through the multi-agent system.
        
        Args:
            query: User's question
            subscriber_id: ManyChat subscriber ID
            use_all_agents: Whether to use all agents or just essential ones
            
        Returns:
            Dictionary containing:
                - messages: List of conversational messages to send
                - agents_used: Which agents were invoked
                - citations: Scripture citations included
                - metadata: Additional information
        """
        logger.info(f"[Orchestrator] Processing query: {query[:50]}...")
        
                       
        context = {
            "subscriber_id": subscriber_id,
            "query": query
        }
        
                                            
        agent_responses = await self._query_all_agents(query, context, use_all_agents)
        
                                                 
        verified_answer = await self._verify_responses(query, agent_responses)
        
                                        
        messages = await self._generate_conversational_response(verified_answer)
        
                                   
        citations = self._extract_citations(verified_answer)
        
                                  
        await self.context_agent.save_message(
            subscriber_id=subscriber_id,
            role="user",
            content=query,
            message_type="text"
        )
        
                                                  
        full_response = " ".join(messages)
        await self.context_agent.save_message(
            subscriber_id=subscriber_id,
            role="assistant",
            content=full_response,
            message_type="text",
            agents_used=[r["agent"] for r in agent_responses if r["success"]],
            citations=citations
        )
        
        return {
            "messages": messages,
            "agents_used": [r["agent"] for r in agent_responses if r["success"]],
            "citations": citations,
            "metadata": {
                "agent_responses": agent_responses,
                "verified_answer": verified_answer
            }
        }
    
    async def _query_all_agents(
        self,
        query: str,
        context: Dict[str, Any],
        use_all: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query all agents in parallel.
        
        Returns:
            List of agent responses
        """
        tasks = []
        
                                 
        tasks.append(self.rag_agent.execute(query, context))
        tasks.append(self.context_agent.execute(query, context))
        
        if use_all:
                                                            
            tasks.append(self.web_agent.execute(query, context))
            tasks.append(self.gemini_agent.execute(query, context))
        
                             
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
                               
        valid_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                logger.error(f"Agent {i} failed: {response}")
            else:
                valid_responses.append(response)
        
        return valid_responses
    
    async def _verify_responses(
        self,
        query: str,
        agent_responses: List[Dict[str, Any]]
    ) -> str:
        """
        Use verification agent to cross-check and synthesize responses.
        
        Args:
            query: Original user query
            agent_responses: Responses from all agents
            
        Returns:
            Verified, synthesized answer
        """
                                         
        rag_response = ""
        web_response = ""
        gemini_response = ""
        context_response = ""
        
        for response in agent_responses:
            if not response["success"]:
                continue
            
            agent_name = response["agent"]
            content = response["response"]
            
            if "RAG" in agent_name:
                rag_response = content
            elif "Web" in agent_name:
                web_response = content
            elif "Gemini" in agent_name:
                gemini_response = content
            elif "Context" in agent_name:
                context_response = content
        
                                   
        verification_prompt = self.verification_prompt.format(
            user_question=query,
            rag_response=rag_response or "No scripture database results",
            web_response=web_response or "No web search results",
            gemini_response=gemini_response or "No Gemini response",
            context=context_response or "No conversation history"
        )
        
        try:
                                          
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a verification agent that synthesizes and validates information from multiple sources."
                    },
                    {
                        "role": "user",
                        "content": verification_prompt
                    }
                ],
                temperature=0.3,                                  
                max_tokens=1024
            )
            
            verified_answer = response.choices[0].message.content.strip()
            logger.info("[Orchestrator] Verification complete")
            
            return verified_answer
            
        except Exception as e:
            logger.error(f"[Orchestrator] Verification failed: {e}")
                                                                                           
            if rag_response and "No relevant scripture" not in rag_response:
                return rag_response
            elif gemini_response:
                return gemini_response
            elif rag_response:
                return rag_response
            else:
                return "I apologize, but I couldn't generate a verified answer at this time."
    
    async def _generate_conversational_response(self, verified_answer: str) -> List[str]:
        """
        Convert verified answer into conversational messages.
        
        Args:
            verified_answer: The verified, synthesized answer
            
        Returns:
            List of short, conversational messages
        """
                      
        conversational_prompt = self.conversational_prompt.format(
            verified_answer=verified_answer
        )
        
        try:
                         
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at converting information into natural, conversational WhatsApp messages."
                    },
                    {
                        "role": "user",
                        "content": conversational_prompt
                    }
                ],
                temperature=0.8,                                            
                max_tokens=800
            )
            
            result = response.choices[0].message.content.strip()
            
                                
            messages = [msg.strip() for msg in result.split("|||") if msg.strip()]
            
                                                 
            if len(messages) > settings.MAX_MESSAGES_PER_RESPONSE:
                messages = messages[:settings.MAX_MESSAGES_PER_RESPONSE]
            
                                         
            if not messages:
                messages = [verified_answer]
            
            logger.info(f"[Orchestrator] Generated {len(messages)} conversational messages")
            
            return messages
            
        except Exception as e:
            logger.error(f"[Orchestrator] Conversational generation failed: {e}")
                                                                
            return [verified_answer]
    
    def _extract_citations(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract scripture citations from text.
        
        Looks for pattern: "As mentioned in [Book], Chapter [X], Verse [Y]"
        
        Returns:
            List of citation dictionaries
        """
        import re
        
        citations = []
        
                                    
        pattern = r"As mentioned in ([^,]+), Chapter (\d+), Verse (\d+)"
        
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            book = match.group(1).strip()
            chapter = int(match.group(2))
            verse = int(match.group(3))
            
            citations.append({
                "book": book,
                "chapter": chapter,
                "verse": verse,
                "source": f"{book}, Chapter {chapter}, Verse {verse}"
            })
        
        return citations
    
    async def quick_response(self, query: str, subscriber_id: str) -> Dict[str, Any]:
        """
        Generate a quick response using only RAG and Context agents.
        Faster but less verified. Use for simple queries.
        
        Args:
            query: User's question
            subscriber_id: User's subscriber ID
            
        Returns:
            Response dictionary
        """
        return await self.process_query(
            query=query,
            subscriber_id=subscriber_id,
            use_all_agents=False
        )