#!/usr/bin/env python3
"""
Script to fix the vector database schema issue.

This script will drop and recreate the langchain vector tables
with the correct schema for the current version of langchain.
"""

import psycopg
from config import settings

def fix_vector_schema():
    """Fix the vector database schema by recreating tables."""
    connection_string = settings.get_postgres_connection_string()
    
    # Convert psycopg format back to standard format for psycopg connection
    if "postgresql+psycopg://" in connection_string:
        connection_string = connection_string.replace("postgresql+psycopg://", "postgresql://")
    
    try:
        print("Connecting to database...")
        with psycopg.connect(connection_string) as conn:
            with conn.cursor() as cur:
                print("Dropping existing langchain tables...")
                
                # Drop existing tables if they exist
                cur.execute("DROP TABLE IF EXISTS langchain_pg_embedding CASCADE;")
                cur.execute("DROP TABLE IF EXISTS langchain_pg_collection CASCADE;")
                
                print("Tables dropped successfully.")
                print("Note: The tables will be recreated automatically when the vector store is used.")
                
                conn.commit()
                
        print("✅ Schema fix completed successfully!")
        print("You can now restart your backend server.")
        
    except Exception as e:
        print(f"❌ Error fixing schema: {e}")
        return False
    
    return True

if __name__ == "__main__":
    fix_vector_schema()