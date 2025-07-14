-- Fix foreign key constraint to allow cascading deletes
-- This allows stories to be deleted even if they have branches

-- First, drop the existing constraint
ALTER TABLE branches DROP CONSTRAINT IF EXISTS branches_story_id_fkey;

-- Recreate the constraint with CASCADE DELETE
ALTER TABLE branches 
ADD CONSTRAINT branches_story_id_fkey 
FOREIGN KEY (story_id) 
REFERENCES "Stories"(id) 
ON DELETE CASCADE;

-- Also fix the chapters constraint if it exists
ALTER TABLE "Chapters" DROP CONSTRAINT IF EXISTS fk_chapters_branch;
ALTER TABLE "Chapters" 
ADD CONSTRAINT fk_chapters_branch 
FOREIGN KEY (branch_id) 
REFERENCES branches(id) 
ON DELETE CASCADE;

-- Fix story_choices constraint
ALTER TABLE story_choices DROP CONSTRAINT IF EXISTS story_choices_story_id_fkey;
ALTER TABLE story_choices 
ADD CONSTRAINT story_choices_story_id_fkey 
FOREIGN KEY (story_id) 
REFERENCES "Stories"(id) 
ON DELETE CASCADE;

-- Fix story_choices branch constraint
ALTER TABLE story_choices DROP CONSTRAINT IF EXISTS story_choices_branch_id_fkey;
ALTER TABLE story_choices 
ADD CONSTRAINT story_choices_branch_id_fkey 
FOREIGN KEY (branch_id) 
REFERENCES branches(id) 
ON DELETE CASCADE;

-- Verify the constraints
SELECT 
    tc.table_name, 
    tc.constraint_name, 
    tc.constraint_type,
    rc.delete_rule
FROM information_schema.table_constraints tc
LEFT JOIN information_schema.referential_constraints rc 
    ON tc.constraint_name = rc.constraint_name
WHERE tc.table_name IN ('branches', 'Chapters', 'story_choices')
    AND tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name, tc.constraint_name; 