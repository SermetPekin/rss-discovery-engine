import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List

from .validation import is_likely_blog

logger = logging.getLogger(__name__)

def extract_blog_links(content: str, source_url: str) -> List[str]:
    """Extract potential blog URLs from HTML content"""
    if not content:
        return []
    
    try:
        soup = BeautifulSoup(content, 'html.parser')
        links = []
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            
            # Skip non-HTTP(S) URLs (mailto, tel, javascript, etc.)
            if href.startswith(('mailto:', 'tel:', 'javascript:', 'data:', 'ftp:', '#')):
                continue
            
            # Make absolute URL
            full_url = urljoin(source_url, href)
            
            # Only accept http/https URLs
            if not full_url.startswith(('http://', 'https://')):
                continue
            
            # Check if likely a blog
            if is_likely_blog(full_url):
                # Get the root domain URL
                parsed = urlparse(full_url)
                root_url = f"{parsed.scheme}://{parsed.netloc}"
                links.append(root_url)
        
        return list(set(links))  # Unique links
        
    except Exception as e:
        return []
