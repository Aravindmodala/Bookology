-- Add choice tracking columns to Chapters table for branching Stories
-- This allows us to track which user choice led to each chapter generation

-- Add columns to track user choices
ALTER TABLE "Chapters" ADD COLUMN IF NOT EXISTS "user_choice_id" INTEGER;
ALTER TABLE "Chapters" ADD COLUMN IF NOT EXISTS "user_choice_title" TEXT;
ALTER TABLE "Chapters" ADD COLUMN IF NOT EXISTS "user_choice_type" TEXT;

-- Add comments to document the new columns
COMMENT ON COLUMN "Chapters"."user_choice_id" IS 'The ID of the choice the user selected that led to this chapter';
COMMENT ON COLUMN "Chapters"."user_choice_title" IS 'The title of the choice that led to this chapter';
COMMENT ON COLUMN "Chapters"."user_choice_type" IS 'The type of choice (action, character, mystery, etc.)';

-- Create an index for faster queries on choice data
CREATE INDEX IF NOT EXISTS "idx_Chapters_user_choice" ON "Chapters" ("user_choice_id");

-- Show the updated table structure
\d "Chapters"; 