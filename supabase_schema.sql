-- Supabase Database Schema for Twitter Bounty Bot
-- Run this SQL in your Supabase SQL Editor to create the required tables

-- Table to track bounties we've already seen
CREATE TABLE IF NOT EXISTS seen_bounty (
    id TEXT PRIMARY KEY,
    title TEXT,
    url TEXT,
    seen_at BIGINT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table to track posted threads
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    bounty_id TEXT,
    posted_at BIGINT,
    tweet_thread_root_id TEXT,
    thread_tweets TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_seen_bounty_seen_at ON seen_bounty(seen_at);
CREATE INDEX IF NOT EXISTS idx_posts_posted_at ON posts(posted_at);
CREATE INDEX IF NOT EXISTS idx_posts_bounty_id ON posts(bounty_id);

-- Enable Row Level Security (RLS) for better security
ALTER TABLE seen_bounty ENABLE ROW LEVEL SECURITY;
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated users (adjust as needed for your use case)
CREATE POLICY "Allow all operations for authenticated users" ON seen_bounty
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON posts
    FOR ALL USING (auth.role() = 'authenticated');

-- Optional: Create a view for recent activity
CREATE OR REPLACE VIEW recent_activity AS
SELECT 
    'bounty' as type,
    id,
    title,
    seen_at as timestamp,
    url
FROM seen_bounty
WHERE seen_at > EXTRACT(EPOCH FROM NOW() - INTERVAL '7 days')
UNION ALL
SELECT 
    'post' as type,
    bounty_id as id,
    'Posted thread' as title,
    posted_at as timestamp,
    CONCAT('https://twitter.com/i/status/', tweet_thread_root_id) as url
FROM posts
WHERE posted_at > EXTRACT(EPOCH FROM NOW() - INTERVAL '7 days')
ORDER BY timestamp DESC;
