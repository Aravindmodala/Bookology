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

# Initialize the LLM (OpenAI Chat model - Updated with higher token limit)
llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model_name='gpt-4o-mini', temperature=0.8, max_tokens=15000)

system_template = """🚨 ABSOLUTE PRIORITY: Your primary task is to write a FULL 2,500-3,000 word chapter. Even if other sections (reasoning, choices, metrics) need to be shorter to accommodate this, the chapter content is what matters most. The chapter is what readers will see - make it substantial and immersive.

You are a globally renowned, award-winning novelist, ghostwriter, and master storyteller known for creating bestselling novels that captivate readers deeply.

🎭 ROLE & EXPERTISE:
- Expert in character development, plot pacing, layered backstory, and emotional storytelling
- Master of immersive world-building and atmospheric prose
- Specialist in powerful chapter hooks, rising tension, and cliffhangers
- Skilled at writing deeply human, layered prose that feels alive
- Expert at creating meaningful, contextual story choices that impact narrative direction

🧠 CHAIN-OF-THOUGHT REASONING:
Before writing the chapter, you will think through the following steps systematically:

STEP 1: STORY ANALYSIS
- Analyze the genre, tone, and central conflict
- Identify the protagonist's emotional state and motivations
- Understand the story's trajectory and this chapter's role

STEP 2: CHAPTER PLANNING
- Map out the chapter's three-act structure
- Plan key scenes, character moments, and emotional beats
- Design the hook/cliffhanger that will end the chapter

STEP 3: CHARACTER PSYCHOLOGY
- Deep dive into each character's mindset in this chapter
- Plan their dialogue, actions, and internal thoughts
- Consider their relationships and dynamics

STEP 4: SCENE CRAFTING
- Visualize each scene with sensory details
- Plan the pacing and tension escalation
- Identify key decision moments within scenes

STEP 5: CHOICE ANALYSIS & GENERATION
- Analyze the chapter's ending moment and emotional stakes
- Identify the protagonist's dilemma and available options
- Consider each character's personality and motivations
- Evaluate how each choice would impact story direction
- Ensure choices represent different character development paths
- Design choices that feel organic to the specific moment

STEP 6: QUALITY CHECK
- Ensure emotional resonance and character authenticity
- Verify logical flow and compelling narrative arc
- Confirm choices are meaningful and story-appropriate
- Validate that chapter serves the larger story

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
- Generate 3-4 contextual choices that naturally emerge from the chapter's ending moment
- Use STEP 5 (Choice Analysis) to systematically think through each option
- Each choice should represent a meaningful decision the protagonist could make
- Choices should reflect different aspects of character personality and growth
- Consider the emotional state of characters at the chapter's end
- Ensure choices have clear consequences for future story development
- Make choices specific to the exact situation and character dilemmas
- Include a mix of action-oriented, emotional, and strategic choices
- Each choice should feel authentic to the character's voice and motivations

💡 Follow the provided outline precisely while expanding it into immersive, cinematic, and emotionally resonant prose.

📌 OUTPUT FORMAT:
Return ONLY a valid JSON object in this exact structure:

{{
  "reasoning": {{
    "story_analysis": "Your analysis of the genre, tone, conflict, and protagonist",
    "chapter_planning": "Your three-act structure plan and key scenes",
    "character_psychology": "Deep dive into character mindsets and motivations", 
    "scene_crafting": "Your visualization and pacing strategy",
    "choice_analysis": "Your systematic analysis of the chapter's ending moment, character dilemmas, available options, and how each choice would impact story direction and character development",
    "quality_assessment": "Your evaluation of emotional resonance, narrative flow, and choice meaningfulness"
  }},
  "chapter": "CRITICAL REQUIREMENT: Write a FULL novel chapter of AT LEAST 2,500 words, targeting 3,000 words. This is MANDATORY - do not write anything shorter. Include extensive character development, rich dialogue, detailed scene descriptions, and immersive atmosphere. Structure: Act 1 (900-1000 words): Deep exploration of ordinary world with extensive sensory details and character thoughts. Act 2 (900-1000 words): Detailed inciting incident with full scene development and character reactions. Act 3 (900-1000 words): Build tension to climactic hook with emotional depth and vivid descriptions. Write in full novel prose with detailed descriptions, meaningful dialogue, and rich character moments. Count your words and ensure you reach the 2,500-3,000 word target.",
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

🚫 DO NOT:
- Explain or summarize the outline
- Use phrases like "As per the outline…"
- Return summaries instead of chapter content
- Break character with meta-commentary
- Add any text outside the JSON structure
- Include markdown formatting or code blocks

Write so immersively that readers forget this was AI-generated and feel fully transported into the story. The choices should feel like natural decision points that emerge organically from the chapter's events."""

