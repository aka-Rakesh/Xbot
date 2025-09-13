"""
Twitter/X posting functionality for the Twitter Bounty Bot.
Handles posting threads via the Twitter API.
"""
import tweepy
import logging
import time
from typing import List, Dict, Optional
from .config import (
    TW_API_KEY, TW_API_SECRET, TW_ACCESS_TOKEN, TW_ACCESS_SECRET,
    TW_BEARER_TOKEN, MAX_TWEET_LENGTH
)
from .utils import exponential_backoff, log_with_context, rate_limit_check

logger = logging.getLogger(__name__)

class TwitterPoster:
    """Handles posting to Twitter/X using the Twitter API v2."""
    
    def __init__(self):
        self.client = None
        self.last_post_time = 0
        self._setup_client()
    
    def _setup_client(self):
        """Initialize the Twitter API client."""
        try:
            # Validate required credentials
            if not all([TW_API_KEY, TW_API_SECRET, TW_ACCESS_TOKEN, TW_ACCESS_SECRET]):
                raise ValueError("Missing required Twitter API credentials")
            
            # Create OAuth 1.0a handler for user context
            auth = tweepy.OAuth1UserHandler(
                TW_API_KEY,
                TW_API_SECRET,
                TW_ACCESS_TOKEN,
                TW_ACCESS_SECRET
            )
            
            # Create API client
            self.client = tweepy.API(auth, wait_on_rate_limit=True)
            
            # Verify credentials
            try:
                user = self.client.verify_credentials()
                log_with_context(logging.INFO, "Twitter API client initialized", 
                               username=user.screen_name, user_id=user.id)
            except Exception as e:
                log_with_context(logging.ERROR, "Failed to verify Twitter credentials", error=str(e))
                raise
                
        except Exception as e:
            log_with_context(logging.ERROR, "Failed to setup Twitter client", error=str(e))
            raise
    
    @exponential_backoff(max_retries=3)
    def post_thread(self, thread: List[str]) -> Dict:
        """
        Post a thread of tweets to Twitter.
        
        Args:
            thread: List of tweet texts to post as a thread
            
        Returns:
            Dictionary with thread information and tweet IDs
        """
        if not self.client:
            raise RuntimeError("Twitter client not initialized")
        
        if not thread:
            raise ValueError("Thread cannot be empty")
        
        # Check rate limits
        if not rate_limit_check(self.last_post_time):
            wait_time = 60 - (time.time() - self.last_post_time)
            log_with_context(logging.WARNING, "Rate limit check failed, waiting", wait_seconds=wait_time)
            time.sleep(wait_time)
        
        try:
            log_with_context(logging.INFO, "Posting thread", tweet_count=len(thread))
            
            # Post first tweet
            first_tweet = self._post_tweet(thread[0])
            root_tweet_id = first_tweet.id
            tweet_ids = [str(root_tweet_id)]
            
            # Post subsequent tweets as replies
            in_reply_to_id = root_tweet_id
            for i, tweet_text in enumerate(thread[1:], 1):
                try:
                    reply_tweet = self._post_tweet(tweet_text, in_reply_to_id)
                    tweet_ids.append(str(reply_tweet.id))
                    in_reply_to_id = reply_tweet.id
                    
                    # Small delay between tweets in the thread
                    time.sleep(1)
                    
                except Exception as e:
                    log_with_context(logging.ERROR, f"Failed to post tweet {i+1} in thread", 
                                   error=str(e), tweet_text=tweet_text[:50])
                    # Continue with the rest of the thread
                    continue
            
            self.last_post_time = time.time()
            
            result = {
                'success': True,
                'root_tweet_id': str(root_tweet_id),
                'tweet_ids': tweet_ids,
                'thread_length': len(tweet_ids),
                'posted_at': int(time.time())
            }
            
            log_with_context(logging.INFO, "Thread posted successfully", 
                           root_tweet_id=root_tweet_id, thread_length=len(tweet_ids))
            
            return result
            
        except Exception as e:
            log_with_context(logging.ERROR, "Failed to post thread", error=str(e))
            raise
    
    def _post_tweet(self, text: str, in_reply_to_id: Optional[int] = None):
        """
        Post a single tweet.
        
        Args:
            text: Tweet text
            in_reply_to_id: ID of tweet to reply to (for threading)
            
        Returns:
            Posted tweet object (tweepy Status)
        """
        try:
            if in_reply_to_id:
                # Post as reply
                tweet = self.client.update_status(
                    status=text,
                    in_reply_to_status_id=in_reply_to_id,
                    auto_populate_reply_metadata=True
                )
            else:
                # Post as new tweet
                tweet = self.client.update_status(status=text)
            
            return tweet
            
        except tweepy.TooManyRequests:
            log_with_context(logging.WARNING, "Rate limit exceeded, waiting...")
            time.sleep(900)  # Wait 15 minutes
            raise
        except tweepy.Unauthorized:
            log_with_context(logging.ERROR, "Twitter API unauthorized - check credentials")
            raise
        except tweepy.Forbidden:
            log_with_context(logging.ERROR, "Twitter API forbidden - check permissions")
            raise
        except Exception as e:
            log_with_context(logging.ERROR, "Failed to post tweet", error=str(e), text=text[:50])
            raise
    
    def test_connection(self) -> bool:
        """
        Test the Twitter API connection.
        
        Returns:
            True if connection is working, False otherwise
        """
        try:
            if not self.client:
                return False
            
            user = self.client.verify_credentials()
            log_with_context(logging.INFO, "Twitter connection test successful", 
                           username=user.screen_name)
            return True
            
        except Exception as e:
            log_with_context(logging.ERROR, "Twitter connection test failed", error=str(e))
            return False
    
    def get_rate_limit_status(self) -> Dict:
        """
        Get current rate limit status.
        
        Returns:
            Dictionary with rate limit information
        """
        try:
            if not self.client:
                return {'error': 'Client not initialized'}
            
            # Get rate limit status for statuses/update endpoint
            rate_limit = self.client.get_rate_limit_status()
            return rate_limit.get('resources', {}).get('statuses', {}).get('/statuses/update', {})
            
        except Exception as e:
            log_with_context(logging.ERROR, "Failed to get rate limit status", error=str(e))
            return {'error': str(e)}

# Convenience function for backward compatibility
def post_thread(thread: List[str]) -> Dict:
    """
    Post a thread of tweets to Twitter.
    
    Args:
        thread: List of tweet texts to post as a thread
        
    Returns:
        Dictionary with thread information and tweet IDs
    """
    poster = TwitterPoster()
    return poster.post_thread(thread)
