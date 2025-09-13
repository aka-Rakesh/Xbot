"""
Database storage and deduplication logic for the Twitter Bounty Bot.
Handles Supabase operations for tracking seen bounties and posted threads.
"""
import time
import json
from typing import List, Dict, Optional
from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_KEY, DATABASE_URL

# Initialize Supabase client
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def init_db():
    """Initialize the database and create tables."""
    if supabase:
        print("Supabase client initialized successfully")
        # Supabase tables are created via the dashboard or SQL editor
        # We'll assume the tables exist or create them via SQL
        try:
            # Test connection
            supabase.table('seen_bounty').select('id').limit(1).execute()
            print("Supabase connection verified")
        except Exception as e:
            print(f"Supabase connection test failed: {e}")
            print("Please ensure your Supabase tables are created. See README for SQL schema.")
    else:
        print("Using SQLite fallback - Supabase not configured")
        # Fallback to SQLite for local development
        import sqlite3
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS seen_bounty (
                id TEXT PRIMARY KEY,
                title TEXT,
                url TEXT,
                seen_at INTEGER,
                description TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bounty_id TEXT,
                posted_at INTEGER,
                tweet_thread_root_id TEXT,
                thread_tweets TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("SQLite database initialized successfully")

def is_bounty_seen(bounty_id: str) -> bool:
    """Check if a bounty has already been seen."""
    if supabase:
        try:
            result = supabase.table('seen_bounty').select('id').eq('id', bounty_id).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error checking bounty in Supabase: {e}")
            return False
    else:
        # SQLite fallback
        import sqlite3
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM seen_bounty WHERE id = ?', (bounty_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

def mark_bounty_seen(bounty_id: str, title: str, url: str, description: str = None):
    """Mark a bounty as seen."""
    if supabase:
        try:
            supabase.table('seen_bounty').insert({
                'id': bounty_id,
                'title': title,
                'url': url,
                'seen_at': int(time.time()),
                'description': description
            }).execute()
        except Exception as e:
            print(f"Error marking bounty as seen in Supabase: {e}")
            raise e
    else:
        # SQLite fallback
        import sqlite3
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO seen_bounty (id, title, url, seen_at, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (bounty_id, title, url, int(time.time()), description))
        conn.commit()
        conn.close()

def record_post(bounty_id: str, tweet_thread_root_id: str, thread_tweets: List[str]):
    """Record a posted thread."""
    if supabase:
        try:
            supabase.table('posts').insert({
                'bounty_id': bounty_id,
                'posted_at': int(time.time()),
                'tweet_thread_root_id': tweet_thread_root_id,
                'thread_tweets': ','.join(thread_tweets)
            }).execute()
        except Exception as e:
            print(f"Error recording post in Supabase: {e}")
            raise e
    else:
        # SQLite fallback
        import sqlite3
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO posts (bounty_id, posted_at, tweet_thread_root_id, thread_tweets)
            VALUES (?, ?, ?, ?)
        ''', (bounty_id, int(time.time()), tweet_thread_root_id, ','.join(thread_tweets)))
        conn.commit()
        conn.close()

def get_recent_posts(hours: int = 24) -> List[Dict]:
    """Get posts from the last N hours."""
    cutoff_time = int(time.time()) - (hours * 3600)
    
    if supabase:
        try:
            result = supabase.table('posts').select('*').gte('posted_at', cutoff_time).execute()
            return [
                {
                    'bounty_id': post['bounty_id'],
                    'posted_at': post['posted_at'],
                    'tweet_thread_root_id': post['tweet_thread_root_id'],
                    'thread_tweets': post['thread_tweets'].split(',') if post['thread_tweets'] else []
                }
                for post in result.data
            ]
        except Exception as e:
            print(f"Error getting recent posts from Supabase: {e}")
            return []
    else:
        # SQLite fallback
        import sqlite3
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM posts WHERE posted_at >= ?', (cutoff_time,))
        posts = cursor.fetchall()
        conn.close()
        
        return [
            {
                'bounty_id': post[1],
                'posted_at': post[2],
                'tweet_thread_root_id': post[3],
                'thread_tweets': post[4].split(',') if post[4] else []
            }
            for post in posts
        ]

def get_daily_post_count() -> int:
    """Get the number of posts made today."""
    today_start = int(time.time()) - (int(time.time()) % 86400)  # Start of today
    
    if supabase:
        try:
            result = supabase.table('posts').select('id', count='exact').gte('posted_at', today_start).execute()
            return result.count or 0
        except Exception as e:
            print(f"Error getting daily post count from Supabase: {e}")
            return 0
    else:
        # SQLite fallback
        import sqlite3
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM posts WHERE posted_at >= ?', (today_start,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
