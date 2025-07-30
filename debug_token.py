#!/usr/bin/env python3
"""
Debug script to check token format
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def debug_token_format():
    """Debug the token format issue"""
    
    print("🔍 Debugging Token Format...")
    
    # Test with a simple request to see what happens
    print("\n1. Testing like endpoint with detailed error...")
    try:
        response = requests.post(
            f"{BASE_URL}/story/177/like",
            headers={
                "Authorization": "Bearer test-token",
                "Content-Type": "application/json"
            }
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n📋 Analysis:")
    print("The backend is rejecting the Supabase token format.")
    print("We need to either:")
    print("1. Modify the backend to accept Supabase tokens")
    print("2. Use a different authentication method")
    print("3. Extract the user ID from the token differently")

if __name__ == "__main__":
    debug_token_format() 