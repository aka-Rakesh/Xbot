"""
Database storage and deduplication logic for the Twitter Bounty Bot.
Handles SQLite/PostgreSQL operations for tracking seen bounties and posted threads.
"""
import sqlite3
import time
from typing import List, Dict, Optional
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL

Base = declarative_base()

class SeenBounty(Base):
    """Table to track bounties we've already seen."""
    __tablename__ = 'seen_bounty'
    
    id = Column(String, primary_key=True)  # bounty_id from the site
    title = Column(Text)
    url = Column(Text)
    seen_at = Column(Integer)  # Unix timestamp
    description = Column(Text, nullable=True)

class Post(Base):
    """Table to track posted threads."""
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bounty_id = Column(String)
    posted_at = Column(Integer)  # Unix timestamp
    tweet_thread_root_id = Column(String)
    thread_tweets = Column(Text)  # JSON string of all tweet IDs in thread

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize the database and create tables."""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")

def get_db_session():
    """Get a database session."""
    return SessionLocal()

def is_bounty_seen(bounty_id: str) -> bool:
    """Check if a bounty has already been seen."""
    session = get_db_session()
    try:
        bounty = session.query(SeenBounty).filter(SeenBounty.id == bounty_id).first()
        return bounty is not None
    finally:
        session.close()

def mark_bounty_seen(bounty_id: str, title: str, url: str, description: str = None):
    """Mark a bounty as seen."""
    session = get_db_session()
    try:
        bounty = SeenBounty(
            id=bounty_id,
            title=title,
            url=url,
            seen_at=int(time.time()),
            description=description
        )
        session.add(bounty)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def record_post(bounty_id: str, tweet_thread_root_id: str, thread_tweets: List[str]):
    """Record a posted thread."""
    session = get_db_session()
    try:
        post = Post(
            bounty_id=bounty_id,
            posted_at=int(time.time()),
            tweet_thread_root_id=tweet_thread_root_id,
            thread_tweets=','.join(thread_tweets)
        )
        session.add(post)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_recent_posts(hours: int = 24) -> List[Dict]:
    """Get posts from the last N hours."""
    session = get_db_session()
    try:
        cutoff_time = int(time.time()) - (hours * 3600)
        posts = session.query(Post).filter(Post.posted_at >= cutoff_time).all()
        return [
            {
                'bounty_id': post.bounty_id,
                'posted_at': post.posted_at,
                'tweet_thread_root_id': post.tweet_thread_root_id,
                'thread_tweets': post.thread_tweets.split(',') if post.thread_tweets else []
            }
            for post in posts
        ]
    finally:
        session.close()

def get_daily_post_count() -> int:
    """Get the number of posts made today."""
    session = get_db_session()
    try:
        today_start = int(time.time()) - (time.time() % 86400)  # Start of today
        count = session.query(Post).filter(Post.posted_at >= today_start).count()
        return count
    finally:
        session.close()
