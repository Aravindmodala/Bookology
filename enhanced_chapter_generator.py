from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
import json
import logging
import time
from typing import Dict, Any, Optional, List

# Load environment variables from .env
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the LLM
llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"), 
    model_name='gpt-4o-mini', 
    temperature=0.8, 
    max_tokens=15000
)

# FIXED: Updated System Template with Properly Escaped JSON
system_template = """You are a master storyteller creating the FIRST CHAPTER of a story.

CRITICAL REQUIREMENTS:
- Write EXACTLY 1800-2000 words for the chapter content
- Include 3 meaningful story choices at the end
- Return ONLY valid JSON with NO additional text whatsoever

You must return ONLY this exact JSON structure with NO markdown, NO explanations, NO extra text:

{{
  "chapter": "Your complete 1800-2000 word chapter content goes here with vivid descriptions, character development, dialogue, and rich storytelling that establishes the setting, introduces main characters, creates an engaging hook, and sets up the central conflict of the story...",
  "choices": [
    {{
      "id": "choice_1",
      "text": "First choice option that significantly impacts the story direction",
      "consequence": "Clear description of what this choice will lead to"
    }},
    {{
      "id": "choice_2", 
      "text": "Second choice option with different story implications",
      "consequence": "Clear description of what this choice will lead to"
    }},
    {{
      "id": "choice_3",
      "text": "Third choice option offering another story path",
      "consequence": "Clear description of what this choice will lead to"
    }}
  ]
}}

CRITICAL OUTPUT RULES:
- Start your response with {{ and end with }}
- Use ONLY double quotes for all strings
- NO ```json or ``` markdown formatting
- NO explanatory text before or after JSON
- The chapter field must contain 1800-2000 words
- Include rich descriptions, dialogue, character development
- Create an engaging opening that hooks readers immediately
- End with a compelling moment that leads to the choices"""

human_template = """Story Title: {story_title}
Story Outline: {story_outline}
Genre: {genre}
Tone: {tone}

Generate the FIRST CHAPTER following the system instructions exactly. Return ONLY the JSON object."""

# Create the prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", system_template),
    ("human", human_template)
])

# FIXED: Use modern LangChain syntax
chain = prompt | llm

