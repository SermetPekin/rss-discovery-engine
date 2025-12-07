import time
import logging
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Tuple, Optional

from config import Settings
from .utils import extract_domain

# Initialize settings
settings = Settings()
logger = logging.getLogger(__name__)

class Fetcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Priority': 'u=0, i',
        }
        self.domain_last_request: Dict[str, float] = {}
        self.min_delay_between_requests = 2  # seconds

    def enforce_rate_limit(self, domain: str):
        """Enforce rate limiting per domain"""
        if not domain:
            return
        
        current_time = time.time()
        
        if domain in self.domain_last_request:
            elapsed = current_time - self.domain_last_request[domain]
            if elapsed < self.min_delay_between_requests:
                sleep_time = self.min_delay_between_requests - elapsed
                logger.debug(f"  ⏳ Rate limiting: waiting {sleep_time:.1f}s for {domain}")
                time.sleep(sleep_time)
        
        self.domain_last_request[domain] = time.time()

    def check_sitemap(self, url: str) -> List[str]:
        """Check sitemap.xml for blog/feed URLs"""
        sitemap_urls = []
        base_url = url.rstrip('/')
        
        # First, try to get sitemap location from robots.txt
        sitemap_paths = []
        try:
            robots_url = base_url + '/robots.txt'
            response = requests.get(robots_url, headers=self.headers, timeout=5, verify=False)
            if response.status_code == 200:
                # Parse robots.txt for Sitemap: directives
                for line in response.text.split('\n'):
                    line = line.strip()
                    if line.lower().startswith('sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        # Convert full URL to path if it's for this domain
                        if sitemap_url.startswith(base_url):
                            sitemap_path = sitemap_url[len(base_url):]
                            sitemap_paths.append(sitemap_path)
                        elif sitemap_url.startswith('/'):
                            sitemap_paths.append(sitemap_url)
                if sitemap_paths:
                    logger.debug(f"Found {len(sitemap_paths)} sitemap(s) in robots.txt")
        except:
            pass
        
        # Add common sitemap locations as fallback
        if not sitemap_paths:
            sitemap_paths = ['/sitemap.xml', '/sitemap_index.xml', '/sitemap-index.xml', '/rss-sitemap.xml']
        
        for sitemap_path in sitemap_paths:
            try:
                sitemap_url = base_url + sitemap_path
                response = requests.get(sitemap_url, headers=self.headers, timeout=5, verify=False)
                if response.status_code == 200:
                    # Parse sitemap XML
                    soup = BeautifulSoup(response.text, 'xml')
                    # Look for RSS/feed URLs in sitemap
                    for loc in soup.find_all('loc'):
                        loc_url = loc.get_text()
                        if any(kw in loc_url.lower() for kw in ['feed', 'rss', 'atom', 'blog']):
                            sitemap_urls.append(loc_url)
                    if sitemap_urls:
                        logger.debug(f"Found {len(sitemap_urls)} potential feeds in sitemap")
                        return sitemap_urls[:10]  # Limit to 10
            except:
                continue
        
        return sitemap_urls

    def discover_feeds(self, url: str) -> Tuple[List[str], str]:
        """Try to discover RSS/Atom feeds from a URL"""
        feed_urls = []
        has_blog_indicators = False
        
        # Enforce rate limiting for this domain
        domain = extract_domain(url)
        self.enforce_rate_limit(domain)
        
        try:
            # Try to fetch the main page first
            response = requests.get(url, headers=self.headers, timeout=settings.REQUEST_TIMEOUT, verify=False)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            logger.debug(f"Timeout accessing {url}")
            return ([], 'unreachable')
        except requests.exceptions.ConnectionError:
            logger.debug(f"Connection error accessing {url}")
            return ([], 'unreachable')
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [403, 404, 410, 451]:
                logger.debug(f"HTTP {e.response.status_code} for {url}")
            return ([], 'unreachable')
        except Exception as e:
            logger.debug(f"Error accessing {url}: {type(e).__name__}")
            return ([], 'unreachable')
        
        # Main URL is accessible, now parse it
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for known blog platforms and add their standard feed URLs first
            domain_lower = urlparse(url).netloc.lower()
            
            # Substack
            if 'substack.com' in domain_lower:
                feed_urls.append(urljoin(url, '/feed'))
                has_blog_indicators = True
            
            # Blogspot
            elif 'blogspot.com' in domain_lower:
                feed_urls.append(urljoin(url, '/feeds/posts/default'))
                feed_urls.append(urljoin(url, '/feeds/posts/default?alt=rss'))
                has_blog_indicators = True
            
            # WordPress
            elif 'wordpress.com' in domain_lower or soup.find('meta', {'name': 'generator', 'content': lambda x: x and 'wordpress' in x.lower()}):
                feed_urls.append(urljoin(url, '/feed/'))
                feed_urls.append(urljoin(url, '/feed'))
                has_blog_indicators = True
            
            # Medium
            elif 'medium.com' in domain_lower:
                feed_urls.append(urljoin(url, '/feed'))
                has_blog_indicators = True
            
            # Ghost
            elif 'ghost.io' in domain_lower:
                feed_urls.append(urljoin(url, '/rss/'))
                feed_urls.append(urljoin(url, '/rss'))
                has_blog_indicators = True
            
            # Look for feed links in HTML
            for link in soup.find_all('link', type=['application/rss+xml', 'application/atom+xml']):
                href = link.get('href')
                if href:
                    feed_urls.append(urljoin(url, href))
                    has_blog_indicators = True
            
            # Check sitemap for additional feed URLs
            sitemap_feeds = self.check_sitemap(url)
            feed_urls.extend(sitemap_feeds)
            if sitemap_feeds:
                has_blog_indicators = True
            
            # Parse navigation menus for blog/RSS links
            nav_keywords = ['blog', 'rss', 'feed', 'atom', 'subscribe', 'news', 'articles', 'posts']
            
            search_elements = soup.find_all(['nav', 'header', 'footer', 'menu', 'aside'])
            search_elements.extend(soup.find_all(['div', 'ul'], class_=lambda x: x and any(
                c in str(x).lower() for c in ['nav', 'menu', 'header', 'top', 'main-menu']
            )))
            search_elements.extend(soup.find_all(['div', 'ul'], id=lambda x: x and any(
                c in str(x).lower() for c in ['nav', 'menu', 'header', 'top-menu']
            )))
            
            for nav_element in search_elements:
                for a in nav_element.find_all('a', href=True):
                    href_lower = a.get('href', '').lower()
                    text_lower = a.get_text().lower().strip()
                    
                    if any(kw in href_lower or kw in text_lower for kw in nav_keywords):
                        has_blog_indicators = True
                        full_url = urljoin(url, a['href'])
                        
                        if 'blog' in href_lower or 'blog' in text_lower:
                            for suffix in ['/feed', '/rss', '/atom']:
                                feed_urls.append(full_url.rstrip('/') + suffix)
                        
                        if any(kw in href_lower for kw in ['rss', 'feed', 'atom', '.xml']):
                            feed_urls.append(full_url)
            
            # Try common feed URLs
            common_feeds = [
                '/feed/', '/feed', '/rss/', '/rss', '/atom/', '/atom',
                '/index.xml', '/rss.xml', '/feed.xml', '/atom.xml',
                '/blog/feed/', '/blog/feed', '/blog/rss/', '/blog/rss'
            ]
            
            for feed_path in common_feeds:
                feed_url = urljoin(url, feed_path)
                if feed_url not in feed_urls:
                    feed_urls.append(feed_url)
            
            if len(feed_urls) > 15:
                feed_urls = feed_urls[:10] + feed_urls[10:15]
            
            if feed_urls:
                return (feed_urls, 'success')
            elif has_blog_indicators:
                return (feed_urls, 'has_blog_indicators')
            else:
                return (feed_urls, 'no_blog_indicators')
        
        except Exception as e:
            logger.debug(f"Error parsing {url}: {type(e).__name__}")
            return ([], 'unreachable')

    def fetch_feed(self, feed_url: str) -> List[Dict]:
        """Fetch and parse RSS/Atom feed, return posts"""
        try:
            domain = extract_domain(feed_url)
            self.enforce_rate_limit(domain)
            
            response = requests.get(feed_url, headers=self.headers, timeout=settings.REQUEST_TIMEOUT, verify=False)
            
            if response.status_code != 200:
                return []
            
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                return []
            
            blog_title = feed.feed.get('title', urlparse(feed_url).netloc)
            
            posts = []
            for entry in feed.entries[:settings.MAX_POSTS_TO_CHECK]:
                try:
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6])
                    
                    content = ''
                    raw_content = ''
                    if hasattr(entry, 'content') and entry.content:
                        raw_content = entry.content[0].get('value', '')
                        content = raw_content
                    elif hasattr(entry, 'summary'):
                        raw_content = entry.summary
                        content = entry.summary
                    
                    content_text = ''
                    if content:
                        soup = BeautifulSoup(content, 'html.parser')
                        content_text = soup.get_text(separator=' ', strip=True)[:500]
                    
                    full_content_text = ''
                    if content:
                        soup = BeautifulSoup(content, 'html.parser')
                        full_content_text = soup.get_text(separator=' ', strip=True)
                    
                    posts.append({
                        'title': entry.get('title', 'No Title'),
                        'link': entry.get('link', ''),
                        'published': pub_date.isoformat() if pub_date else None,
                        'published_timestamp': pub_date.timestamp() if pub_date else 0,
                        'summary': content_text,
                        'full_content': full_content_text,
                        'raw_html_content': raw_content,
                        'blog_name': blog_title,
                        'feed_url': feed_url
                    })
                    
                except Exception as e:
                    logger.warning(f"Error parsing entry: {e}")
                    continue
            
            if posts:
                logger.info(f"{blog_title} ({len(posts)} posts fetched for discovery)")
            
            return posts
            
        except Exception as e:
            if not isinstance(e, (requests.exceptions.RequestException, ValueError)):
                logger.debug(f"Error fetching feed {feed_url}: {e}")
            return []
