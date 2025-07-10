-- Fix choice ID column type to support string choice IDs like "choice_1", "choice_2", etc.
-- The LLM generates choices with string IDs, not integer IDs

-- Change the column type from INTEGER to TEXT
ALTER TABLE "Chapters" ALTER COLUMN "user_choice_id" TYPE TEXT;

-- Update the comment
COMMENT ON COLUMN "Chapters"."user_choice_id" IS 'The string ID of the choice the user selected that led to this chapter (e.g., "choice_1", "choice_2")';

-- Recreate the index (dropping old one first)
DROP INDEX IF EXISTS "idx_Chapters_user_choice";
CREATE INDEX IF NOT EXISTS "idx_Chapters_user_choice" ON "Chapters" ("user_choice_id");

-- Show the updated table structure
\d "Chapters"; 