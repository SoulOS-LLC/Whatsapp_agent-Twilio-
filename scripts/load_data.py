"""
Data Loading Script
Downloads Hindu scripture datasets and loads them into Pinecone
"""

import os
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec
from loguru import logger
import time

               
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config.config import settings


class DataLoader:
    """Loads Hindu scriptures into vector database"""
    
    def __init__(self):
                                          
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        
                             
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        
                                    
        self._setup_index()
        
        logger.info("DataLoader initialized")
    
    def _setup_index(self):
        """Create Pinecone index if it doesn't exist"""
        index_name = settings.PINECONE_INDEX_NAME
        
                               
        existing_indexes = self.pc.list_indexes()
        
        if index_name not in [idx['name'] for idx in existing_indexes]:
            logger.info(f"Creating new index: {index_name}")
            
            self.pc.create_index(
                name=index_name,
                dimension=768,                              
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="gcp",
                    region="us-central1"
                )
            )
            
                                        
            while not self.pc.describe_index(index_name).status['ready']:
                time.sleep(1)
            
            logger.success(f"Index {index_name} created")
        else:
            logger.info(f"Using existing index: {index_name}")
        
        self.index = self.pc.Index(index_name)
    
    def load_bhagavad_gita(self, filepath: str):
        """
        Load Bhagavad Gita data.
        Expected format: JSON with chapters and verses
        """
        logger.info(f"Loading Bhagavad Gita from {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        passages = []
        
                              
        for chapter_num, chapter_data in data.items():
            if not isinstance(chapter_data, dict):
                continue
            
            for verse_num, verse_data in chapter_data.items():
                if not isinstance(verse_data, dict):
                    continue
                
                text = verse_data.get('text', verse_data.get('verse', ''))
                
                if text:
                    passages.append({
                        'text': text,
                        'book': 'Bhagavad Gita',
                        'chapter': int(chapter_num),
                        'verse': int(verse_num),
                        'source': f'Bhagavad Gita, Chapter {chapter_num}, Verse {verse_num}'
                    })
        
        logger.info(f"Loaded {len(passages)} verses from Bhagavad Gita")
        return passages
    
    def load_from_csv(self, filepath: str, book_name: str):
        """
        Load scripture data from CSV.
        Expected columns: text, chapter, verse (or similar)
        """
        logger.info(f"Loading {book_name} from {filepath}")
        
        df = pd.read_csv(filepath)
        passages = []
        
        for idx, row in df.iterrows():
                                                  
            text = row.get('text', row.get('verse', row.get('content', '')))
            chapter = row.get('chapter', row.get('chapter_number', None))
            verse = row.get('verse', row.get('verse_number', idx + 1))
            
            if text and isinstance(text, str) and len(text.strip()) > 0:
                passages.append({
                    'text': text.strip(),
                    'book': book_name,
                    'chapter': int(chapter) if chapter else None,
                    'verse': int(verse) if verse else None,
                    'source': f'{book_name}, Chapter {chapter}, Verse {verse}' if chapter else f'{book_name}, Verse {verse}'
                })
        
        logger.info(f"Loaded {len(passages)} passages from {book_name}")
        return passages
    
    def generate_embeddings(self, passages: List[Dict[str, Any]], batch_size: int = 100):
        """
        Generate embeddings for passages using Gemini.
        
        Args:
            passages: List of passage dictionaries
            batch_size: Number of passages to process at once
        """
        logger.info(f"Generating embeddings for {len(passages)} passages...")
        
        vectors = []
        
        for i in range(0, len(passages), batch_size):
            batch = passages[i:i + batch_size]
            
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(passages)-1)//batch_size + 1}")
            
            for passage in batch:
                try:
                                        
                    result = genai.embed_content(
                        model=settings.EMBEDDING_MODEL,
                        content=passage['text'],
                        task_type="retrieval_document"
                    )
                    
                    embedding = result['embedding']
                    
                                                 
                    vector = {
                        'id': f"{passage['book']}_{passage.get('chapter', 0)}_{passage.get('verse', 0)}_{i}",
                        'values': embedding,
                        'metadata': {
                            'text': passage['text'][:500],                           
                            'book': passage['book'],
                            'chapter': passage.get('chapter'),
                            'verse': passage.get('verse'),
                            'source': passage['source']
                        }
                    }
                    
                    vectors.append(vector)
                    
                except Exception as e:
                    logger.error(f"Failed to generate embedding for passage: {e}")
                    continue
            
                                              
            time.sleep(0.1)
        
        logger.success(f"Generated {len(vectors)} embeddings")
        return vectors
    
    def upload_to_pinecone(self, vectors: List[Dict[str, Any]], batch_size: int = 100):
        """Upload vectors to Pinecone"""
        logger.info(f"Uploading {len(vectors)} vectors to Pinecone...")
        
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            
            try:
                self.index.upsert(vectors=batch)
                logger.info(f"Uploaded batch {i//batch_size + 1}/{(len(vectors)-1)//batch_size + 1}")
            except Exception as e:
                logger.error(f"Failed to upload batch: {e}")
        
        logger.success("All vectors uploaded successfully")
    
    def load_and_process_all(self, data_dir: str = "data/religious_texts"):
        """
        Main function to load all scripture data.
        
        Args:
            data_dir: Directory containing scripture data files
        """
        all_passages = []
        
        data_path = Path(data_dir)
        
                                           
        gita_file = data_path / "bhagavad_gita.json"
        if gita_file.exists():
            passages = self.load_bhagavad_gita(str(gita_file))
            all_passages.extend(passages)
        
                                        
        csv_files = list(data_path.glob("*.csv"))

                         
        txt_files = list(data_path.glob("*.txt"))
        for txt_file in txt_files:
            book_name = txt_file.stem.replace("_", " ").replace("pg", "Scripture ").title()
            passages = self.load_from_txt(str(txt_file), book_name)
            all_passages.extend(passages)
        for csv_file in csv_files:
            book_name = csv_file.stem.replace('_', ' ').title()
            passages = self.load_from_csv(str(csv_file), book_name)
            all_passages.extend(passages)
        
        logger.info(f"Total passages loaded: {len(all_passages)}")
        
                             
        vectors = self.generate_embeddings(all_passages)
        
                            
        self.upload_to_pinecone(vectors)
        
        logger.success("Data loading complete!")


def main():
    """Main entry point"""
    logger.info("Starting data loading process...")
    
                                    
    data_dir = "data/religious_texts"
    if not os.path.exists(data_dir):
        logger.error(f"Data directory not found: {data_dir}")
        logger.info("Please download datasets and place them in data/religious_texts/")
        logger.info("See data/README.md for instructions")
        return
    
                       
    loader = DataLoader()
    
                               
    loader.load_and_process_all(data_dir)


if __name__ == "__main__":
    main()
    def load_from_txt(self, file_path: str, book_name: str):
        """Load scripture from txt file"""
        passages = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
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
