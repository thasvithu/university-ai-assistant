"""
VavuniBot - University of Vavuniya Web Scraper
Scrapes data from Nov 2025+ from 3 sitemaps
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
import requests
import xml.etree.ElementTree as ET
from firecrawl import FirecrawlApp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VavuniyaUniversityScraper:
    """
    Scraper for University of Vavuniya website
    Filters data from November 2025 onwards
    """
    
    def __init__(self):
        # Initialize Firecrawl
        api_key = os.getenv('FIRECRAWL_API_KEY')
        if not api_key:
            raise ValueError("FIRECRAWL_API_KEY not found in .env file")
        
        self.firecrawl = FirecrawlApp(api_key=api_key)
        
        # Configuration
        self.base_url = "https://www.vau.ac.lk"
        self.cutoff_date = datetime(2025, 11, 1)  # November 2025
        
        # Sitemaps to scrape
        self.sitemaps = {
            'posts': 'https://www.vau.ac.lk/post-sitemap.xml',
            'pages': 'https://www.vau.ac.lk/page-sitemap.xml',
            'categories': 'https://www.vau.ac.lk/category-sitemap.xml'
        }
        
        # Create directories
        self.setup_directories()
        
        # Statistics
        self.stats = {
            'total_urls_found': 0,
            'urls_after_filter': 0,
            'successfully_scraped': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def setup_directories(self):
        """Create necessary directories"""
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        Path("data/logs").mkdir(parents=True, exist_ok=True)
        print("✅ Directories created/verified")
    
    def parse_sitemap(self, sitemap_url, sitemap_name):
        """
        Parse a single sitemap XML and extract URLs with metadata
        """
        print(f"\n{'='*60}")
        print(f"📍 Parsing: {sitemap_name}")
        print(f"{'='*60}")
        
        try:
            response = requests.get(sitemap_url, timeout=15)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            urls = []
            for url_elem in root.findall('ns:url', namespace):
                loc = url_elem.find('ns:loc', namespace)
                lastmod = url_elem.find('ns:lastmod', namespace)
                
                if loc is not None:
                    url_data = {
                        'url': loc.text,
                        'last_modified': lastmod.text if lastmod is not None else None,
                        'sitemap': sitemap_name
                    }
                    urls.append(url_data)
            
            print(f"✅ Found {len(urls)} URLs in {sitemap_name}")
            return urls
            
        except Exception as e:
            print(f"❌ Error parsing {sitemap_name}: {e}")
            return []
    
    def filter_by_date(self, urls):
        """
        Filter URLs to only include those from November 2025 onwards
        """
        print(f"\n🔍 Filtering URLs (keeping Nov 2025+ only)...")
        
        filtered = []
        skipped = []
        
        for url_data in urls:
            if not url_data['last_modified']:
                skipped.append(url_data)
                continue
            
            try:
                # Extract just the date portion (YYYY-MM-DD)
                date_str = url_data['last_modified']
                
                # Handle different formats:
                # "2025-12-31 04:14 +00:00" -> "2025-12-31"
                # "2025-12-31T04:14:21+00:00" -> "2025-12-31"
                
                # Take first 10 characters (always YYYY-MM-DD)
                date_only = date_str[:10]
                
                url_date = datetime.strptime(date_only, '%Y-%m-%d')
                
                if url_date >= self.cutoff_date:
                    filtered.append(url_data)
                else:
                    skipped.append(url_data)
                    
            except Exception as e:
                # Silently skip problematic dates
                skipped.append(url_data)
        
        print(f"✅ Kept: {len(filtered)} URLs")
        print(f"⏭️  Skipped: {len(skipped)} URLs (before Nov 2025)")
        
        return filtered
    
    def scrape_single_url(self, url_data):
        """
        Scrape a single URL using Firecrawl with improved error handling
        """
        url = url_data['url']
        
        try:
            # Call Firecrawl API
            result = self.firecrawl.scrape(
                url,
                formats=['markdown']
            )
            
            # Debug first URL to see response structure
            if not hasattr(self, '_debug_done'):
                self._debug_done = True
                print(f"\n   🔍 DEBUG - First URL Response:")
                print(f"   Type: {type(result)}")
                if result:
                    if isinstance(result, dict):
                        print(f"   Keys: {list(result.keys())}")
                        for key, value in result.items():
                            if isinstance(value, str):
                                print(f"   - {key}: string ({len(value)} chars)")
                            elif isinstance(value, dict):
                                print(f"   - {key}: dict (keys: {list(value.keys())})")
                            else:
                                print(f"   - {key}: {type(value).__name__}")
                    else:
                        print(f"   Content: {str(result)[:200]}")
                else:
                    print(f"   Result is None or False")
                print()
            
            # Check if we got a valid result
            if not result:
                return None
            
            # Extract markdown content - handle Document object
            markdown_content = None
            metadata = {}
            
            # Handle firecrawl Document object
            if hasattr(result, 'markdown'):
                markdown_content = result.markdown
            elif hasattr(result, 'content'):
                markdown_content = result.content
            elif isinstance(result, dict):
                # Try different possible response structures
                if 'markdown' in result:
                    markdown_content = result['markdown']
                elif 'content' in result:
                    markdown_content = result['content']
                elif 'data' in result and isinstance(result['data'], dict):
                    markdown_content = result['data'].get('markdown') or result['data'].get('content')
            elif isinstance(result, str):
                markdown_content = result
            
            # Extract metadata from Document object
            if hasattr(result, 'metadata'):
                metadata = result.metadata if isinstance(result.metadata, dict) else {}
            elif isinstance(result, dict):
                metadata = result.get('metadata', {})
            
            if not markdown_content or len(markdown_content) < 50:
                return None
            
            return {
                'url': url,
                'title': metadata.get('title', '') if metadata else '',
                'description': metadata.get('description', '') if metadata else '',
                'content': markdown_content,
                'scraped_date': datetime.now().isoformat(),
                'last_modified': url_data['last_modified'],
                'source_type': 'web',
                'sitemap': url_data['sitemap'],
                'word_count': len(markdown_content.split()),
                'char_count': len(markdown_content)
            }
            
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            import traceback
            if not hasattr(self, '_traceback_shown'):
                self._traceback_shown = True
                print(f"   Full traceback:")
                traceback.print_exc()
        return None
    
    def scrape_all(self):
        """
        Main scraping function - scrapes all 3 sitemaps with filtering
        """
        print("\n" + "="*60)
        print("🚀 STARTING VAVUNIYA UNIVERSITY SCRAPER")
        print("="*60)
        print(f"Date filter: From {self.cutoff_date.strftime('%Y-%m-%d')} onwards")
        print(f"Sitemaps: {len(self.sitemaps)}")
        
        all_scraped_data = []
        
        # Step 1: Parse all sitemaps
        print("\n" + "="*60)
        print("STEP 1: PARSING SITEMAPS")
        print("="*60)
        
        all_urls = []
        for name, url in self.sitemaps.items():
            urls = self.parse_sitemap(url, name)
            all_urls.extend(urls)
        
        self.stats['total_urls_found'] = len(all_urls)
        print(f"\n📊 Total URLs found: {len(all_urls)}")
        
        # Step 2: Filter by date
        print("\n" + "="*60)
        print("STEP 2: FILTERING BY DATE")
        print("="*60)
        
        filtered_urls = self.filter_by_date(all_urls)
        self.stats['urls_after_filter'] = len(filtered_urls)
        
        # Step 3: Scrape filtered URLs
        print("\n" + "="*60)
        print("STEP 3: SCRAPING CONTENT")
        print("="*60)
        print(f"URLs to scrape: {len(filtered_urls)}\n")
        
        for i, url_data in enumerate(filtered_urls, 1):
            url = url_data['url']
            print(f"[{i}/{len(filtered_urls)}] {url}")
            
            try:
                scraped = self.scrape_single_url(url_data)
                
                if scraped:
                    all_scraped_data.append(scraped)
                    self.stats['successfully_scraped'] += 1
                    print(f"   ✅ {scraped['word_count']} words, {scraped['char_count']} chars")
                else:
                    self.stats['failed'] += 1
                    print(f"   ⚠️  No content extracted")
                
                # Respectful delay (2 seconds between requests)
                if i < len(filtered_urls):
                    time.sleep(2)
                
            except Exception as e:
                self.stats['failed'] += 1
                print(f"   ❌ Exception: {str(e)[:100]}")
                time.sleep(1)
        
        # Step 4: Save results
        self.save_data(all_scraped_data)
        
        # Step 5: Print summary
        self.print_summary()
        
        return all_scraped_data
    
    def save_data(self, data):
        """
        Save scraped data to JSON files
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save full data with timestamp
        output_path = f"data/raw/vau_scraped_{timestamp}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Save as "latest" for easy access
        latest_path = "data/raw/vau_scraped_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Save summary statistics
        summary = {
            'timestamp': timestamp,
            'cutoff_date': self.cutoff_date.strftime('%Y-%m-%d'),
            'statistics': self.stats,
            'total_documents': len(data),
            'total_words': sum(d['word_count'] for d in data),
            'total_chars': sum(d['char_count'] for d in data),
            'by_sitemap': self._group_by_sitemap(data),
            'urls': [d['url'] for d in data]
        }
        
        summary_path = f"data/raw/vau_summary_{timestamp}.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n💾 Data saved:")
        print(f"   • {output_path}")
        print(f"   • {latest_path}")
        print(f"   • {summary_path}")
    
    def _group_by_sitemap(self, data):
        """Group documents by sitemap source"""
        grouped = {}
        for doc in data:
            sitemap = doc['sitemap']
            grouped[sitemap] = grouped.get(sitemap, 0) + 1
        return grouped
    
    def print_summary(self):
        """
        Print final scraping summary
        """
        print("\n" + "="*60)
        print("📊 SCRAPING SUMMARY")
        print("="*60)
        print(f"Total URLs found:        {self.stats['total_urls_found']}")
        print(f"After date filter:       {self.stats['urls_after_filter']}")
        print(f"Successfully scraped:    {self.stats['successfully_scraped']}")
        print(f"Failed:                  {self.stats['failed']}")
        print("="*60)
        
        if self.stats['successfully_scraped'] > 0:
            success_rate = (self.stats['successfully_scraped'] / 
                          self.stats['urls_after_filter'] * 100)
            print(f"Success rate:            {success_rate:.1f}%")
        
        print("="*60)


def main():
    """
    Main execution function
    """
    print("\n🎓 VavuniBot - University of Vavuniya Scraper")
    print("=" * 60)
    
    try:
        scraper = VavuniyaUniversityScraper()
        data = scraper.scrape_all()
        
        print("\n✅ Scraping completed successfully!")
        print(f"📦 Collected {len(data)} documents")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()