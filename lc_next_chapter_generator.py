from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import os
import logging
from typing import List, Optional, Dict, Any
import json # Added for JSON parsing

# Import the new hierarchical summarization module
from hierarchial_summarizer import get_smart_context_for_chapter, hierarchical_summarizer

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the LLM for next chapter generation with optimized settings (using ChatOpenAI for GPT-4o-mini)
llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model_name='gpt-4o-mini', temperature=0.7, max_tokens=6000)

# Create a more concise prompt template for generating subsequent Chapters
next_chapter_prompt = PromptTemplate(
    input_variables=["story_title", "story_outline", "previous_summaries", "chapter_number", "user_choice"],
    template="""You are a globally renowned, award-winning novelist, ghostwriter, and master storyteller known for creating bestselling novels that captivate readers deeply.

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

🎯 CHAPTER {chapter_number} REQUIREMENTS:
- Continue seamlessly from the previous chapter events and the user's choice
- Maintain character consistency and plot continuity with all previous Chapters
- Show the direct consequences and results of the user's chosen path
- Advance the story meaningfully while building tension
- Include compelling dialogue and rich sensory descriptions
- End with a compelling hook that naturally leads to meaningful choices

🎯 CHOICE GENERATION REQUIREMENTS:
- Generate 3-4 contextual choices that naturally emerge from this chapter's events
- Each choice should represent a meaningful decision the protagonist could make
- Choices should feel organic to the story and character motivations
- Include a mix of action-oriented, emotional, and strategic choices
- Each choice should have clear story implications and character development potential
- Choices should be specific enough to guide the next chapter's direction

STORY CONTEXT:
Title: "{story_title}"

STORY OUTLINE:
{story_outline}

PREVIOUS Chapters SUMMARY:
{previous_summaries}

USER'S CHOICE FOR THIS CHAPTER:
{user_choice}

📌 OUTPUT FORMAT:
Return ONLY a valid JSON object in this exact structure:

{{
  "chapter": "The full chapter content here as immersive, novel-quality prose that continues from the user's choice in 3000 words, strictly 3000 words",
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
    }},
    {{
      "id": "choice_4",
      "title": "Brief choice title (3-6 words)", 
      "description": "Detailed description of what this choice involves and its immediate implications",
      "story_impact": "How this choice would affect the story direction and character development",
      "choice_type": "action/emotional/strategic/dialogue"
    }}
  ]
}}

🚫 DO NOT:
- Explain or summarize the outline or previous Chapters
- Use phrases like "As per the outline…" or "Based on the user's choice…"
- Return summaries instead of chapter content
- Break character with meta-commentary
- Add any text outside the JSON structure
- Include markdown formatting or code blocks

Write Chapter {chapter_number} that flows naturally from the user's choice, showing its consequences while maintaining the immersive storytelling quality. The choices should feel like natural decision points that emerge organically from the chapter's climactic moment."""
)

# Build the chain for next chapter generation
next_chapter_chain = next_chapter_prompt | llm

