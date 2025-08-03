#!/usr/bin/env python3
"""
Test script to debug the rewrite function
"""

import os
import sys
import json
import requests
from typing import Dict, Any

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_rewrite_endpoint():
    """Test the rewrite endpoint with different payloads"""
    
    # Test payload 1: Correct format
    payload1 = {
        "selected_text": "This is a test sentence that needs to be rewritten.",
        "story_context": {
            "title": "Test Story",
            "genre": "Fiction",
            "content": "This is some story content for context."
        }
    }
    
    # Test payload 2: Wrong field names (what the frontend was sending)
    payload2 = {
        "text": "This is a test sentence that needs to be rewritten.",
        "context": "This is some story content for context."
    }
    
    # Test payload 3: Minimal payload
    payload3 = {
        "selected_text": "Test text"
    }
    
    # Test payload 4: Empty text
    payload4 = {
        "selected_text": ""
    }
    
    # Test payload 5: Very long text
    payload5 = {
        "selected_text": "A" * 2500  # Exceeds max_length=2000
    }
    
    test_cases = [
        ("Correct format", payload1),
        ("Wrong field names", payload2),
        ("Minimal payload", payload3),
        ("Empty text", payload4),
        ("Text too long", payload5)
    ]
    
    base_url = "http://localhost:8000"
    
    for test_name, payload in test_cases:
        print(f"\n{'='*50}")
        print(f"Testing: {test_name}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(
                f"{base_url}/rewrite_text",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 422:
                print("✅ This is the expected 422 error for invalid payload")
            elif response.status_code == 200:
                print("✅ Success!")
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection error - make sure the server is running")
        except Exception as e:
            print(f"❌ Error: {e}")

def test_rewrite_function_directly():
    """Test the rewrite function directly without the API"""
    
    print(f"\n{'='*50}")
    print("Testing rewrite function directly")
    
    try:
        from lc_book_generator_prompt import rewrite_text_with_context
        
        # Test with sample text
        original_text = "This is a test sentence that needs to be rewritten."
        context = {
            "story_title": "Test Story",
            "story_genre": "Fiction",
            "story_outline": "A test story outline",
            "current_chapter": "Chapter 1",
            "chapter_content": "Some chapter content"
        }
        
        print(f"Original text: {original_text}")
        print(f"Context: {context}")
        
        result = rewrite_text_with_context(original_text, context)
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"❌ Error testing rewrite function: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing rewrite function...")
    
    # Test the API endpoint
    test_rewrite_endpoint()
    
    # Test the function directly
    test_rewrite_function_directly() 