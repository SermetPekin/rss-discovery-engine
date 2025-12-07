from typing import Set, List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Configuration settings for the Recursive Blog Discovery Crawler.
    Uses Pydantic for validation and environment variable support.
    """
    
    # File paths
    JSON_DIR: str = 'json'
    CHECKPOINT_FILENAME: str = 'crawler_checkpoint.json'
    
    # Crawl Settings
    MAX_BLOGS_DEFAULT: int = 250
    MAX_POSTS_TO_CHECK: int = 40
    CHECKPOINT_INTERVAL: int = 5
    REQUEST_TIMEOUT: int = 20
    
    # Queue Strategy
    QUEUE_STRATEGY: str = 'mixed'

    # Allowed TLDs/Extensions
    ALLOWED_EXTENSIONS: Set[str] = {
        # Generic
        '.com', '.org', '.net', '.edu', '.gov', '.mil', '.int',
        # Tech/Web
        '.io', '.co', '.ai', '.dev', '.app', '.me', '.info', '.biz', '.xyz', '.tech', '.site', '.online',
        # Country Codes
        '.uk', '.ca', '.au', '.nz', '.de', '.fr', '.jp', '.tr', '.br', '.in',
        '.us', '.eu', '.nl', '.se', '.no', '.es', '.it', '.ch', '.at', '.dk',
        '.be', '.pl', '.ru', '.cn', '.kr', '.sg', '.hk', '.tw'
    }

    # Common blog platforms/indicators
    BLOG_INDICATORS: List[str] = [
        'blog', 'posts', 'articles', 'wordpress', 'blogspot', 'medium.com',
        'substack', 'ghost.io', 'write.as', 'tumblr', 'github.io', 'netlify.app'
    ]

    # Keywords that suggest a site is NOT a blog
    NON_BLOG_KEYWORDS: List[str] = [
        'agency', 'consulting', 'solutions', 'services', 'products', 'pricing',
        'shop', 'store', 'market', 'news', 'media', 'press', 'corp', 'inc',
        'ltd', 'group', 'holdings', 'careers', 'jobs', 'support', 'help',
        'status', 'api', 'docs', 'portal', 'login', 'signin', 'signup',
        'register', 'account', 'dashboard', 'admin', 'billing'
    ]
    
    # Domains to skip (not blogs)
    SKIP_DOMAINS: Set[str] = {
        'twitter.com', 'facebook.com', 'linkedin.com', 'instagram.com',
        'youtube.com', 'github.com', 'wikipedia.org', 'reddit.com',
        'medium.com', 'substack.com', 'ghost.org', 'wordpress.com',
        'google.com', 'amazon.com', 'microsoft.com', 'apple.com',
        'nytimes.com', 'wsj.com', 'bbc.com', 'cnn.com', 'reuters.com',
        'bloomberg.com', 'forbes.com', 'techcrunch.com', 'wired.com',
        'theverge.com', 'arstechnica.com', 'ycombinator.com',
        'stackoverflow.com', 'quora.com', 'pinterest.com', 'tiktok.com'
    }

    # Major sites where if one subdomain fails, blacklist the whole base domain
    BLACKLIST_BASE_DOMAIN_SITES: Set[str] = {
        'blogspot.com', 'wordpress.com', 'tumblr.com', 'medium.com', 
        'substack.com', 'github.io', 'netlify.app', 'vercel.app'
    }

    # Dangerous file extensions to block
    DANGEROUS_EXTENSIONS: Set[str] = {
        '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.mp4', '.mp3',
        '.zip', '.tar', '.gz', '.rar', '.exe', '.dmg', '.iso', '.bin',
        '.css', '.js', '.json', '.xml', '.csv', '.txt', '.doc', '.docx',
        '.xls', '.xlsx', '.ppt', '.pptx'
    }

    class Config:
        env_prefix = "RSS_"

# Instantiate settings
settings = Settings()

# Dangerous file extensions to block
DANGEROUS_EXTENSIONS = {
    '.exe', '.sh', '.bash', '.bat', '.cmd', '.scr',
    '.vbs', '.jar', '.deb', '.rpm', '.dmg',
    '.pkg', '.msi', '.dll', '.so', '.dylib', '.bin'
}
