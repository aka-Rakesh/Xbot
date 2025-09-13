-- Enhanced Database Schema for Crypto News Bot with Bounty Integration
-- Run this SQL in your Supabase SQL Editor to create the required tables

-- News articles table
CREATE TABLE IF NOT EXISTS news_articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    url TEXT UNIQUE,
    source TEXT,
    published_at TIMESTAMP,
    category TEXT,
    sentiment_score FLOAT,
    relevance_score FLOAT,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Bounties table
CREATE TABLE IF NOT EXISTS bounties (
    id TEXT PRIMARY KEY,
    title TEXT,
    description TEXT,
    url TEXT,
    reward_amount TEXT,
    reward_currency TEXT,
    deadline TIMESTAMP,
    category TEXT,
    difficulty TEXT,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    posted_at TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Content queue for scheduled posts
CREATE TABLE IF NOT EXISTS content_queue (
    id SERIAL PRIMARY KEY,
    content_type TEXT NOT NULL CHECK (content_type IN ('news', 'bounty')),
    thread_content JSONB NOT NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    posted_at TIMESTAMP WITH TIME ZONE,
    engagement_metrics JSONB DEFAULT '{}',
    source_id TEXT, -- references news_articles.id or bounties.id
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'posted', 'failed', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Posts table for tracking posted content
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    content_id INTEGER REFERENCES content_queue(id),
    tweet_id TEXT,
    thread_root_id TEXT,
    posted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    engagement_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Analytics table for performance tracking
CREATE TABLE IF NOT EXISTS analytics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    posts_count INTEGER DEFAULT 0,
    engagement_total INTEGER DEFAULT 0,
    revenue_total DECIMAL(10,2) DEFAULT 0.00,
    top_performing_content JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User engagement tracking
CREATE TABLE IF NOT EXISTS user_engagement (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id),
    user_id TEXT,
    engagement_type TEXT CHECK (engagement_type IN ('like', 'retweet', 'reply', 'quote_tweet')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Content performance metrics
CREATE TABLE IF NOT EXISTS content_performance (
    id SERIAL PRIMARY KEY,
    content_id INTEGER REFERENCES content_queue(id),
    impressions INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    retweets INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    engagement_rate FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- LLM context storage
CREATE TABLE IF NOT EXISTS llm_context (
    id SERIAL PRIMARY KEY,
    context_type TEXT NOT NULL CHECK (context_type IN ('prompt', 'response', 'template')),
    content JSONB NOT NULL,
    model_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Bounty revenue tracking
CREATE TABLE IF NOT EXISTS bounty_revenue (
    id SERIAL PRIMARY KEY,
    bounty_id TEXT REFERENCES bounties(id),
    post_id INTEGER REFERENCES posts(id),
    revenue_amount DECIMAL(10,2),
    currency TEXT DEFAULT 'USDC',
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_news_articles_published_at ON news_articles(published_at);
CREATE INDEX IF NOT EXISTS idx_news_articles_category ON news_articles(category);
CREATE INDEX IF NOT EXISTS idx_news_articles_sentiment ON news_articles(sentiment_score);
CREATE INDEX IF NOT EXISTS idx_bounties_deadline ON bounties(deadline);
CREATE INDEX IF NOT EXISTS idx_bounties_category ON bounties(category);
CREATE INDEX IF NOT EXISTS idx_content_queue_scheduled_at ON content_queue(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_content_queue_status ON content_queue(status);
CREATE INDEX IF NOT EXISTS idx_content_queue_content_type ON content_queue(content_type);
CREATE INDEX IF NOT EXISTS idx_posts_posted_at ON posts(posted_at);
CREATE INDEX IF NOT EXISTS idx_analytics_date ON analytics(date);
CREATE INDEX IF NOT EXISTS idx_user_engagement_post_id ON user_engagement(post_id);
CREATE INDEX IF NOT EXISTS idx_content_performance_content_id ON content_performance(content_id);

-- Enable Row Level Security (RLS)
ALTER TABLE news_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE bounties ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_engagement ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE llm_context ENABLE ROW LEVEL SECURITY;
ALTER TABLE bounty_revenue ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated users
CREATE POLICY "Allow all operations for authenticated users" ON news_articles
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON bounties
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON content_queue
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON posts
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON analytics
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON user_engagement
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON content_performance
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON llm_context
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON bounty_revenue
    FOR ALL USING (auth.role() = 'authenticated');

-- Create views for common queries
CREATE OR REPLACE VIEW daily_content_summary AS
SELECT 
    DATE(created_at) as date,
    content_type,
    COUNT(*) as total_posts,
    COUNT(CASE WHEN status = 'posted' THEN 1 END) as posted_count,
    AVG((engagement_metrics->>'likes')::int) as avg_likes,
    AVG((engagement_metrics->>'retweets')::int) as avg_retweets
FROM content_queue
GROUP BY DATE(created_at), content_type
ORDER BY date DESC;

CREATE OR REPLACE VIEW bounty_performance AS
SELECT 
    b.title,
    b.reward_amount,
    b.reward_currency,
    br.revenue_amount,
    br.status,
    cp.engagement_rate,
    cp.likes,
    cp.retweets
FROM bounties b
LEFT JOIN bounty_revenue br ON b.id = br.bounty_id
LEFT JOIN content_queue cq ON b.id = cq.source_id AND cq.content_type = 'bounty'
LEFT JOIN content_performance cp ON cq.id = cp.content_id
ORDER BY br.revenue_amount DESC NULLS LAST;

CREATE OR REPLACE VIEW top_performing_content AS
SELECT 
    cq.id,
    cq.content_type,
    cq.thread_content,
    cp.engagement_rate,
    cp.likes,
    cp.retweets,
    cp.replies,
    cq.posted_at
FROM content_queue cq
JOIN content_performance cp ON cq.id = cp.content_id
WHERE cq.status = 'posted'
ORDER BY cp.engagement_rate DESC
LIMIT 50;

-- Create functions for common operations
CREATE OR REPLACE FUNCTION update_content_performance()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO content_performance (content_id, impressions, likes, retweets, replies, clicks, engagement_rate)
    VALUES (NEW.id, 0, 0, 0, 0, 0, 0.0)
    ON CONFLICT (content_id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically create performance tracking
CREATE TRIGGER trigger_create_content_performance
    AFTER INSERT ON content_queue
    FOR EACH ROW
    EXECUTE FUNCTION update_content_performance();

-- Create function to update engagement metrics
CREATE OR REPLACE FUNCTION update_engagement_metrics()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE content_performance
    SET 
        likes = COALESCE((NEW.engagement_data->>'likes')::int, 0),
        retweets = COALESCE((NEW.engagement_data->>'retweets')::int, 0),
        replies = COALESCE((NEW.engagement_data->>'replies')::int, 0),
        clicks = COALESCE((NEW.engagement_data->>'clicks')::int, 0),
        engagement_rate = CASE 
            WHEN COALESCE((NEW.engagement_data->>'impressions')::int, 0) > 0 
            THEN (COALESCE((NEW.engagement_data->>'likes')::int, 0) + 
                  COALESCE((NEW.engagement_data->>'retweets')::int, 0) + 
                  COALESCE((NEW.engagement_data->>'replies')::int, 0))::float / 
                 (NEW.engagement_data->>'impressions')::int
            ELSE 0.0
        END,
        updated_at = NOW()
    WHERE content_id = (
        SELECT id FROM content_queue WHERE id = NEW.content_id
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update engagement metrics
CREATE TRIGGER trigger_update_engagement_metrics
    AFTER UPDATE OF engagement_data ON posts
    FOR EACH ROW
    EXECUTE FUNCTION update_engagement_metrics();