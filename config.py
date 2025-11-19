"""
Configuration settings for the Recursive Blog Discovery Crawler
"""

# File paths
JSON_DIR = 'json'

# Crawl Settings
MAX_BLOGS_DEFAULT = 250
MAX_POSTS_TO_CHECK = 20
CHECKPOINT_FILENAME = 'crawler_checkpoint.json'
CHECKPOINT_INTERVAL = 5
REQUEST_TIMEOUT = 10

# Queue Strategy
# Options: 'breadth_first', 'depth_first', 'random', 'mixed'
# - breadth_first: Process seed blogs first, then discovered blogs in order (FIFO)
# - depth_first: Prioritize newly discovered blogs (explore network deeply)
# - random: Random selection from queue
# - mixed: 50% chance to prioritize new discoveries (current default)
QUEUE_STRATEGY = 'breadth_first'

# Allowed TLDs/Extensions
ALLOWED_EXTENSIONS = {
    # Generic
    '.com', '.org', '.net', '.edu', '.gov', '.mil', '.int',
    # Tech/Web
    '.io', '.co', '.ai', '.dev', '.app', '.me', '.info', '.biz', '.xyz', '.tech', '.site', '.online',
    # Country Codes (Common ones)
    '.uk', '.ca', '.au', '.nz', '.de', '.fr', '.jp', '.tr', '.br', '.in',
    '.us', '.eu', '.nl', '.se', '.no', '.es', '.it', '.ch', '.at', '.dk',
    '.be', '.pl', '.ru', '.cn', '.kr', '.sg', '.hk', '.tw'
}

# Common blog platforms/indicators
BLOG_INDICATORS = [
    'blog', 'posts', 'articles', 'wordpress', 'blogspot', 'medium.com',
    'substack', 'ghost.io', 'write.as', 'tumblr', 'github.io', 'netlify.app'
]

# Domains to skip (not blogs)
SKIP_DOMAINS = {
    'twitter.com', 'x.com', 'facebook.com', 'linkedin.com', 
    'youtube.com', 'github.com', 'arxiv.org', 'wikipedia.org',
    'doi.org', 'jstor.org', 'researchgate.net', 'scholar.google.com',
    'amazon.com', 'reddit.com', 'stackoverflow.com', 'google.com',
    'microsoft.com', 'apple.com', 'cran.r-project.org', 'pypi.org',
    'imgur.com', 'gstatic.com', 'googleapis.com', 'cloudflare.com',
    'feedburner.com', 'gravatar.com', 'wp.com'
}

# Major sites where if one subdomain fails, blacklist the whole base domain
# (These are large orgs that won't have random blog subdomains)
BLACKLIST_BASE_DOMAIN_SITES = {
    'github.com', 'microsoft.com', 'google.com', 'apple.com',
    'facebook.com', 'amazon.com', 'youtube.com', 'twitter.com',
    'linkedin.com', 'reddit.com', 'stackoverflow.com',
    'wikipedia.org', 'arxiv.org'
}

# Dangerous file extensions to block
DANGEROUS_EXTENSIONS = {
    '.exe', '.sh', '.bash', '.bat', '.cmd', '.scr',
    '.vbs', '.jar', '.deb', '.rpm', '.dmg',
    '.pkg', '.msi', '.dll', '.so', '.dylib', '.bin'
}
