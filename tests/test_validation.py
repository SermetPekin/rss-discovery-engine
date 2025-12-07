import pytest
from unittest.mock import MagicMock, patch
from crawler.validation import Validator, is_safe_url, is_likely_blog

class TestValidation:
    
    def test_is_safe_url(self):
        # Safe URLs
        assert is_safe_url("https://example.com/blog/post-1")
        assert is_safe_url("http://mysite.org/article")
        
        # Unsafe URLs (extensions)
        assert not is_safe_url("https://example.com/malware.exe")
        assert not is_safe_url("https://example.com/archive.zip")
        
        # Unsafe URLs (patterns)
        assert not is_safe_url("https://example.com/download/file")
        assert not is_safe_url("https://example.com/phishing-site")
        
        # Safe URLs with suspicious words in context
        assert is_safe_url("https://example.com/blog/how-to-install-python")

    def test_is_likely_blog(self):
        # Likely blogs
        assert is_likely_blog("https://example.com/blog")
        assert is_likely_blog("https://my-personal-site.com")
        assert is_likely_blog("https://tech-blog.io/some-story")
        
        # Unlikely blogs
        assert not is_likely_blog("https://google.com")
        assert not is_likely_blog("https://facebook.com")
        # www.example.com fails the "personal site" heuristic (starts with www)
        # and has no blog indicators, so it should be False
        assert not is_likely_blog("https://www.example.com/shop/product")

    @patch('crawler.validation.requests.get')
    def test_is_allowed_by_robots(self, mock_get):
        validator = Validator()
        url = "https://example.com/secret"
        
        # Mock robots.txt response - Disallow /secret
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *\nDisallow: /secret"
        mock_get.return_value = mock_response
        
        assert validator.is_allowed_by_robots(url) is False
        assert validator.is_allowed_by_robots("https://example.com/public") is True
        
        # Test cache usage
        validator.is_allowed_by_robots(url)
        assert mock_get.call_count == 1  # Should be called only once due to cache

    @patch('crawler.validation.requests.get')
    def test_robots_txt_failure(self, mock_get):
        validator = Validator()
        url = "https://example.com/any"
        
        # Mock 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # Should allow all if robots.txt is missing
        assert validator.is_allowed_by_robots(url) is True
