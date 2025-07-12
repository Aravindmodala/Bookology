from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import os
import json
import logging
from typing import Dict, Any, Optional

# Load environment variables from .env
load_dotenv()

# Set up logging for JSON output display
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the LLM (OpenAI Chat model - correct for GPT-4o)
llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model_name='gpt-4o', temperature=0.8, max_tokens=6000)

system_template = """You are a globally renowned, award-winning novelist, ghostwriter, and master storyteller known for creating bestselling novels that captivate readers deeply.

🎭 ROLE & EXPERTISE:
- Expert in character development, plot pacing, layered backstory, and emotional storytelling
- Master of immersive world-building and atmospheric prose
- Specialist in powerful chapter hooks, rising tension, and cliffhangers
- Skilled at writing deeply human, layered prose that feels alive
- Expert at creating meaningful, contextual story choices that impact narrative direction

✍️ WRITING STANDARDS:
- Format: Novel-style prose (not script or bullet points)
- Perspective: Third-person limited (or first-person if the outline requires)
- Voice: Masterful, human author quality with vivid, emotionally expressive language
- Characters: Complex, with contradictions, depth, and vulnerability
- Continuity: Logical, immersive world consistency

🎯 CHAPTER 1 REQUIREMENTS:
- Start in the protagonist's **ordinary world**, showing their current daily life, environment, and small details that reveal their personality and emotions.
- Reveal the protagonist's **inner conflicts, longings, and emotional stakes**.
- Use **layered sensory details** (smells, sounds, sights, textures) and **micro-emotions** to create immersion.
- Transition naturally into the **inciting incident** that will propel the protagonist into the journey.
- End with a **compelling hook**, signaling the change about to come.

🎯 CHOICE GENERATION REQUIREMENTS:
- Generate 3-4 contextual choices that naturally emerge from the chapter's events
- Each choice should represent a meaningful decision the protagonist could make
- Choices should feel organic to the story and character motivations
- Include a mix of action-oriented, emotional, and strategic choices
- Each choice should have clear story implications and character development potential
- Choices should be specific enough to guide the next chapter's direction

💡 Follow the provided outline precisely while expanding it into immersive, cinematic, and emotionally resonant prose.

📌 OUTPUT FORMAT:
Return ONLY a valid JSON object in this exact structure:

{{
 "chapter": "The full chapter content as immersive, novel-quality prose, exactly 3000 words. Structure the chapter in three acts: Act 1 (1000 words) establishes the protagonist’s ordinary world and inner conflict; Act 2 (1000 words) introduces the inciting incident with rising tension; Act 3 (1000 words) builds to a climactic hook with vivid sensory details and emotional stakes.",
  "choices": [
    {{
      "id": "choice_1",
      "title": "Brief choice title (3-6 words)",
      "description": "Detailed description of what this choice involves and its immediate implications",
      "story_impact": "How this choice would affect the story direction and character development",
      "choice_type": "action/emotional/strategic/dialogue"
    }},
    {{
      "id": "choice_2", 
      "title": "Brief choice title (3-6 words)",
      "description": "Detailed description of what this choice involves and its immediate implications",
      "story_impact": "How this choice would affect the story direction and character development",
      "choice_type": "action/emotional/strategic/dialogue"
    }},
    {{
      "id": "choice_3",
      "title": "Brief choice title (3-6 words)", 
      "description": "Detailed description of what this choice involves and its immediate implications",
      "story_impact": "How this choice would affect the story direction and character development",
      "choice_type": "action/emotional/strategic/dialogue"
    }}
  ]
}}

🚫 DO NOT:
- Explain or summarize the outline
- Use phrases like "As per the outline…"
- Return summaries instead of chapter content
- Break character with meta-commentary
- Add any text outside the JSON structure
- Include markdown formatting or code blocks

Write so immersively that readers forget this was AI-generated and feel fully transported into the story. The choices should feel like natural decision points that emerge organically from the chapter's events."""


# Create user message template (the actual request)
user_template = """Please write **Chapter {chapter_number} of a novel** using the fully expanded story outline below:

📘 STORY OUTLINE:
{outline}

Write Chapter {chapter_number} following all the guidelines provided. Focus on creating a deeply immersive, cinematic, emotionally powerful opening chapter that makes readers feel as if a world-class human author wrote it. The chapter should draw readers deeply into the protagonist’s world, making them care about the journey before it begins, and ending with a compelling hook."""


# Create the chat prompt template
system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
human_message_prompt = HumanMessagePromptTemplate.from_template(user_template)

prompt = ChatPromptTemplate.from_messages([
    system_message_prompt,
    human_message_prompt
])

# Build the chain
chain = prompt | llm

def generate_chapter_from_outline(outline: str):
    """Legacy function for backward compatibility."""
    try:
        generator = BookStoryGenerator()
        result = generator.generate_chapter(outline, 1)
        
        # Handle new JSON response format for backward compatibility
        if isinstance(result, dict) and result.get("success"):
            return result.get("chapter_content", "")
        elif isinstance(result, dict):
            return result.get("chapter_content", f"❌ Error: {result.get('error', 'Unknown error')}")
        else:
            return str(result)
    except Exception as e:
        return f"❌ Error generating Chapter 1: {str(e)}"

