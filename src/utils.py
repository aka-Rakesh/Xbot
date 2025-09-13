"""
Utility functions for rate limiting, backoff, and general helpers.
"""
import time
import random
import logging
from typing import Callable, Any
from functools import wraps
from .config import MAX_RETRIES, RETRY_DELAY_SECONDS, MIN_POST_INTERVAL_SECONDS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def exponential_backoff(max_retries: int = MAX_RETRIES, base_delay: int = RETRY_DELAY_SECONDS):
    """
    Decorator for exponential backoff on function failures.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise e
                    
                    # Calculate delay with jitter
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. Retrying in {delay:.2f}s")
                    time.sleep(delay)
            
            raise last_exception
        return wrapper
    return decorator

def rate_limit_check(last_post_time: float) -> bool:
    """
    Check if enough time has passed since the last post to respect rate limits.
    
    Args:
        last_post_time: Unix timestamp of the last post
        
    Returns:
        True if we can post, False if we need to wait
    """
    time_since_last_post = time.time() - last_post_time
    return time_since_last_post >= MIN_POST_INTERVAL_SECONDS

def truncate_text(text: str, max_length: int) -> str:
    """
    Truncate text to fit within character limits, preserving word boundaries.
    
    Args:
        text: Text to truncate
        max_length: Maximum allowed length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    
    # Find the last space before the limit to avoid cutting words
    truncated = text[:max_length-3]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # Only use word boundary if it's not too far back
        truncated = truncated[:last_space]
    
    return truncated + '...'

def sanitize_text(text: str) -> str:
    """
    Sanitize text for safe posting by removing potentially problematic characters.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text safe for posting
    """
    # Remove or replace characters that might cause issues
    replacements = {
        '\n': ' ',
        '\r': ' ',
        '\t': ' ',
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'",
        '–': '-',
        '—': '-',
    }
    
    sanitized = text
    for old, new in replacements.items():
        sanitized = sanitized.replace(old, new)
    
    # Remove multiple consecutive spaces
    while '  ' in sanitized:
        sanitized = sanitized.replace('  ', ' ')
    
    return sanitized.strip()

def validate_tweet_content(text: str) -> bool:
    """
    Validate that tweet content meets platform requirements.
    
    Args:
        text: Tweet text to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not text or not text.strip():
        return False
    
    if len(text) > 280:  # Twitter character limit
        return False
    
    # Check for potentially problematic content
    spam_indicators = ['click here', 'free money', 'guaranteed', 'act now']
    text_lower = text.lower()
    
    for indicator in spam_indicators:
        if indicator in text_lower:
            logger.warning(f"Tweet content flagged for potential spam: {indicator}")
            return False
    
    return True

def get_user_agent() -> str:
    """Get a realistic user agent string for web requests."""
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def log_with_context(level: int, message: str, **kwargs):
    """
    Log a message with additional context.
    
    Args:
        level: Logging level
        message: Log message
        **kwargs: Additional context to include in the log
    """
    context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    full_message = f"{message} | {context}" if context else message
    logger.log(level, full_message)
