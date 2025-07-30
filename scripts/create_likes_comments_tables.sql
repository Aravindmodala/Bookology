-- Create StoryLikes table
CREATE TABLE IF NOT EXISTS "StoryLikes" (
    "id" SERIAL PRIMARY KEY,
    "story_id" INTEGER NOT NULL REFERENCES "Stories"("id") ON DELETE CASCADE,
    "user_id" UUID NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE("story_id", "user_id")
);

-- Create StoryComments table
CREATE TABLE IF NOT EXISTS "StoryComments" (
    "id" SERIAL PRIMARY KEY,
    "story_id" INTEGER NOT NULL REFERENCES "Stories"("id") ON DELETE CASCADE,
    "user_id" UUID NOT NULL,
    "comment" TEXT NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS "idx_story_likes_story_id" ON "StoryLikes"("story_id");
CREATE INDEX IF NOT EXISTS "idx_story_likes_user_id" ON "StoryLikes"("user_id");
CREATE INDEX IF NOT EXISTS "idx_story_comments_story_id" ON "StoryComments"("story_id");
CREATE INDEX IF NOT EXISTS "idx_story_comments_user_id" ON "StoryComments"("user_id");
CREATE INDEX IF NOT EXISTS "idx_story_comments_created_at" ON "StoryComments"("created_at"); 