def extract_chapter_info_from_json(json_data: Dict[str, Any], chapter_number: int = 1) -> str:
    """Extract relevant chapter and story information from JSON outline."""
    logger.info(f"🔍 Extracting Chapter {chapter_number} info from JSON outline...")

    
    # Extract story-level information
    story_info = {
        "title": json_data.get("book_title", "Untitled"),
        "genre": json_data.get("genre", "General Fiction"),
        "theme": json_data.get("theme", ""),
        "style": json_data.get("style", "Modern narrative"),
        "description": json_data.get("description", ""),
        "main_characters": json_data.get("main_characters", []),
        "key_locations": json_data.get("key_locations", []),
        "conflict": json_data.get("conflict", ""),
        "tone_keywords": json_data.get("tone_keywords", []),
        "writing_guidelines": json_data.get("writing_guidelines", "")
    }
    
    # Extract specific chapter information
    Chapters = json_data.get("Chapters", [])
    target_chapter = None
    
    for chapter in Chapters:
        if chapter.get("chapter_number") == chapter_number:
            target_chapter = chapter
            break
    
    # Log extracted chapter info
    if target_chapter:
        logger.info(f"✅ Found Chapter {chapter_number} in JSON:")
        logger.info(f"   Title: {target_chapter.get('chapter_title', 'N/A')}")
        logger.info(f"   Summary: {target_chapter.get('chapter_summary', 'N/A')[:100]}...")
        logger.info(f"   Word Count: {target_chapter.get('estimated_word_count', 'N/A')}")
    else:
        logger.warning(f"⚠️ Chapter {chapter_number} not found in JSON outline!")
    
    # Build comprehensive outline text for LLM
    outline_text = f"""
BOOK TITLE: {story_info['title']}
GENRE: {story_info['genre']}
THEME: {story_info['theme']}
STYLE: {story_info['style']}

DESCRIPTION:
{story_info['description']}

MAIN CHARACTERS:
"""
    
    for char in story_info['main_characters']:
        if isinstance(char, dict):
            name = char.get('name', 'Unknown')
            role = char.get('role', 'Character')
            description = char.get('description', 'No description')
            outline_text += f"- {name} ({role}): {description}\n"
        else:
            outline_text += f"- {char}\n"
    
    outline_text += f"""
KEY LOCATIONS:
"""
    
    for loc in story_info['key_locations']:
        if isinstance(loc, dict):
            name = loc.get('name', 'Unknown Location')
            description = loc.get('description', 'No description')
            outline_text += f"- {name}: {description}\n"
        else:
            outline_text += f"- {loc}\n"
    
    outline_text += f"""
CENTRAL CONFLICT: {story_info['conflict']}

TONE KEYWORDS: {', '.join(story_info['tone_keywords'])}

WRITING GUIDELINES:
{story_info['writing_guidelines']}

CHAPTER {chapter_number} DETAILS:
"""
    
    if target_chapter:
        outline_text += f"""
Chapter Title: {target_chapter.get('chapter_title', f'Chapter {chapter_number}')}
Chapter Summary: {target_chapter.get('chapter_summary', 'First chapter of the story')}
Estimated Word Count: {target_chapter.get('estimated_word_count', 'Not specified')}
Key Events: {target_chapter.get('key_events', 'Introduction and setup')}
Character Focus: {target_chapter.get('character_appearances', 'Main characters')}
Setting/Location: {target_chapter.get('location', 'Primary setting')}
Mood/Atmosphere: {target_chapter.get('mood', 'Engaging and immersive')}
Cliffhanger/Hook: {target_chapter.get('cliffhanger_cta', 'Compelling chapter ending')}
"""
    else:
        outline_text += f"""
Chapter Title: Chapter {chapter_number}
Chapter Summary: Opening chapter that introduces the world, characters, and central conflict
Note: This chapter should establish the tone and draw readers into the story immediately.
"""
    
    logger.info(f"📝 Generated outline text for LLM ({len(outline_text)} characters)")
    return outline_text

