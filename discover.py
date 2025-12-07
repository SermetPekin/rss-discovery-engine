#!/usr/bin/env python3
"""
Recursive Blog Discovery Crawler
Discovers blogs recursively by following links in posts
Goal: Find up to 250 unique blogs, showing only the latest post from each
"""

import logging
import argparse
import warnings
import urllib3

import os
import glob
import re
import json

# Suppress SSL warnings for unverified HTTPS requests
warnings.filterwarnings('ignore', category=urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config import Settings
from crawler import RecursiveBlogDiscovery, load_seeds, archive_old_results

# Initialize settings
settings = Settings()

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def get_blog_count(filepath):
    """Get blog count from filename or file content"""
    # Try filename first: ..._123_2023...json
    match = re.search(r'_(\d+)_\d{8}_\d{6}\.json$', filepath)
    if match:
        return int(match.group(1))
    
    # Fallback to reading file
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            if 'discovered_blogs' in data:
                return len(data['discovered_blogs'])
            if 'blogs' in data and isinstance(data['blogs'], list):
                return len(data['blogs'])
    except:
        pass
    return 0

def find_best_checkpoint():
    """Find the checkpoint with the most blogs"""
    candidates = []
    
    # 1. Current default checkpoint
    default_cp = os.path.join(settings.JSON_DIR, settings.CHECKPOINT_FILENAME)
    if os.path.exists(default_cp):
        count = get_blog_count(default_cp)
        logger.info(f"Checking default checkpoint: {default_cp} -> {count} blogs")
        candidates.append((count, os.path.getmtime(default_cp), default_cp))
        
    # 2. Archived checkpoints
    archive_pattern = os.path.join('archive', '*.json')
    for filepath in glob.glob(archive_pattern):
        count = get_blog_count(filepath)
        logger.info(f"Checking archive: {filepath} -> {count} blogs")
        if count > 0:
            candidates.append((count, os.path.getmtime(filepath), filepath))
            
    if not candidates:
        logger.info("No valid checkpoints found")
        return None, 0
        
    # Sort by count (descending), then by time (descending)
    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    
    best_count, _, best_path = candidates[0]
    logger.info(f"Best checkpoint: {best_path} ({best_count} blogs)")
    return best_path, best_count

def find_checkpoint_file(checkpoint_arg):
    """Find checkpoint file based on argument (path or count)"""
    if not checkpoint_arg:
        return None
        
    # If it's a direct path to an existing file
    if os.path.exists(checkpoint_arg):
        return checkpoint_arg
        
    # If it's a number (e.g. "140"), look for files with that count
    # Pattern: *checkpoint*140*.json
    search_patterns = [
        f"*{checkpoint_arg}*.json",
        f"*_{checkpoint_arg}_*.json"
    ]
    
    search_dirs = ['archive', 'json', '.']
    
    for directory in search_dirs:
        if not os.path.exists(directory):
            continue
            
        for pattern in search_patterns:
            matches = glob.glob(os.path.join(directory, pattern))
            if matches:
                # Return the most recent one (sort by name usually works for timestamps, or modification time)
                matches.sort(key=os.path.getmtime, reverse=True)
                return matches[0]
                
    return None

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
  python discover.py --checkpoint 140           # Resume from a backup with ~140 blogs
  python discover.py --strategy breadth_first   # Use breadth-first (seed blogs first)
        """
    )
    parser.add_argument(
        '--fresh',
        action='store_true',
        help='Archive old results and start fresh discovery'
    )
    parser.add_argument(
        '--checkpoint',
        help='Resume from a specific checkpoint file or blog count (e.g. "140")'
    )
    parser.add_argument(
        '--strategy',
        choices=['breadth_first', 'depth_first', 'random', 'mixed'],
        default=settings.QUEUE_STRATEGY,
        help='Queue strategy: breadth_first (seeds first), depth_first (explore deep), random, or mixed (default from config)'
    )
    
    args = parser.parse_args()
    
    # Handle fresh start
    if args.fresh:
        logger.info("\n" + "="*60)
        logger.info("FRESH START MODE")
        logger.info("="*60)
        archive_old_results()
        logger.info("")
    
    # Handle specific checkpoint loading
    load_from_checkpoint = None
    if args.checkpoint:
        found_checkpoint = find_checkpoint_file(args.checkpoint)
        if found_checkpoint:
            logger.info(f"Found checkpoint file: {found_checkpoint}")
            load_from_checkpoint = found_checkpoint
        else:
            logger.error(f"Could not find checkpoint matching: {args.checkpoint}")
            return
    elif not args.fresh:
        # Auto-find best checkpoint
        best_cp, count = find_best_checkpoint()
        if best_cp:
            default_cp = os.path.join(settings.JSON_DIR, settings.CHECKPOINT_FILENAME)
            
            # If best checkpoint is the default one, we don't need to do anything special
            # The crawler will load it automatically.
            # But if it's an archive file, we must tell crawler to load it.
            
            if os.path.abspath(best_cp) != os.path.abspath(default_cp):
                logger.info(f"Auto-selected best checkpoint: {best_cp} ({count} blogs)")
                load_from_checkpoint = best_cp
            else:
                logger.info(f"Continuing from current checkpoint ({count} blogs)")

    # Seed blogs - high quality blogs from:
    # https://statmodeling.stat.columbia.edu/blogs-i-read/
    
    # Load seeds from file
    seed_blogs = load_seeds('seeds.txt')
    
    if not seed_blogs:
        logger.error("No seed blogs found! Please check seeds.txt")
        return
    
    crawler = RecursiveBlogDiscovery(
        max_blogs=250, 
        max_posts_to_check=20, 
        queue_strategy=args.strategy,
        load_from_checkpoint=load_from_checkpoint
    )
    
    # seed_blogs = seed_blogs[0 : 10]  # Limit for testing
    # Run discovery
    discovered_blogs = crawler.run_discovery(seed_blogs)
    
    # Save results
    crawler.save_results('discovery_results.json')
    
    # Show top blogs
    logger.info("\nSample of Discovered Blogs:")
    blogs_list = list(discovered_blogs.items())[:20]
    for i, (domain, info) in enumerate(blogs_list, 1):
        logger.info(f"\n{i}. {info.name}")
        logger.info(f"   {info.url}")
        logger.info(f"   Latest: {info.latest_post.title[:60]}...")


if __name__ == "__main__":
    main()
