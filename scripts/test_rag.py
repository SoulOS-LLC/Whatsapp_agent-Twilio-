
import asyncio
import sys
import os

                              
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.rag_agent import RAGAgent
from loguru import logger

async def test_rag():
    print("🕉️  Testing RAG Agent...")
    print("=======================")
    
    agent = RAGAgent()
    
                
    query = "What does the Gita say about duty?"
    print(f"\nQuery: {query}")
    print("Searching vector database...")
    
    result = await agent.execute(query)
    
    if result["success"]:
        print("\n✅ Success!")
        print(f"Confidence: {result['confidence']}%")
        print("\nResponse:")
        print(result['response'])
        
        print("\nSources:")
        for source in result['sources']:
            print(f"- {source}")
            
        print("\nMetadata:")
        meta = result.get('metadata', {})
        print(f"Passages found: {meta.get('num_passages', 0)}")
    else:
        print(f"\n❌ Failed: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_rag())
