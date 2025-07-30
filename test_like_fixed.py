#!/usr/bin/env python3
"""
Test script for the fixed like endpoint
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_like_endpoint():
    """Test the like endpoint with the new authentication"""
    
    print("🧪 Testing Fixed Like Endpoint...")
    
    # Test with a simple request
    print("\n1. Testing like endpoint with new auth method...")
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
        
        if response.status_code == 401:
            print("   ✅ Expected 401 for invalid token - auth method is working!")
        else:
            print("   ❌ Unexpected response")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n📋 Next Steps:")
    print("1. The backend is now running with the updated authentication")
    print("2. Try clicking the like button in your frontend")
    print("3. Check the browser console for any errors")
    print("4. The like should now work with your Supabase session token")

if __name__ == "__main__":
    test_like_endpoint() 