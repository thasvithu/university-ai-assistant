"""
Knowledge Base Builder
Combines all data sources and builds the vector database
"""

import json
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm
import sys

sys.path.append(str(Path(__file__).parent.parent))

from src.config import Config
from src.utils.logger import setup_logger
from src.rag.vector_store import get_vector_store

logger = setup_logger(
    "kb_builder",
    log_file=str(Config.LOGS_DIR / "kb_builder.log")
)


class KnowledgeBaseBuilder:
    """Build knowledge base from all data sources"""
    
    def __init__(self):
        """Initialize builder"""
        self.vector_store = get_vector_store()
        self.stats = {
            'web_docs': 0,
            'faculty_docs': 0,
            'handbook_pages': 0,
            'total_chunks': 0
        }
        
        logger.info("Knowledge Base Builder initialized")
    
    def load_web_data(self) -> List[Dict]:
        """Load main website data"""
        logger.info("Loading main website data...")
        
        web_file = Config.RAW_DATA_DIR / "vau_scraped_latest.json"
        
        if not web_file.exists():
            logger.warning(f"Web data not found: {web_file}")
            return []
        
        with open(web_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"✅ Loaded {len(data)} web documents")
        self.stats['web_docs'] = len(data)
        
        return data
    
    def load_faculty_data(self, faculty_code: str = "FTS") -> List[Dict]:
        """Load faculty website data"""
        logger.info(f"Loading {faculty_code} faculty data...")
        
        faculty_file = Config.RAW_DATA_DIR / f"{faculty_code.lower()}_scraped_latest.json"
        
        if not faculty_file.exists():
            logger.warning(f"Faculty data not found: {faculty_file}")
            return []
        
        with open(faculty_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"✅ Loaded {len(data)} faculty documents")
        self.stats['faculty_docs'] += len(data)
        
        return data
    
    def load_handbook_data(self) -> List[Dict]:
        """Load processed handbook data"""
        logger.info("Loading handbook data...")
        
        handbook_file = Config.PROCESSED_DATA_DIR / "handbooks_processed_latest.json"
        
        if not handbook_file.exists():
            logger.warning(f"Handbook data not found: {handbook_file}")
            return []
        
        with open(handbook_file, 'r', encoding='utf-8') as f:
            handbooks = json.load(f)
        
        # Flatten handbook pages into individual documents
        documents = []
        for handbook in handbooks:
            for page in handbook['pages']:
                doc = {
                    'content': page['content'],
                    'metadata': {
                        'source_type': 'handbook_pdf',
                        'faculty': handbook['faculty'],
                        'department': handbook['department'],
                        'year': str(handbook['year']),
                        'page_number': str(page['page_number']),
                        'source_file': handbook['source_file'],
                        'title': f"{handbook['faculty']} {handbook['department']} Handbook - Page {page['page_number']}"
                    }
                }
                documents.append(doc)
                self.stats['handbook_pages'] += 1
        
        logger.info(f"✅ Loaded {len(documents)} handbook pages")
        
        return documents
    
    def chunk_document(self, content: str, chunk_size: int = None, 
                      overlap: int = None) -> List[str]:
        """
        Split document into chunks
        
        Args:
            content: Document content
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks
        
        Returns:
            List of chunks
        """
        chunk_size = chunk_size or Config.CHUNK_SIZE
        overlap = overlap or Config.CHUNK_OVERLAP
        
        # Simple chunking by characters
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            chunk = content[start:end]
            
            if chunk.strip():
                chunks.append(chunk.strip())
            
            start = end - overlap
        
        return chunks
    
    def prepare_documents_for_vectorstore(self, documents: List[Dict]) -> List[Dict]:
        """
        Prepare documents for vector store
        
        Args:
            documents: Raw documents
        
        Returns:
            Prepared documents with chunks
        """
        logger.info("Preparing documents for vector store...")
        
        prepared_docs = []
        
        for doc in tqdm(documents, desc="Chunking documents"):
            content = doc.get('content', '')
            
            # Skip empty documents
            if not content or len(content.strip()) < 100:
                continue
            
            # For short documents, don't chunk
            if len(content) < Config.CHUNK_SIZE:
                prepared_doc = {
                    'content': content,
                    'metadata': doc.get('metadata', {})
                }
                # Add additional metadata from top level
                for key in ['url', 'title', 'faculty', 'source_type', 'department']:
                    if key in doc and key not in prepared_doc['metadata']:
                        prepared_doc['metadata'][key] = doc[key]
                
                prepared_docs.append(prepared_doc)
                self.stats['total_chunks'] += 1
            else:
                # Chunk long documents
                chunks = self.chunk_document(content)
                
                for i, chunk in enumerate(chunks):
                    metadata = doc.get('metadata', {}).copy()
                    metadata['chunk_index'] = str(i)
                    metadata['total_chunks'] = str(len(chunks))
                    
                    # Add additional metadata from top level
                    for key in ['url', 'title', 'faculty', 'source_type', 'department']:
                        if key in doc and key not in metadata:
                            metadata[key] = doc[key]
                    
                    prepared_doc = {
                        'content': chunk,
                        'metadata': metadata
                    }
                    prepared_docs.append(prepared_doc)
                    self.stats['total_chunks'] += 1
        
        logger.info(f"✅ Prepared {len(prepared_docs)} document chunks")
        
        return prepared_docs
    
    def build_knowledge_base(self, rebuild: bool = False):
        """
        Build complete knowledge base
        
        Args:
            rebuild: If True, delete existing collection and rebuild
        """
        logger.info("Building knowledge base...")
        
        if rebuild:
            logger.warning("Rebuilding knowledge base (deleting existing data)")
            try:
                self.vector_store.delete_collection()
                # Reinitialize vector store
                from src.rag.vector_store import VectorStore
                self.vector_store = VectorStore()
            except Exception as e:
                logger.warning(f"Could not delete collection: {e}")
        
        # Load all data sources
        all_documents = []
        
        # 1. Main website
        web_docs = self.load_web_data()
        all_documents.extend(web_docs)
        
        # 2. Faculty website (FTS)
        faculty_docs = self.load_faculty_data("FTS")
        all_documents.extend(faculty_docs)
        
        # 3. Handbooks
        handbook_docs = self.load_handbook_data()
        all_documents.extend(handbook_docs)
        
        logger.info(f"Total raw documents: {len(all_documents)}")
        
        # Prepare documents (chunking)
        prepared_docs = self.prepare_documents_for_vectorstore(all_documents)
        
        # Add to vector store
        logger.info("Adding documents to vector store...")
        self.vector_store.add_documents(prepared_docs, batch_size=100)
        
        # Print statistics
        self.print_stats()
        
        logger.info("✅ Knowledge base built successfully!")
    
    def print_stats(self):
        """Print build statistics"""
        print("\n" + "="*60)
        print("📊 KNOWLEDGE BASE STATISTICS")
        print("="*60)
        print(f"Main website documents:    {self.stats['web_docs']}")
        print(f"Faculty website documents: {self.stats['faculty_docs']}")
        print(f"Handbook pages:            {self.stats['handbook_pages']}")
        print(f"Total chunks in DB:        {self.stats['total_chunks']}")
        print("="*60)
        
        # Vector store stats
        vs_stats = self.vector_store.get_stats()
        print(f"\nVector Store: {vs_stats['collection_name']}")
        print(f"Documents: {vs_stats['document_count']}")
        print(f"Embedding dimension: {vs_stats['embedding_dimension']}")
        print("="*60)


def main():
    """Main execution"""
    print("\n" + "="*60)
    print("🏗️  Knowledge Base Builder")
    print("="*60)
    
    # Create directories
    Config.create_directories()
    
    try:
        builder = KnowledgeBaseBuilder()
        
        # Build knowledge base (rebuild=True to start fresh)
        builder.build_knowledge_base(rebuild=True)
        
        print("\n✅ Knowledge base ready!")
        print("\nYou can now run the Streamlit app:")
        print("  streamlit run app/streamlit_app.py")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
