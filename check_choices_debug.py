#!/usr/bin/env python3
"""Debug script to check if choices are being saved to the database"""

import os
import sys
sys.path.append('.')

from supabase import create_client, Client
from config import get_settings

# Get settings
settings = get_settings()

# Database connection with service key
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

def main():
    print("🔍 Debugging Choice Storage Issue...")
    print("=" * 50)
    
    # Check choices for chapter 342 (from the logs)
    print('🔍 Checking choices for chapter 342...')
    choices_response = supabase.table('story_choices').select('*').eq('chapter_id', 342).execute()
    print(f'📊 Found {len(choices_response.data)} choices in story_choices table for chapter 342:')
    for choice in choices_response.data:
        print(f'  - Choice ID: {choice.get("choice_id", "N/A")}, Title: {choice.get("title", "N/A")}')
        print(f'    Description: {choice.get("description", "N/A")[:100]}...')
    
    print("\n" + "=" * 50)
    
    # Also check for story_id 180
    print('🔍 Checking all choices for story 180...')
    story_choices_response = supabase.table('story_choices').select('*').eq('story_id', 180).execute()
    print(f'📊 Found {len(story_choices_response.data)} total choices for story 180:')
    for choice in story_choices_response.data:
        print(f'  - Chapter {choice.get("chapter_number", "N/A")}, Choice: {choice.get("title", "N/A")}')
        print(f'    Chapter ID: {choice.get("chapter_id", "N/A")}, Choice ID: {choice.get("choice_id", "N/A")}')
    
    print("\n" + "=" * 50)
    
    # Check chapters for story 180
    print('🔍 Checking chapters for story 180...')
    chapters_response = supabase.table('Chapters').select('id, chapter_number, title').eq('story_id', 180).eq('is_active', True).execute()
    print(f'📊 Found {len(chapters_response.data)} chapters for story 180:')
    for chapter in chapters_response.data:
        print(f'  - Chapter {chapter.get("chapter_number", "N/A")}: {chapter.get("title", "N/A")} (ID: {chapter.get("id", "N/A")})')
        
        # Check choices for each chapter
        chapter_choices = supabase.table('story_choices').select('*').eq('chapter_id', chapter.get("id")).execute()
        print(f'    → {len(chapter_choices.data)} choices found')
        for choice in chapter_choices.data:
            print(f'      * {choice.get("title", "N/A")}')

if __name__ == "__main__":
    main()