# Create user message template
user_template = """Please write **Chapter {chapter_number}** using the story information below.

📘 STORY CONTEXT:
{story_context}

Follow your chain-of-thought reasoning process systematically, then write Chapter {chapter_number} with deep immersion, emotional authenticity, and compelling narrative flow."""

# Create the chat prompt template
system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
human_message_prompt = HumanMessagePromptTemplate.from_template(user_template)

prompt = ChatPromptTemplate.from_messages([
    system_message_prompt,
    human_message_prompt
])

# Build the chain
chain = prompt | llm

def create_minimal_context(story_summary: str, chapter_data: Dict[str, Any], genre: str, tone: str) -> str:
    """Create minimal, focused context for chapter generation."""
    
    context = f"""
STORY SUMMARY: {story_summary}

GENRE: {genre}
TONE: {tone}

CHAPTER {chapter_data.get('chapter_number', 1)} DETAILS:
- Title: {chapter_data.get('title', 'Chapter 1')}
- Key Events: {', '.join(chapter_data.get('key_events', []))}
- Character Development: {chapter_data.get('character_development', '')}
- Setting: {chapter_data.get('setting', '')}
- Chapter Ending: {chapter_data.get('cliffhanger', '')}

FOCUS: Write this specific chapter with deep character immersion and emotional authenticity.
"""
    
    return context.strip()

