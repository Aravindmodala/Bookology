#!/usr/bin/env python3
"""
Script to check if story_choices table exists and create it if needed.
"""

import psycopg
from app.core.config import settings

def check_and_create_story_choices_table():
    """Check if story_choices table exists and create it if needed."""
    connection_string = settings.get_postgres_connection_string()
    
    # Convert psycopg format back to standard format for psycopg connection
    if "postgresql+psycopg://" in connection_string:
        connection_string = connection_string.replace("postgresql+psycopg://", "postgresql://")
    
    try:
        print("Connecting to database...")
        with psycopg.connect(connection_string) as conn:
            with conn.cursor() as cur:
                # Check if story_choices table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'story_choices'
                    );
                """)
                
                table_exists = cur.fetchone()[0]
                
                if table_exists:
                    print("✅ story_choices table already exists!")
                    return True
                else:
                    print("❌ story_choices table does not exist. Creating it...")
                    
                    # Create story_choices table
                    cur.execute("""
                        CREATE TABLE story_choices (
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
                    """)
                    
                    # Create indexes
                    print("Creating indexes...")
                    cur.execute("CREATE INDEX idx_story_choices_story_id ON story_choices(story_id);")
                    cur.execute("CREATE INDEX idx_story_choices_chapter_id ON story_choices(chapter_id);")
                    cur.execute("CREATE INDEX idx_story_choices_chapter_number ON story_choices(chapter_number);")
                    cur.execute("CREATE INDEX idx_story_choices_user_id ON story_choices(user_id);")
                    cur.execute("CREATE INDEX idx_story_choices_branch_id ON story_choices(branch_id);")
                    cur.execute("CREATE INDEX idx_story_choices_is_selected ON story_choices(is_selected) WHERE is_selected = true;")
                    
                    conn.commit()
                    print("✅ story_choices table created successfully!")
                    return True
                    
    except Exception as e:
        print(f"❌ Error checking/creating story_choices table: {e}")
        return False

if __name__ == "__main__":
    check_and_create_story_choices_table() 