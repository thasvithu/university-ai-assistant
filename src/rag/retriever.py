"""
Document Retriever
Handles intelligent retrieval of relevant documents
"""

from typing import List, Dict, Optional
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config import Config
from src.utils.logger import setup_logger
from src.rag.vector_store import get_vector_store

logger = setup_logger("retriever")


class DocumentRetriever:
    """Intelligent document retrieval system"""
    
    def __init__(self):
        """Initialize retriever"""
        self.vector_store = get_vector_store()
        logger.info("Document retriever initialized")
    
    def retrieve(self, query: str, top_k: int = None, 
                faculty: Optional[str] = None,
                source_type: Optional[str] = None) -> List[Dict]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            faculty: Filter by faculty (FTS, FAS, FBS)
            source_type: Filter by source type (web, handbook_pdf, faculty_web)
        
        Returns:
            List of relevant documents with metadata
        """
        top_k = top_k or Config.TOP_K_RESULTS
        
        logger.info(f"Retrieving documents for query: '{query}'")
        
        # Build filters
        filters = {}
        if faculty:
            filters['faculty'] = faculty
        if source_type:
            filters['source_type'] = source_type
        
        # Search vector store
        results = self.vector_store.search(
            query=query,
            top_k=top_k,
            filters=filters if filters else None
        )
        
        # Enhance results with relevance scores
        enhanced_results = []
        for i, result in enumerate(results):
            enhanced_result = {
                'rank': i + 1,
                'content': result['document'],
                'metadata': result['metadata'],
                'distance': result.get('distance', 0),
                'relevance_score': self._calculate_relevance_score(result)
            }
            enhanced_results.append(enhanced_result)
        
        logger.info(f"✅ Retrieved {len(enhanced_results)} documents")
        
        return enhanced_results
    
    def _calculate_relevance_score(self, result: Dict) -> float:
        """
        Calculate relevance score from distance
        
        Args:
            result: Search result
        
        Returns:
            Relevance score (0-1, higher is better)
        """
        distance = result.get('distance', 1.0)
        
        # Convert distance to similarity score
        # Lower distance = higher similarity
        # Using exponential decay
        relevance = max(0, 1 - (distance / 2))
        
        return round(relevance, 3)
    
    def retrieve_with_context(self, query: str, top_k: int = None,
                            faculty: Optional[str] = None) -> Dict:
        """
        Retrieve documents with formatted context for LLM
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            faculty: Filter by faculty
        
        Returns:
            Dictionary with context and sources
        """
        results = self.retrieve(query, top_k, faculty)
        
        # Format context for LLM
        context_parts = []
        sources = []
        
        for i, result in enumerate(results, 1):
            content = result['content']
            metadata = result['metadata']
            
            # Add source reference
            source_ref = f"[Source {i}]"
            
            # Build context entry
            context_entry = f"{source_ref}\n{content}\n"
            context_parts.append(context_entry)
            
            # Build source info
            source_info = {
                'id': i,
                'title': metadata.get('title', 'Untitled'),
                'url': metadata.get('url', ''),
                'faculty': metadata.get('faculty', ''),
                'source_type': metadata.get('source_type', ''),
                'relevance_score': result['relevance_score']
            }
            sources.append(source_info)
        
        context = "\n\n".join(context_parts)
        
        return {
            'context': context,
            'sources': sources,
            'num_sources': len(sources)
        }


# Singleton instance
_retriever = None


def get_retriever() -> DocumentRetriever:
    """Get or create retriever singleton"""
    global _retriever
    
    if _retriever is None:
        _retriever = DocumentRetriever()
    
    return _retriever
