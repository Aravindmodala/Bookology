#!/usr/bin/env python3
"""
Simple script to check if story_choices table exists.
"""

import os
import psycopg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_story_choices_table():
    """Check if story_choices table exists."""
    # Get database connection from environment variables
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL environment variable not found")
        return False
    
    try:
        print("Connecting to database...")
        with psycopg.connect(db_url) as conn:
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
                    print("✅ story_choices table exists!")
                    
                    # Check table structure
                    cur.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'story_choices' 
                        ORDER BY ordinal_position;
                    """)
                    
                    columns = cur.fetchall()
                    print("📋 Table structure:")
                    for column in columns:
                        print(f"   - {column[0]}: {column[1]}")
                    
                    return True
                else:
                    print("❌ story_choices table does not exist!")
                    print("💡 You need to create the story_choices table.")
                    return False
                    
    except Exception as e:
        print(f"❌ Error checking story_choices table: {e}")
        return False

if __name__ == "__main__":
    check_story_choices_table() 