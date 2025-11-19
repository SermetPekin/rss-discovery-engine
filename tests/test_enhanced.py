#!/usr/bin/env python3
"""
Quick test to verify the enhanced crawler features
"""
import logging
from discover import RecursiveBlogDiscovery

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_enhanced_crawler():
    print("\n" + "="*80)
    print("TESTING ENHANCED CRAWLER")
    print("="*80 + "\n")
    
    # Test with just 3 blogs to see the new features
    crawler = RecursiveBlogDiscovery(max_blogs=3, max_posts_to_check=20)
    
    test_seeds = [
        "https://statmodeling.stat.columbia.edu/",
    ]
    
    results = crawler.run_discovery(test_seeds)
    
    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)
    
    # Check if full content is saved
    for domain, info in results.items():
        post = info['latest_post']
        print(f"\nBlog: {info['name']}")
        print(f"Has full_content: {bool(post.get('full_content'))}")
        print(f"Has raw_html: {bool(post.get('raw_html'))}")
        print(f"Full content length: {len(post.get('full_content', ''))} chars")
        break  # Just show first one
    
    crawler.save_results('test_enhanced_results.json')
    print("\n✅ Test complete! Check test_enhanced_results.json for full content")

if __name__ == "__main__":
    test_enhanced_crawler()
