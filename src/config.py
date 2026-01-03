"""
Configuration module for University AI Assistant
Centralizes all settings and environment variables
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    RAW_DATA_DIR = DATA_DIR / "raw"
    PROCESSED_DATA_DIR = DATA_DIR / "processed"
    CHROMADB_DIR = DATA_DIR / "chromadb"
    LOGS_DIR = DATA_DIR / "logs"
    
    # API Keys
    FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # Vector Database
    VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "chromadb")
    CHROMADB_PATH = os.getenv("CHROMADB_PATH", str(CHROMADB_DIR))
    
    # Model Configuration
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    LLM_PRIMARY = os.getenv("LLM_PRIMARY", "groq")
    LLM_FALLBACK = os.getenv("LLM_FALLBACK", "openai")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # RAG Configuration
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
    TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))
    
    # UI Configuration
    APP_TITLE = os.getenv("APP_TITLE", "Vavuniya University AI Assistant")
    APP_ICON = os.getenv("APP_ICON", "🎓")
    
    # Faculty URLs
    FACULTY_URLS = {
        "FAS": "https://fas.vau.ac.lk/",
        "FBS": "https://fbs.vau.ac.lk/",
        "FTS": "https://fts.vau.ac.lk/"
    }
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []
        
        if not cls.FIRECRAWL_API_KEY:
            errors.append("FIRECRAWL_API_KEY is required")
        
        if not cls.GROQ_API_KEY:
            errors.append("GROQ_API_KEY is required")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories"""
        for dir_path in [
            cls.DATA_DIR,
            cls.RAW_DATA_DIR,
            cls.PROCESSED_DATA_DIR,
            cls.CHROMADB_DIR,
            cls.LOGS_DIR,
            cls.RAW_DATA_DIR / "pdfs"
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        print("✅ Directories created/verified")


# Validate configuration on import
if __name__ != "__main__":
    try:
        Config.validate()
    except ValueError as e:
        print(f"⚠️  Configuration warning: {e}")
