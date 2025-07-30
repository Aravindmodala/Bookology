-- =====================================================
-- Explore Features Database Setup
-- Run this script in your Supabase SQL Editor
-- =====================================================

-- 1. Add columns to Stories table
ALTER TABLE "Stories" 
ADD COLUMN IF NOT EXISTS "is_public" BOOLEAN DEFAULT FALSE;

ALTER TABLE "Stories" 
ADD COLUMN IF NOT EXISTS "published_at" TIMESTAMP WITH TIME ZONE;

-- 2. Create StoryLikes table
CREATE TABLE IF NOT EXISTS "StoryLikes" (
    "id" SERIAL PRIMARY KEY,
    "story_id" INTEGER NOT NULL REFERENCES "Stories"("id") ON DELETE CASCADE,
    "user_id" UUID NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE("story_id", "user_id")
);

-- 3. Create StoryComments table
CREATE TABLE IF NOT EXISTS "StoryComments" (
    "id" SERIAL PRIMARY KEY,
    "story_id" INTEGER NOT NULL REFERENCES "Stories"("id") ON DELETE CASCADE,
    "user_id" UUID NOT NULL,
    "comment" TEXT NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Create indexes for better performance
CREATE INDEX IF NOT EXISTS "idx_stories_is_public" ON "Stories"("is_public");
CREATE INDEX IF NOT EXISTS "idx_stories_published_at" ON "Stories"("published_at");
CREATE INDEX IF NOT EXISTS "idx_story_likes_story_id" ON "StoryLikes"("story_id");
CREATE INDEX IF NOT EXISTS "idx_story_likes_user_id" ON "StoryLikes"("user_id");
CREATE INDEX IF NOT EXISTS "idx_story_comments_story_id" ON "StoryComments"("story_id");
CREATE INDEX IF NOT EXISTS "idx_story_comments_user_id" ON "StoryComments"("user_id");
CREATE INDEX IF NOT EXISTS "idx_story_comments_created_at" ON "StoryComments"("created_at");

-- 5. Enable Row Level Security (RLS) for new tables
ALTER TABLE "StoryLikes" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "StoryComments" ENABLE ROW LEVEL SECURITY;

-- 6. Create RLS policies for StoryLikes
CREATE POLICY "Users can view all story likes" ON "StoryLikes"
    FOR SELECT USING (true);

CREATE POLICY "Users can insert their own likes" ON "StoryLikes"
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own likes" ON "StoryLikes"
    FOR DELETE USING (auth.uid() = user_id);

-- 7. Create RLS policies for StoryComments
CREATE POLICY "Users can view all story comments" ON "StoryComments"
    FOR SELECT USING (true);

CREATE POLICY "Users can insert their own comments" ON "StoryComments"
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own comments" ON "StoryComments"
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own comments" ON "StoryComments"
    FOR DELETE USING (auth.uid() = user_id);

-- 8. Verify the setup
SELECT 'Stories table columns:' as info;
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'Stories' 
AND column_name IN ('is_public', 'published_at');

SELECT 'StoryLikes table created:' as info;
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'StoryLikes'
) as story_likes_exists;

SELECT 'StoryComments table created:' as info;
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'StoryComments'
) as story_comments_exists;

-- =====================================================
-- Setup Complete! 
-- You can now use the Explore features in your app.
-- ===================================================== 