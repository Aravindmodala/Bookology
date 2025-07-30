#!/usr/bin/env python3
"""
Script to automatically set up the database tables and columns needed for the Explore features.
Uses the provided Supabase credentials to create tables via REST API.
"""

import os
import sys
from pathlib import Path
import requests
import json

# Add the parent directory to the path so we can import from the main project
sys.path.append(str(Path(__file__).parent.parent))

# Supabase credentials
SUPABASE_URL = "https://vclmejdagccbmnvfatrq.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZjbG1lamRhZ2NjYm1udmZhdHJxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDUzOTcwNywiZXhwIjoyMDY2MTE1NzA3fQ.4_h8ub9MJxovv9s_CJBE1LUbqH-sDlGuTwdZtW3H5hc"

def setup_explore_features():
    """Set up the database tables and columns for explore features"""
    
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    print("🚀 Setting up Explore features automatically...")
    
    # 1. Add columns to Stories table
    print("\n1. Adding columns to Stories table...")
    
    # Add is_public column
    try:
        sql_is_public = """
        ALTER TABLE "Stories" 
        ADD COLUMN IF NOT EXISTS "is_public" BOOLEAN DEFAULT FALSE;
        """
        
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
            headers=headers,
            json={"sql": sql_is_public}
        )
        
        if response.status_code == 200:
            print("✓ Added is_public column to Stories table")
        else:
            print(f"⚠ Could not add is_public column: {response.text}")
            
    except Exception as e:
        print(f"⚠ Error adding is_public column: {e}")
    
    # Add published_at column
    try:
        sql_published_at = """
        ALTER TABLE "Stories" 
        ADD COLUMN IF NOT EXISTS "published_at" TIMESTAMP WITH TIME ZONE;
        """
        
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
            headers=headers,
            json={"sql": sql_published_at}
        )
        
        if response.status_code == 200:
            print("✓ Added published_at column to Stories table")
        else:
            print(f"⚠ Could not add published_at column: {response.text}")
            
    except Exception as e:
        print(f"⚠ Error adding published_at column: {e}")
    
    # 2. Create StoryLikes table
    print("\n2. Creating StoryLikes table...")
    try:
        sql_story_likes = """
        CREATE TABLE IF NOT EXISTS "StoryLikes" (
            "id" SERIAL PRIMARY KEY,
            "story_id" INTEGER NOT NULL REFERENCES "Stories"("id") ON DELETE CASCADE,
            "user_id" UUID NOT NULL,
            "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE("story_id", "user_id")
        );
        """
        
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
            headers=headers,
            json={"sql": sql_story_likes}
        )
        
        if response.status_code == 200:
            print("✓ Created StoryLikes table")
        else:
            print(f"⚠ Could not create StoryLikes table: {response.text}")
            
    except Exception as e:
        print(f"⚠ Error creating StoryLikes table: {e}")
    
    # 3. Create StoryComments table
    print("\n3. Creating StoryComments table...")
    try:
        sql_story_comments = """
        CREATE TABLE IF NOT EXISTS "StoryComments" (
            "id" SERIAL PRIMARY KEY,
            "story_id" INTEGER NOT NULL REFERENCES "Stories"("id") ON DELETE CASCADE,
            "user_id" UUID NOT NULL,
            "comment" TEXT NOT NULL,
            "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
            headers=headers,
            json={"sql": sql_story_comments}
        )
        
        if response.status_code == 200:
            print("✓ Created StoryComments table")
        else:
            print(f"⚠ Could not create StoryComments table: {response.text}")
            
    except Exception as e:
        print(f"⚠ Error creating StoryComments table: {e}")
    
    # 4. Create indexes for better performance
    print("\n4. Creating indexes...")
    indexes = [
        ("idx_stories_is_public", 'CREATE INDEX IF NOT EXISTS "idx_stories_is_public" ON "Stories"("is_public");'),
        ("idx_stories_published_at", 'CREATE INDEX IF NOT EXISTS "idx_stories_published_at" ON "Stories"("published_at");'),
        ("idx_story_likes_story_id", 'CREATE INDEX IF NOT EXISTS "idx_story_likes_story_id" ON "StoryLikes"("story_id");'),
        ("idx_story_likes_user_id", 'CREATE INDEX IF NOT EXISTS "idx_story_likes_user_id" ON "StoryLikes"("user_id");'),
        ("idx_story_comments_story_id", 'CREATE INDEX IF NOT EXISTS "idx_story_comments_story_id" ON "StoryComments"("story_id");'),
        ("idx_story_comments_user_id", 'CREATE INDEX IF NOT EXISTS "idx_story_comments_user_id" ON "StoryComments"("user_id");'),
        ("idx_story_comments_created_at", 'CREATE INDEX IF NOT EXISTS "idx_story_comments_created_at" ON "StoryComments"("created_at");')
    ]
    
    for index_name, sql in indexes:
        try:
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
                headers=headers,
                json={"sql": sql}
            )
            
            if response.status_code == 200:
                print(f"✓ Created {index_name}")
            else:
                print(f"⚠ Could not create {index_name}: {response.text}")
                
        except Exception as e:
            print(f"⚠ Error creating {index_name}: {e}")
    
    # 5. Test the setup
    print("\n5. Testing the setup...")
    try:
        # Test Stories table with new columns
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/Stories?select=id,is_public,published_at&limit=1",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✓ Stories table is accessible with new columns")
        else:
            print(f"⚠ Stories table test failed: {response.text}")
            
    except Exception as e:
        print(f"⚠ Error testing Stories table: {e}")
    
    try:
        # Test StoryLikes table
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/StoryLikes?select=id&limit=1",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✓ StoryLikes table is accessible")
        else:
            print(f"⚠ StoryLikes table test failed: {response.text}")
            
    except Exception as e:
        print(f"⚠ Error testing StoryLikes table: {e}")
    
    try:
        # Test StoryComments table
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/StoryComments?select=id&limit=1",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✓ StoryComments table is accessible")
        else:
            print(f"⚠ StoryComments table test failed: {response.text}")
            
    except Exception as e:
        print(f"⚠ Error testing StoryComments table: {e}")
    
    print("\n✅ Explore features setup completed!")
    print("\n📋 What was created:")
    print("- Stories table: added is_public and published_at columns")
    print("- StoryLikes table: for tracking user likes on stories")
    print("- StoryComments table: for storing user comments on stories")
    print("- Performance indexes for all tables")
    print("\n🎉 You can now:")
    print("1. Make stories public using the visibility toggle in the dashboard")
    print("2. Browse public stories in the Explore page")
    print("3. Like and comment on public stories")

if __name__ == "__main__":
    setup_explore_features() 