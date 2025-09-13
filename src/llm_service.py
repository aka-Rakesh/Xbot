"""
LLM Service for Crypto News Bot
Handles DeepSeek model integration via Ollama for content generation.
"""
import requests
import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from .config import OLLAMA_BASE_URL, DEEPSEEK_MODEL, MAX_TOKENS, TEMPERATURE

logger = logging.getLogger(__name__)

class OllamaService:
    """Service for interacting with DeepSeek model via Ollama."""
    
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or OLLAMA_BASE_URL
        self.model = model or DEEPSEEK_MODEL
        self.session = requests.Session()
        self.session.timeout = 60
    
    def generate_content(self, prompt: str, context: Dict = None, max_tokens: int = None) -> str:
        """
        Generate content using DeepSeek via Ollama.
        
        Args:
            prompt: The main prompt for content generation
            context: Additional context data (posting history, trends, etc.)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated content string
        """
        try:
            full_prompt = self._build_prompt(prompt, context)
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": TEMPERATURE,
                    "max_tokens": max_tokens or MAX_TOKENS,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            }
            
            logger.info(f"Generating content with DeepSeek model: {self.model}")
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            generated_content = result.get("response", "")
            
            logger.info(f"Generated content length: {len(generated_content)} characters")
            return generated_content.strip()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Ollama API: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise
    
    def generate_thread(self, content_type: str, source_data: Dict, context: Dict = None) -> List[str]:
        """
        Generate a Twitter thread for the given content type and source data.
        
        Args:
            content_type: 'news' or 'bounty'
            source_data: The source article or bounty data
            context: Additional context for generation
            
        Returns:
            List of tweet strings for the thread
        """
        try:
            if content_type == 'news':
                prompt = self._build_news_prompt(source_data, context)
            elif content_type == 'bounty':
                prompt = self._build_bounty_prompt(source_data, context)
            else:
                raise ValueError(f"Unknown content type: {content_type}")
            
            generated_content = self.generate_content(prompt, context)
            thread = self._parse_thread(generated_content)
            
            logger.info(f"Generated {len(thread)} tweets for {content_type} content")
            return thread
            
        except Exception as e:
            logger.error(f"Error generating thread: {e}")
            raise
    
    def _build_prompt(self, prompt: str, context: Dict = None) -> str:
        """Build context-aware prompt for the LLM."""
        context_str = ""
        if context:
            context_str = f"\n\nContext Information:\n{json.dumps(context, indent=2)}"
        
        return f"{prompt}{context_str}"
    
    def _build_news_prompt(self, article: Dict, context: Dict = None) -> str:
        """Build prompt for news content generation."""
        title = article.get('title', '')
        content = article.get('content', '')
        source = article.get('source', '')
        category = article.get('category', '')
        
        prompt = f"""
You are a crypto news bot that creates engaging Twitter threads about cryptocurrency and Web3 news.

Article Information:
- Title: {title}
- Source: {source}
- Category: {category}
- Content: {content[:1000]}...

Create a Twitter thread (3-6 tweets) that:
1. Captures the key points of the news
2. Explains why it matters to the crypto community
3. Uses engaging language and relevant hashtags
4. Maintains a professional but accessible tone
5. Includes a call-to-action for engagement

Format each tweet on a new line, starting with "Tweet 1:", "Tweet 2:", etc.
Keep each tweet under 280 characters.
Use relevant crypto hashtags but don't overuse them.
Make it engaging and shareable.

Thread:
"""
        return prompt
    
    def _build_bounty_prompt(self, bounty: Dict, context: Dict = None) -> str:
        """Build prompt for bounty content generation."""
        title = bounty.get('title', '')
        description = bounty.get('description', '')
        reward = bounty.get('reward_amount', '')
        currency = bounty.get('reward_currency', 'USDC')
        deadline = bounty.get('deadline', '')
        category = bounty.get('category', '')
        
        prompt = f"""
You are a crypto bounty bot that creates engaging Twitter threads about bounty opportunities.

Bounty Information:
- Title: {title}
- Description: {description}
- Reward: {reward} {currency}
- Deadline: {deadline}
- Category: {category}

Create a Twitter thread (3-4 tweets) that:
1. Introduces the bounty opportunity naturally
2. Explains what skills are needed
3. Highlights the reward and deadline
4. Encourages qualified developers to apply
5. Feels organic and not spammy

Format each tweet on a new line, starting with "Tweet 1:", "Tweet 2:", etc.
Keep each tweet under 280 characters.
Use relevant hashtags but keep it natural.
Make it appealing to developers and builders.

Thread:
"""
        return prompt
    
    def _parse_thread(self, content: str) -> List[str]:
        """Parse generated content into individual tweets."""
        tweets = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('Tweet ') and ':' in line:
                # Extract tweet content after "Tweet X:"
                tweet_content = line.split(':', 1)[1].strip()
                if tweet_content and len(tweet_content) <= 280:
                    tweets.append(tweet_content)
            elif line and not line.startswith('Tweet ') and len(line) <= 280:
                # Handle case where tweets aren't prefixed
                tweets.append(line)
        
        # Filter out empty tweets and ensure they're within limits
        valid_tweets = []
        for tweet in tweets:
            if tweet and len(tweet) <= 280:
                valid_tweets.append(tweet)
        
        return valid_tweets[:6]  # Maximum 6 tweets per thread
    
    def test_connection(self) -> bool:
        """Test connection to Ollama service."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            
            if self.model in model_names:
                logger.info(f"Ollama connection successful, model {self.model} available")
                return True
            else:
                logger.warning(f"Model {self.model} not found. Available models: {model_names}")
                return False
                
        except Exception as e:
            logger.error(f"Ollama connection test failed: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available models from Ollama."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            
            models = response.json().get('models', [])
            return [model['name'] for model in models]
            
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []

# Convenience function for backward compatibility
def generate_content(prompt: str, context: Dict = None) -> str:
    """Generate content using the default Ollama service."""
    service = OllamaService()
    return service.generate_content(prompt, context)
