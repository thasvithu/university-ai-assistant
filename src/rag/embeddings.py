"""
Embedding Generator
Generates embeddings using sentence-transformers
"""

from typing import List, Union
from sentence_transformers import SentenceTransformer
import numpy as np
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger("embeddings")


class EmbeddingGenerator:
    """Generate embeddings for text using sentence-transformers"""
    
    def __init__(self, model_name: str = None):
        """
        Initialize embedding generator
        
        Args:
            model_name: Model name (default from config)
        """
        self.model_name = model_name or Config.EMBEDDING_MODEL
        logger.info(f"Loading embedding model: {self.model_name}")
        
        try:
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"✅ Model loaded. Embedding dimension: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text
        
        Returns:
            Embedding vector
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str], batch_size: int = 32, 
                          show_progress: bool = True) -> np.ndarray:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            show_progress: Show progress bar
        
        Returns:
            Array of embeddings
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts...")
            
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )
            
            logger.info(f"✅ Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def get_embedding_dim(self) -> int:
        """Get embedding dimension"""
        return self.embedding_dim


# Singleton instance
_embedding_generator = None


def get_embedding_generator() -> EmbeddingGenerator:
    """Get or create embedding generator singleton"""
    global _embedding_generator
    
    if _embedding_generator is None:
        _embedding_generator = EmbeddingGenerator()
    
    return _embedding_generator
