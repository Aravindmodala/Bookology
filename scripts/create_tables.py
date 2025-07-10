#!/usr/bin/env python3
"""
Script to create the necessary database tables for Bookology.
"""

import psycopg
from config import settings

def create_tables():
    """Create the necessary database tables."""
    connection_string = settings.get_postgres_connection_string()
    
    # Convert psycopg format back to standard format for psycopg connection
    if "postgresql+psycopg://" in connection_string:
        connection_string = connection_string.replace("postgresql+psycopg://", "postgresql://")
    
    try:
        print("Connecting to database...")
        with psycopg.connect(connection_string) as conn:
            with conn.cursor() as cur:
                print("Creating Stories table...")
                
                # Create Stories table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS Stories (
                        id SERIAL PRIMARY KEY,
                        user_id UUID NOT NULL,
                        title TEXT NOT NULL,
                        outline TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)
                
                print("Creating Chapters table...")
                
                # Create Chapters table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS Chapters (
                        id SERIAL PRIMARY KEY,
                        story_id INTEGER REFERENCES Stories(id) ON DELETE CASCADE,
                        chapter_number INTEGER NOT NULL,
                        title TEXT,
                        content TEXT NOT NULL,
                        summary TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        UNIQUE(story_id, chapter_number)
                    );
                """)
                
                print("Creating indexes...")
                
                # Create indexes for better performance
                cur.execute("CREATE INDEX IF NOT EXISTS idx_Stories_user_id ON Stories(user_id);")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_Chapters_story_id ON Chapters(story_id);")
                
                conn.commit()
                
        print("✅ Database tables created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    create_tables()