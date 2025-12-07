import os
import shutil
import logging
from datetime import datetime
from urllib.parse import urlparse
from typing import List

from config import Settings

# Initialize settings
settings = Settings()
logger = logging.getLogger(__name__)

def extract_domain(url: str) -> str:
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

def get_base_domain(domain: str) -> str:
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

def archive_old_results() -> int:
    """Archive old results to archive directory"""
    archive_dir = 'archive'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create archive directory if it doesn't exist
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
        logger.info(f"Created archive directory: {archive_dir}")
    
    # Files to archive (now located in the json directory)
    json_files_to_archive = [
        settings.CHECKPOINT_FILENAME,
        'discovery_results.json'
    ]
    
    archived_count = 0
    for filename in json_files_to_archive:
        source_path = os.path.join(settings.JSON_DIR, filename)
        if os.path.exists(source_path):
            # Try to get blog count from JSON
            count_suffix = ""
            try:
                import json
                with open(source_path, 'r') as f:
                    data = json.load(f)
                    if 'discovered_blogs' in data:
                        count = len(data['discovered_blogs'])
                        count_suffix = f"_{count}"
                    elif 'blogs' in data and isinstance(data['blogs'], list):
                        count = len(data['blogs'])
                        count_suffix = f"_{count}"
            except:
                pass

            archive_name = f"{os.path.splitext(filename)[0]}{count_suffix}_{timestamp}{os.path.splitext(filename)[1]}"
            archive_path = os.path.join(archive_dir, archive_name)
            shutil.move(source_path, archive_path)
            logger.info(f"Archived: {source_path} -> {archive_path}")
            archived_count += 1
    
    if archived_count > 0:
        logger.info(f"Archived {archived_count} files to {archive_dir}/")
    else:
        logger.info("No files to archive")
    
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
        logger.info(f"Loaded {len(seeds)} seed blogs from {filename}")
        return seeds
    except FileNotFoundError:
        logger.warning(f"⚠️  Seed file {filename} not found!")
        return []
    except Exception as e:
        logger.warning(f"⚠️  Error loading seeds from {filename}: {e}")
        return []
