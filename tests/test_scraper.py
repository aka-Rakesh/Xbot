"""
Tests for the scraper module.
"""
import pytest
from unittest.mock import Mock, patch
from src.scraper import BountyScraper, fetch_bounties

class TestBountyScraper:
    """Test cases for BountyScraper class."""
    
    def test_init(self):
        """Test scraper initialization."""
        scraper = BountyScraper("https://example.com")
        assert scraper.site_url == "https://example.com"
        assert scraper.session is not None
    
    def test_extract_bounty_id_from_url(self):
        """Test bounty ID extraction from URL."""
        scraper = BountyScraper()
        
        # Test numeric ID
        assert scraper._extract_bounty_id("https://example.com/bounty/123", "Test Bounty") == "123"
        
        # Test slug ID
        assert scraper._extract_bounty_id("https://example.com/bounty/test-bounty", "Test Bounty") == "test-bounty"
        
        # Test fallback to hash
        result = scraper._extract_bounty_id("https://example.com/bounty", "Test Bounty")
        assert len(result) == 12  # MD5 hash length
    
    @patch('src.scraper.requests.Session.get')
    def test_fetch_bounties_requests_success(self, mock_get):
        """Test successful bounty fetching with requests."""
        # Mock response
        mock_response = Mock()
        mock_response.text = """
        <html>
            <body>
                <div class="bounty-row">
                    <a href="/bounty/123">Test Bounty 1</a>
                    <div class="description">Test description 1</div>
                </div>
                <div class="bounty-row">
                    <a href="/bounty/456">Test Bounty 2</a>
                    <div class="description">Test description 2</div>
                </div>
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        scraper = BountyScraper("https://example.com")
        bounties = scraper.fetch_bounties_requests()
        
        assert len(bounties) == 2
        assert bounties[0]['title'] == "Test Bounty 1"
        assert bounties[0]['id'] == "123"
        assert bounties[1]['title'] == "Test Bounty 2"
        assert bounties[1]['id'] == "456"
    
    @patch('src.scraper.requests.Session.get')
    def test_fetch_bounties_requests_error(self, mock_get):
        """Test error handling in bounty fetching."""
        mock_get.side_effect = Exception("Network error")
        
        scraper = BountyScraper("https://example.com")
        
        with pytest.raises(Exception):
            scraper.fetch_bounties_requests()
    
    def test_fetch_bounties_function(self):
        """Test the convenience fetch_bounties function."""
        with patch('src.scraper.BountyScraper.fetch_bounties') as mock_fetch:
            mock_fetch.return_value = [{'id': '123', 'title': 'Test'}]
            
            result = fetch_bounties("https://example.com")
            assert result == [{'id': '123', 'title': 'Test'}]
            mock_fetch.assert_called_once_with(False)
