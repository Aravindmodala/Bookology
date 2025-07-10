from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import os
import json
from typing import Dict, Any, List, Optional

# Load environment variables from .env
load_dotenv()

# Initialize the LLM (OpenAI Chat model - correct for GPT-4o-mini)
llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model_name='gpt-4o-mini', temperature=0.7, max_tokens=3000)

# Create system message template (role and instructions)
system_template = system_template = """
You are a world-famous novelist, creative writing coach, and master storyteller with the following expertise:

🎭 ROLE & EXPERTISE:
- Bestselling author with mastery across genres
- You think like world-renowned authors relevant to the user's genre:
    - Fantasy: J.R.R. Tolkien, Neil Gaiman, Madeline Miller
    - Sci-Fi: Isaac Asimov, Philip K. Dick, Margaret Atwood
    - Thriller: Stephen King, Gillian Flynn, Dan Brown
    - Mystery: Agatha Christie, Arthur Conan Doyle
    - Romance: Jane Austen, Nicholas Sparks
    - Historical Fiction: Hilary Mantel, Ken Follett
    - Literary Fiction: Kazuo Ishiguro, Haruki Murakami
    - Horror: Stephen King, Shirley Jackson
    - Young Adult: Suzanne Collins, Rick Riordan
    - Children's Literature: Roald Dahl, C.S. Lewis
- Expert in layered character development, world-building, and emotional resonance

📊 ANALYSIS CAPABILITIES:
- Automatically detect and classify genre from user input
- Select matching authors to emulate narrative style, tone, and pacing
- Generate genre-consistent story structures with compelling chapter progression

🎯 YOUR TASK:
Analyze the user’s story idea, determine its genre, and generate a comprehensive, structured book outline emulating the style, tone, and pacing of the world-famous authors associated with that genre.


📋 OUTPUT REQUIREMENTS:
- Return ONLY valid, parseable JSON
- No markdown formatting, explanations, or commentary
- Follow the exact JSON structure provided
- Fill all fields meaningfully with engaging, professional detail

🚫 DO NOT:
- Add text outside the JSON structure
- Include markdown code blocks
- Provide commentary or placeholders

Generate outlines with the narrative quality and emotional depth of bestselling novels aligned with the detected genre.
"""

# Create user message template (the actual request)
user_template = """Please analyze this story idea and create a comprehensive, structured book outline:

💡 STORY IDEA:
{idea}

📝 ANALYSIS STEPS:
1. Automatically detect the core genre (Fantasy, Thriller, Romance, Sci-Fi, etc.) from the idea.
2. Determine the emotional tone (Dark, hopeful, mysterious, playful, tense).
3. Select an appropriate narrative style (Cinematic, fast-paced, poetic, minimalistic).
4. Identify world-famous authors aligned with the detected genre and emulate their narrative style, tone, and pacing while creating the outline.
5. Build compelling characters and layered conflicts.
6. Structure a logical, professional chapter progression.


📄 RETURN FORMAT (JSON ONLY):
{{
  "book_title": "",
  "genre": "",
  "theme": "",
  "style": "",
  "description": "",
  "language": "English",
  "tags": [],
  "estimated_total_chapters": 0,
  "main_characters": [
    {{
      "name": "",
      "role": "",
      "description": ""
    }}
  ],
  "character_arcs_summary": "",
  "key_locations": [
    {{
      "name": "",
      "description": ""
    }}
  ],
  "conflict": "",
  "tone_keywords": [],
  "writing_guidelines": "",
  "Chapters": [
    {{
      "chapter_number": 1,
      "chapter_title": "",
      "chapter_summary": "",
      "estimated_word_count": 0,
      "cliffhanger_cta": ""
    }}
  ]
}}
"""

# Create the chat prompt template
system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
human_message_prompt = HumanMessagePromptTemplate.from_template(user_template)

prompt = ChatPromptTemplate.from_messages([
    system_message_prompt,
    human_message_prompt
])

# Build the chain
chain = prompt | llm

