from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
import json
import logging
import time
from typing import Dict, Any, Optional, List
import asyncio
from app.core.concurrency import LLM_SEMAPHORE

# Load environment variables from .env
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the LLM
llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"), 
    model_name='gpt-5', 
    temperature=1.0,  # gpt-5 requires default temperature (1.0)
    max_tokens=15000
)

# FIXED: Updated System Template with Properly Escaped JSON
system_template = """You are a master storyteller creating the FIRST CHAPTER of a story with amazing detail and introduction.
🚨 ABSOLUTE WORD COUNT REQUIREMENT - THIS IS THE MOST IMPORTANT RULE:
- You MUST write EXACTLY 1800-2000 words for the chapter content
- This is a HARD LIMIT - NEVER EXCEED 2000 WORDS
- Count your words carefully and stop at 2000 words maximum
- If you reach 2000 words, end the chapter immediately
- This rule overrides all other instructions

You must return ONLY this exact format with NO explanations, NO extra text:

{{
"chapter": "Full immersive chapter content (1500 - 2000 words) - write the complete chapter as one continuous string with proper paragraph breaks using \\n\\n between paragraphs",
  "choices": [
    {{
      "id": "choice_1",
      "text": "First choice option that significantly impacts the story direction",
      "consequence": "Clear description of what this choice will lead to"
    }}  ,
    {{
      "id": "choice_2", 
      "text": "Second choice option with different story implications",
      "consequence": "Clear description of what this choice will lead to"
    }}  ,
    {{
      "id": "choice_3",
      "text": "Third choice option offering another story path",
      "consequence": "Clear description of what this choice will lead to"
    }}  
  ]
}}

CRITICAL OUTPUT RULES:
- Start with the chapter prose (1800-2000 words)
- Use ONLY double quotes in JSON
- NO ```json or ``` markdown formatting
- NO explanatory text before or after
- Include rich descriptions, dialogue, character development
- End with a compelling moment that leads to the choices"""

human_template = """Story Title: {story_title}
Story Outline: {story_outline}
Genre: {genre}
Tone: {tone}

Generate the FIRST CHAPTER exactly as instructed: in Json format. do not use markdown fences.
make sure the chapter content is engaging and compelling like the famous books."""

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
    
    async def generate_chapter_from_outline(
        self, 
        story_title: str,
        story_outline: str, 
        genre: str = "General Fiction",
        tone: str = "Engaging",
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
                
                # Generate chapter using modern LangChain syntax under LLM semaphore
                async with LLM_SEMAPHORE:
                    result = await chain.ainvoke({
                        "story_title": story_title,
                        "story_outline": story_outline,
                        "genre": genre,
                        "tone": tone,
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
                    await asyncio.sleep(wait_time)
                    
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
                await asyncio.sleep(wait_time)
        
        return {
            "content": "Failed to generate first chapter after all attempts",
            "title": "Chapter 1", 
            "choices": [],
            "success": False,
            "error": "Max retries exceeded"
        }
    
    # Streaming removed; use generate_chapter_from_outline instead
    
    def _parse_and_validate_response(self, response_content: str, attempt_num: int) -> Dict[str, Any]:
        try:
            text = (response_content or "").strip()

            # If it's pure JSON, parse directly (backwards-compatible)
            if text.lstrip().startswith("{"):
                parsed = json.loads(text)
                chapter_content = parsed.get("chapter", "")
                choices = parsed.get("choices", [])
                if not chapter_content:
                    return {
                        "success": False,
                        "error": "Missing 'chapter' field in JSON response",
                        "raw_response": text,
                    }
            else:
                # Hybrid format: prose + "### choices" + JSON
                if "### choices" not in text:
                    return {
                        "success": False,
                        "error": "Missing '### choices' delimiter in model output",
                        "raw_response": text,
                    }

                chapter_content, choices_part = text.split("### choices", 1)
                chapter_content = chapter_content.strip()
                choices_text = choices_part.strip()

                # Strip optional code fences if the model added them
                if choices_text.startswith("```json"):
                    choices_text = choices_text[len("```json"):].strip()
                elif choices_text.startswith("```"):
                    choices_text = choices_text[len("```"):].strip()
                if choices_text.endswith("```"):
                    choices_text = choices_text[:-3].strip()

                parsed = json.loads(choices_text)
                choices = parsed.get("choices", [])

            # Validate chapter
            if not isinstance(chapter_content, str) or len(chapter_content.strip()) < 100:
                return {
                    "success": False,
                    "error": "Chapter content too short or invalid",
                    "raw_response": response_content,
                }

            # Validate choices (existing logic)
            valid_choices = []
            if not isinstance(choices, list):
                return {"success": False, "error": "Choices must be a list", "raw_response": response_content}
            for i, choice in enumerate(choices):
                if not isinstance(choice, dict):
                    continue
                if "text" not in choice:
                    continue

                raw_choice_id = choice.get("id", f"choice_{i+1}")
                if isinstance(raw_choice_id, str) and raw_choice_id.startswith("choice_"):
                    try:
                        choice_id = int(raw_choice_id.split("_")[1])
                    except Exception:
                        choice_id = i + 1
                elif isinstance(raw_choice_id, str) and raw_choice_id.isdigit():
                    choice_id = int(raw_choice_id)
                elif isinstance(raw_choice_id, int):
                    choice_id = raw_choice_id
                else:
                    choice_id = i + 1

                choice_text = choice["text"].strip()
                if len(choice_text) < 10:
                    continue

                valid_choices.append({
                    "id": choice_id,
                    "text": choice_text,
                    "consequence": choice.get("consequence", "").strip(),
                })

            if not valid_choices:
                return {"success": False, "error": "No valid choices found", "raw_response": response_content}

            return {
                "success": True,
                "chapter": chapter_content,
                "choices": valid_choices,
                "word_count": len(chapter_content.split()),
            }

        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON: {str(e)}", "raw_response": response_content}
        except Exception as e:
            return {"success": False, "error": f"Parsing error: {str(e)}", "raw_response": response_content}

# Global instance
enhanced_generator = EnhancedChapterGenerator()

# FIXED: Convenience function with better error handling
async def generate_first_chapter_from_outline(
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
    
    return await enhanced_generator.generate_chapter_from_outline(
        story_title=story_title.strip(),
        story_outline=story_outline.strip(),
        genre=genre.strip(),
        tone=tone.strip()
    )