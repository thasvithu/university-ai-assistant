"""
API Manager for LLM providers
Handles Groq (primary) and OpenAI (fallback)
"""

from typing import Optional, Dict
from pathlib import Path
import sys
from groq import Groq
from openai import OpenAI

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger("api_manager")


class LLMAPIManager:
    """Manage multiple LLM API providers with fallback"""
    
    def __init__(self):
        """Initialize API clients"""
        logger.info("Initializing LLM API Manager")
        
        # Initialize Groq (primary)
        self.groq_client = None
        if Config.GROQ_API_KEY:
            try:
                self.groq_client = Groq(api_key=Config.GROQ_API_KEY)
                logger.info("✅ Groq client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq: {e}")
        
        # Initialize OpenAI (fallback)
        self.openai_client = None
        if Config.OPENAI_API_KEY:
            try:
                self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
                logger.info("✅ OpenAI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")
        
        if not self.groq_client and not self.openai_client:
            raise ValueError("No LLM API clients available. Please set GROQ_API_KEY or OPENAI_API_KEY")
        
        self.stats = {
            'groq_calls': 0,
            'openai_calls': 0,
            'groq_errors': 0,
            'openai_errors': 0
        }
    
    def generate_response(self, messages: list, temperature: float = 0.7,
                         max_tokens: int = 1000, use_fallback: bool = True) -> Dict:
        """
        Generate response using primary (Groq) or fallback (OpenAI)
        
        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            use_fallback: Whether to use fallback on error
        
        Returns:
            Dictionary with response and metadata
        """
        # Try Groq first
        if self.groq_client:
            try:
                logger.info("Calling Groq API...")
                response = self._call_groq(messages, temperature, max_tokens)
                self.stats['groq_calls'] += 1
                return response
            except Exception as e:
                logger.warning(f"Groq API error: {e}")
                self.stats['groq_errors'] += 1
                
                if not use_fallback:
                    raise
        
        # Fallback to OpenAI
        if self.openai_client:
            try:
                logger.info("Calling OpenAI API (fallback)...")
                response = self._call_openai(messages, temperature, max_tokens)
                self.stats['openai_calls'] += 1
                return response
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
                self.stats['openai_errors'] += 1
                raise
        
        raise RuntimeError("No LLM API available")
    
    def _call_groq(self, messages: list, temperature: float, max_tokens: int) -> Dict:
        """Call Groq API"""
        response = self.groq_client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            'content': response.choices[0].message.content,
            'model': Config.GROQ_MODEL,
            'provider': 'groq',
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
        }
    
    def _call_openai(self, messages: list, temperature: float, max_tokens: int) -> Dict:
        """Call OpenAI API"""
        response = self.openai_client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            'content': response.choices[0].message.content,
            'model': Config.OPENAI_MODEL,
            'provider': 'openai',
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
        }
    
    def get_stats(self) -> Dict:
        """Get API usage statistics"""
        return self.stats.copy()


# Singleton instance
_api_manager = None


def get_api_manager() -> LLMAPIManager:
    """Get or create API manager singleton"""
    global _api_manager
    
    if _api_manager is None:
        _api_manager = LLMAPIManager()
    
    return _api_manager
