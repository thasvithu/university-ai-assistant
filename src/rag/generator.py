"""
Response Generator
Combines retrieval and LLM to generate responses
"""

from typing import Dict, Optional
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config import Config
from src.utils.logger import setup_logger
from src.rag.retriever import get_retriever
from src.llm.api_manager import get_api_manager
from src.llm.prompts import get_system_prompt, format_query_prompt

logger = setup_logger("generator")


class ResponseGenerator:
    """Generate responses using RAG pipeline"""
    
    def __init__(self):
        """Initialize generator"""
        self.retriever = get_retriever()
        self.api_manager = get_api_manager()
        self.system_prompt = get_system_prompt()
        
        logger.info("Response generator initialized")
    
    def generate(self, query: str, faculty: Optional[str] = None,
                top_k: int = None, temperature: float = 0.7) -> Dict:
        """
        Generate response for a query
        
        Args:
            query: User query
            faculty: Filter by faculty
            top_k: Number of documents to retrieve
            temperature: LLM temperature
        
        Returns:
            Dictionary with response and metadata
        """
        logger.info(f"Generating response for: '{query}'")
        
        try:
            # Step 1: Retrieve relevant documents
            retrieval_result = self.retriever.retrieve_with_context(
                query=query,
                faculty=faculty,
                top_k=top_k
            )
            
            context = retrieval_result['context']
            sources = retrieval_result['sources']
            
            logger.info(f"Retrieved {len(sources)} sources")
            
            # Step 2: Format prompt
            user_prompt = format_query_prompt(query, context)
            
            # Step 3: Generate response with LLM
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            llm_response = self.api_manager.generate_response(
                messages=messages,
                temperature=temperature,
                max_tokens=1000
            )
            
            # Step 4: Format final response
            response = {
                'answer': llm_response['content'],
                'sources': sources,
                'metadata': {
                    'query': query,
                    'faculty_filter': faculty,
                    'num_sources': len(sources),
                    'model': llm_response['model'],
                    'provider': llm_response['provider'],
                    'usage': llm_response['usage']
                }
            }
            
            logger.info(f"✅ Response generated using {llm_response['provider']}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def format_response_for_display(self, response: Dict) -> str:
        """
        Format response for display in UI
        
        Args:
            response: Response dictionary
        
        Returns:
            Formatted string
        """
        answer = response['answer']
        sources = response['sources']
        
        # Build formatted response
        formatted = answer + "\n\n"
        
        if sources:
            formatted += "---\n**Sources:**\n"
            for source in sources:
                title = source.get('title', 'Untitled')
                url = source.get('url', '')
                faculty = source.get('faculty', '')
                relevance = source.get('relevance_score', 0)
                
                formatted += f"\n{source['id']}. **{title}**"
                if faculty:
                    formatted += f" ({faculty})"
                if url:
                    formatted += f"\n   {url}"
                formatted += f"\n   Relevance: {relevance:.2%}\n"
        
        return formatted


# Singleton instance
_generator = None


def get_generator() -> ResponseGenerator:
    """Get or create generator singleton"""
    global _generator
    
    if _generator is None:
        _generator = ResponseGenerator()
    
    return _generator
