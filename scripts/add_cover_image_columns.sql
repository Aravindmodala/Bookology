-- Add cover image related columns to Stories table
-- This script adds support for AI-generated book covers

-- Add cover_image_url column to store the generated image URL
ALTER TABLE "Stories" 
ADD COLUMN IF NOT EXISTS "cover_image_url" TEXT;

-- Add cover_generation_status column to track generation state
ALTER TABLE "Stories" 
ADD COLUMN IF NOT EXISTS "cover_generation_status" TEXT DEFAULT 'none';

-- Add cover_generated_at timestamp for tracking when cover was created
ALTER TABLE "Stories" 
ADD COLUMN IF NOT EXISTS "cover_generated_at" TIMESTAMP WITH TIME ZONE;

-- Add cover_prompt column to store the prompt used for generation (for debugging/regeneration)
ALTER TABLE "Stories" 
ADD COLUMN IF NOT EXISTS "cover_prompt" TEXT;

-- Create index on cover_generation_status for efficient queries
CREATE INDEX IF NOT EXISTS "idx_stories_cover_status" ON "Stories" ("cover_generation_status");

-- Add comments for documentation
COMMENT ON COLUMN "Stories"."cover_image_url" IS 'URL of the AI-generated book cover image';
COMMENT ON COLUMN "Stories"."cover_generation_status" IS 'Status of cover generation: none, generating, completed, failed';
COMMENT ON COLUMN "Stories"."cover_generated_at" IS 'Timestamp when the cover was successfully generated';
COMMENT ON COLUMN "Stories"."cover_prompt" IS 'The prompt used to generate the cover image';

-- Display success message
DO $$
BEGIN
    RAISE NOTICE 'Cover image columns added successfully to Stories table';
END $$; 