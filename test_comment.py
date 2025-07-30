#!/usr/bin/env python3
"""
Test script for the comment endpoint
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_comment_endpoint():
    """Test the comment endpoint with the new authentication"""
    
    print("💬 Testing Comment Endpoint...")
    
    # Test with a simple request
    print("\n1. Testing comment endpoint with new auth method...")
    try:
        response = requests.post(
            f"{BASE_URL}/story/177/comment",
            headers={
                "Authorization": "Bearer test-token",
                "Content-Type": "application/json"
            },
            json={
                "comment": "This is a test comment"
            }
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 401:
            print("   ✅ Expected 401 for invalid token - auth method is working!")
        else:
            print("   ❌ Unexpected response")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n📋 Comment Functionality:")
    print("1. The comment button should open a prompt dialog")
    print("2. Enter your comment and click OK")
    print("3. The comment should be saved to the database")
    print("4. The comment count should update")
    print("5. You should see a success alert")

if __name__ == "__main__":
    test_comment_endpoint() 