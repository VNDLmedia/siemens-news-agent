-- News AI Agent Database Schema
-- This script initializes the database for the news aggregation system

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Articles table: Stores all fetched news articles
CREATE TABLE IF NOT EXISTS articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    content TEXT,
    source TEXT NOT NULL,
    published_at TIMESTAMP,
    fetched_at TIMESTAMP NOT NULL DEFAULT NOW(),
    summary_short TEXT,
    summary_long TEXT,
    processed BOOLEAN NOT NULL DEFAULT FALSE,
    sent BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url);
CREATE INDEX IF NOT EXISTS idx_articles_processed ON articles(processed) WHERE processed = FALSE;
CREATE INDEX IF NOT EXISTS idx_articles_sent ON articles(sent) WHERE sent = FALSE;
CREATE INDEX IF NOT EXISTS idx_articles_fetched_at ON articles(fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_articles_updated_at BEFORE UPDATE ON articles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert a test article (optional, for verification)
INSERT INTO articles (url, title, content, source, published_at)
VALUES (
    'https://example.com/test-article',
    'Test Article - Database Setup Successful',
    'This is a test article to verify the database setup is working correctly.',
    'System',
    NOW()
) ON CONFLICT (url) DO NOTHING;

-- Create a view for easy querying of unprocessed articles
CREATE OR REPLACE VIEW unprocessed_articles AS
SELECT * FROM articles
WHERE processed = FALSE
ORDER BY fetched_at ASC;

-- Create a view for articles ready to send
CREATE OR REPLACE VIEW unsent_articles AS
SELECT * FROM articles
WHERE processed = TRUE AND sent = FALSE
ORDER BY fetched_at DESC;

COMMENT ON TABLE articles IS 'Stores all fetched news articles with their summaries';
COMMENT ON COLUMN articles.url IS 'Unique URL of the article (used for deduplication)';
COMMENT ON COLUMN articles.processed IS 'TRUE if article has been summarized by AI';
COMMENT ON COLUMN articles.sent IS 'TRUE if article was included in an email digest';
