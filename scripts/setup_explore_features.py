#!/usr/bin/env python3
"""
Script to set up the database tables and columns needed for the Explore features.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import from the main project
sys.path.append(str(Path(__file__).parent.parent))

from supabase import create_client, Client
from config import get_settings

def setup_explore_features():
    """Set up the database tables and columns for explore features"""
    
    # Get settings
    settings = get_settings()
    
    # Initialize Supabase client
    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    
    print("Setting up Explore features...")
    
    # 1. Add public visibility columns to Stories table
    print("1. Adding public visibility columns to Stories table...")
    try:
        # Add is_public column
        supabase.rpc('exec_sql', {
            'sql': 'ALTER TABLE "Stories" ADD COLUMN IF NOT EXISTS "is_public" BOOLEAN DEFAULT FALSE;'
        }).execute()
        print("✓ Added is_public column")
        
        # Add published_at column
        supabase.rpc('exec_sql', {
            'sql': 'ALTER TABLE "Stories" ADD COLUMN IF NOT EXISTS "published_at" TIMESTAMP WITH TIME ZONE;'
        }).execute()
        print("✓ Added published_at column")
        
        # Create indexes
        supabase.rpc('exec_sql', {
            'sql': 'CREATE INDEX IF NOT EXISTS "idx_stories_is_public" ON "Stories"("is_public");'
        }).execute()
        supabase.rpc('exec_sql', {
            'sql': 'CREATE INDEX IF NOT EXISTS "idx_stories_published_at" ON "Stories"("published_at");'
        }).execute()
        print("✓ Created indexes for Stories table")
        
    except Exception as e:
        print(f"✗ Error adding visibility columns: {e}")
    
    # 2. Create StoryLikes table
    print("\n2. Creating StoryLikes table...")
    try:
        supabase.rpc('exec_sql', {
            'sql': '''
            CREATE TABLE IF NOT EXISTS "StoryLikes" (
                "id" SERIAL PRIMARY KEY,
                "story_id" INTEGER NOT NULL REFERENCES "Stories"("id") ON DELETE CASCADE,
                "user_id" UUID NOT NULL,
                "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                UNIQUE("story_id", "user_id")
            );
            '''
        }).execute()
        print("✓ Created StoryLikes table")
        
        # Create indexes
        supabase.rpc('exec_sql', {
            'sql': 'CREATE INDEX IF NOT EXISTS "idx_story_likes_story_id" ON "StoryLikes"("story_id");'
        }).execute()
        supabase.rpc('exec_sql', {
            'sql': 'CREATE INDEX IF NOT EXISTS "idx_story_likes_user_id" ON "StoryLikes"("user_id");'
        }).execute()
        print("✓ Created indexes for StoryLikes table")
        
    except Exception as e:
        print(f"✗ Error creating StoryLikes table: {e}")
    
    # 3. Create StoryComments table
    print("\n3. Creating StoryComments table...")
    try:
        supabase.rpc('exec_sql', {
            'sql': '''
            CREATE TABLE IF NOT EXISTS "StoryComments" (
                "id" SERIAL PRIMARY KEY,
                "story_id" INTEGER NOT NULL REFERENCES "Stories"("id") ON DELETE CASCADE,
                "user_id" UUID NOT NULL,
                "comment" TEXT NOT NULL,
                "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            '''
        }).execute()
        print("✓ Created StoryComments table")
        
        # Create indexes
        supabase.rpc('exec_sql', {
            'sql': 'CREATE INDEX IF NOT EXISTS "idx_story_comments_story_id" ON "StoryComments"("story_id");'
        }).execute()
        supabase.rpc('exec_sql', {
            'sql': 'CREATE INDEX IF NOT EXISTS "idx_story_comments_user_id" ON "StoryComments"("user_id");'
        }).execute()
        supabase.rpc('exec_sql', {
            'sql': 'CREATE INDEX IF NOT EXISTS "idx_story_comments_created_at" ON "StoryComments"("created_at");'
        }).execute()
        print("✓ Created indexes for StoryComments table")
        
    except Exception as e:
        print(f"✗ Error creating StoryComments table: {e}")
    
    print("\n✅ Explore features setup completed!")
    print("\nTables and columns created:")
    print("- Stories table: added is_public and published_at columns")
    print("- StoryLikes table: for tracking user likes on stories")
    print("- StoryComments table: for storing user comments on stories")
    print("\nYou can now:")
    print("1. Make stories public using the visibility toggle in the dashboard")
    print("2. Browse public stories in the Explore page")
    print("3. Like and comment on public stories")

if __name__ == "__main__":
    setup_explore_features() 