#!/usr/bin/env python3
"""
Fix foreign key constraints to allow cascading deletes.
This allows stories to be deleted even if they have branches.
"""

import psycopg
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def fix_foreign_key_constraints():
    """Fix foreign key constraints to use CASCADE deletion."""
    try:
        connection_string = settings.get_postgres_connection_string()
        if 'postgresql+psycopg://' in connection_string:
            connection_string = connection_string.replace('postgresql+psycopg://', 'postgresql://')

        with psycopg.connect(connection_string) as conn:
            with conn.cursor() as cur:
                print('🔧 Fixing foreign key constraints...')
                
                # Drop existing constraints
                print('  - Dropping existing constraints...')
                cur.execute('ALTER TABLE branches DROP CONSTRAINT IF EXISTS branches_story_id_fkey;')
                cur.execute('ALTER TABLE "Chapters" DROP CONSTRAINT IF EXISTS fk_chapters_branch;')
                cur.execute('ALTER TABLE story_choices DROP CONSTRAINT IF EXISTS story_choices_story_id_fkey;')
                cur.execute('ALTER TABLE story_choices DROP CONSTRAINT IF EXISTS story_choices_branch_id_fkey;')
                
                # Recreate with CASCADE
                print('  - Creating new constraints with CASCADE...')
                cur.execute('''
                    ALTER TABLE branches 
                    ADD CONSTRAINT branches_story_id_fkey 
                    FOREIGN KEY (story_id) 
                    REFERENCES "Stories"(id) 
                    ON DELETE CASCADE;
                ''')
                
                cur.execute('''
                    ALTER TABLE "Chapters" 
                    ADD CONSTRAINT fk_chapters_branch 
                    FOREIGN KEY (branch_id) 
                    REFERENCES branches(id) 
                    ON DELETE CASCADE;
                ''')
                
                cur.execute('''
                    ALTER TABLE story_choices 
                    ADD CONSTRAINT story_choices_story_id_fkey 
                    FOREIGN KEY (story_id) 
                    REFERENCES "Stories"(id) 
                    ON DELETE CASCADE;
                ''')
                
                cur.execute('''
                    ALTER TABLE story_choices 
                    ADD CONSTRAINT story_choices_branch_id_fkey 
                    FOREIGN KEY (branch_id) 
                    REFERENCES branches(id) 
                    ON DELETE CASCADE;
                ''')
                
                conn.commit()
                print('✅ Foreign key constraints fixed with CASCADE deletion')
                return True
                
    except Exception as e:
        print(f'❌ Error fixing foreign key constraints: {e}')
        return False

if __name__ == '__main__':
    success = fix_foreign_key_constraints()
    sys.exit(0 if success else 1) 