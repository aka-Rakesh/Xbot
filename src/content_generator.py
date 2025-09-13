"""
Content Generator for Crypto News Bot
Uses LLM service to generate engaging Twitter content with context awareness.
"""
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from .llm_service import OllamaService
from .storage import get_recent_posts, get_engagement_data
from .config import MAX_THREAD_LENGTH, MIN_ENGAGEMENT_THRESHOLD

logger = logging.getLogger(__name__)

class ContentGenerator:
    """Generates Twitter content using LLM with context awareness."""
    
    def __init__(self):
        self.llm_service = OllamaService()
        self.content_templates = self._load_templates()
    
    def generate_news_thread(self, article: Dict, context: Dict = None) -> List[str]:
        """
        Generate a Twitter thread for a news article.
        
        Args:
            article: News article data
            context: Additional context for generation
            
        Returns:
            List of tweet strings for the thread
        """
        try:
            # Build context from recent posts and engagement data
            full_context = self._build_news_context(article, context)
            
            # Generate thread using LLM
            thread = self.llm_service.generate_thread('news', article, full_context)
            
            # Validate and clean the thread
            validated_thread = self._validate_thread(thread, 'news')
            
            logger.info(f"Generated news thread with {len(validated_thread)} tweets")
            return validated_thread
            
        except Exception as e:
            logger.error(f"Error generating news thread: {e}")
            # Fallback to template-based generation
            return self._generate_template_news_thread(article)
    
    def generate_bounty_thread(self, bounty: Dict, context: Dict = None) -> List[str]:
        """
        Generate a Twitter thread for a bounty opportunity.
        
        Args:
            bounty: Bounty data
            context: Additional context for generation
            
        Returns:
            List of tweet strings for the thread
        """
        try:
            # Build context from recent posts and engagement data
            full_context = self._build_bounty_context(bounty, context)
            
            # Generate thread using LLM
            thread = self.llm_service.generate_thread('bounty', bounty, full_context)
            
            # Validate and clean the thread
            validated_thread = self._validate_thread(thread, 'bounty')
            
            logger.info(f"Generated bounty thread with {len(validated_thread)} tweets")
            return validated_thread
            
        except Exception as e:
            logger.error(f"Error generating bounty thread: {e}")
            # Fallback to template-based generation
            return self._generate_template_bounty_thread(bounty)
    
    def generate_daily_content_plan(self, news_articles: List[Dict], bounties: List[Dict]) -> List[Dict]:
        """
        Generate a daily content plan with scheduled posts.
        
        Args:
            news_articles: List of news articles
            bounties: List of bounty opportunities
            
        Returns:
            List of scheduled content items
        """
        try:
            content_plan = []
            
            # Calculate content mix based on configuration
            news_count = int(len(news_articles) * 0.8)  # 80% news
            bounty_count = int(len(bounties) * 0.2)     # 20% bounties
            
            # Select top news articles
            top_news = self._select_top_news(news_articles, news_count)
            
            # Select relevant bounties
            relevant_bounties = self._select_relevant_bounties(bounties, bounty_count)
            
            # Generate content for each item
            for article in top_news:
                thread = self.generate_news_thread(article)
                if thread:
                    content_plan.append({
                        'type': 'news',
                        'content': thread,
                        'source_data': article,
                        'scheduled_time': self._calculate_optimal_time('news'),
                        'priority': self._calculate_news_priority(article)
                    })
            
            for bounty in relevant_bounties:
                thread = self.generate_bounty_thread(bounty)
                if thread:
                    content_plan.append({
                        'type': 'bounty',
                        'content': thread,
                        'source_data': bounty,
                        'scheduled_time': self._calculate_optimal_time('bounty'),
                        'priority': self._calculate_bounty_priority(bounty)
                    })
            
            # Sort by priority and schedule
            content_plan.sort(key=lambda x: x['priority'], reverse=True)
            
            logger.info(f"Generated content plan with {len(content_plan)} items")
            return content_plan
            
        except Exception as e:
            logger.error(f"Error generating daily content plan: {e}")
            return []
    
    def _build_news_context(self, article: Dict, context: Dict = None) -> Dict:
        """Build context for news content generation."""
        base_context = {
            'article_title': article.get('title', ''),
            'article_category': article.get('category', ''),
            'article_source': article.get('source', ''),
            'current_time': datetime.now().isoformat(),
            'content_type': 'news'
        }
        
        # Add recent posting history
        recent_posts = get_recent_posts(hours=24)
        base_context['recent_posts'] = recent_posts[:5]  # Last 5 posts
        
        # Add engagement data
        engagement_data = get_engagement_data(hours=24)
        base_context['recent_engagement'] = engagement_data
        
        # Add trending topics (if available)
        if context:
            base_context.update(context)
        
        return base_context
    
    def _build_bounty_context(self, bounty: Dict, context: Dict = None) -> Dict:
        """Build context for bounty content generation."""
        base_context = {
            'bounty_title': bounty.get('title', ''),
            'bounty_reward': bounty.get('reward_amount', ''),
            'bounty_currency': bounty.get('reward_currency', 'USDC'),
            'bounty_deadline': bounty.get('deadline', ''),
            'bounty_category': bounty.get('category', ''),
            'current_time': datetime.now().isoformat(),
            'content_type': 'bounty'
        }
        
        # Add recent bounty posting history
        recent_bounty_posts = get_recent_posts(hours=168, content_type='bounty')  # Last week
        base_context['recent_bounty_posts'] = recent_bounty_posts[:3]
        
        # Add engagement data for bounty posts
        bounty_engagement = get_engagement_data(hours=168, content_type='bounty')
        base_context['bounty_engagement'] = bounty_engagement
        
        if context:
            base_context.update(context)
        
        return base_context
    
    def _validate_thread(self, thread: List[str], content_type: str) -> List[str]:
        """Validate and clean generated thread."""
        if not thread:
            return []
        
        validated_thread = []
        for tweet in thread:
            # Basic validation
            if tweet and len(tweet) <= 280 and len(tweet) > 10:
                # Clean up common issues
                cleaned_tweet = self._clean_tweet(tweet)
                if cleaned_tweet:
                    validated_thread.append(cleaned_tweet)
        
        # Ensure we don't exceed maximum thread length
        return validated_thread[:MAX_THREAD_LENGTH]
    
    def _clean_tweet(self, tweet: str) -> str:
        """Clean up generated tweet content."""
        # Remove common LLM artifacts
        tweet = tweet.replace('Tweet 1:', '').replace('Tweet 2:', '').replace('Tweet 3:', '')
        tweet = tweet.replace('Tweet 4:', '').replace('Tweet 5:', '').replace('Tweet 6:', '')
        
        # Remove excessive whitespace
        tweet = ' '.join(tweet.split())
        
        # Ensure it starts with content, not metadata
        if tweet.startswith('Thread:') or tweet.startswith('Content:'):
            tweet = tweet.split(':', 1)[1].strip()
        
        return tweet.strip()
    
    def _select_top_news(self, articles: List[Dict], count: int) -> List[Dict]:
        """Select top news articles based on relevance and engagement potential."""
        # Sort by relevance score and sentiment
        sorted_articles = sorted(
            articles,
            key=lambda x: (
                x.get('relevance_score', 0),
                x.get('sentiment_score', 0)
            ),
            reverse=True
        )
        
        return sorted_articles[:count]
    
    def _select_relevant_bounties(self, bounties: List[Dict], count: int) -> List[Dict]:
        """Select relevant bounty opportunities."""
        # Filter for crypto/Web3 related bounties
        relevant_bounties = [
            bounty for bounty in bounties
            if any(keyword in bounty.get('title', '').lower() or 
                   keyword in bounty.get('description', '').lower()
                   for keyword in ['crypto', 'blockchain', 'web3', 'defi', 'nft', 'dao', 'token'])
        ]
        
        # Sort by reward amount and deadline
        sorted_bounties = sorted(
            relevant_bounties,
            key=lambda x: (
                float(x.get('reward_amount', '0').replace('USDC', '').replace(',', '') or 0),
                x.get('deadline', '')
            ),
            reverse=True
        )
        
        return sorted_bounties[:count]
    
    def _calculate_optimal_time(self, content_type: str) -> datetime:
        """Calculate optimal posting time based on content type and engagement data."""
        now = datetime.now()
        
        # Base optimal times for different content types
        if content_type == 'news':
            # News posts work well in morning and afternoon
            optimal_hours = [8, 12, 16, 20]
        else:  # bounty
            # Bounty posts work well in evening
            optimal_hours = [18, 19, 20, 21]
        
        # Find next optimal hour
        for hour in optimal_hours:
            optimal_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if optimal_time > now:
                return optimal_time
        
        # If no optimal time today, use tomorrow
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=optimal_hours[0], minute=0, second=0, microsecond=0)
    
    def _calculate_news_priority(self, article: Dict) -> float:
        """Calculate priority score for news article."""
        priority = 0.0
        
        # Relevance score
        priority += article.get('relevance_score', 0) * 0.4
        
        # Sentiment score
        priority += article.get('sentiment_score', 0) * 0.3
        
        # Recency (newer is better)
        published_at = article.get('published_at')
        if published_at:
            hours_old = (datetime.now() - published_at).total_seconds() / 3600
            priority += max(0, 1 - hours_old / 24) * 0.3
        
        return priority
    
    def _calculate_bounty_priority(self, bounty: Dict) -> float:
        """Calculate priority score for bounty opportunity."""
        priority = 0.0
        
        # Reward amount
        reward_amount = float(bounty.get('reward_amount', '0').replace('USDC', '').replace(',', '') or 0)
        priority += min(reward_amount / 1000, 1.0) * 0.4  # Normalize to 0-1
        
        # Deadline urgency
        deadline = bounty.get('deadline')
        if deadline:
            days_left = (deadline - datetime.now()).days
            priority += max(0, 1 - days_left / 30) * 0.3  # More urgent = higher priority
        
        # Category relevance
        category = bounty.get('category', '').lower()
        if any(keyword in category for keyword in ['content', 'writing', 'social', 'marketing']):
            priority += 0.3
        
        return priority
    
    def _load_templates(self) -> Dict[str, List[str]]:
        """Load content templates for fallback generation."""
        return {
            'news': [
                "🔔 {title}",
                "📈 {summary}",
                "🔗 Read more: {url} | Follow for crypto updates! #Crypto #Web3"
            ],
            'bounty': [
                "💰 New bounty opportunity: {title}",
                "🎯 {description}",
                "⏰ Deadline: {deadline} | Reward: {reward}",
                "🔗 Apply: {url} | RT if you're interested! #Bounty #Crypto"
            ]
        }
    
    def _generate_template_news_thread(self, article: Dict) -> List[str]:
        """Generate news thread using templates as fallback."""
        template = self.content_templates['news']
        return [
            template[0].format(title=article.get('title', '')[:200]),
            template[1].format(summary=article.get('content', '')[:150]),
            template[2].format(url=article.get('url', ''))
        ]
    
    def _generate_template_bounty_thread(self, bounty: Dict) -> List[str]:
        """Generate bounty thread using templates as fallback."""
        template = self.content_templates['bounty']
        return [
            template[0].format(title=bounty.get('title', '')[:200]),
            template[1].format(description=bounty.get('description', '')[:150]),
            template[2].format(
                deadline=bounty.get('deadline', 'TBD'),
                reward=bounty.get('reward_amount', 'TBD')
            ),
            template[3].format(url=bounty.get('url', ''))
        ]

# Convenience functions for backward compatibility
def generate_news_thread(article: Dict, context: Dict = None) -> List[str]:
    """Generate news thread using default content generator."""
    generator = ContentGenerator()
    return generator.generate_news_thread(article, context)

def generate_bounty_thread(bounty: Dict, context: Dict = None) -> List[str]:
    """Generate bounty thread using default content generator."""
    generator = ContentGenerator()
    return generator.generate_bounty_thread(bounty, context)