def parse_json_response(response_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON response from LLM, handling common formatting issues.
    """
    import re
    
    try:
        # Clean up the response
        cleaned_text = response_text.strip()
        
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
        # Remove trailing commas before closing braces and brackets
        cleaned_text = re.sub(r',(\s*[}\]])', r'\1', cleaned_text)
        
        # Remove any trailing commas at the end of objects or arrays
        cleaned_text = re.sub(r',(\s*})', r'\1', cleaned_text)
        cleaned_text = re.sub(r',(\s*])', r'\1', cleaned_text)
        
        # Parse JSON
        parsed_json = json.loads(cleaned_text)
        return parsed_json
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Raw response: {response_text[:500]}...")
        
        # Try one more time with even more aggressive cleaning
        try:
            # More aggressive comma removal
            cleaned_text = response_text.strip()
            
            # Remove markdown blocks
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            
            cleaned_text = cleaned_text.strip()
            
            # Remove ALL trailing commas more aggressively
            cleaned_text = re.sub(r',\s*([}\]])', r'\1', cleaned_text)
            
            # Try parsing again
            parsed_json = json.loads(cleaned_text)
            print(f"✅ JSON parsed successfully after aggressive cleaning")
            return parsed_json
            
        except json.JSONDecodeError as e2:
            print(f"❌ JSON parsing failed even after aggressive cleaning: {e2}")
            return None
        
    except Exception as e:
        print(f"Unexpected error parsing JSON: {e}")
        return None

def extract_metadata(outline_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract metadata from the parsed JSON outline.
    """
    metadata = {
        # Basic story info
        "title": outline_json.get("book_title", ""),
        "genre": outline_json.get("genre", ""),
        "theme": outline_json.get("theme", ""),
        "style": outline_json.get("style", ""),
        "description": outline_json.get("description", ""),
        "language": outline_json.get("language", "English"),
        
        # Structure info
        "estimated_total_chapters": outline_json.get("estimated_total_chapters", 0),
        "tags": outline_json.get("tags", []),
        "tone_keywords": outline_json.get("tone_keywords", []),
        
        # Character info
        "main_characters": outline_json.get("main_characters", []),
        "character_count": len(outline_json.get("main_characters", [])),
        "character_arcs_summary": outline_json.get("character_arcs_summary", ""),
        
        # Setting info
        "key_locations": outline_json.get("key_locations", []),
        "location_count": len(outline_json.get("key_locations", [])),
        
        # Plot info
        "conflict": outline_json.get("conflict", ""),
        "writing_guidelines": outline_json.get("writing_guidelines", ""),
        
        # Chapter info
        "Chapters": outline_json.get("Chapters", []),
        "chapter_count": len(outline_json.get("Chapters", [])),
        
        # Calculated metadata
        "total_estimated_words": sum(
            chapter.get("estimated_word_count", 0) 
            for chapter in outline_json.get("Chapters", [])
        ),
        "estimated_reading_time_hours": 0,  # Will calculate based on word count
    }
    
    # Calculate estimated reading time (250 words per minute)
    if metadata["total_estimated_words"] > 0:
        reading_time_minutes = metadata["total_estimated_words"] / 250
        metadata["estimated_reading_time_hours"] = round(reading_time_minutes / 60, 2)
    
    return metadata

def format_json_to_display_text(outline_json: Dict[str, Any]) -> str:
    """
    Convert JSON outline to a SIMPLE formatted text display for the frontend.
    Only shows: Title, Genre, Characters, and Chapter summaries (no word counts or cliffhangers).
    """
    try:
        if not outline_json:
            return "❌ No outline data available"
        
        # Create formatted text output
        formatted_text = ""
        
        # Title Section
        title = outline_json.get("book_title", "Untitled Story")
        formatted_text += f"📚 **{title}**\n\n"
        
        # Basic Info Section (simplified)
        genre = outline_json.get("genre", "Unknown")
        formatted_text += f"🎭 **Genre:** {genre}\n\n"
        
        # Description (brief)
        description = outline_json.get("description", "")
        if description:
            formatted_text += f"📖 **Story:** {description}\n\n"
        
        # Characters Section (simple list)
        main_characters = outline_json.get("main_characters", [])
        if main_characters:
            formatted_text += f"👥 **Characters:**\n"
            for i, char in enumerate(main_characters, 1):
                name = char.get("name", f"Character {i}")
                description = char.get("description", "")
                formatted_text += f"• **{name}** - {description}\n"
            formatted_text += "\n"
        
        # Chapter Breakdown (simple - only titles and summaries)
        Chapters = outline_json.get("Chapters", [])
        if Chapters:
            formatted_text += f"📑 **Chapters:**\n\n"
            
            for chapter in Chapters:
                chapter_num = chapter.get("chapter_number", "?")
                chapter_title = chapter.get("chapter_title", "Untitled Chapter")
                chapter_summary = chapter.get("chapter_summary", "No summary available")
                
                formatted_text += f"**Chapter {chapter_num}: {chapter_title}**\n"
                formatted_text += f"{chapter_summary}\n\n"
        
        return formatted_text.strip()
        
    except Exception as e:
        return f"❌ Error formatting outline: {str(e)}"

def generate_book_outline_json(idea: str) -> Dict[str, Any]:
    """
    Generate book outline and return both JSON and extracted metadata with LLM usage metrics.
    """
    try:
        # Capture LLM parameters for metrics (all dynamic from actual LLM object)
        llm_temperature = llm.temperature
        llm_model = llm.model_name  # Get actual model name directly
        llm_max_tokens = llm.max_tokens
        
        # Calculate input metrics
        input_text = prompt.format(idea=idea)
        input_word_count = len(input_text.split())
        
        # Generate the outline
        result = chain.invoke({"idea": idea})
        raw_response = result.content.strip()
        
        # Calculate output metrics
        output_word_count = len(raw_response.split())
        total_word_count = input_word_count + output_word_count
        
        # Estimate token count (rough approximation: 1 token ≈ 0.75 words)
        estimated_input_tokens = int(input_word_count * 1.33)
        estimated_output_tokens = int(output_word_count * 1.33)
        estimated_total_tokens = estimated_input_tokens + estimated_output_tokens
        
        # Parse JSON
        outline_json = parse_json_response(raw_response)
        
        if not outline_json:
            return {
                "success": False,
                "error": "Failed to parse JSON response",
                "raw_response": raw_response,
                "outline_json": None,
                "metadata": {},
                "formatted_text": "❌ Failed to generate outline",
                # Include usage metrics even on failure
                "usage_metrics": {
                    "temperature_used": llm_temperature,
                    "model_used": llm_model,
                    "max_tokens": llm_max_tokens,
                    "input_word_count": input_word_count,
                    "output_word_count": output_word_count,
                    "total_word_count": total_word_count,
                    "estimated_input_tokens": estimated_input_tokens,
                    "estimated_output_tokens": estimated_output_tokens,
                    "estimated_total_tokens": estimated_total_tokens
                }
            }
        
        # Extract metadata
        metadata = extract_metadata(outline_json)
        
        # Create formatted text for frontend display
        formatted_text = format_json_to_display_text(outline_json)
        
        return {
            "success": True,
            "outline_json": outline_json,
            "metadata": metadata,
            "formatted_text": formatted_text,  # New: formatted text for frontend
            "raw_response": raw_response,
            # LLM Usage Metrics for database storage
            "usage_metrics": {
                "temperature_used": llm_temperature,
                "model_used": llm_model,
                "max_tokens": llm_max_tokens,
                "input_word_count": input_word_count,
                "output_word_count": output_word_count,
                "total_word_count": total_word_count,
                "estimated_input_tokens": estimated_input_tokens,
                "estimated_output_tokens": estimated_output_tokens,
                "estimated_total_tokens": estimated_total_tokens,
                # Calculated story metrics
                "story_estimated_words": metadata.get("total_estimated_words", 0),
                "story_Chapters_count": len(outline_json.get("Chapters", [])),
                "story_characters_count": len(outline_json.get("main_characters", [])),
                "story_locations_count": len(outline_json.get("key_locations", []))
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "raw_response": "",
            "outline_json": None,
            "metadata": {},
            "formatted_text": f"❌ Error generating outline: {str(e)}",
            "usage_metrics": {
                "temperature_used": llm.temperature,
                "model_used": llm.model_name,
                "max_tokens": llm.max_tokens,
                "error": str(e)
            }
        }

def generate_book_outline(idea: str) -> str:
    """
    Backward compatibility function - returns formatted text.
    """
    try:
        result = generate_book_outline_json(idea)
        
        if not result["success"]:
            return f"❌ Error generating book outline: {result['error']}"
        
        # Return the formatted text for display
        return result["formatted_text"]
        
    except Exception as e:
        return f"❌ Error generating book outline: {str(e)}"

# Entry point