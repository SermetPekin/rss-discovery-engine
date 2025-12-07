import os
import json
import time
import random
import logging
import warnings
from collections import deque
from datetime import datetime
from typing import List, Dict, Any, Set, Tuple, Optional

import urllib3
# Suppress SSL warnings for unverified HTTPS requests
warnings.filterwarnings('ignore', category=urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config import Settings
from models import BlogInfo, BlogPost, DiscoveryState
from .utils import extract_domain, get_base_domain
from .validation import Validator
from .network import Fetcher
from .parser import extract_blog_links

# Initialize settings
settings = Settings()
logger = logging.getLogger(__name__)

class RecursiveBlogDiscovery:
    """Recursively discover blogs by following references in posts"""
    
    def __init__(self, max_blogs: int = settings.MAX_BLOGS_DEFAULT, max_posts_to_check: int = settings.MAX_POSTS_TO_CHECK, checkpoint_file: str = settings.CHECKPOINT_FILENAME, queue_strategy: str = settings.QUEUE_STRATEGY, load_from_checkpoint: str = None):
        self.max_blogs = max_blogs
        self.max_posts_to_check = max_posts_to_check
        self.checkpoint_file = checkpoint_file
        self.load_from_checkpoint_path = load_from_checkpoint
        self.checkpoint_interval = settings.CHECKPOINT_INTERVAL
        self.queue_strategy = queue_strategy
        
        # Validate queue strategy
        valid_strategies = ['breadth_first', 'depth_first', 'random', 'mixed']
        if self.queue_strategy not in valid_strategies:
            logger.warning(f"Invalid queue strategy '{self.queue_strategy}', using 'mixed'")
            self.queue_strategy = 'mixed'
        
        # Components
        self.validator = Validator()
        self.fetcher = Fetcher()
        
        # State management using Pydantic models
        self.state = DiscoveryState()
        self.blogs_to_process = deque()
        
        # Load from checkpoint
        self.load_checkpoint()
        
    def save_checkpoint(self):
        """Save current state to checkpoint file"""
        try:
            # Update state object from working variables
            self.state.blogs_to_process = list(self.blogs_to_process)
            self.state.timestamp = datetime.now()
            
            # Ensure the json folder exists
            os.makedirs(settings.JSON_DIR, exist_ok=True)
            checkpoint_path = os.path.join(settings.JSON_DIR, self.checkpoint_file)
            
            with open(checkpoint_path, 'w') as f:
                f.write(self.state.model_dump_json(indent=2))
                
            logger.info(f"Checkpoint saved: {len(self.state.discovered_blogs)} blogs, {len(self.state.blogs_to_process)} queued, {len(self.state.queued_domains)} pending, {len(self.state.failed_base_domains)} blacklisted")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
    
    def load_checkpoint(self) -> bool:
        """Load state from checkpoint file if it exists"""
        try:
            # Determine which file to load
            if self.load_from_checkpoint_path:
                checkpoint_path = self.load_from_checkpoint_path
                logger.info(f"Loading specific checkpoint: {checkpoint_path}")
            else:
                # Ensure the json folder exists
                os.makedirs(settings.JSON_DIR, exist_ok=True)
                checkpoint_path = os.path.join(settings.JSON_DIR, self.checkpoint_file)
            
            if not os.path.exists(checkpoint_path):
                if self.load_from_checkpoint_path:
                    logger.error(f"Specified checkpoint file not found: {checkpoint_path}")
                else:
                    logger.info("No checkpoint file found, starting fresh")
                return False
                
            with open(checkpoint_path, 'r') as f:
                checkpoint_data = json.load(f)
            
            # Validate and load into state object
            self.state = DiscoveryState.model_validate(checkpoint_data)
            
            # Restore working queue
            self.blogs_to_process = deque(self.state.blogs_to_process)
            
            # Backward compatibility: if queued_domains is empty but we have items in queue
            if not self.state.queued_domains and self.blogs_to_process:
                self.state.queued_domains = {extract_domain(url) for url, _ in self.blogs_to_process if extract_domain(url)}
            
            if self.state.discovered_blogs:
                logger.info(f"Resumed from checkpoint: {len(self.state.discovered_blogs)} blogs, {len(self.state.blogs_to_process)} queued, {len(self.state.queued_domains)} pending")
                logger.info(f"Blacklist: {len(self.state.failed_domains)} domains, {len(self.state.failed_base_domains)} base domains")
                logger.info(f"Checkpoint from: {self.state.timestamp}")
                return True
            return False
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return False

    def add_to_queue(self, blog_url: str, source_info: dict = None, new_depth: int = 0):
        """Add a blog to the queue based on the configured strategy"""
        blog_item = (blog_url, source_info)
        
        if self.queue_strategy == 'breadth_first':
            self.blogs_to_process.append(blog_item)
            
        elif self.queue_strategy == 'depth_first':
            self.blogs_to_process.appendleft(blog_item)
            
        elif self.queue_strategy == 'random':
            if len(self.blogs_to_process) == 0:
                self.blogs_to_process.append(blog_item)
            else:
                insert_pos = random.randint(0, len(self.blogs_to_process))
                temp_list = list(self.blogs_to_process)
                temp_list.insert(insert_pos, blog_item)
                self.blogs_to_process = deque(temp_list)
                
        elif self.queue_strategy == 'mixed':
            if new_depth > 0 and random.random() < 0.5 and len(self.blogs_to_process) > 0:
                insert_pos = random.randint(0, max(1, len(self.blogs_to_process) // 2))
                temp_list = list(self.blogs_to_process)
                temp_list.insert(insert_pos, blog_item)
                self.blogs_to_process = deque(temp_list)
            else:
                self.blogs_to_process.append(blog_item)

    def crawl_blog(self, blog_url: str, source_info: Dict = None, attempt_number: int = 1) -> bool:
        """Crawl a single blog and extract its latest post + discover new blogs"""
    
        domain = extract_domain(blog_url)
        
        if not domain:
            logger.info(f"Skipped (no domain): {blog_url}")
            return False
        
        # Check if base domain is blacklisted
        base_domain = get_base_domain(domain)
        if base_domain in self.state.failed_base_domains:
            logger.info(f"Skipped (base domain blacklisted): {domain} [{base_domain}]")
            self.state.processed_domains.add(domain)
            return False
            
        if domain in self.state.processed_domains:
            logger.info(f"Skipped (already processed): {domain}")
            return False
        
        self.state.processed_domains.add(domain)
        
        # Check robots.txt
        if not self.validator.is_allowed_by_robots(blog_url):
            logger.info(f"Skipped (robots.txt disallowed): {blog_url}")
            return False
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Crawling blog #{attempt_number}: {blog_url}")
        logger.info(f"{'='*60}")
        
        # Discover feeds
        feed_urls, status = self.fetcher.discover_feeds(blog_url)
        
        # Check if this is a subdomain
        is_subdomain = domain != base_domain
        
        # Blacklist based on status
        if status == 'unreachable':
            self.state.failed_domains.add(domain)
            if not is_subdomain:
                logger.info(f"Website unreachable - blacklisting base domain {base_domain}")
                self.state.failed_base_domains.add(base_domain)
            else:
                logger.info(f"Website unreachable (subdomain only, base domain {base_domain} still allowed)")
            return False
        
        if status == 'no_blog_indicators':
            self.state.failed_domains.add(domain)
            if not is_subdomain:
                logger.info(f"No blog presence detected - blacklisting base domain {base_domain}")
                self.state.failed_base_domains.add(base_domain)
            else:
                logger.info(f"No blog presence on subdomain (base domain {base_domain} still allowed)")
            return False
        
        if not feed_urls:
            if status == 'has_blog_indicators':
                logger.info(f"Has blog indicators but no feeds found (trying subdomains later)")
                self.state.failed_domains.add(domain)
                return False
            else:
                logger.info(f"No feeds found")
                self.state.failed_domains.add(domain)
                return False
        
        # Try each feed URL
        logger.info(f"Trying {len(feed_urls)} feed URLs...")
        for i, feed_url in enumerate(feed_urls, 1):
            logger.debug(f"[{i}/{len(feed_urls)}] {feed_url}")
            posts = self.fetcher.fetch_feed(feed_url)
            
            if posts:
                logger.info(f"Found working feed: {feed_url}")
                latest_post = max(posts, key=lambda p: p['published_timestamp'])
                
                discovery_source = None
                blog_depth = 0
                if source_info:
                    discovery_source = {
                        'source_blog': source_info.get('source_blog'),
                        'source_blog_name': source_info.get('source_blog_name'),
                        'source_post_title': source_info.get('source_post_title'),
                        'source_post_link': source_info.get('source_post_link')
                    }
                    blog_depth = source_info.get('parent_depth', 0) + 1
                
                blog_info = BlogInfo(
                    url=blog_url,
                    name=latest_post['blog_name'],
                    feed_url=feed_url,
                    latest_post=BlogPost(
                        title=latest_post['title'],
                        link=latest_post['link'],
                        published=latest_post['published'],
                        summary=latest_post['summary'],
                        full_content=latest_post.get('full_content', ''),
                        raw_html_content=latest_post.get('raw_html_content', '')
                    ),
                    discovered_at=datetime.now(),
                    depth=blog_depth,
                    discovered_from=discovery_source
                )
                
                self.state.discovered_blogs[domain] = blog_info
                
                logger.info(f"Added blog: {latest_post['blog_name']}")
                logger.info(f"Latest post: {latest_post['title']}")
                logger.info(f"Published: {latest_post['published']}")
                if discovery_source:
                    logger.info(f"Discovered from: {discovery_source['source_blog_name']}")
                    logger.info(f"via post: {discovery_source['source_post_title'][:60]}...")
                
                logger.info(f"Scanning {len(posts)} posts for new blog links...")
                new_blogs_with_source = {}
                for post in posts:
                    blog_links = extract_blog_links(
                        post['raw_html_content'], 
                        post['link']
                    )
                    for blog_link in blog_links:
                        if blog_link not in new_blogs_with_source:
                            new_blogs_with_source[blog_link] = {
                                'source_blog': blog_url,
                                'source_blog_name': latest_post['blog_name'],
                                'source_post_title': post['title'],
                                'source_post_link': post['link']
                            }
                
                newly_added = []
                current_depth = self.state.discovered_blogs.get(domain).depth if domain in self.state.discovered_blogs else 0
                
                for new_blog_url, source_info in new_blogs_with_source.items():
                    new_domain = extract_domain(new_blog_url)
                    if new_domain and new_domain not in self.state.processed_domains and new_domain not in self.state.queued_domains:
                        source_info['parent_depth'] = current_depth
                        new_depth = current_depth + 1
                        self.add_to_queue(new_blog_url, source_info, new_depth)
                        self.state.queued_domains.add(new_domain)
                        newly_added.append(new_blog_url)
                
                if newly_added:
                    logger.info(f"DISCOVERED {len(newly_added)} NEW BLOGS from {len(posts)} posts:")
                    for i, new_url in enumerate(newly_added[:5], 1):
                        logger.info(f"{i}. {new_url}")
                    if len(newly_added) > 5:
                        logger.info(f"... and {len(newly_added) - 5} more")
                else:
                    logger.info(f"No new blogs found in {len(posts)} posts")
                
                return True
        
        self.state.failed_domains.add(domain)
        if base_domain in settings.BLACKLIST_BASE_DOMAIN_SITES:
            logger.info(f"No valid feeds - blacklisting base domain {base_domain}")
            self.state.failed_base_domains.add(base_domain)
        else:
            logger.info(f"No valid feeds (domain-only blacklist)")
        return False

    def run_discovery(self, seed_blogs: List[str]):
        """Run blog discovery"""
        logger.info("="*60)
        logger.info("BLOG DISCOVERY")
        logger.info(f"Target: {self.max_blogs} blogs | Posts per blog: {self.max_posts_to_check}")
        logger.info(f"Seed blogs: {len(seed_blogs)}")
        logger.info(f"Queue strategy: {self.queue_strategy}")
        logger.info("="*60 + "\n")
        
        for blog_url in seed_blogs:
            domain = extract_domain(blog_url)
            if domain not in self.state.processed_domains:
                self.blogs_to_process.append((blog_url, None))
        
        self.state.queued_domains = {extract_domain(url) for url, _ in self.blogs_to_process if extract_domain(url)}
        
        blogs_crawled_since_checkpoint = 0
        attempt_counter = 0
        
        while self.blogs_to_process and len(self.state.discovered_blogs) < self.max_blogs:
            blog_item = self.blogs_to_process.popleft()
            if isinstance(blog_item, (tuple, list)) and len(blog_item) == 2:
                blog_url, source_info = blog_item
            elif isinstance(blog_item, str):
                blog_url, source_info = blog_item, None
            else:
                logger.warning(f"Invalid queue item format: {type(blog_item)} - {blog_item}")
                continue
            
            attempt_counter += 1
            domain = extract_domain(blog_url)
            self.state.queued_domains.discard(domain)
            
            try:
                success = self.crawl_blog(blog_url, source_info, attempt_counter)
                
                if success:
                    blogs_crawled_since_checkpoint += 1
                    if blogs_crawled_since_checkpoint >= self.checkpoint_interval:
                        self.save_checkpoint()
                        blogs_crawled_since_checkpoint = 0
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.warning("\nInterrupted by user! Saving checkpoint...")
                self.save_checkpoint()
                raise
            except Exception as e:
                logger.error(f"Error crawling {blog_url}: {e}")
                continue
            
            processed_count = len(self.state.processed_domains)
            logger.info(f"Progress: {len(self.state.discovered_blogs)}/{self.max_blogs} blogs | Processed: {processed_count} | Queue: {len(self.blogs_to_process)} waiting")
        
        self.save_checkpoint()
        
        logger.info("\n" + "="*60)
        logger.info("DISCOVERY COMPLETE!")
        logger.info("="*60)
        logger.info(f"Total blogs discovered: {len(self.state.discovered_blogs)}")
        logger.info(f"Blogs remaining in queue: {len(self.blogs_to_process)}")
        logger.info("="*60 + "\n")
        
        return self.state.discovered_blogs

    def save_results(self, filename: str = 'discovery_results.json'):
        """Save discovered blogs to JSON in the json folder"""
        os.makedirs(settings.JSON_DIR, exist_ok=True)
        results_path = os.path.join(settings.JSON_DIR, filename)
        
        blogs_list = [
            {
                'domain': domain,
                **info.model_dump()
            }
            for domain, info in self.state.discovered_blogs.items()
        ]
        
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
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"\nSaved {len(blogs_list)} blogs to {filename}")