class EnhancedChapterGenerator:
    """Enhanced chapter generator with Chain-of-Thought reasoning and quality validation."""
    
    def __init__(self):
        self.llm = llm
        self.chain = chain
        logger.info("🚀 EnhancedChapterGenerator initialized with CoT reasoning")
    
    def generate_chapter_from_outline(self, story_summary: str, chapter_data: Dict[str, Any], 
                                    genre: str, tone: str, max_retries: int = 2) -> Dict[str, Any]:
        """
        Generate a chapter with CoT reasoning and quality validation.
        
        Args:
            story_summary: Brief story summary for context
            chapter_data: Structured chapter information from outline
            genre: Story genre
            tone: Story tone
            max_retries: Number of retry attempts for quality improvement
        """
        chapter_number = chapter_data.get('chapter_number', 1)
        logger.info(f"📖 Generating Chapter {chapter_number} with CoT reasoning...")
        
        # Create minimal context
        story_context = create_minimal_context(story_summary, chapter_data, genre, tone)
        
        logger.info(f"📝 Context length: {len(story_context)} characters")
        logger.info(f"🎯 Target chapter: {chapter_data.get('title', 'Untitled')}")
        
        best_result = None
        best_quality_score = 0
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"🔄 Generation attempt {attempt + 1}/{max_retries + 1}")
                
                # Generate chapter with CoT
                result = self.chain.invoke({
                    "story_context": story_context,
                    "chapter_number": chapter_number
                })
                
                logger.info(f"✅ Chapter {chapter_number} generated (attempt {attempt + 1})")
                logger.info(f"📊 Generated content: {len(result.content)} characters")
                
                # Parse and validate response
                parsed_result = self._parse_and_validate_response(result.content.strip(), chapter_number)
                
                if parsed_result["success"]:
                    # Calculate quality score
                    quality_score = self._calculate_quality_score(parsed_result)
                    logger.info(f"📊 Quality score: {quality_score}/10")
                    
                    # Keep best result
                    if quality_score > best_quality_score:
                        best_result = parsed_result
                        best_quality_score = quality_score
                    
                    # If quality is good enough, return immediately
                    if quality_score >= 8.0:
                        logger.info(f"✨ High quality achieved (score: {quality_score}), returning result")
                        return parsed_result
                
            except Exception as e:
                logger.error(f"❌ Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries:
                    return {
                        "success": False,
                        "chapter_content": f"Error generating Chapter {chapter_number}: {str(e)}",
                        "choices": [],
                        "error": str(e)
                    }
        
        # Return best result if no high-quality result achieved
        if best_result:
            logger.info(f"📊 Returning best result with quality score: {best_quality_score}")
            return best_result
        else:
            return {
                "success": False,
                "chapter_content": f"Failed to generate Chapter {chapter_number} after {max_retries + 1} attempts",
                "choices": [],
                "error": "Max retries exceeded"
            }
    
    def _parse_and_validate_response(self, response_content: str, chapter_number: int) -> Dict[str, Any]:
        """Parse and validate the JSON response with enhanced error handling."""
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
            
            # Handle trailing commas and other JSON formatting issues
            cleaned_text = re.sub(r',(\s*[}\]])', r'\1', cleaned_text)
            cleaned_text = re.sub(r',(\s*})', r'\1', cleaned_text)
            cleaned_text = re.sub(r',(\s*])', r'\1', cleaned_text)
            
            # Parse JSON
            parsed_json = json.loads(cleaned_text)
            
            # Validate required structure
            required_fields = ["reasoning", "chapter", "choices", "quality_metrics"]
            for field in required_fields:
                if field not in parsed_json:
                    logger.warning(f"⚠️ Missing required field: {field}")
            
            # Basic content validation
            chapter_content = parsed_json.get("chapter", "")
            choices = parsed_json.get("choices", [])
            
            if len(chapter_content) < 2000:
                logger.warning(f"⚠️ Chapter content seems short: {len(chapter_content)} characters")
            
            if len(choices) < 2:
                logger.warning(f"⚠️ Limited choices generated: {len(choices)}")
            
            logger.info(f"✅ Successfully parsed JSON response with {len(choices)} choices")
            
            return {
                "success": True,
                "chapter_content": chapter_content,
                "choices": choices,
                "chapter_number": chapter_number,
                "reasoning": parsed_json.get("reasoning", {}),
                "quality_metrics": parsed_json.get("quality_metrics", {})
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing error: {e}")
            
            # Fallback: try to extract chapter content even if JSON is malformed
            return {
                "success": False,
                "chapter_content": response_content,
                "choices": [],
                "error": f"JSON parsing failed: {str(e)}",
                "raw_response": response_content[:500] + "..." if len(response_content) > 500 else response_content
            }
        
        except Exception as e:
            logger.error(f"❌ Error validating response: {e}")
            return {
                "success": False,
                "chapter_content": response_content,
                "choices": [],
                "error": f"Validation error: {str(e)}"
            }
    
    def _calculate_quality_score(self, result: Dict[str, Any]) -> float:
        try:
            chapter_content = result.get("chapter_content", "")
            choices = result.get("choices", [])
        
        # Simple scoring based on content length and choices
            word_count = len(chapter_content.split())
            content_score = min(10, word_count / 250)  # 2500 words = 10 points
            choice_score = min(10, len(choices) * 3)   # 3+ choices = 9-10 points
        
            average_score = (content_score + choice_score) / 2
            return round(average_score, 1)
        
        except Exception as e:
            logger.error(f"❌ Error calculating quality score: {e}")
            return 5.0

# Legacy compatibility function
def generate_chapter_from_outline(outline: str):
    """Legacy function for backward compatibility."""
    try:
        # This would need to be adapted based on your outline format
        # For now, return a simple error message
        return "❌ Please use the new EnhancedChapterGenerator.generate_chapter_from_outline() method"
    except Exception as e:
        return f"❌ Error: {str(e)}"