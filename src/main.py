"""
Main scheduler and entry point for the Twitter Bounty Bot.
Coordinates scraping, deduplication, thread generation, and posting.
"""
import os
import sys
import time
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Add src directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .config import (
    POST_INTERVAL_MINUTES, MAX_POSTS_PER_DAY, USER_DISPLAY_NAME,
    validate_config
)
from .scraper import BountyScraper
from .generator import ThreadGenerator
from .poster import TwitterPoster
from .storage import (
    init_db, is_bounty_seen, mark_bounty_seen, record_post,
    get_daily_post_count, get_recent_posts
)
from .utils import log_with_context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bounty_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class BountyBot:
    """Main bot class that coordinates all operations."""
    
    def __init__(self):
        self.scraper = BountyScraper()
        self.generator = ThreadGenerator(use_llm=bool(os.getenv('OPENAI_API_KEY')))
        self.poster = TwitterPoster()
        self.is_running = False
        
        # Initialize database
        init_db()
        
        # Test connections
        self._test_connections()
    
    def _test_connections(self):
        """Test all external connections."""
        logger.info("Testing connections...")
        
        # Test Twitter connection
        if not self.poster.test_connection():
            logger.error("Twitter connection test failed")
            raise RuntimeError("Cannot connect to Twitter API")
        
        logger.info("All connections tested successfully")
    
    def run_scheduler(self):
        """Run the main scheduler loop."""
        logger.info(f"Starting bounty bot scheduler (interval: {POST_INTERVAL_MINUTES} minutes)")
        
        scheduler = BlockingScheduler()
        
        # Add the main job
        scheduler.add_job(
            func=self.check_and_post_bounties,
            trigger=IntervalTrigger(minutes=POST_INTERVAL_MINUTES),
            id='bounty_checker',
            name='Check for new bounties and post threads',
            replace_existing=True
        )
        
        # Add a daily reset job
        scheduler.add_job(
            func=self.daily_reset,
            trigger='cron',
            hour=0,
            minute=0,
            id='daily_reset',
            name='Daily reset and cleanup',
            replace_existing=True
        )
        
        try:
            self.is_running = True
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            raise
        finally:
            self.is_running = False
    
    def check_and_post_bounties(self):
        """Main job: check for new bounties and post threads."""
        try:
            log_with_context(logging.INFO, "Starting bounty check cycle")
            
            # Check daily post limit
            daily_count = get_daily_post_count()
            if daily_count >= MAX_POSTS_PER_DAY:
                log_with_context(logging.INFO, "Daily post limit reached", 
                               daily_count=daily_count, max_posts=MAX_POSTS_PER_DAY)
                return
            
            # Fetch new bounties (use Playwright for JavaScript-heavy sites)
            bounties = self.scraper.fetch_bounties(use_playwright=True)
            log_with_context(logging.INFO, "Fetched bounties", count=len(bounties))
            
            # Process each bounty
            new_bounties = []
            for bounty in bounties:
                bounty_id = bounty.get('id')
                if not bounty_id:
                    continue
                
                # Check if we've already seen this bounty
                if is_bounty_seen(bounty_id):
                    continue
                
                new_bounties.append(bounty)
            
            log_with_context(logging.INFO, "Found new bounties", count=len(new_bounties))
            
            # Process new bounties (limit to avoid hitting daily limit)
            remaining_posts = MAX_POSTS_PER_DAY - daily_count
            bounties_to_process = new_bounties[:remaining_posts]
            
            for bounty in bounties_to_process:
                try:
                    self._process_bounty(bounty)
                    
                    # Mark as seen
                    mark_bounty_seen(
                        bounty['id'],
                        bounty['title'],
                        bounty['url'],
                        bounty.get('description', '')
                    )
                    
                    # Small delay between posts
                    time.sleep(30)
                    
                except Exception as e:
                    log_with_context(logging.ERROR, "Failed to process bounty", 
                                   bounty_id=bounty.get('id'), error=str(e))
                    continue
            
            log_with_context(logging.INFO, "Bounty check cycle completed")
            
        except Exception as e:
            log_with_context(logging.ERROR, "Error in bounty check cycle", error=str(e))
    
    def _process_bounty(self, bounty: dict):
        """Process a single bounty: generate thread and post."""
        try:
            bounty_id = bounty['id']
            log_with_context(logging.INFO, "Processing bounty", bounty_id=bounty_id, title=bounty['title'])
            
            # Generate thread
            thread = self.generator.generate_thread(bounty)
            if not thread:
                log_with_context(logging.WARNING, "Failed to generate thread", bounty_id=bounty_id)
                return
            
            log_with_context(logging.INFO, "Generated thread", bounty_id=bounty_id, tweet_count=len(thread))
            
            # Post thread
            result = self.poster.post_thread(thread)
            if result['success']:
                # Record the post
                record_post(
                    bounty_id,
                    result['root_tweet_id'],
                    result['tweet_ids']
                )
                
                log_with_context(logging.INFO, "Successfully posted bounty thread", 
                               bounty_id=bounty_id, root_tweet_id=result['root_tweet_id'])
            else:
                log_with_context(logging.ERROR, "Failed to post thread", bounty_id=bounty_id)
                
        except Exception as e:
            log_with_context(logging.ERROR, "Error processing bounty", 
                           bounty_id=bounty.get('id'), error=str(e))
            raise
    
    def daily_reset(self):
        """Daily reset and cleanup tasks."""
        try:
            log_with_context(logging.INFO, "Running daily reset")
            
            # Log daily statistics
            recent_posts = get_recent_posts(24)  # Last 24 hours
            log_with_context(logging.INFO, "Daily statistics", posts_count=len(recent_posts))
            
            # Test connections
            self._test_connections()
            
            log_with_context(logging.INFO, "Daily reset completed")
            
        except Exception as e:
            log_with_context(logging.ERROR, "Error in daily reset", error=str(e))
    
    def run_once(self):
        """Run a single check cycle (useful for testing)."""
        logger.info("Running single bounty check cycle")
        self.check_and_post_bounties()
        logger.info("Single check cycle completed")

def main():
    """Main entry point."""
    try:
        # Validate configuration
        validate_config()
        
        # Create and run bot
        bot = BountyBot()
        
        # Check command line arguments
        if len(sys.argv) > 1 and sys.argv[1] == '--once':
            # Run once for testing
            bot.run_once()
        else:
            # Run scheduler
            bot.run_scheduler()
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
