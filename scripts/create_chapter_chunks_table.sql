-- Create chapter_chunks table for vector storage in Supabase
-- Run this in your Supabase SQL editor

-- Enable vector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create chapter_chunks table
CREATE TABLE IF NOT EXISTS chapter_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chapter_id INTEGER REFERENCES chapters(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content_chunk TEXT NOT NULL,
    embedding VECTOR(768),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chapter_id, chunk_index)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_chapter_chunks_chapter_id ON chapter_chunks(chapter_id);
CREATE INDEX IF NOT EXISTS idx_chapter_chunks_embedding ON chapter_chunks USING ivfflat (embedding vector_cosine_ops);

-- Enable Row Level Security
ALTER TABLE chapter_chunks ENABLE ROW LEVEL SECURITY;

-- Verify the table was created
SELECT 'chapter_chunks table created successfully!' as message;