class EnhancedChapterGenerator:
    """
    Enhanced Chapter Generator for FIRST CHAPTER ONLY.
    Generates 1800-2000 word chapters with proper JSON output.
    """
    
    def __init__(self):
        logger.info("🚀 EnhancedChapterGenerator initialized for FIRST CHAPTER generation")
    
    def generate_chapter_from_outline(
        self, 
        story_title: str,
        story_outline: str, 
        genre: str = "General Fiction",
        tone: str = "Dramatic",
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Generate the FIRST CHAPTER from story outline.
        
        Args:
            story_title: The title of the story
            story_outline: The story outline
            genre: The story genre
            tone: The story tone
            max_retries: Maximum retry attempts
            
        Returns:
            Dict containing chapter content and choices
        """
        logger.info(f"🎯 Generating FIRST CHAPTER for: {story_title}")
        logger.info(f"📝 Outline length: {len(story_outline)} characters")
        logger.info(f"🎭 Genre: {genre}, Tone: {tone}")
        
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                # Generate chapter using modern LangChain syntax
                result = chain.invoke({
                    "story_title": story_title,
                    "story_outline": story_outline,
                    "genre": genre,
                    "tone": tone
                })
                
                # FIXED: Correct way to access LangChain response
                if hasattr(result, 'content'):
                    llm_output = result.content
                elif isinstance(result, dict):
                    llm_output = result.get('text', result.get('content', str(result)))
                else:
                    llm_output = str(result)
                
                # Debug logging
                logger.info(f"🔍 RESULT TYPE: {type(result)}")
                logger.info(f"🔍 LLM OUTPUT (first 300 chars): {llm_output[:300]}...")
                logger.info(f"📏 Output length: {len(llm_output)} characters")
                
                # Parse and validate response
                parsed_result = self._parse_and_validate_response(llm_output, attempt + 1)
                
                if parsed_result.get("success", False):
                    generation_time = time.time() - start_time
                    word_count = len(parsed_result["chapter"].split())
                    
                    logger.info(f"✅ FIRST CHAPTER generated successfully!")
                    logger.info(f"📊 Word count: {word_count} words")
                    logger.info(f"⏱️ Generation time: {generation_time:.2f}s")
                    logger.info(f"🎮 Choices generated: {len(parsed_result.get('choices', []))}")
                    
                    return {
                        "content": parsed_result["chapter"],
                        "title": "Chapter 1",
                        "choices": parsed_result.get("choices", []),
                        "success": True,
                        "word_count": word_count,
                        "generation_time": generation_time,
                        "attempt": attempt + 1
                    }
                else:
                    error_msg = parsed_result.get('error', 'Unknown error')
                    logger.error(f"❌ Attempt {attempt + 1} failed: {error_msg}")
                    
                    # Log raw response for debugging
                    if 'raw_response' in parsed_result:
                        logger.error(f"🔍 Raw response: {parsed_result['raw_response'][:500]}...")
                    
                    # Continue to next attempt unless this is the last one
                    if attempt == max_retries - 1:
                        return {
                            "content": f"Error generating first chapter after {max_retries} attempts: {error_msg}",
                            "title": "Chapter 1",
                            "choices": [],
                            "success": False,
                            "error": error_msg,
                            "raw_response": parsed_result.get('raw_response', '')
                        }
                        
                    # Wait before retry with exponential backoff
                    wait_time = 2 ** attempt
                    logger.info(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"❌ Attempt {attempt + 1} failed with exception: {str(e)}")
                if attempt == max_retries - 1:
                    return {
                        "content": f"Error generating first chapter: {str(e)}",
                        "title": "Chapter 1",
                        "choices": [],
                        "success": False,
                        "error": str(e)
                    }
                    
                # Wait before retry
                wait_time = 2 ** attempt
                logger.info(f"⏳ Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
        
        return {
            "content": "Failed to generate first chapter after all attempts",
            "title": "Chapter 1", 
            "choices": [],
            "success": False,
            "error": "Max retries exceeded"
        }
    
    def _parse_and_validate_response(self, response_content: str, attempt_num: int) -> Dict[str, Any]:
        """
        Parse and validate the LLM response for first chapter generation.
        FIXED: Simplified parsing with strict validation.
        """
        try:
            # Clean the response
            cleaned_response = response_content.strip()
            
            # Remove markdown code blocks if present (though they shouldn't be there)
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
                logger.warning("⚠️ Found ```json wrapper - LLM didn't follow instructions")
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
                logger.warning("⚠️ Found ``` wrapper - LLM didn't follow instructions")
            
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            cleaned_response = cleaned_response.strip()
            
            # Log cleaned response for debugging
            logger.info(f"🧹 Cleaned response length: {len(cleaned_response)} characters")
            logger.info(f"🔍 First 200 chars: {cleaned_response[:200]}...")
            logger.info(f"🔍 Last 200 chars: ...{cleaned_response[-200:]}")
            
            # FIXED: Direct JSON parsing with better error handling
            try:
                parsed_data = json.loads(cleaned_response)
                logger.info("✅ JSON parsed successfully")
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON parsing failed on attempt {attempt_num}: {str(e)}")
                logger.error(f"🔍 Error position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
                
                # Try to find where the JSON might be malformed
                lines = cleaned_response.split('\n')
                for i, line in enumerate(lines[:10]):  # Show first 10 lines
                    logger.error(f"Line {i+1}: {line}")
                
                return {
                    "success": False, 
                    "error": f"Invalid JSON (attempt {attempt_num}): {str(e)}", 
                    "raw_response": cleaned_response
                }
            
            # FIXED: Strict validation of required fields
            if "chapter" not in parsed_data:
                logger.error("❌ Missing 'chapter' field in response")
                return {
                    "success": False, 
                    "error": "Missing 'chapter' field", 
                    "raw_response": cleaned_response
                }
            
            chapter_content = parsed_data["chapter"]
            if not isinstance(chapter_content, str):
                logger.error(f"❌ Chapter content is not a string: {type(chapter_content)}")
                return {
                    "success": False, 
                    "error": "Chapter content must be a string", 
                    "raw_response": cleaned_response
                }
            
            if len(chapter_content.strip()) < 100:
                logger.error(f"❌ Chapter content too short: {len(chapter_content)} characters")
                return {
                    "success": False, 
                    "error": f"Chapter content too short: {len(chapter_content)} characters", 
                    "raw_response": cleaned_response
                }
            
            # Calculate word count for logging - NO VALIDATION, accept whatever LLM gives
            word_count = len(chapter_content.split())
            logger.info(f"📊 Chapter word count: {word_count} words (accepting any length)")
            
            # Validate choices
            choices = parsed_data.get("choices", [])
            if not isinstance(choices, list):
                logger.error(f"❌ Choices must be a list, got: {type(choices)}")
                return {
                    "success": False, 
                    "error": "Choices must be a list", 
                    "raw_response": cleaned_response
                }
            
            # FIXED: Strict choice validation with integer IDs
            valid_choices = []
            for i, choice in enumerate(choices):
                if not isinstance(choice, dict):
                    logger.warning(f"⚠️ Choice {i+1} is not a dict: {choice}")
                    continue
                
                if "text" not in choice:
                    logger.warning(f"⚠️ Choice {i+1} missing 'text' field: {choice}")
                    continue
                
                # Convert choice ID to integer format for database compatibility
                raw_choice_id = choice.get("id", f"choice_{i+1}")
                if isinstance(raw_choice_id, str) and raw_choice_id.startswith("choice_"):
                    # Extract number from "choice_1", "choice_2", etc.
                    try:
                        choice_id = int(raw_choice_id.split("_")[1])
                    except (ValueError, IndexError):
                        choice_id = i + 1
                elif isinstance(raw_choice_id, str) and raw_choice_id.isdigit():
                    # Already a numeric string
                    choice_id = int(raw_choice_id)
                elif isinstance(raw_choice_id, int):
                    # Already an integer
                    choice_id = raw_choice_id
                else:
                    # Fallback to index + 1
                    choice_id = i + 1
                
                choice_text = choice["text"]
                choice_consequence = choice.get("consequence", "")
                
                if len(choice_text.strip()) < 10:
                    logger.warning(f"⚠️ Choice {i+1} text too short: {choice_text}")
                    continue
                
                valid_choices.append({
                    "id": choice_id,
                    "text": choice_text.strip(),
                    "consequence": choice_consequence.strip()
                })
            
            if len(valid_choices) == 0:
                logger.error("❌ No valid choices found")
                return {
                    "success": False, 
                    "error": "No valid choices found", 
                    "raw_response": cleaned_response
                }
            
            logger.info(f"✅ Validation successful: {word_count} words, {len(valid_choices)} choices")
            
            return {
                "success": True,
                "chapter": chapter_content,
                "choices": valid_choices,
                "word_count": word_count
            }
            
        except Exception as e:
            logger.error(f"❌ Unexpected parsing error: {str(e)}")
            return {
                "success": False, 
                "error": f"Parsing error: {str(e)}", 
                "raw_response": response_content
            }

# Global instance
enhanced_generator = EnhancedChapterGenerator()

# FIXED: Convenience function with better error handling
def generate_first_chapter_from_outline(
    story_title: str,
    story_outline: str,
    genre: str = "General Fiction",
    tone: str = "Dramatic"
) -> Dict[str, Any]:
    """
    Generate the first chapter from story outline.
    
    Args:
        story_title: The title of the story
        story_outline: The story outline
        genre: The story genre
        tone: The story tone
        
    Returns:
        Dict containing chapter content and choices
    """
    # Validate inputs
    if not story_title or not story_title.strip():
        return {
            "content": "Error: Story title is required",
            "title": "Chapter 1",
            "choices": [],
            "success": False,
            "error": "Story title is required"
        }
    
    if not story_outline or len(story_outline.strip()) < 50:
        return {
            "content": "Error: Story outline must be at least 50 characters",
            "title": "Chapter 1",
            "choices": [],
            "success": False,
            "error": "Story outline too short"
        }
    
    return enhanced_generator.generate_chapter_from_outline(
        story_title=story_title.strip(),
        story_outline=story_outline.strip(),
        genre=genre.strip(),
        tone=tone.strip()
    )