class NextChapterGenerator:
    """Specialized generator for creating subsequent Chapters (Chapter 2+) with story continuity."""
    
    def __init__(self):
        self.llm = llm
        self.chain = next_chapter_chain
        logger.info("🚀 NextChapterGenerator initialized for subsequent chapter generation")
    
    def _truncate_for_token_limit(self, story_outline: str, previous_summaries: str) -> tuple[str, str]:
        """
        Truncate inputs to fit within token limits.
        Rough estimate: 1 token ≈ 4 characters for English text.
        Target: Keep total input under 1500 tokens to leave room for prompt + output.
        """
        MAX_INPUT_CHARS = 6000  # ~1500 tokens
        
        # If combined length is acceptable, return as-is
        total_chars = len(story_outline) + len(previous_summaries)
        if total_chars <= MAX_INPUT_CHARS:
            return story_outline, previous_summaries
        
        logger.warning(f"⚠️ Input too long ({total_chars} chars), truncating to fit token limits")
        
        # Prioritize previous summaries over outline for continuity
        if len(previous_summaries) > MAX_INPUT_CHARS * 0.7:  # 70% for summaries
            max_summary_chars = int(MAX_INPUT_CHARS * 0.7)
            previous_summaries = previous_summaries[:max_summary_chars] + "...[truncated]"
            logger.info(f"📝 Truncated previous summaries to {len(previous_summaries)} chars")
        
        remaining_chars = MAX_INPUT_CHARS - len(previous_summaries)
        if len(story_outline) > remaining_chars:
            story_outline = story_outline[:remaining_chars] + "...[truncated]"
            logger.info(f"📋 Truncated story outline to {len(story_outline)} chars")
        
        return story_outline, previous_summaries

    def generate_next_chapter(
        self, 
        story_title: str,
        story_outline: str, 
        previous_chapter_summaries: List[str], 
        chapter_number: int,
        user_choice: str = ""
    ) -> Dict[str, Any]:
        """
        Generate the next chapter in a story using hierarchical summarization for optimal context.
        
        Args:
            story_title: The title of the story
            story_outline: The original story outline
            previous_chapter_summaries: List of summaries from all previous Chapters
            chapter_number: The chapter number to generate
            user_choice: The user's selected choice from the previous chapter
            
        Returns:
            Dict containing chapter content, choices, and token usage metrics
        """
        logger.info(f"📖 Generating Chapter {chapter_number} for '{story_title}' using HIERARCHICAL SUMMARIZATION")
        logger.info(f"📚 Available chapter summaries: {len(previous_chapter_summaries)}")
        logger.info(f"🎯 User choice provided: {'Yes' if user_choice else 'No'}")
        
        try:
            # Convert list of summaries to dict format expected by hierarchical summarizer
            all_chapter_summaries = {}
            for i, summary in enumerate(previous_chapter_summaries, 1):
                all_chapter_summaries[i] = summary
            
            logger.info(f"📊 Chapter summaries converted: {list(all_chapter_summaries.keys())}")
            
            # Use hierarchical summarization to get smart context
            smart_context = get_smart_context_for_chapter(
                chapter_number=chapter_number,
                all_chapter_summaries=all_chapter_summaries,
                story_outline=story_outline,
                max_chars=6000  # Conservative limit to leave room for chapter generation
            )
            
            logger.info(f"🧠 Smart context generated: {len(smart_context)} characters")
            logger.info(f"📝 Smart context preview: {smart_context[:300]}...")
            
            # Calculate input metrics for token tracking
            prompt_input = self.chain.first.format(
                story_title=story_title,
                story_outline=story_outline,
                previous_summaries=smart_context,
                chapter_number=chapter_number,
                user_choice=user_choice or "No specific choice - continue story naturally"
            )
            
            # Calculate input tokens (rough estimate: 1 token ≈ 0.75 words)
            input_word_count = len(prompt_input.split())
            estimated_input_tokens = int(input_word_count * 1.33)

            # Generate the chapter using the smart context
            logger.info(f"📝 LLM Input: Title='{story_title}', Previous={len(previous_chapter_summaries)} chapters, Choice='{user_choice or 'continue naturally'}'")
            
            result = self.chain.invoke({
                "story_title": story_title,
                "story_outline": story_outline,
                "previous_summaries": smart_context,
                "chapter_number": chapter_number,
                "user_choice": user_choice or "No specific choice - continue story naturally"
            })
            
            generated_response = result.content.strip()
            
            # Parse the JSON response from LLM
            parsed_result = self._parse_chapter_response(generated_response, chapter_number)
            
            if not parsed_result.get("success", False):
                # If parsing failed, treat as legacy text response
                chapter_content = generated_response
                choices = []
            else:
                chapter_content = parsed_result.get("chapter_content", "")
                choices = parsed_result.get("choices", [])
            
            # Calculate output metrics for token tracking
            output_word_count = len(chapter_content.split())
            estimated_output_tokens = int(output_word_count * 1.33)
            estimated_total_tokens = estimated_input_tokens + estimated_output_tokens
            
            # Get LLM parameters
            temperature_used = self.llm.temperature
            model_used = self.llm.model_name
            
            logger.info(f"✅ Chapter {chapter_number} generated successfully!")
            logger.info(f"📊 Generated: {len(chapter_content)} chars, {output_word_count} words, {len(choices)} choices")
            
            # Return both chapter content, choices, and token metrics
            return {
                "chapter_content": chapter_content,
                "choices": choices,
                "token_metrics": {
                    "token_count_prompt": estimated_input_tokens,
                    "token_count_completion": estimated_output_tokens,
                    "token_count_total": estimated_total_tokens,
                    "temperature_used": temperature_used,
                    "model_used": model_used,
                    "input_word_count": input_word_count,
                    "output_word_count": output_word_count
                },
                "success": True
            }
            
        except Exception as e:
            error_msg = f"❌ Error generating Chapter {chapter_number}: {str(e)}"
            logger.error(error_msg)
            logger.error(f"🔍 Error details: {type(e).__name__}: {str(e)}")
            return {
                "chapter_content": error_msg,
                "choices": [],
                "token_metrics": {
                    "token_count_prompt": 0,
                    "token_count_completion": 0,
                    "token_count_total": 0,
                    "temperature_used": self.llm.temperature,
                    "model_used": self.llm.model_name,
                    "error": str(e)
                },
                "success": False
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
                "success": False,
                "chapter_content": response_content,
                "choices": [],
                "error": f"Failed to parse JSON: {str(e)}"
            }
        except Exception as e:
            logger.error(f"❌ Error parsing chapter response: {e}")
            return {
                "success": False,
                "chapter_content": response_content,
                "choices": [],
                "error": f"Parsing error: {str(e)}"
            }
    
    def _format_previous_summaries(self, summaries: List[str]) -> str:
        """Format previous chapter summaries into a concise narrative for the LLM."""
        if not summaries:
            return "No previous Chapters."
        
        # More concise formatting to save tokens
        formatted = ""
        for i, summary in enumerate(summaries, 1):
            # Limit each summary to avoid token bloat
            truncated_summary = summary.strip()
            if len(truncated_summary) > 200:  # Limit individual summaries
                truncated_summary = truncated_summary[:200] + "..."
            formatted += f"Ch{i}: {truncated_summary}\n"
        
        return formatted.strip()

# Create global instance for backward compatibility
next_chapter_generator = NextChapterGenerator()

def generate_next_chapter(
    story_title: str,
    story_outline: str, 
    previous_chapter_summaries: List[str], 
    chapter_number: int,
    user_choice: str = ""
) -> Dict[str, Any]:
    """
    Convenience function for generating next Chapters.
    
    Args:
        story_title: The title of the story
        story_outline: The original story outline
        previous_chapter_summaries: List of summaries from all previous Chapters
        chapter_number: The chapter number to generate
        user_choice: The user's selected choice from the previous chapter
        
    Returns:
        Dict containing chapter content and token usage metrics
    """
    return next_chapter_generator.generate_next_chapter(
        story_title=story_title,
        story_outline=story_outline,
        previous_chapter_summaries=previous_chapter_summaries,
        chapter_number=chapter_number,
        user_choice=user_choice
    ) 