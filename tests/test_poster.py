"""
Tests for the poster module.
"""
import pytest
from unittest.mock import Mock, patch
from src.poster import TwitterPoster, post_thread

class TestTwitterPoster:
    """Test cases for TwitterPoster class."""
    
    @patch('src.poster.tweepy.OAuth1UserHandler')
    @patch('src.poster.tweepy.API')
    def test_init_success(self, mock_api_class, mock_oauth):
        """Test successful poster initialization."""
        # Mock API response
        mock_api = Mock()
        mock_user = Mock()
        mock_user.screen_name = "test_user"
        mock_user.id = 12345
        mock_api.verify_credentials.return_value = mock_user
        mock_api_class.return_value = mock_api
        
        with patch.dict('os.environ', {
            'TW_API_KEY': 'test_key',
            'TW_API_SECRET': 'test_secret',
            'TW_ACCESS_TOKEN': 'test_token',
            'TW_ACCESS_SECRET': 'test_secret'
        }):
            poster = TwitterPoster()
            assert poster.client is not None
            assert poster.last_post_time == 0
    
    def test_init_missing_credentials(self):
        """Test initialization with missing credentials."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="Missing required Twitter API credentials"):
                TwitterPoster()
    
    @patch('src.poster.tweepy.OAuth1UserHandler')
    @patch('src.poster.tweepy.API')
    def test_post_thread_success(self, mock_api_class, mock_oauth):
        """Test successful thread posting."""
        # Mock API and tweets
        mock_api = Mock()
        mock_user = Mock()
        mock_user.screen_name = "test_user"
        mock_user.id = 12345
        mock_api.verify_credentials.return_value = mock_user
        
        # Mock tweet objects
        mock_tweet1 = Mock()
        mock_tweet1.id = 111
        mock_tweet2 = Mock()
        mock_tweet2.id = 222
        
        mock_api.update_status.side_effect = [mock_tweet1, mock_tweet2]
        mock_api_class.return_value = mock_api
        
        with patch.dict('os.environ', {
            'TW_API_KEY': 'test_key',
            'TW_API_SECRET': 'test_secret',
            'TW_ACCESS_TOKEN': 'test_token',
            'TW_ACCESS_SECRET': 'test_secret'
        }):
            poster = TwitterPoster()
            poster.client = mock_api
            
            thread = ["First tweet", "Second tweet"]
            result = poster.post_thread(thread)
            
            assert result['success'] is True
            assert result['root_tweet_id'] == '111'
            assert result['tweet_ids'] == ['111', '222']
            assert result['thread_length'] == 2
    
    @patch('src.poster.tweepy.OAuth1UserHandler')
    @patch('src.poster.tweepy.API')
    def test_post_thread_empty(self, mock_api_class, mock_oauth):
        """Test posting empty thread."""
        mock_api = Mock()
        mock_user = Mock()
        mock_user.screen_name = "test_user"
        mock_user.id = 12345
        mock_api.verify_credentials.return_value = mock_user
        mock_api_class.return_value = mock_api
        
        with patch.dict('os.environ', {
            'TW_API_KEY': 'test_key',
            'TW_API_SECRET': 'test_secret',
            'TW_ACCESS_TOKEN': 'test_token',
            'TW_ACCESS_SECRET': 'test_secret'
        }):
            poster = TwitterPoster()
            
            with pytest.raises(ValueError, match="Thread cannot be empty"):
                poster.post_thread([])
    
    @patch('src.poster.tweepy.OAuth1UserHandler')
    @patch('src.poster.tweepy.API')
    def test_test_connection_success(self, mock_api_class, mock_oauth):
        """Test successful connection test."""
        mock_api = Mock()
        mock_user = Mock()
        mock_user.screen_name = "test_user"
        mock_user.id = 12345
        mock_api.verify_credentials.return_value = mock_user
        mock_api_class.return_value = mock_api
        
        with patch.dict('os.environ', {
            'TW_API_KEY': 'test_key',
            'TW_API_SECRET': 'test_secret',
            'TW_ACCESS_TOKEN': 'test_token',
            'TW_ACCESS_SECRET': 'test_secret'
        }):
            poster = TwitterPoster()
            poster.client = mock_api
            
            assert poster.test_connection() is True
    
    def test_post_thread_function(self):
        """Test the convenience post_thread function."""
        with patch('src.poster.TwitterPoster.post_thread') as mock_post:
            mock_post.return_value = {'success': True, 'root_tweet_id': '123'}
            
            result = post_thread(["Test tweet"])
            assert result['success'] is True
            mock_post.assert_called_once_with(["Test tweet"])
