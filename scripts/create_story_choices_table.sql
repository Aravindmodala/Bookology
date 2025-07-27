-- Create story_choices table for storing story choices
CREATE TABLE IF NOT EXISTS story_choices (
    id SERIAL PRIMARY KEY,
    story_id INTEGER REFERENCES Stories(id) ON DELETE CASCADE,
    chapter_id INTEGER REFERENCES Chapters(id) ON DELETE CASCADE,
    chapter_number INTEGER NOT NULL,
    choice_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    story_impact TEXT,
    choice_type TEXT DEFAULT 'story_choice',
    is_selected BOOLEAN DEFAULT FALSE,
    selected_at TIMESTAMP WITH TIME ZONE,
    user_id UUID,
    branch_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(story_id, chapter_number, choice_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_story_choices_story_id ON story_choices(story_id);
CREATE INDEX IF NOT EXISTS idx_story_choices_chapter_id ON story_choices(chapter_id);
CREATE INDEX IF NOT EXISTS idx_story_choices_chapter_number ON story_choices(chapter_number);
CREATE INDEX IF NOT EXISTS idx_story_choices_user_id ON story_choices(user_id);
CREATE INDEX IF NOT EXISTS idx_story_choices_branch_id ON story_choices(branch_id);
CREATE INDEX IF NOT EXISTS idx_story_choices_is_selected ON story_choices(is_selected) WHERE is_selected = true; 