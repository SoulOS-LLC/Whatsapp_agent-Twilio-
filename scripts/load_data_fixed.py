"""
Data Loading Script for Hindu Scriptures
Loads scripture data and uploads to Pinecone vector database
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any
import time
from loguru import logger
from pinecone import Pinecone, ServerlessSpec
import google.generativeai as genai
from config.config import settings

class DataLoader:
    def __init__(self):
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.index = self._setup_index()
        logger.info("DataLoader initialized")
    
    def _setup_index(self):
        index_name = settings.PINECONE_INDEX_NAME
        
        if index_name not in [index.name for index in self.pc.list_indexes()]:
            self.pc.create_index(
                name=index_name,
                dimension=768,
                metric='cosine',
                spec=ServerlessSpec(cloud='gcp', region='us-central1')
            )
            logger.info(f"Created new index: {index_name}")
        else:
            logger.info(f"Using existing index: {index_name}")
        
        return self.pc.Index(index_name)
    
    def load_from_txt(self, file_path: str, book_name: str):
        passages = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                
                for idx, text in enumerate(paragraphs[:500]):
                    if len(text) > 100:
                        passages.append({
                            'book': book_name,
                            'text': text,
                            'chapter': None,
                            'verse': idx + 1
                        })
            logger.info(f"Loaded {len(passages)} passages from {book_name}")
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
        return passages
    
    def generate_embeddings(self, passages: List[Dict[str, Any]]):
        logger.info(f"Generating embeddings for {len(passages)} passages...")
        vectors = []
        
        for i, passage in enumerate(passages):
            try:
                text = f"{passage['book']}: {passage['text']}"
                
                result = genai.embed_content(
                    model=settings.GEMINI_EMBEDDING_MODEL,
                    content=text,
                    task_type="retrieval_document"
                )
                
                vector_id = f"{passage['book']}_{passage.get('chapter', 0)}_{passage.get('verse', i)}"
                
                vectors.append({
                    'id': vector_id,
                    'values': result['embedding'],
                    'metadata': {
                        'book': passage['book'],
                        'chapter': passage.get('chapter'),
                        'verse': passage.get('verse'),
                        'text': passage['text'][:1000]
                    }
                })
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Generated {i + 1}/{len(passages)} embeddings")
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error generating embedding for passage {i}: {e}")
                continue
        
        logger.success(f"Generated {len(vectors)} embeddings")
        return vectors
    
    def upload_to_pinecone(self, vectors: List[Dict[str, Any]]):
        logger.info(f"Uploading {len(vectors)} vectors to Pinecone...")
        
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)
            logger.info(f"Uploaded batch {i//batch_size + 1}/{(len(vectors)-1)//batch_size + 1}")
            time.sleep(1)
        
        logger.success("All vectors uploaded successfully")
    
    def load_and_process_all(self, data_dir: str = "data/religious_texts"):
        all_passages = []
        data_path = Path(data_dir)
        
        txt_files = list(data_path.glob("*.txt"))
        for txt_file in txt_files:
            book_name = txt_file.stem.replace("_", " ").replace("pg", "Scripture ").title()
            passages = self.load_from_txt(str(txt_file), book_name)
            all_passages.extend(passages)
        
        logger.info(f"Total passages loaded: {len(all_passages)}")
        
        if len(all_passages) > 0:
            vectors = self.generate_embeddings(all_passages)
            self.upload_to_pinecone(vectors)
        else:
            logger.warning("No passages loaded!")
        
        logger.success("Data loading complete!")

def main():
    logger.info("Starting data loading process...")
    loader = DataLoader()
    data_dir = "data/religious_texts"
    loader.load_and_process_all(data_dir)

if __name__ == "__main__":
    main()
