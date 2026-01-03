"""
PDF Handbook Processor
Extracts and processes content from faculty handbooks
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import PyPDF2
from tqdm import tqdm

# Add parent directory to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.config import Config
from src.utils.logger import setup_logger

# Setup logger
logger = setup_logger(
    "pdf_processor",
    log_file=str(Config.LOGS_DIR / f"pdf_processor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
)


class PDFProcessor:
    """Process PDF handbooks and extract structured content"""
    
    def __init__(self):
        """Initialize PDF processor"""
        self.pdfs_dir = Config.RAW_DATA_DIR / "pdfs"
        self.stats = {
            'total_pdfs': 0,
            'successfully_processed': 0,
            'failed': 0,
            'total_pages': 0
        }
        
        logger.info("PDF Processor initialized")
    
    def extract_text_from_pdf(self, pdf_path: Path) -> List[Dict]:
        """
        Extract text from PDF with page-level granularity
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            List of page data dictionaries
        """
        logger.info(f"Processing PDF: {pdf_path.name}")
        
        pages_data = []
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                logger.info(f"Total pages: {total_pages}")
                
                for page_num in tqdm(range(total_pages), desc=f"Processing {pdf_path.name}"):
                    try:
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        
                        if text and len(text.strip()) > 50:
                            page_data = {
                                'page_number': page_num + 1,
                                'content': text.strip(),
                                'word_count': len(text.split()),
                                'char_count': len(text)
                            }
                            pages_data.append(page_data)
                        
                    except Exception as e:
                        logger.warning(f"Error extracting page {page_num + 1}: {e}")
                        continue
                
                self.stats['total_pages'] += total_pages
                logger.info(f"✅ Extracted {len(pages_data)} pages with content")
                
        except Exception as e:
            logger.error(f"Error reading PDF {pdf_path}: {e}")
            raise
        
        return pages_data
    
    def process_handbook(self, pdf_filename: str, faculty: str = "FTS", 
                        department: str = "DICT", year: int = 2022) -> Dict:
        """
        Process a single handbook PDF
        
        Args:
            pdf_filename: Name of PDF file
            faculty: Faculty code
            department: Department code
            year: Handbook year
        
        Returns:
            Processed handbook data
        """
        pdf_path = self.pdfs_dir / pdf_filename
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        logger.info(f"Processing handbook: {pdf_filename}")
        logger.info(f"Faculty: {faculty}, Department: {department}, Year: {year}")
        
        # Extract pages
        pages = self.extract_text_from_pdf(pdf_path)
        
        if not pages:
            logger.warning(f"No content extracted from {pdf_filename}")
            return None
        
        # Create structured document
        handbook_data = {
            'source_file': pdf_filename,
            'faculty': faculty,
            'department': department,
            'year': year,
            'source_type': 'handbook_pdf',
            'processed_date': datetime.now().isoformat(),
            'total_pages': len(pages),
            'total_words': sum(p['word_count'] for p in pages),
            'total_chars': sum(p['char_count'] for p in pages),
            'pages': pages,
            'metadata': {
                'title': f"{faculty} {department} Handbook {year}",
                'description': f"Student handbook for {department} department, {faculty} faculty",
                'faculty': faculty,
                'department': department,
                'year': year
            }
        }
        
        logger.info(f"Handbook processed: {handbook_data['total_pages']} pages, "
                   f"{handbook_data['total_words']} words")
        
        return handbook_data
    
    def process_all_handbooks(self) -> List[Dict]:
        """
        Process all PDF handbooks in the pdfs directory
        
        Returns:
            List of processed handbooks
        """
        logger.info("Processing all handbooks...")
        
        all_handbooks = []
        
        # Find all PDFs
        pdf_files = list(self.pdfs_dir.glob("*.pdf"))
        self.stats['total_pdfs'] = len(pdf_files)
        
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        for pdf_file in pdf_files:
            try:
                # Parse filename to extract metadata
                # Expected format: FTS-DICT-HB-2022.pdf
                filename = pdf_file.stem
                parts = filename.split('-')
                
                if len(parts) >= 3:
                    faculty = parts[0]
                    department = parts[1]
                    year = int(parts[3]) if len(parts) > 3 else 2022
                else:
                    # Default values
                    faculty = "FTS"
                    department = "DICT"
                    year = 2022
                
                handbook_data = self.process_handbook(
                    pdf_file.name,
                    faculty=faculty,
                    department=department,
                    year=year
                )
                
                if handbook_data:
                    all_handbooks.append(handbook_data)
                    self.stats['successfully_processed'] += 1
                else:
                    self.stats['failed'] += 1
                
            except Exception as e:
                logger.error(f"Error processing {pdf_file.name}: {e}")
                self.stats['failed'] += 1
        
        logger.info(f"Processing complete: {self.stats['successfully_processed']}/{self.stats['total_pdfs']} handbooks")
        
        return all_handbooks
    
    def save_data(self, handbooks: List[Dict]):
        """
        Save processed handbook data
        
        Args:
            handbooks: List of processed handbooks
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save with timestamp
        output_path = Config.PROCESSED_DATA_DIR / f"handbooks_processed_{timestamp}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(handbooks, f, indent=2, ensure_ascii=False)
        
        # Save as latest
        latest_path = Config.PROCESSED_DATA_DIR / "handbooks_processed_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(handbooks, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Data saved to {output_path}")
        logger.info(f"Latest copy: {latest_path}")
        
        # Save summary
        summary = {
            'timestamp': timestamp,
            'statistics': self.stats,
            'total_handbooks': len(handbooks),
            'total_pages': sum(h['total_pages'] for h in handbooks),
            'total_words': sum(h['total_words'] for h in handbooks),
            'handbooks': [
                {
                    'file': h['source_file'],
                    'faculty': h['faculty'],
                    'department': h['department'],
                    'year': h['year'],
                    'pages': h['total_pages'],
                    'words': h['total_words']
                }
                for h in handbooks
            ]
        }
        
        summary_path = Config.PROCESSED_DATA_DIR / f"handbooks_summary_{timestamp}.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Summary saved to {summary_path}")


def main():
    """Main execution"""
    print("\n" + "="*60)
    print("📚 PDF Handbook Processor")
    print("="*60)
    
    # Create directories
    Config.create_directories()
    
    try:
        processor = PDFProcessor()
        handbooks = processor.process_all_handbooks()
        
        if handbooks:
            processor.save_data(handbooks)
            print(f"\n✅ Successfully processed {len(handbooks)} handbook(s)")
            
            for handbook in handbooks:
                print(f"\n  📖 {handbook['source_file']}")
                print(f"     Faculty: {handbook['faculty']}, Department: {handbook['department']}")
                print(f"     Pages: {handbook['total_pages']}, Words: {handbook['total_words']:,}")
        else:
            print("\n⚠️  No handbooks processed")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
