from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
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

# Initialize the LLM (OpenAI model)
llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), temperature=0.7, max_tokens=2000)

# Create a prompt template for generating Chapter 1 from an outline
prompt = PromptTemplate(
    input_variables=["outline"],
    template="""
You are a globally renowned novelist, ghostwriter, and master storyteller.

Your task is to take the following fully expanded story outline and write **one emotionally immersive, professionally written Chapter 1** of a novel that feels like it belongs on a bestselling shelf.

---

📘 STORY OUTLINE:
{outline}

---

🎯 OBJECTIVE:
Write **Chapter 1** of this novel. Follow the chapter description and structure given in the outline. The chapter must:

1. Begin with an emotionally gripping or atmospheric hook
2. Introduce or re-establish the main characters with rich depth — not just facts, but emotions, inner flaws, secrets, or memories
3. Build tension, emotion, or mystery through:
   - Dialogue
   - Internal monologue
   - Descriptive world-building (sights, sounds, sensations)
   - Character conflict or decisions
4. Progress the story in a meaningful way (emotionally or plot-wise)
5. End on a compelling cliffhanger that makes the reader **desperate for the next chapter** — like a reveal, betrayal, twist, or shocking action

---

✍️ WRITING STYLE:
- Format: **Novel-style prose**, not a script or bullet points
- Voice: Write as if this was penned by a masterful human author
- Perspective: Use third-person limited (or first-person if the outline suggests it)
- Language: Vivid, dramatic, and emotionally expressive — avoid robotic tone
- Make characters feel alive — full of contradictions, depth, and vulnerability
- Build the **first few paragraphs of Chapter 1** to make readers feel *this is a real book*, not AI output

---

📌 START FORMAT:
**Chapter 1: [Use the Chapter Title from the outline]**

(Then begin the chapter)

---

DO NOT:
- Explain the outline
- Return summaries
- Repeat any outline section
- Say "As per the outline..."

Just write the actual chapter content. Make it so immersive that the reader forgets it was written by a machine.
"""
)

# Build the chain
chain = prompt | llm

def generate_chapter_from_outline(outline: str):
    """Legacy function for backward compatibility."""
    try:
        result = chain.invoke({"outline": outline})
        return result.strip()
    except Exception as e:
        return f"❌ Error generating Chapter 1: {str(e)}"

def extract_chapter_info_from_json(json_data: Dict[str, Any], chapter_number: int = 1) -> str:
    """Extract relevant chapter and story information from JSON outline."""
    logger.info(f"🔍 Extracting Chapter {chapter_number} info from JSON outline...")
    
    # Log the full JSON for debugging
    logger.info("📄 FULL JSON OUTLINE:")
    logger.info("=" * 80)
    logger.info(json.dumps(json_data, indent=2, ensure_ascii=False))
    logger.info("=" * 80)
    
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
    chapters = json_data.get("chapters", [])
    target_chapter = None
    
    for chapter in chapters:
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
    
    def generate_chapter(self, outline: str, chapter_number: int = 1) -> str:
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
                logger.info("-" * 50)
                logger.info(formatted_outline[:500] + "..." if len(formatted_outline) > 500 else formatted_outline)
                logger.info("-" * 50)
                
                # Generate chapter
                result = self.chain.invoke({"outline": formatted_outline})
                
                logger.info(f"✅ Chapter {chapter_number} generated successfully!")
                logger.info(f"📊 Generated content length: {len(result)} characters")
                
                return result.strip()
                
            except json.JSONDecodeError:
                # If not JSON, treat as regular text outline
                logger.info("📄 Input detected as text outline (not JSON)")
                
                logger.info("🤖 SENDING TO LLM:")
                logger.info("-" * 50)
                logger.info(outline[:500] + "..." if len(outline) > 500 else outline)
                logger.info("-" * 50)
                
                result = self.chain.invoke({"outline": outline})
                
                logger.info(f"✅ Chapter {chapter_number} generated successfully!")
                logger.info(f"📊 Generated content length: {len(result)} characters")
                
                return result.strip()
                
        except Exception as e:
            error_msg = f"❌ Error generating Chapter {chapter_number}: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def generate_chapter_from_json(self, json_outline: Dict[str, Any], chapter_number: int = 1) -> str:
        """Generate a chapter specifically from JSON outline data."""
        logger.info(f"📖 Generating Chapter {chapter_number} from JSON data...")
        
        # Log the JSON we received
        logger.info("📥 RECEIVED JSON OUTLINE:")
        logger.info("=" * 80)
        logger.info(json.dumps(json_outline, indent=2, ensure_ascii=False))
        logger.info("=" * 80)
        
        try:
            formatted_outline = extract_chapter_info_from_json(json_outline, chapter_number)
            
            # Generate chapter
            result = self.chain.invoke({"outline": formatted_outline})
            
            logger.info(f"✅ Chapter {chapter_number} generated from JSON successfully!")
            logger.info(f"📊 Generated content length: {len(result)} characters")
            
            return result.strip()
            
        except Exception as e:
            error_msg = f"❌ Error generating Chapter {chapter_number} from JSON: {str(e)}"
            logger.error(error_msg)
            return error_msg

