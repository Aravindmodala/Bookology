-- Add public visibility columns to Stories table
ALTER TABLE "Stories" 
ADD COLUMN IF NOT EXISTS "is_public" BOOLEAN DEFAULT FALSE;

ALTER TABLE "Stories" 
ADD COLUMN IF NOT EXISTS "published_at" TIMESTAMP WITH TIME ZONE;

-- Create index for better performance on public stories queries
CREATE INDEX IF NOT EXISTS "idx_stories_is_public" ON "Stories"("is_public");
CREATE INDEX IF NOT EXISTS "idx_stories_published_at" ON "Stories"("published_at"); 