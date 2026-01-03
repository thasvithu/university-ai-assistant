"""
Faculty Website Scraper
Scrapes Faculty of Technological Studies website using Firecrawl
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from firecrawl import FirecrawlApp
from dotenv import load_dotenv

# Add parent directory to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.config import Config
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger(
    "faculty_scraper",
    log_file=str(Config.LOGS_DIR / f"faculty_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
)


class FacultyScraper:
    """Scraper for faculty websites"""
    
    def __init__(self, faculty_code: str = "FTS"):
        """
        Initialize scraper
        
        Args:
            faculty_code: Faculty code (FTS, FAS, or FBS)
        """
        self.faculty_code = faculty_code
        self.faculty_url = Config.FACULTY_URLS.get(faculty_code)
        
        if not self.faculty_url:
            raise ValueError(f"Invalid faculty code: {faculty_code}")
        
        # Initialize Firecrawl
        api_key = Config.FIRECRAWL_API_KEY
        if not api_key:
            raise ValueError("FIRECRAWL_API_KEY not found in environment")
        
        self.firecrawl = FirecrawlApp(api_key=api_key)
        
        # Statistics
        self.stats = {
            'total_pages': 0,
            'successfully_scraped': 0,
            'failed': 0
        }
        
        logger.info(f"Initialized scraper for {faculty_code}: {self.faculty_url}")
    
    def scrape_single_page(self, url: str) -> Optional[Dict]:
        """
        Scrape a single page
        
        Args:
            url: Page URL
        
        Returns:
            Scraped data or None
        """
        try:
            logger.info(f"Scraping: {url}")
            
            result = self.firecrawl.scrape(
                url,
                formats=['markdown']
            )
            
            if not result:
                logger.warning(f"No result for {url}")
                return None
            
            # Extract content
            markdown_content = None
            metadata = {}
            
            if hasattr(result, 'markdown'):
                markdown_content = result.markdown
            elif hasattr(result, 'content'):
                markdown_content = result.content
            elif isinstance(result, dict):
                markdown_content = result.get('markdown') or result.get('content')
                metadata = result.get('metadata', {})
            
            if hasattr(result, 'metadata'):
                metadata = result.metadata if isinstance(result.metadata, dict) else {}
            
            if not markdown_content or len(markdown_content) < 50:
                logger.warning(f"Insufficient content for {url}")
                return None
            
            data = {
                'url': url,
                'title': metadata.get('title', ''),
                'description': metadata.get('description', ''),
                'content': markdown_content,
                'scraped_date': datetime.now().isoformat(),
                'source_type': 'faculty_web',
                'faculty': self.faculty_code,
                'word_count': len(markdown_content.split()),
                'char_count': len(markdown_content)
            }
            
            logger.info(f"✅ Scraped {data['word_count']} words from {url}")
            return data
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
    def discover_all_pages(self) -> List[str]:
        """
        Discover all pages on the faculty website using Firecrawl's map
        
        Returns:
            List of discovered URLs
        """
        logger.info("🔍 Discovering all pages on the website...")
        
        try:
            # Use Firecrawl's map to discover all links
            map_result = self.firecrawl.map_url(self.faculty_url)
            
            if not map_result:
                logger.warning("Map returned no results, using fallback URLs")
                return self._get_fallback_urls()
            
            # Extract URLs from map result
            discovered_urls = []
            
            if isinstance(map_result, dict):
                # Try different possible response structures
                urls = map_result.get('links', []) or map_result.get('urls', []) or map_result.get('pages', [])
                
                if hasattr(map_result, 'links'):
                    urls = map_result.links
                
                if urls:
                    discovered_urls = urls if isinstance(urls, list) else [urls]
            elif isinstance(map_result, list):
                discovered_urls = map_result
            
            # Filter to only include URLs from the faculty domain
            faculty_domain = self.faculty_url.replace('https://', '').replace('http://', '').rstrip('/')
            filtered_urls = []
            
            for url in discovered_urls:
                if isinstance(url, dict):
                    url = url.get('url', '')
                
                if faculty_domain in url:
                    filtered_urls.append(url)
            
            if filtered_urls:
                logger.info(f"✅ Discovered {len(filtered_urls)} pages on {self.faculty_code} website")
                return filtered_urls
            else:
                logger.warning("No URLs found in map result, using fallback")
                return self._get_fallback_urls()
                
        except Exception as e:
            logger.warning(f"Map feature failed: {e}. Using fallback URLs")
            return self._get_fallback_urls()
    
    def _get_fallback_urls(self) -> List[str]:
        """Get fallback URLs if map feature doesn't work"""
        return [
            self.faculty_url,
            f"{self.faculty_url}about/",
            f"{self.faculty_url}about-us/",
            f"{self.faculty_url}programs/",
            f"{self.faculty_url}departments/",
            f"{self.faculty_url}admissions/",
            f"{self.faculty_url}faculty/",
            f"{self.faculty_url}staff/",
            f"{self.faculty_url}research/",
            f"{self.faculty_url}news/",
            f"{self.faculty_url}events/",
            f"{self.faculty_url}contact/",
            f"{self.faculty_url}contact-us/",
        ]
    
    def scrape_faculty_site(self, max_pages: int = 100) -> List[Dict]:
        """
        Scrape entire faculty website by discovering and scraping all pages
        
        Args:
            max_pages: Maximum pages to scrape
        
        Returns:
            List of scraped documents
        """
        logger.info(f"Starting scrape of {self.faculty_code} website")
        logger.info(f"Base URL: {self.faculty_url}")
        
        all_data = []
        
        try:
            # Step 1: Discover all pages
            urls_to_scrape = self.discover_all_pages()
            
            # Limit to max_pages
            if len(urls_to_scrape) > max_pages:
                logger.info(f"Limiting to {max_pages} pages (found {len(urls_to_scrape)})")
                urls_to_scrape = urls_to_scrape[:max_pages]
            
            self.stats['total_pages'] = len(urls_to_scrape)
            
            logger.info(f"\n📋 Will scrape {len(urls_to_scrape)} pages:")
            for i, url in enumerate(urls_to_scrape[:10], 1):
                logger.info(f"   {i}. {url}")
            if len(urls_to_scrape) > 10:
                logger.info(f"   ... and {len(urls_to_scrape) - 10} more")
            
            # Step 2: Scrape each page
            print(f"\n🌐 Scraping {len(urls_to_scrape)} pages from {self.faculty_code}...")
            
            for i, url in enumerate(urls_to_scrape, 1):
                print(f"\n[{i}/{len(urls_to_scrape)}] {url}")
                logger.info(f"[{i}/{len(urls_to_scrape)}] Processing {url}")
                
                data = self.scrape_single_page(url)
                
                if data:
                    all_data.append(data)
                    self.stats['successfully_scraped'] += 1
                    print(f"  ✅ {data['word_count']} words")
                else:
                    self.stats['failed'] += 1
                    print(f"  ⚠️  Failed or no content")
                
                # Respectful delay (2 seconds between requests)
                if i < len(urls_to_scrape):
                    time.sleep(2)
            
            logger.info(f"Scraping complete: {self.stats['successfully_scraped']}/{self.stats['total_pages']} pages")
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
        
        return all_data
    
    def save_data(self, data: List[Dict]):
        """
        Save scraped data to JSON
        
        Args:
            data: List of scraped documents
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save with timestamp
        output_path = Config.RAW_DATA_DIR / f"{self.faculty_code.lower()}_scraped_{timestamp}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Save as latest
        latest_path = Config.RAW_DATA_DIR / f"{self.faculty_code.lower()}_scraped_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Data saved to {output_path}")
        logger.info(f"Latest copy: {latest_path}")
        
        # Save summary
        summary = {
            'timestamp': timestamp,
            'faculty': self.faculty_code,
            'base_url': self.faculty_url,
            'statistics': self.stats,
            'total_documents': len(data),
            'total_words': sum(d['word_count'] for d in data),
            'total_chars': sum(d['char_count'] for d in data),
            'urls': [d['url'] for d in data]
        }
        
        summary_path = Config.RAW_DATA_DIR / f"{self.faculty_code.lower()}_summary_{timestamp}.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Summary saved to {summary_path}")


def main():
    """Main execution"""
    print("\n" + "="*60)
    print("🎓 Faculty Website Scraper")
    print("="*60)
    
    # Create directories
    Config.create_directories()
    
    # Scrape FTS (Faculty of Technological Studies)
    try:
        scraper = FacultyScraper(faculty_code="FTS")
        data = scraper.scrape_faculty_site()
        
        if data:
            scraper.save_data(data)
            print(f"\n✅ Successfully scraped {len(data)} pages from FTS")
        else:
            print("\n⚠️  No data scraped")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
