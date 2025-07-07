from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import os
import json
from typing import Dict, Any, List, Optional

# Load environment variables from .env
load_dotenv()

# Initialize the LLM (OpenAI model)
llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), model_name='gpt-4o-mini', temperature=0.7, max_tokens=3000)

# Create a prompt template
prompt = PromptTemplate(
    input_variables=["idea"],
    template="""You are a professional book author, creative writing coach, and world-class storyteller who deeply understands user ideas and adapts to their emotional tone, genre, and desired atmosphere.

Your task is to analyze the user's idea carefully and **adapt your output to match its genre, emotion, pacing, and narrative needs**.

**GOALS:**
✅ Think like a professional book author (or a famous author if specified).  
✅ Deeply understand the **emotional DNA** of the user's idea.  
✅ Match **tone, style, and genre** aligned with the user's intention.  
✅ Build a compelling, structured book outline to guide seamless chapter generation.

---

**INPUT (User Idea):**
{idea}

---

**ANALYZE:**
- What is the core genre? (Thriller, Fantasy, Romance, Sci-Fi, etc.)
- What is the emotional tone? (Dark, hopeful, mysterious, playful, tense)
- What narrative style suits the idea? (Cinematic, fast-paced, poetic, minimalistic)

---

**OUTPUT:**
Return **only valid, parseable JSON** for Bookology, without additional commentary.

**JSON Structure:**
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
  "chapters": [
    {{
      "chapter_number": 1,
      "chapter_title": "",
      "chapter_summary": "",
      "estimated_word_count": 0,
      "cliffhanger_cta": ""
    }}
  ]
}}

IMPORTANT: Output ONLY the JSON, no markdown formatting, no extra text, no explanations."""
)

# Build the chain
chain = prompt | llm

def parse_json_response(response_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON response from LLM, handling common formatting issues.
    """
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
        
        # Parse JSON
        parsed_json = json.loads(cleaned_text)
        return parsed_json
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Raw response: {response_text}")
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
        "chapters": outline_json.get("chapters", []),
        "chapter_count": len(outline_json.get("chapters", [])),
        
        # Calculated metadata
        "total_estimated_words": sum(
            chapter.get("estimated_word_count", 0) 
            for chapter in outline_json.get("chapters", [])
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
    Convert JSON outline to a nicely formatted text display for the frontend.
    Uses static field labels with dynamic JSON data.
    """
    try:
        if not outline_json:
            return "❌ No outline data available"
        
        # Create formatted text output
        formatted_text = ""
        
        # Title Section
        title = outline_json.get("book_title", "Untitled Story")
        formatted_text += f"📚 **TITLE:** {title}\n\n"
        
        # Basic Info Section
        genre = outline_json.get("genre", "Unknown")
        theme = outline_json.get("theme", "Not specified")
        style = outline_json.get("style", "Not specified")
        language = outline_json.get("language", "English")
        
        formatted_text += f"🎭 **GENRE:** {genre}\n"
        formatted_text += f"🎯 **THEME:** {theme}\n"
        formatted_text += f"✍️ **STYLE:** {style}\n"
        formatted_text += f"🌍 **LANGUAGE:** {language}\n\n"
        
        # Description
        description = outline_json.get("description", "")
        if description:
            formatted_text += f"📖 **DESCRIPTION:**\n{description}\n\n"
        
        # Story Stats
        estimated_chapters = outline_json.get("estimated_total_chapters", 0)
        tags = outline_json.get("tags", [])
        tone_keywords = outline_json.get("tone_keywords", [])
        
        formatted_text += f"📊 **STORY STATISTICS:**\n"
        formatted_text += f"   • Total Chapters: {estimated_chapters}\n"
        if tags:
            formatted_text += f"   • Tags: {', '.join(tags)}\n"
        if tone_keywords:
            formatted_text += f"   • Tone: {', '.join(tone_keywords)}\n"
        formatted_text += "\n"
        
        # Characters Section
        main_characters = outline_json.get("main_characters", [])
        if main_characters:
            formatted_text += f"👥 **MAIN CHARACTERS:**\n"
            for i, char in enumerate(main_characters, 1):
                name = char.get("name", f"Character {i}")
                role = char.get("role", "Unknown role")
                description = char.get("description", "No description")
                formatted_text += f"   {i}. **{name}** ({role})\n"
                formatted_text += f"      {description}\n\n"
        
        # Locations Section
        key_locations = outline_json.get("key_locations", [])
        if key_locations:
            formatted_text += f"🗺️ **KEY LOCATIONS:**\n"
            for i, location in enumerate(key_locations, 1):
                name = location.get("name", f"Location {i}")
                description = location.get("description", "No description")
                formatted_text += f"   {i}. **{name}**\n"
                formatted_text += f"      {description}\n\n"
        
        # Conflict/Plot
        conflict = outline_json.get("conflict", "")
        if conflict:
            formatted_text += f"⚔️ **CENTRAL CONFLICT:**\n{conflict}\n\n"
        
        # Chapter Breakdown
        chapters = outline_json.get("chapters", [])
        if chapters:
            formatted_text += f"📑 **CHAPTER BREAKDOWN:**\n\n"
            total_words = 0
            
            for chapter in chapters:
                chapter_num = chapter.get("chapter_number", "?")
                chapter_title = chapter.get("chapter_title", "Untitled Chapter")
                chapter_summary = chapter.get("chapter_summary", "No summary available")
                estimated_words = chapter.get("estimated_word_count", 0)
                cliffhanger = chapter.get("cliffhanger_cta", "")
                
                formatted_text += f"**Chapter {chapter_num}: {chapter_title}**\n"
                formatted_text += f"📝 Summary: {chapter_summary}\n"
                if estimated_words > 0:
                    formatted_text += f"📊 Estimated Words: {estimated_words:,}\n"
                    total_words += estimated_words
                if cliffhanger:
                    formatted_text += f"🎬 Cliffhanger: {cliffhanger}\n"
                formatted_text += "\n"
            
            if total_words > 0:
                reading_time = max(1, total_words // 250)  # 250 words per minute
                formatted_text += f"📈 **TOTAL ESTIMATED WORDS:** {total_words:,}\n"
                formatted_text += f"⏱️ **ESTIMATED READING TIME:** ~{reading_time} minutes\n\n"
        
        # Writing Guidelines
        writing_guidelines = outline_json.get("writing_guidelines", "")
        if writing_guidelines:
            formatted_text += f"📋 **WRITING GUIDELINES:**\n{writing_guidelines}\n\n"
        
        # Character Arcs Summary
        character_arcs = outline_json.get("character_arcs_summary", "")
        if character_arcs:
            formatted_text += f"🎭 **CHARACTER DEVELOPMENT:**\n{character_arcs}\n\n"
        
        formatted_text += "✨ **Ready to begin writing your story!** ✨"
        
        return formatted_text
        
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
        raw_response = result.strip()
        
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
                "story_chapters_count": len(outline_json.get("chapters", [])),
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