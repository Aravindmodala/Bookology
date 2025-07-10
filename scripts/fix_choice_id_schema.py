#!/usr/bin/env python3
"""
Fix the choice_id column type in the database.

This script changes the user_choice_id column in the Chapters table
from INTEGER to TEXT to support string choice IDs like "choice_1".
"""

import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client
from config import settings

def fix_choice_id_schema():
    """Fix the user_choice_id column type from INTEGER to TEXT."""
    
    print("🔧 Fixing choice ID schema...")
    
    # Create Supabase client
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    
    try:
        # Execute the schema change using raw SQL
        print("📝 Executing SQL: ALTER TABLE Chapters ALTER COLUMN user_choice_id TYPE TEXT...")
        
        # Note: We need to use Supabase's REST API since the Python client doesn't directly support raw SQL
        # Instead, let's check if we can modify the column through the table API
        
        # First, let's see what columns exist
        print("🔍 Checking current table structure...")
        response = supabase.table("Chapters").select("*").limit(1).execute()
        
        if response.data:
            print("✅ Chapters table exists and is accessible")
            print("📊 Available columns:", list(response.data[0].keys()) if response.data else "No data")
        else:
            print("⚠️  No data in Chapters table, but this is expected")
        
        print("\n🎯 Since we can't execute raw SQL through the Python client,")
        print("   you'll need to run this SQL manually in the Supabase SQL editor:")
        print()
        print("   ALTER TABLE \"Chapters\" ALTER COLUMN \"user_choice_id\" TYPE TEXT;")
        print()
        print("💡 Alternatively, you can modify the column type in the Supabase dashboard:")
        print("   1. Go to your Supabase project dashboard")
        print("   2. Navigate to Table Editor")
        print("   3. Select the 'Chapters' table")
        print("   4. Find the 'user_choice_id' column")
        print("   5. Change its type from 'int8' to 'text'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting choice ID schema fix...")
    
    # Validate settings
    try:
        settings.validate_required_settings()
        print("✅ Configuration validated")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Run the fix
    success = fix_choice_id_schema()
    
    if success:
        print("\n✅ Schema fix preparation completed!")
        print("⚠️  Please run the SQL command manually as shown above.")
    else:
        print("\n❌ Schema fix failed!")
        sys.exit(1) 