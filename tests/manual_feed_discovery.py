#!/usr/bin/env python3
"""
Test Feed Discovery - Test individual URLs to debug feed discovery logic
Usage: python test_feed_discovery.py <url>
Example: python test_feed_discovery.py http://www.fharrell.com/
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import sys
import logging
import warnings

# Suppress SSL warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_feed_discovery(url: str):
    """Test feed discovery for a single URL with detailed output"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    print("=" * 80)
    print(f"🔍 Testing Feed Discovery for: {url}")
    print("=" * 80)
    
    feed_urls = []
    has_blog_indicators = False
    
    try:
        # Step 1: Fetch the page
        print("\n📡 Step 1: Fetching page...")
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        print(f"   ✅ Status: {response.status_code}")
        print(f"   📄 Content-Type: {response.headers.get('content-type', 'unknown')}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Step 2: Look for feed links in HTML <link> tags
        print("\n🔗 Step 2: Checking HTML <link> tags for feeds...")
        link_feeds = soup.find_all('link', type=['application/rss+xml', 'application/atom+xml'])
        if link_feeds:
            print(f"   ✅ Found {len(link_feeds)} feed link(s):")
            for link in link_feeds:
                href = link.get('href')
                if href:
                    feed_url = urljoin(url, href)
                    feed_urls.append(feed_url)
                    has_blog_indicators = True
                    title = link.get('title', 'No title')
                    print(f"      • {feed_url}")
                    print(f"        Title: {title}")
        else:
            print("   ⚠️  No feed links found in HTML")
        
        # Step 3: Check sitemap
        print("\n🗺️  Step 3: Checking sitemap.xml...")
        base_url = url.rstrip('/')
        sitemap_paths = ['/sitemap.xml', '/sitemap_index.xml', '/sitemap-index.xml', '/rss-sitemap.xml']
        sitemap_found = False
        
        for sitemap_path in sitemap_paths:
            try:
                sitemap_url = base_url + sitemap_path
                sitemap_resp = requests.get(sitemap_url, headers=headers, timeout=5, verify=False)
                if sitemap_resp.status_code == 200:
                    print(f"   ✅ Found sitemap at: {sitemap_path}")
                    sitemap_found = True
                    sitemap_soup = BeautifulSoup(sitemap_resp.text, 'xml')
                    locs = sitemap_soup.find_all('loc')
                    print(f"      Total URLs in sitemap: {len(locs)}")
                    
                    blog_urls = []
                    for loc in locs:
                        loc_url = loc.get_text()
                        if any(kw in loc_url.lower() for kw in ['feed', 'rss', 'atom', 'blog']):
                            blog_urls.append(loc_url)
                            if 'feed' in loc_url.lower() or 'rss' in loc_url.lower():
                                feed_urls.append(loc_url)
                            has_blog_indicators = True
                    
                    if blog_urls:
                        print(f"      Blog-related URLs found ({len(blog_urls)}):")
                        for i, burl in enumerate(blog_urls[:5], 1):
                            print(f"         {i}. {burl}")
                        if len(blog_urls) > 5:
                            print(f"         ... and {len(blog_urls) - 5} more")
                    break
            except:
                continue
        
        if not sitemap_found:
            print("   ⚠️  No sitemap found")
        
        # Step 4: Parse navigation for blog/feed links
        print("\n🧭 Step 4: Scanning navigation for blog indicators...")
        nav_keywords = ['blog', 'rss', 'feed', 'atom', 'subscribe', 'news', 'articles', 'posts']
        
        # Find navigation elements
        search_elements = soup.find_all(['nav', 'header', 'footer', 'menu', 'aside'])
        search_elements.extend(soup.find_all(['div', 'ul'], class_=lambda x: x and any(
            c in str(x).lower() for c in ['nav', 'menu', 'header', 'top', 'main-menu']
        )))
        search_elements.extend(soup.find_all(['div', 'ul'], id=lambda x: x and any(
            c in str(x).lower() for c in ['nav', 'menu', 'header', 'top-menu']
        )))
        
        print(f"   Found {len(search_elements)} navigation-like elements")
        
        blog_links = []
        for nav_element in search_elements:
            for a in nav_element.find_all('a', href=True):
                href_lower = a.get('href', '').lower()
                text_lower = a.get_text().lower().strip()
                
                if any(kw in href_lower or kw in text_lower for kw in nav_keywords):
                    has_blog_indicators = True
                    full_url = urljoin(url, a['href'])
                    blog_links.append({
                        'text': a.get_text().strip()[:50],
                        'href': a.get('href'),
                        'full_url': full_url
                    })
        
        if blog_links:
            print(f"   ✅ Found {len(blog_links)} blog-related link(s):")
            for i, link in enumerate(blog_links[:10], 1):
                print(f"      {i}. Text: '{link['text']}'")
                print(f"         URL: {link['full_url']}")
            if len(blog_links) > 10:
                print(f"      ... and {len(blog_links) - 10} more")
        else:
            print("   ⚠️  No blog-related links found in navigation")
        
        # Step 5: Try common feed paths
        print("\n🔎 Step 5: Testing common feed paths...")
        common_feeds = [
            '/feed/', '/rss/', '/atom/', '/feed', '/rss', '/atom',
            '/index.xml', '/rss.xml', '/feed.xml', '/atom.xml',
            '/blog/feed', '/blog/rss', '/blog/atom',
            '/blog/feed/', '/blog/rss/', '/blog/atom/'
        ]
        
        working_feeds = []
        for feed_path in common_feeds:
            try:
                feed_url = urljoin(url, feed_path)
                if feed_url not in feed_urls:  # Don't test duplicates
                    test_resp = requests.head(feed_url, headers=headers, timeout=3, verify=False, allow_redirects=True)
                    if test_resp.status_code == 200:
                        working_feeds.append(feed_url)
                        feed_urls.append(feed_url)
            except:
                pass
        
        if working_feeds:
            print(f"   ✅ Found {len(working_feeds)} working feed(s):")
            for wf in working_feeds:
                print(f"      • {wf}")
        else:
            print("   ⚠️  No common feed paths found")
        
        # Final Summary
        print("\n" + "=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)
        
        if feed_urls:
            print(f"✅ Status: SUCCESS - Found {len(feed_urls)} feed URL(s)")
            print("\n🎯 Feed URLs to try:")
            for i, feed_url in enumerate(feed_urls[:5], 1):
                print(f"   {i}. {feed_url}")
            if len(feed_urls) > 5:
                print(f"   ... and {len(feed_urls) - 5} more")
        elif has_blog_indicators:
            print("⚠️  Status: HAS_BLOG_INDICATORS")
            print("   Site has blog-related links but no RSS feeds found")
        else:
            print("❌ Status: NO_BLOG_INDICATORS")
            print("   No blog presence detected on this site")
        
        print(f"\n📈 Blog Indicators: {'Yes ✓' if has_blog_indicators else 'No ✗'}")
        
        # Recommendation
        print("\n💡 RECOMMENDATION:")
        if feed_urls:
            print("   ✅ This site should be added to discovered blogs")
        elif has_blog_indicators:
            print("   ⚠️  Don't blacklist base domain - may have blog subdomain")
        else:
            print("   🚫 Safe to blacklist base domain - no blog presence")
        
    except requests.exceptions.Timeout:
        print("\n❌ ERROR: Timeout - Site unreachable")
        print("   🚫 Recommendation: Blacklist base domain")
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Connection failed - Site unreachable")
        print("   🚫 Recommendation: Blacklist base domain")
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ ERROR: HTTP {e.response.status_code}")
        print("   🚫 Recommendation: Blacklist base domain")
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        print("   🚫 Recommendation: Blacklist base domain")


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_feed_discovery.py <url>")
        print("\nExample:")
        print("  python test_feed_discovery.py http://www.fharrell.com/")
        print("  python test_feed_discovery.py https://errorstatistics.com")
        sys.exit(1)
    
    url = sys.argv[1]
    
    # Ensure URL has scheme
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    test_feed_discovery(url)
    print("\n")


if __name__ == "__main__":
    main()
