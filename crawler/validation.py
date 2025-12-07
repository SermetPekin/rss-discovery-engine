import logging
import requests
import urllib.robotparser
from urllib.parse import urlparse, urljoin
from typing import Dict

from config import Settings
from .utils import extract_domain

# Initialize settings
settings = Settings()
logger = logging.getLogger(__name__)

def is_safe_url(url: str) -> bool:
    """Check if URL is safe (no dangerous extensions or suspicious patterns)"""
    try:
        url_lower = url.lower()
        parsed = urlparse(url_lower)
        path = parsed.path
        
        # Check for dangerous file extensions
        for ext in settings.DANGEROUS_EXTENSIONS:
            if path.endswith(ext):
                logger.warning(f"Blocked dangerous URL: {url} (extension: {ext})")
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
                logger.warning(f"Blocked suspicious URL: {url} (pattern: {pattern})")
                return False
        
        return True
    except:
        return False

def is_likely_blog(url: str) -> bool:
    """Check if URL is likely a blog"""
    try:
        # First check if URL is safe
        if not is_safe_url(url):
            return False
        
        domain = urlparse(url).netloc.lower()
        
        # Skip known non-blog domains
        for skip in settings.SKIP_DOMAINS:
            if skip in domain:
                return False
        
        # Check for allowed extensions (TLDs)
        if not any(domain.endswith(ext) for ext in settings.ALLOWED_EXTENSIONS):
            return False
        
        # Check for blog indicators in domain or path
        url_lower = url.lower()
        for indicator in settings.BLOG_INDICATORS:
            if indicator in url_lower:
                return True
        
        # Accept domains that look like personal/organizational sites
        if domain.count('.') <= 2 and not domain.startswith('www.'):
            return True
            
        return False
    except:
        return False

class Validator:
    def __init__(self):
        self.robots_cache: Dict[str, urllib.robotparser.RobotFileParser] = {}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        }

    def is_allowed_by_robots(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt"""
        try:
            domain = extract_domain(url)
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
                    response = requests.get(robots_url, headers=self.headers, timeout=5, verify=False)
                    if response.status_code == 200:
                        rp.parse(response.text.splitlines())
                    else:
                        rp.allow_all = True
                except:
                    rp.allow_all = True
                
                self.robots_cache[domain] = rp
                
            return rp.can_fetch("*", url)
            
        except Exception as e:
            return True

