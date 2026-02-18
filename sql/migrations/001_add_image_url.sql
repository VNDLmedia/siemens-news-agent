-- Migration 001: Add image_url column to articles table
-- Run this against an existing database that was created before image support.
-- init.sql already includes this column for fresh installs.

ALTER TABLE articles ADD COLUMN IF NOT EXISTS image_url TEXT;

COMMENT ON COLUMN articles.image_url IS 'URL of the best representative image found in the RSS feed item (enclosure, media:thumbnail, or first img in description)';
