-- News AI Agent Database Schema
-- This script initializes the database for the news aggregation system

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- RSS Sources table: Manages RSS feed sources
CREATE TABLE IF NOT EXISTS rss_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    language VARCHAR(10) NOT NULL DEFAULT 'de',
    category TEXT,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    article_count INTEGER NOT NULL DEFAULT 0,
    last_fetched TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for RSS sources
CREATE INDEX IF NOT EXISTS idx_rss_sources_url ON rss_sources(url);
CREATE INDEX IF NOT EXISTS idx_rss_sources_enabled ON rss_sources(enabled) WHERE enabled = TRUE;
CREATE INDEX IF NOT EXISTS idx_rss_sources_language ON rss_sources(language);
CREATE INDEX IF NOT EXISTS idx_rss_sources_category ON rss_sources(category);

-- Insert default feeds
-- German Sources
INSERT INTO rss_sources (name, url, language, category, enabled) VALUES
    -- 🇩🇪 German - General
    ('Tagesschau', 'https://www.tagesschau.de/xml/rss2/', 'de', 'general', TRUE),
    ('Spiegel', 'https://www.spiegel.de/schlagzeilen/index.rss', 'de', 'general', TRUE),
    ('FAZ.NET Aktuell', 'https://www.faz.net/rss/aktuell', 'de', 'general', TRUE),
    ('Süddeutsche Zeitung Topthemen', 'https://rss.sueddeutsche.de/rss/Topthemen', 'de', 'general', TRUE),
    ('ZEIT ONLINE News', 'https://newsfeed.zeit.de/index', 'de', 'general', TRUE),
    -- 🇩🇪 German - Business
    ('FAZ.NET Wirtschaft', 'https://www.faz.net/rss/aktuell/wirtschaft', 'de', 'business', TRUE),
    ('Süddeutsche Zeitung Wirtschaft', 'https://rss.sueddeutsche.de/rss/Wirtschaft', 'de', 'business', TRUE),
    ('Handelsblatt Schlagzeilen', 'https://www.handelsblatt.com/contentexport/feed/schlagzeilen', 'de', 'business', TRUE),
    ('Handelsblatt Finanzen', 'https://www.handelsblatt.com/contentexport/feed/finanzen', 'de', 'business', TRUE),
    ('WirtschaftsWoche', 'https://www.wiwo.de/contentexport/feed/rss/schlagzeilen', 'de', 'business', TRUE),
    ('Manager Magazin', 'https://www.manager-magazin.de/unternehmen/index.rss', 'de', 'business', TRUE),
    -- 🇩🇪 German - Tech
    ('Heise', 'https://www.heise.de/rss/heise-atom.xml', 'de', 'tech', TRUE),
    ('Golem.de IT-News', 'https://rss.golem.de/rss.php?feed=RSS2.0', 'de', 'tech', TRUE),
    ('t3n Magazin', 'https://t3n.de/rss.xml', 'de', 'tech', TRUE),
    ('Handelsblatt Technik', 'https://www.handelsblatt.com/contentexport/feed/technik', 'de', 'tech', TRUE),
    -- 🇩🇪 German - Politics
    ('FAZ.NET Politik', 'https://www.faz.net/rss/aktuell/politik', 'de', 'politics', TRUE),
    ('ZEIT ONLINE Politik', 'https://newsfeed.zeit.de/politik', 'de', 'politics', TRUE),
    ('Deutscher Bundestag', 'https://www.bundestag.de/static/rss/presse.xml', 'de', 'politics', TRUE),
    -- 🇬🇧 English - General
    ('BBC News World', 'http://feeds.bbci.co.uk/news/world/rss.xml', 'en', 'general', TRUE),
    ('The Guardian World News', 'https://www.theguardian.com/world/rss', 'en', 'general', TRUE),
    ('The New York Times World', 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml', 'en', 'general', TRUE),
    -- 🇬🇧 English - Business
    ('Bloomberg Business', 'https://feeds.bloomberg.com/business/news.xml', 'en', 'business', TRUE),
    ('Wall Street Journal', 'https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml', 'en', 'business', TRUE),
    ('CNBC Top News', 'https://www.cnbc.com/id/100003114/device/rss/rss.html', 'en', 'business', TRUE),
    ('The Economist Business', 'https://www.economist.com/business/rss.xml', 'en', 'business', TRUE),
    -- 🇬🇧 English - Tech
    ('BBC News Technology', 'http://feeds.bbci.co.uk/news/technology/rss.xml', 'en', 'tech', TRUE),
    ('TechCrunch', 'https://techcrunch.com/feed/', 'en', 'tech', TRUE),
    ('The Verge', 'https://www.theverge.com/rss/index.xml', 'en', 'tech', TRUE),
    ('Wired', 'https://www.wired.com/feed/rss', 'en', 'tech', TRUE),
    ('Ars Technica', 'https://feeds.arstechnica.com/arstechnica/index', 'en', 'tech', TRUE),
    -- 🇬🇧 English - Science
    ('MIT Technology Review', 'https://www.technologyreview.com/feed/', 'en', 'science', TRUE),
    ('Nature News', 'http://www.nature.com/nature/current_issue/rss/', 'en', 'science', TRUE),
    ('Science Daily', 'https://www.sciencedaily.com/rss/top_news.xml', 'en', 'science', TRUE),
    ('New Scientist', 'https://www.newscientist.com/feed/home/', 'en', 'science', TRUE),
    -- 🇬🇧 English - Politics
    ('Politico', 'https://www.politico.com/rss/politics08.xml', 'en', 'politics', TRUE),
    ('Foreign Affairs', 'https://www.foreignaffairs.com/rss.xml', 'en', 'politics', TRUE)
ON CONFLICT (url) DO NOTHING;

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

-- Trigger to automatically update updated_at for articles
CREATE TRIGGER update_articles_updated_at BEFORE UPDATE ON articles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to automatically update updated_at for rss_sources
CREATE TRIGGER update_rss_sources_updated_at BEFORE UPDATE ON rss_sources
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

-- Table comments
COMMENT ON TABLE rss_sources IS 'Manages RSS/Atom feed sources for news aggregation';
COMMENT ON COLUMN rss_sources.url IS 'Unique RSS/Atom feed URL';
COMMENT ON COLUMN rss_sources.enabled IS 'TRUE if feed should be actively scraped';
COMMENT ON COLUMN rss_sources.article_count IS 'Total number of articles fetched from this source';

COMMENT ON TABLE articles IS 'Stores all fetched news articles with their summaries';
COMMENT ON COLUMN articles.url IS 'Unique URL of the article (used for deduplication)';
COMMENT ON COLUMN articles.processed IS 'TRUE if article has been summarized by AI';
COMMENT ON COLUMN articles.sent IS 'TRUE if article was included in an email digest';

-- Digest Recipients table: Manages email recipients for news digests
CREATE TABLE IF NOT EXISTS digest_recipients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(200),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for digest recipients
CREATE INDEX IF NOT EXISTS idx_digest_recipients_email ON digest_recipients(email);
CREATE INDEX IF NOT EXISTS idx_digest_recipients_enabled ON digest_recipients(enabled) WHERE enabled = TRUE;

-- Trigger to automatically update updated_at for digest_recipients
CREATE TRIGGER update_digest_recipients_updated_at BEFORE UPDATE ON digest_recipients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Table comments for digest_recipients
COMMENT ON TABLE digest_recipients IS 'Email recipients for news digest distribution';
COMMENT ON COLUMN digest_recipients.email IS 'Email address (can be individual or distribution list)';
COMMENT ON COLUMN digest_recipients.name IS 'Display name for the recipient';
COMMENT ON COLUMN digest_recipients.enabled IS 'TRUE if recipient should receive digests';
