import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from fake_useragent import UserAgent
import logging
from typing import List, Dict, Optional
import hashlib

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedWebScraper:
    def __init__(self, timeout=15, max_retries=3, delay=1):
        self.timeout = timeout
        self.max_retries = max_retries
        self.delay = delay
        self.session = requests.Session()
        self.ua = UserAgent()
        self.seen_content = set()  # For deduplication
        
    def get_headers(self):
        """Generate random user agent headers"""
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch page content with retry mechanism"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    url, 
                    headers=self.get_headers(), 
                    timeout=self.timeout,
                    allow_redirects=True
                )
                response.raise_for_status()
                
                # Check if content is HTML
                content_type = response.headers.get('content-type', '')
                if 'text/html' in content_type.lower():
                    return response.text
                else:
                    logger.warning(f"Non-HTML content at {url}: {content_type}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay * (attempt + 1))  # Exponential backoff
                else:
                    logger.error(f"All attempts failed for {url}")
                    return None
    
    def extract_content(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract various types of content from the page"""
        content = {
            'paragraphs': [],
            'headings': [],
            'lists': [],
            'tables': [],
            'links': [],
            'metadata': {}
        }
        
        # Extract paragraphs
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if text and len(text) > 20:  # Filter out very short paragraphs
                content['paragraphs'].append(text)
        
        # Extract headings (h1, h2, h3)
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            text = heading.get_text().strip()
            if text:
                content['headings'].append(text)
        
        # Extract list items
        for li in soup.find_all('li'):
            text = li.get_text().strip()
            if text and len(text) > 15:
                content['lists'].append(text)
        
        # Extract table data
        for table in soup.find_all('table'):
            table_text = ' '.join([cell.get_text().strip() for cell in table.find_all(['td', 'th'])])
            if table_text:
                content['tables'].append(table_text[:200])  # Limit table text
        
        # Extract links with context
        for a in soup.find_all('a', href=True):
            href = a.get('href')
            text = a.get_text().strip()
            if text and href and not href.startswith('#'):
                full_url = urljoin(soup.base_url, href)
                content['links'].append({
                    'text': text,
                    'url': full_url,
                    'domain': urlparse(full_url).netloc
                })
        
        # Extract metadata
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            if meta.get('name') and meta.get('content'):
                content['metadata'][meta['name']] = meta['content']
            elif meta.get('property') and meta.get('content'):
                content['metadata'][meta['property']] = meta['content']
        
        return content
    
    def search_in_content(self, content: Dict, keyword: str, context_chars: int = 100) -> List[Dict]:
        """Search for keyword in extracted content with context"""
        matches = []
        keyword_lower = keyword.lower()
        
        for content_type, items in content.items():
            if content_type in ['paragraphs', 'headings', 'lists', 'tables']:
                for item in items:
                    if keyword_lower in item.lower():
                        # Create content hash for deduplication
                        content_hash = hashlib.md5(item.encode()).hexdigest()
                        
                        if content_hash not in self.seen_content:
                            self.seen_content.add(content_hash)
                            
                            # Extract context around keyword
                            positions = [m.start() for m in re.finditer(keyword_lower, item.lower())]
                            contexts = []
                            
                            for pos in positions:
                                start = max(0, pos - context_chars)
                                end = min(len(item), pos + len(keyword) + context_chars)
                                context = item[start:end]
                                if start > 0:
                                    context = "..." + context
                                if end < len(item):
                                    context = context + "..."
                                contexts.append(context)
                            
                            matches.append({
                                'type': content_type,
                                'content': item,
                                'contexts': contexts,
                                'relevance': len(positions),
                                'length': len(item)
                            })
        
        # Sort by relevance (number of keyword occurrences) and length
        matches.sort(key=lambda x: (x['relevance'], x['length']), reverse=True)
        return matches
    
    def scrape_site(self, url: str, keyword: str, max_pages: int = 5) -> Dict:
        """Main scraping function with multi-page support"""
        results = {
            'url': url,
            'keyword': keyword,
            'matches': [],
            'stats': {
                'pages_scraped': 0,
                'total_matches': 0,
                'time_taken': 0
            }
        }
        
        start_time = time.time()
        
        # Start with the main URL
        pages_to_scrape = [url]
        scraped_urls = set()
        
        while pages_to_scrape and len(scraped_urls) < max_pages:
            current_url = pages_to_scrape.pop(0)
            
            if current_url in scraped_urls:
                continue
                
            logger.info(f"Scraping: {current_url}")
            
            # Fetch page
            html_content = self.fetch_page(current_url)
            if not html_content:
                continue
                
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            soup.base_url = current_url  # Store base URL for relative links
            
            # Extract content
            content = self.extract_content(soup)
            
            # Search for keyword
            matches = self.search_in_content(content, keyword)
            
            if matches:
                results['matches'].extend(matches[:5])  # Limit per page
            
            # Find more links within the same domain
            if len(scraped_urls) < max_pages:
                base_domain = urlparse(url).netloc
                for link in content['links']:
                    link_domain = link['domain']
                    if link_domain == base_domain and link['url'] not in scraped_urls:
                        if link['url'] not in pages_to_scrape:
                            pages_to_scrape.append(link['url'])
            
            scraped_urls.add(current_url)
            results['stats']['pages_scraped'] = len(scraped_urls)
            results['stats']['total_matches'] = len(results['matches'])
            
            # Be polite to the server
            time.sleep(self.delay)
        
        results['stats']['time_taken'] = round(time.time() - start_time, 2)
        
        # Limit total results
        results['matches'] = results['matches'][:15]
        
        return results
    
    def scrape_multiple_sites(self, urls: List[str], keyword: str, max_workers: int = 3) -> List[Dict]:
        """Scrape multiple sites concurrently"""
        all_results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(self.scrape_site, url, keyword): url 
                for url in urls
            }
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result(timeout=60)
                    all_results.append(result)
                    logger.info(f"Completed scraping {url} - Found {result['stats']['total_matches']} matches")
                except Exception as e:
                    logger.error(f"Error scraping {url}: {str(e)}")
                    all_results.append({
                        'url': url,
                        'error': str(e),
                        'matches': []
                    })
        
        return all_results

def search_site_advanced(url: str, keyword: str, max_pages: int = 3) -> List[str]:
    """
    Simplified interface for backward compatibility
    Returns list of matching content strings
    """
    scraper = AdvancedWebScraper()
    results = scraper.scrape_site(url, keyword, max_pages)
    
    # Convert to simple list of strings for backward compatibility
    simple_matches = []
    for match in results['matches']:
        simple_matches.append(f"[{match['type']}] {match['content']}")
    
    return simple_matches[:8]

# Example usage
if __name__ == "__main__":
    # Advanced usage
    scraper = AdvancedWebScraper()
    
    # Single site with multiple pages
    results = scraper.scrape_site("https://example.com", "python", max_pages=3)
    print(f"Found {results['stats']['total_matches']} matches in {results['stats']['time_taken']} seconds")
    
    for match in results['matches'][:5]:
        print(f"\n--- {match['type'].upper()} (Relevance: {match['relevance']}) ---")
        print(match['content'][:200] + "...")
    
    # Multiple sites concurrently
    # urls = ["https://site1.com", "https://site2.com"]
    # all_results = scraper.scrape_multiple_sites(urls, "python")
    
    # Simple usage (backward compatible)
    # matches = search_site_advanced("https://example.com", "python")
    # for match in matches:
    #     print(match)
