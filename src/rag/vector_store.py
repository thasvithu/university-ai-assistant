"""
Vector Store using ChromaDB
Stores and retrieves document embeddings
"""

from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings
from pathlib import Path
import sys
import uuid

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config import Config
from src.utils.logger import setup_logger
from src.rag.embeddings import get_embedding_generator

logger = setup_logger("vector_store")


class VectorStore:
    """ChromaDB-based vector store for document retrieval"""
    
    def __init__(self, collection_name: str = "university_docs"):
        """
        Initialize vector store
        
        Args:
            collection_name: Name of the collection
        """
        self.collection_name = collection_name
        
        # Initialize ChromaDB
        logger.info(f"Initializing ChromaDB at {Config.CHROMADB_PATH}")
        
        try:
            self.client = chromadb.PersistentClient(
                path=Config.CHROMADB_PATH,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "University documents and handbooks"}
            )
            
            logger.info(f"✅ Collection '{collection_name}' ready")
            logger.info(f"   Current document count: {self.collection.count()}")
            
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            raise
        
        # Get embedding generator
        self.embedding_generator = get_embedding_generator()
    
    def add_documents(self, documents: List[Dict], batch_size: int = 100):
        """
        Add documents to vector store
        
        Args:
            documents: List of document dictionaries with 'content' and 'metadata'
            batch_size: Batch size for adding documents
        """
        if not documents:
            logger.warning("No documents to add")
            return
        
        logger.info(f"Adding {len(documents)} documents to vector store...")
        
        try:
            # Process in batches
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                
                # Prepare data
                ids = []
                texts = []
                metadatas = []
                
                for doc in batch:
                    # Generate unique ID
                    doc_id = doc.get('id') or str(uuid.uuid4())
                    ids.append(doc_id)
                    
                    # Get text content
                    text = doc.get('content', '')
                    texts.append(text)
                    
                    # Get metadata
                    metadata = doc.get('metadata', {})
                    # Convert all metadata values to strings (ChromaDB requirement)
                    metadata = {k: str(v) for k, v in metadata.items()}
                    metadatas.append(metadata)
                
                # Generate embeddings
                embeddings = self.embedding_generator.generate_embeddings(
                    texts,
                    show_progress=False
                )
                
                # Add to collection
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings.tolist(),
                    documents=texts,
                    metadatas=metadatas
                )
                
                logger.info(f"  Added batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
            
            logger.info(f"✅ Successfully added {len(documents)} documents")
            logger.info(f"   Total documents in collection: {self.collection.count()}")
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    def search(self, query: str, top_k: int = None, 
              filters: Dict[str, Any] = None) -> List[Dict]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            top_k: Number of results to return
            filters: Metadata filters (e.g., {'faculty': 'FTS'})
        
        Returns:
            List of search results with documents and metadata
        """
        top_k = top_k or Config.TOP_K_RESULTS
        
        logger.info(f"Searching for: '{query}' (top_k={top_k})")
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_generator.generate_embedding(query)
            
            # Build where clause for filters
            where = None
            if filters:
                where = filters
            
            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
                where=where
            )
            
            # Format results
            formatted_results = []
            
            if results and results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    result = {
                        'id': results['ids'][0][i],
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    }
                    formatted_results.append(result)
            
            logger.info(f"✅ Found {len(formatted_results)} results")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching: {e}")
            raise
    
    def delete_collection(self):
        """Delete the entire collection"""
        logger.warning(f"Deleting collection '{self.collection_name}'")
        try:
            self.client.delete_collection(self.collection_name)
            logger.info("✅ Collection deleted")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise
    
    def get_stats(self) -> Dict:
        """Get collection statistics"""
        return {
            'collection_name': self.collection_name,
            'document_count': self.collection.count(),
            'embedding_dimension': self.embedding_generator.get_embedding_dim()
        }


# Singleton instance
_vector_store = None


def get_vector_store() -> VectorStore:
    """Get or create vector store singleton"""
    global _vector_store
    
    if _vector_store is None:
        _vector_store = VectorStore()
    
    return _vector_store
