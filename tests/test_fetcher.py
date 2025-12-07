import pytest
import time
import requests
from unittest.mock import MagicMock, patch
from crawler.network import Fetcher

class TestFetcher:
    
    @patch('crawler.network.time.sleep')
    def test_rate_limit(self, mock_sleep):
        fetcher = Fetcher()
        domain = "example.com"
        
        # First request - no sleep
        fetcher.enforce_rate_limit(domain)
        mock_sleep.assert_not_called()
        
        # Immediate second request - should sleep
        fetcher.enforce_rate_limit(domain)
        mock_sleep.assert_called_once()
        
        # Check that sleep time is roughly correct (min_delay is 2s)
        args, _ = mock_sleep.call_args
        assert 0 < args[0] <= 2

    @patch('crawler.network.requests.get')
    def test_check_sitemap(self, mock_get):
        fetcher = Fetcher()
        url = "https://example.com"
        
        # Mock robots.txt response with Sitemap directive
        mock_robots = MagicMock()
        mock_robots.status_code = 200
        mock_robots.text = "Sitemap: https://example.com/sitemap.xml"
        
        # Mock sitemap.xml response
        mock_sitemap = MagicMock()
        mock_sitemap.status_code = 200
        mock_sitemap.text = """
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url><loc>https://example.com/blog/post1</loc></url>
            <url><loc>https://example.com/feed.xml</loc></url>
        </urlset>
        """
        
        # Configure side_effect to return different responses
        def side_effect(url, **kwargs):
            if 'robots.txt' in url:
                return mock_robots
            elif 'sitemap.xml' in url:
                return mock_sitemap
            return MagicMock(status_code=404)
            
        mock_get.side_effect = side_effect
        
        feeds = fetcher.check_sitemap(url)
        assert "https://example.com/feed.xml" in feeds
        assert len(feeds) == 2

    @patch('crawler.network.requests.get')
    def test_discover_feeds_html_link(self, mock_get):
        fetcher = Fetcher()
        url = "https://example.com"
        
        # Mock HTML response with link tag
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <head>
            <link rel="alternate" type="application/rss+xml" title="RSS" href="/rss.xml" />
        </head>
        <body></body>
        </html>
        """
        mock_get.return_value = mock_response
        
        feeds, status = fetcher.discover_feeds(url)
        assert status == 'success'
        assert "https://example.com/rss.xml" in feeds

    @patch('crawler.network.requests.get')
    def test_discover_feeds_known_platform(self, mock_get):
        fetcher = Fetcher()
        url = "https://myblog.wordpress.com"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Wordpress Blog</body></html>"
        mock_get.return_value = mock_response
        
        feeds, status = fetcher.discover_feeds(url)
        assert status == 'success' or status == 'has_blog_indicators'
        # Wordpress should auto-detect /feed/
        assert any('/feed' in f for f in feeds)

    @patch('crawler.network.requests.get')
    def test_discover_feeds_unreachable(self, mock_get):
        fetcher = Fetcher()
        url = "https://broken.com"
        
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        feeds, status = fetcher.discover_feeds(url)
        assert status == 'unreachable'
        assert feeds == []
