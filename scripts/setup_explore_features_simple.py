#!/usr/bin/env python3
"""
Script to set up the database tables and columns needed for the Explore features.
Uses standard Supabase operations instead of exec_sql.
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
    
    # 1. Check if is_public column exists in Stories table
    print("1. Checking Stories table structure...")
    try:
        # Try to query the Stories table to see if is_public column exists
        result = supabase.table("Stories").select("id, is_public").limit(1).execute()
        print("✓ Stories table is accessible")
        
        # Check if is_public column exists by looking at the first result
        if result.data and "is_public" in result.data[0]:
            print("✓ is_public column already exists")
        else:
            print("⚠ is_public column may not exist - you may need to add it manually")
            
    except Exception as e:
        print(f"✗ Error checking Stories table: {e}")
    
    # 2. Check if StoryLikes table exists
    print("\n2. Checking StoryLikes table...")
    try:
        result = supabase.table("StoryLikes").select("id").limit(1).execute()
        print("✓ StoryLikes table exists")
    except Exception as e:
        print(f"✗ StoryLikes table does not exist: {e}")
        print("You need to create this table manually in your Supabase dashboard")
    
    # 3. Check if StoryComments table exists
    print("\n3. Checking StoryComments table...")
    try:
        result = supabase.table("StoryComments").select("id").limit(1).execute()
        print("✓ StoryComments table exists")
    except Exception as e:
        print(f"✗ StoryComments table does not exist: {e}")
        print("You need to create this table manually in your Supabase dashboard")
    
    print("\n📋 Manual Setup Required:")
    print("Since the exec_sql function is not available, you need to manually create the missing tables/columns:")
    print("\n1. In your Supabase dashboard, go to the Table Editor")
    print("2. Add these columns to the Stories table:")
    print("   - is_public (boolean, default: false)")
    print("   - published_at (timestamp with time zone)")
    print("\n3. Create these new tables:")
    print("   - StoryLikes (id, story_id, user_id, created_at)")
    print("   - StoryComments (id, story_id, user_id, comment, created_at)")
    print("\n4. Add appropriate foreign key constraints and indexes")
    
    print("\n✅ Setup check completed!")

if __name__ == "__main__":
    setup_explore_features() 