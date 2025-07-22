-- Add DNA and Vector Support to Bookology Database
-- Run this script to ensure proper storage of DNA and vector embeddings

-- 1. Add DNA column to Chapters table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'chapters' AND column_name = 'dna'
    ) THEN
        ALTER TABLE chapters ADD COLUMN dna JSONB;
        COMMENT ON COLUMN chapters.dna IS 'Story DNA for plot continuity tracking';
    END IF;
END $$;

-- 2. Enable pgvector extension for vector storage
CREATE EXTENSION IF NOT EXISTS vector;

-- 3. Create chapter_vectors table for vector embeddings
CREATE TABLE IF NOT EXISTS chapter_vectors (
    id SERIAL PRIMARY KEY,
    chapter_id INTEGER REFERENCES chapters(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(768) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chapter_id, chunk_index)
);

-- 4. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_chapter_vectors_chapter_id ON chapter_vectors(chapter_id);
CREATE INDEX IF NOT EXISTS idx_chapter_vectors_embedding ON chapter_vectors USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_chapters_dna ON chapters USING gin(dna);

-- 5. Add indexes for story choices if not exist
CREATE INDEX IF NOT EXISTS idx_story_choices_chapter_id ON story_choices(chapter_id);
CREATE INDEX IF NOT EXISTS idx_story_choices_is_selected ON story_choices(is_selected) WHERE is_selected = true;

-- 6. Add performance indexes for chapters
CREATE INDEX IF NOT EXISTS idx_chapters_story_id_active ON chapters(story_id, is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_chapters_story_chapter_active ON chapters(story_id, chapter_number, is_active) WHERE is_active = true;

-- 7. Create view for enhanced chapter context
CREATE OR REPLACE VIEW enhanced_chapter_context AS
SELECT 
    c.id,
    c.story_id,
    c.chapter_number,
    c.title,
    c.content,
    c.summary,
    c.dna,
    c.word_count,
    c.created_at,
    COUNT(cv.id) as vector_chunk_count,
    COUNT(sc.id) as choice_count
FROM chapters c
LEFT JOIN chapter_vectors cv ON c.id = cv.chapter_id
LEFT JOIN story_choices sc ON c.id = sc.chapter_id
WHERE c.is_active = true
GROUP BY c.id, c.story_id, c.chapter_number, c.title, c.content, c.summary, c.dna, c.word_count, c.created_at;

-- 8. Add helpful comments
COMMENT ON TABLE chapter_vectors IS 'Vector embeddings for semantic search of chapter content';
COMMENT ON COLUMN chapter_vectors.embedding IS 'MPNet-base-v2 768-dimensional embedding vector';
COMMENT ON COLUMN chapter_vectors.chunk_text IS 'Text chunk that was embedded (max 2000 chars)';
COMMENT ON COLUMN chapter_vectors.metadata IS 'Additional metadata like chunk_length, position, etc.';

-- 9. Grant necessary permissions (adjust user as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON chapter_vectors TO your_app_user;
-- GRANT USAGE ON SEQUENCE chapter_vectors_id_seq TO your_app_user;

-- 10. Verify setup
SELECT 
    'DNA column exists' as feature,
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'chapters' AND column_name = 'dna'
    ) THEN '✅ YES' ELSE '❌ NO' END as status
UNION ALL
SELECT 
    'Vector extension enabled' as feature,
    CASE WHEN EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'vector'
    ) THEN '✅ YES' ELSE '❌ NO' END as status
UNION ALL
SELECT 
    'Chapter vectors table exists' as feature,
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'chapter_vectors'
    ) THEN '✅ YES' ELSE '❌ NO' END as status;

-- Success message
SELECT 'Database schema updated successfully for DNA and vector support!' as message; 