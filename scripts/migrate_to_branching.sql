-- Migration script to add branching support to existing data
-- This script:
-- 1. Creates a main branch for each existing story
-- 2. Sets all existing chapters and choices to belong to the main branch

-- Step 1: Create a main branch for each existing story
INSERT INTO branches (id, story_id, parent_branch_id, branched_from_chapter, branch_name, created_at)
SELECT 
    gen_random_uuid() as id,
    id as story_id,
    NULL as parent_branch_id,  -- Main branch has no parent
    NULL as branched_from_chapter,  -- Main branch doesn't branch from anywhere
    'main' as branch_name,
    created_at
FROM "Stories"
WHERE id NOT IN (SELECT DISTINCT story_id FROM branches WHERE branch_name = 'main');

-- Step 2: Update all existing chapters to belong to the main branch of their story
UPDATE "Chapters" 
SET branch_id = (
    SELECT b.id 
    FROM branches b 
    WHERE b.story_id = "Chapters".story_id 
    AND b.branch_name = 'main'
)
WHERE branch_id IS NULL;

-- Step 3: Update all existing choices to belong to the main branch of their story
UPDATE story_choices 
SET branch_id = (
    SELECT b.id 
    FROM branches b 
    WHERE b.story_id = story_choices.story_id 
    AND b.branch_name = 'main'
)
WHERE branch_id IS NULL;

-- Step 4: Verify the migration
SELECT 
    s.id as story_id,
    s.story_title,
    b.id as branch_id,
    b.branch_name,
    COUNT(c.id) as chapter_count,
    COUNT(sc.id) as choice_count
FROM "Stories" s
LEFT JOIN branches b ON s.id = b.story_id AND b.branch_name = 'main'
LEFT JOIN "Chapters" c ON s.id = c.story_id AND c.branch_id = b.id
LEFT JOIN story_choices sc ON s.id = sc.story_id AND sc.branch_id = b.id
GROUP BY s.id, s.story_title, b.id, b.branch_name
ORDER BY s.id;

-- Step 5: Add constraints to ensure data integrity
ALTER TABLE "Chapters" ADD CONSTRAINT fk_chapters_branch 
    FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE CASCADE;

ALTER TABLE story_choices ADD CONSTRAINT fk_choices_branch 
    FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE CASCADE; 