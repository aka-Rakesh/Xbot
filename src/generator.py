"""
Thread generation for the Twitter Bounty Bot.
Creates Twitter threads from bounty data using templates or LLM.
"""
import json
import logging
from typing import List, Dict, Optional
from .config import OPENAI_API_KEY, MAX_TWEET_LENGTH
from .utils import truncate_text, sanitize_text, validate_tweet_content

logger = logging.getLogger(__name__)

class ThreadGenerator:
    """Generates Twitter threads from bounty data."""
    
    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm and bool(OPENAI_API_KEY)
        if self.use_llm:
            self._setup_openai()
    
    def _setup_openai(self):
        """Setup OpenAI client if API key is available."""
        try:
            import openai
            self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
            logger.info("OpenAI client initialized for LLM thread generation")
        except ImportError:
            logger.warning("OpenAI package not installed. Falling back to template generation.")
            self.use_llm = False
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}. Falling back to template generation.")
            self.use_llm = False
    
    def generate_thread(self, bounty: Dict) -> List[str]:
        """
        Generate a Twitter thread from bounty data.
        
        Args:
            bounty: Dictionary containing bounty information
            
        Returns:
            List of tweet texts for the thread
        """
        if self.use_llm:
            return self._generate_with_llm(bounty)
        else:
            return self._generate_with_template(bounty)
    
    def _generate_with_template(self, bounty: Dict) -> List[str]:
        """
        Generate thread using predefined templates.
        
        Args:
            bounty: Bounty data dictionary
            
        Returns:
            List of tweet texts
        """
        title = sanitize_text(bounty.get('title', ''))
        description = sanitize_text(bounty.get('description', ''))
        url = bounty.get('url', '')
        
        # Truncate description to fit in tweets
        short_desc = truncate_text(description, 200) if description else "Check out this new bounty opportunity!"
        
        # Template 1: Simple 3-tweet thread
        thread = [
            f"🔔 New bounty: {title}",
            f"📝 {short_desc}",
            f"🔗 Apply here: {url} | Follow for more updates! #Bounty #Crypto"
        ]
        
        # Alternative template for longer descriptions
        if len(description) > 100:
            thread = [
                f"🔔 New bounty: {title}",
                f"📝 {truncate_text(description, 250)}",
                f"💰 Why it matters: {truncate_text(description, 200)}",
                f"🔗 Apply here: {url} | RT & follow for more! #Bounty #Crypto"
            ]
        
        # Ensure all tweets are within character limits
        validated_thread = []
        for tweet in thread:
            if validate_tweet_content(tweet):
                validated_thread.append(tweet)
            else:
                logger.warning(f"Generated tweet failed validation: {tweet}")
        
        return validated_thread
    
    def _generate_with_llm(self, bounty: Dict) -> List[str]:
        """
        Generate thread using OpenAI LLM.
        
        Args:
            bounty: Bounty data dictionary
            
        Returns:
            List of tweet texts
        """
        try:
            prompt = self._build_llm_prompt(bounty)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Twitter bot that creates engaging threads about crypto bounties. Create 3-4 tweets that are informative, engaging, and follow Twitter best practices. Each tweet must be under 280 characters. Include relevant hashtags but don't overuse them."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            # Parse the response into individual tweets
            content = response.choices[0].message.content.strip()
            tweets = self._parse_llm_response(content)
            
            # Validate and truncate tweets
            validated_tweets = []
            for tweet in tweets:
                if validate_tweet_content(tweet):
                    validated_tweets.append(tweet)
                else:
                    logger.warning(f"LLM-generated tweet failed validation: {tweet}")
            
            return validated_tweets if validated_tweets else self._generate_with_template(bounty)
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}. Falling back to template generation.")
            return self._generate_with_template(bounty)
    
    def _build_llm_prompt(self, bounty: Dict) -> str:
        """Build the prompt for LLM generation."""
        return f"""
        Create a Twitter thread about this bounty:
        
        Title: {bounty.get('title', '')}
        Description: {bounty.get('description', '')}
        URL: {bounty.get('url', '')}
        
        Requirements:
        - 3-4 tweets maximum
        - Each tweet under 280 characters
        - Engaging and informative
        - Include relevant hashtags
        - End with a call-to-action
        - Format each tweet on a new line
        """
    
    def _parse_llm_response(self, content: str) -> List[str]:
        """Parse LLM response into individual tweets."""
        # Split by newlines and clean up
        tweets = [line.strip() for line in content.split('\n') if line.strip()]
        
        # Remove numbering if present (1. 2. 3. etc.)
        cleaned_tweets = []
        for tweet in tweets:
            # Remove leading numbers and dots
            if tweet and tweet[0].isdigit():
                tweet = tweet.split('.', 1)[1].strip() if '.' in tweet else tweet[1:].strip()
            cleaned_tweets.append(tweet)
        
        return cleaned_tweets
    
    def validate_thread(self, thread: List[str]) -> bool:
        """
        Validate that a thread meets all requirements.
        
        Args:
            thread: List of tweet texts
            
        Returns:
            True if valid, False otherwise
        """
        if not thread or len(thread) == 0:
            return False
        
        if len(thread) > 6:  # Too many tweets
            return False
        
        for tweet in thread:
            if not validate_tweet_content(tweet):
                return False
        
        return True

# Convenience function for backward compatibility
def generate_thread(bounty: Dict, use_llm: bool = False) -> List[str]:
    """
    Generate a Twitter thread from bounty data.
    
    Args:
        bounty: Bounty data dictionary
        use_llm: Whether to use LLM generation
        
    Returns:
        List of tweet texts for the thread
    """
    generator = ThreadGenerator(use_llm=use_llm)
    return generator.generate_thread(bounty)
