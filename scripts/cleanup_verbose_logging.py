#!/usr/bin/env python3
"""
Clean up verbose logging statements from the codebase.
Keep only essential logging for debugging and user feedback.
"""

import re
import os
import sys

def cleanup_file(file_path):
    """Clean up logging in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Remove SUMMARY DEBUG logs
        content = re.sub(r'.*logger\.info\(f?"🔍 SUMMARY DEBUG:.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.error\(f?"❌ SUMMARY DEBUG:.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.error\(f?"🔍 SUMMARY DEBUG:.*?\n', '', content, flags=re.MULTILINE)
        
        # Remove content length logging (keep only essential ones)
        content = re.sub(r'.*logger\.info\(f?".*content length.*chars.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?".*content_length.*chars.*?\n', '', content, flags=re.MULTILINE)
        
        # Remove story outline preview logs
        content = re.sub(r'.*logger\.info\(f?".*story outline preview.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?".*Story outline preview.*?\n', '', content, flags=re.MULTILINE)
        
        # Remove verbose database response logs
        content = re.sub(r'.*logger\.info\(f?".*insert response.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?".*Database update response.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?".*update response.*?\n', '', content, flags=re.MULTILINE)
        
        # Remove verbose choice debugging logs
        content = re.sub(r'.*logger\.info\(f?"DEBUG: Saving choice dict.*?\n', '', content, flags=re.MULTILINE)
        
        # Remove verbose frontend debugging logs
        content = re.sub(r'.*logger\.info\(f?"🔍.*DEBUG.*?\n', '', content, flags=re.MULTILINE)
        
        # Remove token tracking details (keep summary)
        content = re.sub(r'.*logger\.info\(f?"📊 TOKEN TRACKING: Input prompt.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"📊 TOKEN TRACKING: ~.*?\n', '', content, flags=re.MULTILINE)
        
        # Remove verbose LLM chain logs
        content = re.sub(r'.*logger\.info\(f?"🚀 SUMMARY LLM: Calling LLM chain.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"✅ SUMMARY LLM: LLM chain completed.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"📊 SUMMARY LLM: Raw result.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"📝 SUMMARY LLM: Raw result.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"🔧 SUMMARY LLM: Processing.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"📝 SUMMARY LLM: Summary text.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"📊 SUMMARY LLM: Output metrics.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"   📝 Summary words.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"   📏 Summary length.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"   🎯 Estimated.*tokens.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"📉 SUMMARY LLM: Compression.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"✅ SUMMARY LLM: Summary generated.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"📝 SUMMARY LLM: Summary length.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"🎉 SUMMARY LLM: Returning.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"📋 SUMMARY LLM: Result keys.*?\n', '', content, flags=re.MULTILINE)
        
        # Remove verbose parameter logs
        content = re.sub(r'.*logger\.info\(f?"📊 SUMMARY LLM: Input parameters.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"   📝 Chapter content length.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"   📄 Story context length.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"   📑 Chapter number.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"⚙️ SUMMARY LLM.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"   🤖 Model.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"   🌡️ Temperature.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"   🎯 Max tokens.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"📊 SUMMARY LLM: Input metrics.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"   📝 Chapter words.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"   📄 Context words.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"   📋 Total input words.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'.*logger\.info\(f?"🎯 SUMMARY LLM: Preparing.*?\n', '', content, flags=re.MULTILINE)
        
        # Clean up empty lines that might be left
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Cleaned up logging in {file_path}")
            return True
        else:
            print(f"⚪ No changes needed in {file_path}")
            return False
    
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to clean up logging in all Python files."""
    files_to_clean = [
        'main.py',
        'chapter_summary.py',
        'lc_next_chapter_generator.py',
        'lc_book_generator.py',
        'services/story_service.py',
        'services/embedding_service.py'
    ]
    
    cleaned_count = 0
    
    for file_path in files_to_clean:
        if os.path.exists(file_path):
            if cleanup_file(file_path):
                cleaned_count += 1
        else:
            print(f"⚠️ File not found: {file_path}")
    
    print(f"\n🎉 Cleanup complete! {cleaned_count} files were modified.")
    print("📝 Essential logging has been preserved:")
    print("   - Chapter creation with selected choice")
    print("   - LLM input/output summaries")
    print("   - Error messages")
    print("   - Key process milestones")

if __name__ == '__main__':
    main() 