class BookStoryGenerator:
    """Enhanced story generator that works with both text and JSON outlines."""
    
    def __init__(self):
        self.llm = llm
        self.chain = chain
        logger.info("🚀 BookStoryGenerator initialized with JSON support")
    
    def generate_chapter(self, outline: str, chapter_number: int = 1) -> Dict[str, Any]:
        """Generate a chapter from either text outline or JSON outline."""
        logger.info(f"📖 Generating Chapter {chapter_number}...")
        
        try:
            # Try to parse as JSON first
            try:
                json_outline = json.loads(outline)
                logger.info("✅ Input detected as JSON outline")
                
                # Extract and format information for LLM
                formatted_outline = extract_chapter_info_from_json(json_outline, chapter_number)
                
                # Log what we're sending to LLM
                logger.info("🤖 SENDING TO LLM:")
                logger.info(f"   📝 Formatted outline length: {len(formatted_outline)} chars")
                
                # Generate chapter
                result = self.chain.invoke({"outline": formatted_outline, "chapter_number": chapter_number})
                
                logger.info(f"✅ Chapter {chapter_number} generated successfully!")
                logger.info(f"📊 Generated content: {len(result.content)} characters")
                
                # Parse the JSON response from LLM
                return self._parse_chapter_response(result.content.strip(), chapter_number)
                
            except json.JSONDecodeError:
                # If not JSON, treat as regular text outline
                logger.info("📄 Input detected as text outline (not JSON)")
                
                logger.info("🤖 SENDING TO LLM:")
                logger.info(f"   📝 Text outline length: {len(outline)} chars")
                
                result = self.chain.invoke({"outline": outline, "chapter_number": chapter_number})
                
                logger.info(f"✅ Chapter {chapter_number} generated successfully!")
                logger.info(f"📊 Generated content: {len(result.content)} characters")
                
                # Parse the JSON response from LLM
                return self._parse_chapter_response(result.content.strip(), chapter_number)
                
        except Exception as e:
            error_msg = f"❌ Error generating Chapter {chapter_number}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "chapter_content": error_msg,
                "choices": [],
                "error": str(e)
            }
    
    def _parse_chapter_response(self, response_content: str, chapter_number: int) -> Dict[str, Any]:
        """Parse the JSON response from LLM containing chapter and choices."""
        import re
        
        try:
            # Clean up the response
            cleaned_text = response_content.strip()
            
            # Remove markdown code blocks if present
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            
            # Remove any leading/trailing whitespace
            cleaned_text = cleaned_text.strip()
            
            # CRITICAL FIX: Handle trailing commas and other JSON formatting issues
            cleaned_text = re.sub(r',(\s*[}\]])', r'\1', cleaned_text)
            cleaned_text = re.sub(r',(\s*})', r'\1', cleaned_text)
            cleaned_text = re.sub(r',(\s*])', r'\1', cleaned_text)
            
            # Parse JSON
            parsed_json = json.loads(cleaned_text)
            
            # Validate structure
            if "chapter" not in parsed_json:
                raise ValueError("Response missing 'chapter' field")
            
            if "choices" not in parsed_json:
                raise ValueError("Response missing 'choices' field")
            
            logger.info(f"✅ Successfully parsed JSON response with {len(parsed_json.get('choices', []))} choices")
            
            return {
                "success": True,
                "chapter_content": parsed_json["chapter"],
                "choices": parsed_json["choices"],
                "chapter_number": chapter_number
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing error: {e}")
            logger.error(f"Raw response length: {len(response_content)} chars")
            
            # Try one more time with aggressive cleaning
            try:
                cleaned_text = response_content.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.startswith("```"):
                    cleaned_text = cleaned_text[3:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()
                
                # More aggressive comma removal
                cleaned_text = re.sub(r',\s*([}\]])', r'\1', cleaned_text)
                parsed_json = json.loads(cleaned_text)
                
                logger.info(f"✅ JSON parsed successfully after aggressive cleaning")
                return {
                    "success": True,
                    "chapter_content": parsed_json.get("chapter", ""),
                    "choices": parsed_json.get("choices", []),
                    "chapter_number": chapter_number
                }
            except:
                pass
            
            # Fallback: treat entire response as chapter content
            return {
                "success": True,
                "chapter_content": response_content,
                "choices": [],
                "error": f"Failed to parse JSON: {str(e)}"
            }
        except Exception as e:
            logger.error(f"❌ Error parsing chapter response: {e}")
            return {
                "success": True,
                "chapter_content": response_content,
                "choices": [],
                "error": f"Parsing error: {str(e)}"
            }
    
    def generate_chapter_from_json(self, json_outline: Dict[str, Any], chapter_number: int = 1) -> Dict[str, Any]:
        """Generate a chapter specifically from JSON outline data."""
        logger.info(f"📖 Generating Chapter {chapter_number} from JSON data...")
        
        # Log the JSON we received
        logger.info("📥 RECEIVED JSON OUTLINE:")
        logger.info(f"   📊 Keys: {list(json_outline.keys())}")
        logger.info(f"   📚 Chapters: {len(json_outline.get('Chapters', []))}")
        
        try:
            formatted_outline = extract_chapter_info_from_json(json_outline, chapter_number)
            
            # Generate chapter
            result = self.chain.invoke({"outline": formatted_outline, "chapter_number": chapter_number})
            
            logger.info(f"✅ Chapter {chapter_number} generated from JSON successfully!")
            logger.info(f"📊 Generated content: {len(result.content)} characters")
            
            # Parse the JSON response from LLM
            return self._parse_chapter_response(result.content.strip(), chapter_number)
            
        except Exception as e:
            error_msg = f"❌ Error generating Chapter {chapter_number} from JSON: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "chapter_content": error_msg,
                "choices": [],
                "error": str(e)
            }

