"""
Configuration management for the Twitter Bounty Bot.
Loads environment variables and provides configuration constants.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# X/Twitter API Configuration
TW_API_KEY = os.getenv('TW_API_KEY')
TW_API_SECRET = os.getenv('TW_API_SECRET')
TW_ACCESS_TOKEN = os.getenv('TW_ACCESS_TOKEN')
TW_ACCESS_SECRET = os.getenv('TW_ACCESS_SECRET')
TW_BEARER_TOKEN = os.getenv('TW_BEARER_TOKEN')
OAUTH_CLIENT_ID = os.getenv('OAUTH_CLIENT_ID')
OAUTH_CLIENT_SECRET = os.getenv('OAUTH_CLIENT_SECRET')

# Bounty site configuration
BOUNTY_SITE_URL = os.getenv('BOUNTY_SITE_URL')

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./data.db')

# Optional third-party services
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SENTRY_DSN = os.getenv('SENTRY_DSN')

# Bot behavior configuration
POST_INTERVAL_MINUTES = int(os.getenv('POST_INTERVAL_MINUTES', '10'))
MAX_POSTS_PER_DAY = int(os.getenv('MAX_POSTS_PER_DAY', '10'))
USER_DISPLAY_NAME = os.getenv('USER_DISPLAY_NAME', 'MyBountyBot')

# Rate limiting constants
MAX_TWEET_LENGTH = 280
MIN_POST_INTERVAL_SECONDS = 60  # Minimum 1 minute between posts
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

# Validation
def validate_config():
    """Validate that required configuration is present."""
    required_vars = [
        'TW_API_KEY', 'TW_API_SECRET', 'TW_ACCESS_TOKEN', 'TW_ACCESS_SECRET'
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    if not BOUNTY_SITE_URL:
        raise ValueError("BOUNTY_SITE_URL is required")
