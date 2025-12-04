#!/usr/bin/env python3
"""
Recursive Blog Discovery Crawler
Discovers blogs recursively by following links in posts
Goal: Find up to 250 unique blogs, showing only the latest post from each
"""

import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Any, Set, Tuple
import json
import time
from urllib.parse import urljoin, urlparse
import logging
import re
from collections import deque
import argparse
import os
import shutil
import warnings
import random
import urllib.robotparser
from urllib.parse import urljoin, urlparse

import urllib3
# Suppress SSL warnings for unverified HTTPS requests
warnings.filterwarnings('ignore', category=urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import config

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class RecursiveBlogDiscovery:

    """Recursively discover blogs by following references in posts"""
    
    def __init__(self, max_blogs: int = config.MAX_BLOGS_DEFAULT, max_posts_to_check: int = config.MAX_POSTS_TO_CHECK, checkpoint_file: str = config.CHECKPOINT_FILENAME, queue_strategy: str = config.QUEUE_STRATEGY):
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
        self.max_blogs = max_blogs
        self.max_posts_to_check = max_posts_to_check
        self.checkpoint_file = checkpoint_file
        self.checkpoint_interval = config.CHECKPOINT_INTERVAL  # Save every N blogs
        self.queue_strategy = queue_strategy  # Queue strategy: breadth_first, depth_first, random, mixed
        
        # Validate queue strategy
        valid_strategies = ['breadth_first', 'depth_first', 'random', 'mixed']
        if self.queue_strategy not in valid_strategies:
            logger.warning(f"Invalid queue strategy '{self.queue_strategy}', using 'mixed'")
            self.queue_strategy = 'mixed'
        
        self.discovered_blogs: Dict[str, Dict] = {}  # domain -> blog info
        self.blogs_to_process = deque()  # Queue of (blog_url, source_info) tuples
        self.queued_domains: Set[str] = set()  # Domains already in queue (avoid duplicates)
        self.processed_domains: Set[str] = set()
        self.failed_domains: Set[str] = set()  # Domains that failed to access
        self.failed_base_domains: Set[str] = set()  # Base domains to skip entirely
        self.discovery_graph: Dict[str, Dict] = {}  # Track discovery relationships
        
        # Load from checkpoint (includes blacklist data)
        self.load_checkpoint()
        
        # Common blog platforms/indicators
        self.blog_indicators = config.BLOG_INDICATORS
        
        # Keywords that suggest a site is NOT a blog
        self.non_blog_keywords = getattr(config, 'NON_BLOG_KEYWORDS', [])
        
        # Domains to skip (not blogs)
        self.skip_domains = config.SKIP_DOMAINS
        
        # Major sites where if one subdomain fails, blacklist the whole base domain
        # (These are large orgs that won't have random blog subdomains)
        self.blacklist_base_domain_sites = config.BLACKLIST_BASE_DOMAIN_SITES
        
        # Dangerous file extensions to block
        self.dangerous_extensions = config.DANGEROUS_EXTENSIONS
        
        self.allowed_extensions = config.ALLOWED_EXTENSIONS
        
        # Robots.txt cache: domain -> RobotFileParser
        self.robots_cache = {}
        
        # Rate limiting: domain -> last_request_timestamp
        self.domain_last_request = {}
        self.min_delay_between_requests = 2  # seconds between requests to same domain
    
    def save_checkpoint(self):
        """Save current state to checkpoint file"""
        try:
            checkpoint = {
                'discovered_blogs': self.discovered_blogs,
                'blogs_to_process': list(self.blogs_to_process),
                'queued_domains': list(self.queued_domains),
                'processed_domains': list(self.processed_domains),
                'failed_domains': list(self.failed_domains),
                'failed_base_domains': list(self.failed_base_domains),
                'timestamp': datetime.now().isoformat()
            }
            # Ensure the json folder exists
            os.makedirs(config.JSON_DIR, exist_ok=True)
            checkpoint_path = os.path.join(config.JSON_DIR, self.checkpoint_file)
            with open(checkpoint_path, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            logger.info(f"💾 Checkpoint saved: {len(self.discovered_blogs)} blogs, {len(self.blogs_to_process)} queued, {len(self.queued_domains)} pending, {len(self.failed_base_domains)} blacklisted")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
    
    def load_checkpoint(self) -> bool:
        """Load state from checkpoint file if it exists"""
        try:
            # Ensure the json folder exists
            os.makedirs(config.JSON_DIR, exist_ok=True)
            checkpoint_path = os.path.join(config.JSON_DIR, self.checkpoint_file)
            with open(checkpoint_path, 'r') as f:
                checkpoint = json.load(f)
            
            self.discovered_blogs = checkpoint.get('discovered_blogs', {})
            # Convert lists back to tuples (JSON serializes tuples as lists)
            blogs_queue = checkpoint.get('blogs_to_process', [])
            self.blogs_to_process = deque(
                tuple(item) if isinstance(item, list) else item 
                for item in blogs_queue
            )
            # Load queued_domains from checkpoint (or rebuild if not present)
            self.queued_domains = set(checkpoint.get('queued_domains', []))
            if not self.queued_domains:
                # Rebuild from queue if not in checkpoint (backward compatibility)
                self.queued_domains = {self.extract_domain(url) for url, _ in self.blogs_to_process if self.extract_domain(url)}
            self.processed_domains = set(checkpoint.get('processed_domains', []))
            self.failed_domains = set(checkpoint.get('failed_domains', []))
            self.failed_base_domains = set(checkpoint.get('failed_base_domains', []))
            
            if self.discovered_blogs:
                logger.info(f"📂 Resumed from checkpoint: {len(self.discovered_blogs)} blogs, {len(self.blogs_to_process)} queued, {len(self.queued_domains)} pending")
                logger.info(f"   Blacklist: {len(self.failed_domains)} domains, {len(self.failed_base_domains)} base domains")
                logger.info(f"   Checkpoint from: {checkpoint.get('timestamp', 'unknown')}")
                return True
            return False
        except FileNotFoundError:
            logger.info("No checkpoint file found, starting fresh")
            return False
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return False
    
    def is_allowed_by_robots(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt"""
        try:
            domain = self.extract_domain(url)
            if not domain:
                return True
                
            base_url = f"https://{domain}"
            robots_url = urljoin(base_url, '/robots.txt')
            
            # Check cache
            if domain in self.robots_cache:
                rp = self.robots_cache[domain]
            else:
                rp = urllib.robotparser.RobotFileParser()
                rp.set_url(robots_url)
                try:
                    # Fetch robots.txt with timeout
                    # Note: RobotFileParser.read() uses default urllib which might not have our headers/timeout
                    # So we fetch manually and parse
                    response = requests.get(robots_url, headers=self.headers, timeout=5, verify=False)
                    if response.status_code == 200:
                        rp.parse(response.text.splitlines())
                    else:
                        # If robots.txt doesn't exist or fails, allow all (default behavior)
                        rp.allow_all = True
                except:
                    rp.allow_all = True
                
                self.robots_cache[domain] = rp
                
            # Check permission
            # We use '*' as user-agent since we don't have a specific bot name, 
            # or we could use 'RSS-Crawler' if we defined one.
            # Using our User-Agent string might be too long/complex for simple matching,
            # so we check for '*' (all bots) and maybe a specific one if we had it.
            return rp.can_fetch("*", url)
            
        except Exception as e:
            # If any error occurs during check, default to allowed to avoid blocking valid sites due to bugs
            # logger.debug(f"Robots check error for {url}: {e}")
            return True

    def is_safe_url(self, url: str) -> bool:
        """Check if URL is safe (no dangerous extensions or suspicious patterns)"""
        try:
            url_lower = url.lower()
            parsed = urlparse(url_lower)
            path = parsed.path
            
            # Check for dangerous file extensions
            for ext in self.dangerous_extensions:
                if path.endswith(ext):
                    logger.warning(f"🚫 Blocked dangerous URL: {url} (extension: {ext})")
                    return False
            
            # Check for suspicious patterns
            suspicious_patterns = [
                'download', 'exec', 'install', 'setup',
                '/bin/', '/sbin/', '/usr/bin/',
                'malware', 'virus', 'exploit', 'hack',
                'phishing', 'scam', 'fraud'
            ]
            
            for pattern in suspicious_patterns:
                if pattern in url_lower:
                    # Allow common blog paths that might contain these words
                    if pattern in ['download', 'install'] and any(blog_word in url_lower for blog_word in ['blog', 'post', 'article']):
                        continue
                    logger.warning(f"🚫 Blocked suspicious URL: {url} (pattern: {pattern})")
                    return False
            
            return True
        except:
            return False
    
    def is_likely_blog(self, url: str) -> bool:
        """Check if URL is likely a blog"""
        try:
            # First check if URL is safe
            if not self.is_safe_url(url):
                return False
            
            domain = urlparse(url).netloc.lower()
            
            # Skip known non-blog domains
            for skip in self.skip_domains:
                if skip in domain:
                    return False
            
            # Check for allowed extensions (TLDs)
            if not any(domain.endswith(ext) for ext in self.allowed_extensions):
                return False
            
            # Check for blog indicators in domain or path
            url_lower = url.lower()
            for indicator in self.blog_indicators:
                if indicator in url_lower:
                    return True
            
            # Accept domains that look like personal/organizational sites
            # (e.g., name.com, organization.org)
            if domain.count('.') <= 2 and not domain.startswith('www.'):
                return True
                
            return False
        except:
            return False
    
    def extract_domain(self, url: str) -> str:
        """Extract clean domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return ""
    
    def get_base_domain(self, domain: str) -> str:
        """Extract base domain (e.g., 'blog.example.com' -> 'example.com')"""
        if not domain:
            return ""
        parts = domain.split('.')
        # If it's already a base domain (2 parts) or has common TLDs
        if len(parts) <= 2:
            return domain
        # For subdomains, get the last 2 parts (base domain)
        # Exception: keep 3 parts for .co.uk, .com.ac etc
        if len(parts) >= 3 and parts[-2] in ['co', 'com', 'ac', 'gov', 'org', 'net']:
            return '.'.join(parts[-3:])
        return '.'.join(parts[-2:])
    
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
    
    def add_to_queue(self, blog_url: str, source_info: dict = None, new_depth: int = 0):
        """Add a blog to the queue based on the configured strategy
        
        Args:
            blog_url: URL of the blog to add
            source_info: Discovery source information
            new_depth: Depth level of this blog in the discovery graph
        """
        blog_item = (blog_url, source_info)
        
        if self.queue_strategy == 'breadth_first':
            # FIFO - append to end (processes seeds first, then level by level)
            self.blogs_to_process.append(blog_item)
            
        elif self.queue_strategy == 'depth_first':
            # LIFO - prepend to front (explores deep into network quickly)
            self.blogs_to_process.appendleft(blog_item)
            
        elif self.queue_strategy == 'random':
            # Insert at random position
            if len(self.blogs_to_process) == 0:
                self.blogs_to_process.append(blog_item)
            else:
                insert_pos = random.randint(0, len(self.blogs_to_process))
                temp_list = list(self.blogs_to_process)
                temp_list.insert(insert_pos, blog_item)
                self.blogs_to_process = deque(temp_list)
                
        elif self.queue_strategy == 'mixed':
            # 50% chance to prioritize newly discovered blogs (insert in first half)
            if new_depth > 0 and random.random() < 0.5 and len(self.blogs_to_process) > 0:
                # Insert in first half of queue
                insert_pos = random.randint(0, max(1, len(self.blogs_to_process) // 2))
                temp_list = list(self.blogs_to_process)
                temp_list.insert(insert_pos, blog_item)
                self.blogs_to_process = deque(temp_list)
            else:
                # Add to end normally
                self.blogs_to_process.append(blog_item)
    
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
    
    def discover_feeds(self, url: str) -> tuple[List[str], str]:
        """Try to discover RSS/Atom feeds from a URL
        
        Returns:
            tuple: (list of feed URLs, status string)
            status can be: 'success', 'has_blog_indicators', 'no_blog_indicators', 'unreachable'
        """
        feed_urls = []
        has_blog_indicators = False
        
        # Enforce rate limiting for this domain
        domain = self.extract_domain(url)
        self.enforce_rate_limit(domain)
        
        try:
            # Try to fetch the main page first - early fail if unreachable
            response = requests.get(url, headers=self.headers, timeout=config.REQUEST_TIMEOUT, verify=False)
            response.raise_for_status()  # Raise error for bad status codes
        except requests.exceptions.Timeout:
            logger.debug(f"Timeout accessing {url}")
            return ([], 'unreachable')
        except requests.exceptions.ConnectionError:
            logger.debug(f"Connection error accessing {url}")
            return ([], 'unreachable')
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [403, 404, 410, 451]:  # Forbidden, Not Found, Gone, Unavailable
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
            
            # Substack - has a standard /feed endpoint
            if 'substack.com' in domain_lower:
                feed_urls.append(urljoin(url, '/feed'))
                has_blog_indicators = True
            
            # Blogspot - uses /feeds/posts/default
            elif 'blogspot.com' in domain_lower:
                feed_urls.append(urljoin(url, '/feeds/posts/default'))
                feed_urls.append(urljoin(url, '/feeds/posts/default?alt=rss'))
                has_blog_indicators = True
            
            # WordPress - standard feed URLs
            elif 'wordpress.com' in domain_lower or soup.find('meta', {'name': 'generator', 'content': lambda x: x and 'wordpress' in x.lower()}):
                feed_urls.append(urljoin(url, '/feed/'))
                feed_urls.append(urljoin(url, '/feed'))
                has_blog_indicators = True
            
            # Medium - uses /feed endpoint
            elif 'medium.com' in domain_lower:
                feed_urls.append(urljoin(url, '/feed'))
                has_blog_indicators = True
            
            # Ghost - uses /rss endpoint
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
            
            # Parse navigation menus for blog/RSS links (improved detection)
            nav_keywords = ['blog', 'rss', 'feed', 'atom', 'subscribe', 'news', 'articles', 'posts']
            
            # Search in semantic elements and divs with navigation-related classes
            search_elements = soup.find_all(['nav', 'header', 'footer', 'menu', 'aside'])
            # Also search divs/uls with nav/menu-like classes or ids
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
                    
                    # Check if link contains blog/feed keywords
                    if any(kw in href_lower or kw in text_lower for kw in nav_keywords):
                        has_blog_indicators = True  # Found blog-related links
                        full_url = urljoin(url, a['href'])
                        
                        # If it's a blog page, try feed variants
                        if 'blog' in href_lower or 'blog' in text_lower:
                            for suffix in ['/feed', '/rss', '/atom']:
                                feed_urls.append(full_url.rstrip('/') + suffix)
                        
                        # If it looks like a direct feed link
                        if any(kw in href_lower for kw in ['rss', 'feed', 'atom', '.xml']):
                            feed_urls.append(full_url)
            
            # Try common feed URLs (prioritize most likely ones)
            common_feeds = [
                '/feed/', '/feed', '/rss/', '/rss', '/atom/', '/atom',
                '/index.xml', '/rss.xml', '/feed.xml', '/atom.xml',
                '/blog/feed/', '/blog/feed', '/blog/rss/', '/blog/rss'
            ]
            
            # Only add feeds that aren't already in the list
            for feed_path in common_feeds:
                feed_url = urljoin(url, feed_path)
                if feed_url not in feed_urls:
                    feed_urls.append(feed_url)
            
            # Limit total feed URLs to try (prioritize platform-specific and discovered feeds)
            if len(feed_urls) > 15:
                # Keep first 10 (platform-specific + discovered), then add top common feeds
                feed_urls = feed_urls[:10] + feed_urls[10:15]
            
            # Determine status
            if feed_urls:
                return (feed_urls, 'success')  # Return all candidates (will try in order)
            elif has_blog_indicators:
                return (feed_urls, 'has_blog_indicators')  # Has blog links but no feeds found
            else:
                return (feed_urls, 'no_blog_indicators')  # No blog presence at all
        
        except Exception as e:
            # Parsing error after successful fetch
            logger.debug(f"Error parsing {url}: {type(e).__name__}")
            return ([], 'unreachable')
    
    def fetch_feed(self, feed_url: str) -> List[Dict]:
        """Fetch and parse RSS/Atom feed, return posts"""
        try:
            # Enforce rate limiting for this domain
            domain = self.extract_domain(feed_url)
            self.enforce_rate_limit(domain)
            
            # Try to fetch the feed with a timeout
            response = requests.get(feed_url, headers=self.headers, timeout=config.REQUEST_TIMEOUT, verify=False)
            
            # Check if we got a valid response
            if response.status_code != 200:
                return []
            
            feed = feedparser.parse(response.content)
            
            # Suppress feed parsing errors - they're too verbose and mostly harmless
            # feedparser sets bozo=1 for minor XML issues that don't affect parsing
            
            if not feed.entries:
                return []
            
            blog_title = feed.feed.get('title', urlparse(feed_url).netloc)
            
            posts = []
            # Get up to max_posts_to_check for discovery
            for entry in feed.entries[:self.max_posts_to_check]:
                try:
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6])
                    
                    # Get content
                    content = ''
                    raw_content = ''
                    if hasattr(entry, 'content') and entry.content:
                        raw_content = entry.content[0].get('value', '')
                        content = raw_content
                    elif hasattr(entry, 'summary'):
                        raw_content = entry.summary
                        content = entry.summary
                    
                    # Clean HTML from content for summary
                    content_text = ''
                    if content:
                        soup = BeautifulSoup(content, 'html.parser')
                        content_text = soup.get_text(separator=' ', strip=True)[:500]
                    
                    # Keep full content text for complete body
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
                logger.info(f"  ✓ {blog_title} ({len(posts)} posts fetched for discovery)")
            
            return posts
            
        except Exception as e:
            # Suppress normal feed fetch errors - most feeds won't work and that's expected
            # Only log if it's an unexpected error type
            if not isinstance(e, (requests.exceptions.RequestException, ValueError)):
                logger.debug(f"Error fetching feed {feed_url}: {e}")
            return []
    
    def extract_blog_links(self, content: str, source_url: str) -> List[str]:
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
                if self.is_likely_blog(full_url):
                    # Get the root domain URL
                    parsed = urlparse(full_url)
                    root_url = f"{parsed.scheme}://{parsed.netloc}"
                    links.append(root_url)
            
            return list(set(links))  # Unique links
            
        except Exception as e:
            return []
    
    def crawl_blog(self, blog_url: str, source_info: Dict = None, attempt_number: int = 1) -> bool:
        """Crawl a single blog and extract its latest post + discover new blogs
        
        Args:
            blog_url: URL of the blog to crawl
            source_info: Dict with 'source_blog', 'source_post_title', 'source_post_link' if discovered from another blog
            attempt_number: The sequential attempt number (for logging)
        """
    
        domain = self.extract_domain(blog_url)
        
        if not domain:
            logger.info(f"  ⚠️  Skipped (no domain): {blog_url}")
            return False
        
        # Check if base domain is blacklisted
        base_domain = self.get_base_domain(domain)
        if base_domain in self.failed_base_domains:
            logger.info(f"  🚫 Skipped (base domain blacklisted): {domain} [{base_domain}]")
            self.processed_domains.add(domain)
            return False
            
        if domain in self.processed_domains:
            logger.info(f"  ⏭️  Skipped (already processed): {domain}")
            return False
        
        self.processed_domains.add(domain)
        
        # Check robots.txt
        if not self.is_allowed_by_robots(blog_url):
            logger.info(f"  🚫 Skipped (robots.txt disallowed): {blog_url}")
            return False
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🔍 Crawling blog #{attempt_number}: {blog_url}")
        logger.info(f"{'='*80}")
        
        # Discover feeds
        feed_urls, status = self.discover_feeds(blog_url)
        
        # Check if this is a subdomain (e.g., blog.example.com vs example.com)
        is_subdomain = domain != base_domain
        
        # Blacklist based on status
        if status == 'unreachable':
            self.failed_domains.add(domain)
            # Only blacklist base domain if we're NOT on a blog subdomain
            if not is_subdomain:
                logger.info(f"  🚫 Website unreachable - blacklisting base domain {base_domain}")
                self.failed_base_domains.add(base_domain)
            else:
                logger.info(f"  🚫 Website unreachable (subdomain only, base domain {base_domain} still allowed)")
            return False
        
        if status == 'no_blog_indicators':
            self.failed_domains.add(domain)
            # Only blacklist base domain if we're NOT on a blog subdomain
            if not is_subdomain:
                logger.info(f"  ℹ️  No blog presence detected - blacklisting base domain {base_domain}")
                self.failed_base_domains.add(base_domain)
            else:
                logger.info(f"  ℹ️  No blog presence on subdomain (base domain {base_domain} still allowed)")
            return False
        
        if not feed_urls:
            if status == 'has_blog_indicators':
                # Site has blog links but feeds not working - don't blacklist base domain
                logger.info(f"  ⚠️  Has blog indicators but no feeds found (trying subdomains later)")
                self.failed_domains.add(domain)
                return False
            else:
                # Shouldn't reach here, but handle it
                logger.info(f"  ⚠️  No feeds found")
                self.failed_domains.add(domain)
                return False
        
        # Try each feed URL until we find a working one
        logger.info(f"  🔍 Trying {len(feed_urls)} feed URLs...")
        for i, feed_url in enumerate(feed_urls, 1):
            logger.debug(f"    [{i}/{len(feed_urls)}] {feed_url}")
            posts = self.fetch_feed(feed_url)
            
            if posts:
                # SUCCESS! Found a working feed - stop trying other URLs
                logger.info(f"  ✅ Found working feed: {feed_url}")
                # Store the blog with its latest post
                latest_post = max(posts, key=lambda p: p['published_timestamp'])
                
                # Add source information if this was discovered from another blog
                discovery_source = None
                blog_depth = 0  # Default for seed blogs
                if source_info:
                    discovery_source = {
                        'source_blog': source_info.get('source_blog'),
                        'source_blog_name': source_info.get('source_blog_name'),
                        'source_post_title': source_info.get('source_post_title'),
                        'source_post_link': source_info.get('source_post_link')
                    }
                    # Increment depth from parent
                    blog_depth = source_info.get('parent_depth', 0) + 1
                
                self.discovered_blogs[domain] = {
                    'url': blog_url,
                    'name': latest_post['blog_name'],
                    'feed_url': feed_url,
                    'latest_post': {
                        'title': latest_post['title'],
                        'link': latest_post['link'],
                        'published': latest_post['published'],
                        'summary': latest_post['summary'],
                        'full_content': latest_post.get('full_content', ''),
                        'raw_html': latest_post.get('raw_html_content', '')
                    },
                    'discovered_at': datetime.now().isoformat(),
                    'depth': blog_depth,
                    'discovered_from': discovery_source
                }
                
                logger.info(f"  ✅ Added blog: {latest_post['blog_name']}")
                logger.info(f"  📝 Latest post (1 stored): {latest_post['title']}")
                logger.info(f"  📅 Published: {latest_post['published']}")
                if discovery_source:
                    logger.info(f"  🔍 Discovered from: {discovery_source['source_blog_name']}")
                    logger.info(f"     via post: {discovery_source['source_post_title'][:60]}...")
                
                # Extract blog links from all posts for discovery
                logger.info(f"  🔎 Scanning {len(posts)} posts for new blog links...")
                new_blogs_with_source = {}  # blog_url -> source_post mapping
                for post in posts:
                    blog_links = self.extract_blog_links(
                        post['raw_html_content'], 
                        post['link']
                    )
                    # Track which post each blog was found in
                    for blog_link in blog_links:
                        if blog_link not in new_blogs_with_source:
                            new_blogs_with_source[blog_link] = {
                                'source_blog': blog_url,
                                'source_blog_name': latest_post['blog_name'],
                                'source_post_title': post['title'],
                                'source_post_link': post['link']
                            }
                
                # Add new blogs to queue with priority for deeper discoveries
                newly_added = []
                current_depth = self.discovered_blogs.get(domain, {}).get('depth', 0)
                
                for new_blog_url, source_info in new_blogs_with_source.items():
                    new_domain = self.extract_domain(new_blog_url)
                    # Skip if already processed or already in queue
                    if new_domain and new_domain not in self.processed_domains and new_domain not in self.queued_domains:
                        # Add depth information to source_info
                        source_info['parent_depth'] = current_depth
                        new_depth = current_depth + 1
                        
                        # Add to queue using configured strategy
                        self.add_to_queue(new_blog_url, source_info, new_depth)
                        
                        # Track that this domain is now queued
                        self.queued_domains.add(new_domain)
                        newly_added.append(new_blog_url)
                
                if newly_added:
                    logger.info(f"  🔗 DISCOVERED {len(newly_added)} NEW BLOGS from {len(posts)} posts:")
                    for i, new_url in enumerate(newly_added[:5], 1):  # Show first 5
                        logger.info(f"     {i}. {new_url}")
                    if len(newly_added) > 5:
                        logger.info(f"     ... and {len(newly_added) - 5} more")
                else:
                    logger.info(f"  ℹ️  No new blogs found in {len(posts)} posts")
                
                return True
        
        # No valid feeds found after trying all URLs
        self.failed_domains.add(domain)
        # Only blacklist base domain for major sites
        if base_domain in self.blacklist_base_domain_sites:
            logger.info(f"  ⚠️  No valid feeds - blacklisting base domain {base_domain}")
            self.failed_base_domains.add(base_domain)
        else:
            logger.info(f"  ⚠️  No valid feeds (domain-only blacklist)")
        return False
    
    def run_discovery(self, seed_blogs: List[str]):
        """Run blog discovery"""
        logger.info("="*80)
        logger.info("🚀 BLOG DISCOVERY")
        logger.info(f"📊 Target: {self.max_blogs} blogs | Posts per blog: {self.max_posts_to_check}")
        logger.info(f"🌱 Seed blogs: {len(seed_blogs)}")
        logger.info(f"🎯 Queue strategy: {self.queue_strategy}")
        logger.info("="*80 + "\n")
        
        # Add seed blogs to queue (skip if already processed from checkpoint)
        for blog_url in seed_blogs:
            domain = self.extract_domain(blog_url)
            if domain not in self.processed_domains:
                self.blogs_to_process.append((blog_url, None))  # Seed blogs have no source
        
        # Rebuild queued_domains after adding seeds
        self.queued_domains = {self.extract_domain(url) for url, _ in self.blogs_to_process if self.extract_domain(url)}
        
        # Process blogs until we hit the limit or run out
        blogs_crawled_since_checkpoint = 0
        attempt_counter = 0  # Track total attempts (including failures)
        
        while self.blogs_to_process and len(self.discovered_blogs) < self.max_blogs:
            # Unpack blog URL and source info
            blog_item = self.blogs_to_process.popleft()
            if isinstance(blog_item, (tuple, list)) and len(blog_item) == 2:
                blog_url, source_info = blog_item
            elif isinstance(blog_item, str):
                # Old format: just a URL string
                blog_url, source_info = blog_item, None
            else:
                logger.warning(f"⚠️  Invalid queue item format: {type(blog_item)} - {blog_item}")
                continue
            
            # Increment attempt counter
            attempt_counter += 1
            
            # Remove from queued set since we're processing it now
            domain = self.extract_domain(blog_url)
            self.queued_domains.discard(domain)
            
            try:
                success = self.crawl_blog(blog_url, source_info, attempt_counter)
                
                if success:
                    blogs_crawled_since_checkpoint += 1
                    
                    # Save checkpoint periodically
                    if blogs_crawled_since_checkpoint >= self.checkpoint_interval:
                        self.save_checkpoint()
                        blogs_crawled_since_checkpoint = 0
                
                time.sleep(1)  # Rate limiting
                
            except KeyboardInterrupt:
                logger.warning("\n⚠️  Interrupted by user! Saving checkpoint...")
                self.save_checkpoint()
                raise
            except Exception as e:
                logger.error(f"Error crawling {blog_url}: {e}")
                continue
            
            # Progress update - show every iteration to help debug
            processed_count = len(self.processed_domains)
            logger.info(f"📊 Progress: {len(self.discovered_blogs)}/{self.max_blogs} blogs | Processed: {processed_count} | Queue: {len(self.blogs_to_process)} waiting")
        
        # Final checkpoint save
        self.save_checkpoint()
        
        logger.info("\n" + "="*80)
        logger.info("✅ DISCOVERY COMPLETE!")
        logger.info("="*80)
        logger.info(f"📚 Total blogs discovered: {len(self.discovered_blogs)}")
        logger.info(f"📋 Blogs remaining in queue: {len(self.blogs_to_process)}")
        logger.info("="*80 + "\n")
        
        return self.discovered_blogs
    
    def save_results(self, filename: str = 'discovery_results.json'):
        """Save discovered blogs to JSON in the json folder"""
        # Ensure the json folder exists
        os.makedirs(config.JSON_DIR, exist_ok=True)
        results_path = os.path.join(config.JSON_DIR, filename)
        """Save discovered blogs to JSON"""
        # Convert to list for JSON serialization
        blogs_list = [
            {
                'domain': domain,
                **info
            }
            for domain, info in self.discovered_blogs.items()
        ]
        
        # Sort by published date (newest first)
        blogs_list.sort(
            key=lambda b: b['latest_post']['published'] or '', 
            reverse=True
        )
        
        results = {
            'crawled_at': datetime.now().isoformat(),
            'total_blogs': len(blogs_list),
            'target_blogs': self.max_blogs,
            'blogs': blogs_list
        }
        
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✅ Saved {len(blogs_list)} blogs to {filename}")



def archive_old_results():
    """Archive old results to archive directory"""
    archive_dir = 'archive'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create archive directory if it doesn't exist
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
        logger.info(f"📁 Created archive directory: {archive_dir}")
    
    # Files to archive (now located in the json directory)
    json_files_to_archive = [
        'crawler_checkpoint.json',
        'discovery_results.json'
    ]
    
    archived_count = 0
    for filename in json_files_to_archive:
        source_path = os.path.join(config.JSON_DIR, filename)
        if os.path.exists(source_path):
            archive_name = f"{os.path.splitext(filename)[0]}_{timestamp}{os.path.splitext(filename)[1]}"
            archive_path = os.path.join(archive_dir, archive_name)
            shutil.move(source_path, archive_path)
            logger.info(f"📦 Archived: {source_path} -> {archive_path}")
            archived_count += 1
    
    if archived_count > 0:
        logger.info(f"✅ Archived {archived_count} files to {archive_dir}/")
    else:
        logger.info("ℹ️  No files to archive")
    
    return archived_count


def load_seeds(filename: str) -> List[str]:
    """Load seed blogs from a text file"""
    seeds = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                # Strip whitespace
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                seeds.append(line)
        logger.info(f"🌱 Loaded {len(seeds)} seed blogs from {filename}")
        return seeds
    except FileNotFoundError:
        logger.warning(f"⚠️  Seed file {filename} not found!")
        return []
    except Exception as e:
        logger.warning(f"⚠️  Error loading seeds from {filename}: {e}")
        return []


def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Recursive Blog Discovery Crawler',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python discover.py                            # Resume from checkpoint
  python discover.py --fresh                    # Archive old results and start fresh
  python discover.py --strategy breadth_first   # Use breadth-first (seed blogs first)
  python discover.py --strategy depth_first     # Use depth-first (explore deeply)
        """
    )
    parser.add_argument(
        '--fresh',
        action='store_true',
        help='Archive old results and start fresh discovery'
    )
    parser.add_argument(
        '--strategy',
        choices=['breadth_first', 'depth_first', 'random', 'mixed'],
        default=config.QUEUE_STRATEGY,
        help='Queue strategy: breadth_first (seeds first), depth_first (explore deep), random, or mixed (default from config)'
    )
    
    args = parser.parse_args()
    
    # Handle fresh start
    if args.fresh:
        logger.info("\n" + "="*80)
        logger.info("🆕 FRESH START MODE")
        logger.info("="*80)
        archive_old_results()
        logger.info("")
    
    # Seed blogs - high quality blogs from:
    # https://statmodeling.stat.columbia.edu/blogs-i-read/
    
    # Load seeds from file
    seed_blogs = load_seeds('seeds.txt')
    
    if not seed_blogs:
        logger.error("❌ No seed blogs found! Please check seeds.txt")
        return
    
    crawler = RecursiveBlogDiscovery(max_blogs=250, max_posts_to_check=20, queue_strategy=args.strategy)
    
    # seed_blogs = seed_blogs[0 : 10]  # Limit for testing
    # Run discovery
    discovered_blogs = crawler.run_discovery(seed_blogs)
    
    # Save results
    crawler.save_results('discovery_results.json')
    
    # Show top blogs
    logger.info("\n🌟 Sample of Discovered Blogs:")
    blogs_list = list(discovered_blogs.items())[:20]
    for i, (domain, info) in enumerate(blogs_list, 1):
        logger.info(f"\n{i}. {info['name']}")
        logger.info(f"   {info['url']}")
        logger.info(f"   Latest: {info['latest_post']['title'][:60]}...")


if __name__ == "__main__":
    main()
