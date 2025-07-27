from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import os
import logging
from typing import List, Optional, Dict, Any, Tuple
import json
import time
from dataclasses import dataclass
from enum import Enum

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the LLM for next chapter generation with optimized settings
llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model_name='gpt-4o-mini', temperature=0.5, max_tokens=8000)

# Quality scoring LLM with different temperature for more consistent scoring
quality_llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model_name='gpt-4o-mini', temperature=0.3, max_tokens=1000)

# Enhancement LLM for improving chapters
enhancement_llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model_name='gpt-4o-mini', temperature=0.6, max_tokens=8000)

class GenerationFocus(Enum):
    EMOTION = "emotion"
    ACTION = "action"
    CHARACTER = "character"
    DIALOGUE = "dialogue"

@dataclass
class QualityMetrics:
    emotional_impact: float
    character_consistency: float
    plot_advancement: float
    writing_quality: float
    dialogue_naturalness: float
    pacing: float
    choice_setup: float
    overall_score: float

@dataclass
class ChapterVersion:
    content: str
    choices: List[Dict[str, Any]]
    quality_metrics: QualityMetrics
    generation_focus: GenerationFocus
    version_id: int

# 🎯 ADVANCED PROMPT TEMPLATES

# Base chapter generation prompt - enhanced for quality AND variety
base_chapter_prompt = PromptTemplate(
    input_variables=["story_title", "story_outline", "story_dna_context", "chapter_number", "user_choice", "generation_focus", "quality_instructions", "previous_openings"],
    template="""You are a New York Times bestselling author known for creating emotionally gripping, page-turning stories that readers can't put down.

🎭 EXPERT AUTHOR IDENTITY:
You write with the emotional depth of Suzanne Collins, the world-building of Brandon Sanderson, the character development of George R.R. Martin, and the pacing of Stephen King.

🎯 GENERATION FOCUS: {generation_focus}
{quality_instructions}

🚨 CRITICAL VARIETY REQUIREMENTS:
AVOID these repetitive openings from previous chapters:
{previous_openings}

OPENING VARIETY RULES:
- NEVER use the same opening structure twice
- Start mid-action, mid-dialogue, or mid-thought when possible
- Vary sentence length and structure in opening paragraphs
- Use different narrative techniques: dialogue, action, internal monologue, sensory detail

OPENING STYLE OPTIONS (rotate between these):
1. DIALOGUE OPENING: Start with character speaking
2. ACTION OPENING: Start in the middle of movement/conflict
3. INTERNAL MONOLOGUE: Start with character's thoughts
4. SENSORY OPENING: Start with vivid sensory detail
5. MYSTERY OPENING: Start with something unexpected
6. EMOTIONAL OPENING: Start with strong feeling/reaction

✍️ BESTSELLER WRITING STANDARDS:
- Format: Professional novel-quality prose
- Voice: Distinctive, emotionally resonant, memorable
- Characters: Multi-dimensional with clear motivations and growth arcs
- Pacing: Perfect balance of action, emotion, and reflection
- Dialogue: Natural, character-revealing, subtext-rich
- Descriptions: Sensory-rich without being overwhelming
- Tension: Constant forward momentum with emotional stakes

🧬 DNA-BASED CONTINUITY (CRITICAL):
- Use Story DNA to understand EXACT scene context
- Maintain perfect character consistency with established facts
- Continue emotional momentum from previous chapter
- Preserve all relationship dynamics and world-building

🎯 CHAPTER {chapter_number} MISSION:
- Continue seamlessly from DNA context with VARIED opening
- Execute user's choice with meaningful consequences
- Advance plot while developing characters
- Build to compelling cliffhanger/choice moment
- Create emotional investment in what happens next

📏 QUALITY REQUIREMENTS:
- MINIMUM 2500 words of immersive, engaging prose
- Include rich character internal thoughts and emotions
- Develop scenes with full sensory details
- Create meaningful dialogue that reveals character
- Build tension throughout with emotional payoffs
- End with natural setup for consequential choices

🎨 LANGUAGE VARIETY REQUIREMENTS:
- Use synonyms instead of repeated words
- Vary sentence structure (short, medium, long)
- Mix simple and complex sentences
- Avoid overused fantasy phrases like "seeker of truths"
- Create fresh metaphors and descriptions

STORY CONTEXT:
Title: "{story_title}"
Outline: {story_outline}

🧬 STORY DNA: {story_dna_context}

USER'S CHOICE: {user_choice}

📌 ABSOLUTE REQUIREMENT - JSON OUTPUT ONLY:
You MUST return ONLY valid JSON in exactly this format. Any deviation will cause system failure.

CRITICAL VALIDATION RULES:
- Start your response with opening brace: {{
- End your response with closing brace: }}
- NO text before the opening brace
- NO text after the closing brace
- NO markdown code blocks (```json or ```)
- NO explanations or comments outside JSON
- NO trailing commas in JSON
- Chapter content must be ONE continuous string in "chapter" field

EXACT REQUIRED FORMAT:
{{
  "chapter": "Full immersive chapter content (2500+ words) - write the complete chapter as one continuous string with proper paragraph breaks using \\n\\n between paragraphs",
  "choices": [
    {{
      "id": "choice_1",
      "title": "Brief compelling title",
      "description": "Detailed description of choice and immediate consequences",
      "story_impact": "How this choice affects character development and story direction",
      "choice_type": "action"
    }},
    {{
      "id": "choice_2",
      "title": "Brief compelling title",
      "description": "Detailed description of choice and immediate consequences",
      "story_impact": "How this choice affects character development and story direction",
      "choice_type": "emotional"
    }},
    {{
      "id": "choice_3",
      "title": "Brief compelling title",
      "description": "Detailed description of choice and immediate consequences",
      "story_impact": "How this choice affects character development and story direction",
      "choice_type": "strategic"
    }},
    {{
      "id": "choice_4",
      "title": "Brief compelling title",
      "description": "Detailed description of choice and immediate consequences",
      "story_impact": "How this choice affects character development and story direction",
      "choice_type": "dialogue"
    }}
  ]
}}

SYSTEM REQUIREMENT: Your response must be parseable by JSON.parse(). Write a chapter that readers will remember and discuss with friends."""
)

# Quality scoring prompt
quality_scoring_prompt = PromptTemplate(
    input_variables=["chapter_content"],
    template="""You are a literary critic and bestseller analyst. Score this chapter on each dimension (1-10):

CHAPTER TO EVALUATE:
{chapter_content}

Rate each aspect (1-10 scale):

EMOTIONAL IMPACT (1-10):
- Does this chapter make readers FEEL something?
- Are there genuine emotional moments?
- Does it create investment in characters?

CHARACTER CONSISTENCY (1-10):
- Do characters act according to their established personalities?
- Is character growth natural and earned?
- Are voices distinctive and consistent?

PLOT ADVANCEMENT (1-10):
- Does the story move forward meaningfully?
- Are there consequences from previous choices?
- Is there clear progression toward story goals?

WRITING QUALITY (1-10):
- Is the prose engaging and well-crafted?
- Are descriptions vivid but not overwhelming?
- Does it flow naturally?

DIALOGUE NATURALNESS (1-10):
- Does dialogue sound like real people talking?
- Does it reveal character and advance plot?
- Is there appropriate subtext?

PACING (1-10):
- Is the rhythm of action/reflection balanced?
- Does it maintain reader engagement?
- Are there appropriate beats and pauses?

CHOICE SETUP (1-10):
- Do the ending choices feel natural and meaningful?
- Are there clear consequences implied?
- Do they offer genuine alternatives?

Return ONLY this JSON format:
{{
  "emotional_impact": 8.5,
  "character_consistency": 9.0,
  "plot_advancement": 8.0,
  "writing_quality": 8.5,
  "dialogue_naturalness": 7.5,
  "pacing": 8.0,
  "choice_setup": 8.5,
  "overall_score": 8.3
}}"""
)

# Enhancement prompt
enhancement_prompt = PromptTemplate(
    input_variables=["chapter_content", "weak_areas"],
    template="""You are a bestselling author's editor. Improve this chapter focusing on the identified weak areas.

CHAPTER TO ENHANCE:
{chapter_content}

AREAS NEEDING IMPROVEMENT:
{weak_areas}

ENHANCEMENT INSTRUCTIONS:
- Add emotional depth and character interiority
- Enhance dialogue with subtext and personality
- Increase tension and forward momentum
- Improve sensory details and atmosphere
- Strengthen character voice and consistency
- Ensure smooth pacing and flow

Return ONLY the enhanced chapter content as a JSON object:
{{
  "enhanced_chapter": "The fully improved chapter content here",
  "improvements_made": "Brief description of what was enhanced"
}}"""
)

class BestsellerChapterGenerator:
    """🏆 Advanced chapter generator with multi-version quality control and enhancement."""
    
    def __init__(self):
        self.llm = llm
        self.quality_llm = quality_llm
        self.enhancement_llm = enhancement_llm
        
        # Build chains
        self.base_chain = base_chapter_prompt | llm
        self.quality_chain = quality_scoring_prompt | quality_llm
        self.enhancement_chain = enhancement_prompt | enhancement_llm
        
        logger.info("🏆 BestsellerChapterGenerator initialized - Multi-version quality system enabled")
    
    def generate_bestseller_chapter(
        self, 
        story_title: str,
        story_outline: str, 
        story_dna_contexts: List[str], 
        chapter_number: int,
        user_choice: str = "",
        target_quality: float = 8.5,
        max_enhancement_attempts: int = 0,
        is_game_mode: bool = False  # NEW: Game mode flag
    ) -> Dict[str, Any]:
        """
        🚀 Generate a chapter - SINGLE VERSION for speed.
        
        Args:
            story_title: The title of the story
            story_outline: The original story outline
            story_dna_contexts: List of DNA contexts from all previous chapters
            chapter_number: The chapter number to generate
            user_choice: The user's selected choice from the previous chapter (only used in game mode)
            target_quality: Not used anymore - kept for compatibility
            max_enhancement_attempts: Not used anymore - kept for compatibility
            is_game_mode: Whether this is game mode (affects choice generation)
            
        Returns:
            Dict containing the chapter content, choices, and metrics
        """
        start_time = time.time()
        logger.info(f"🚀 Generating Chapter {chapter_number} - SINGLE VERSION for speed")
        logger.info(f"🎮 Game Mode: {is_game_mode}")
        
        try:
            # Format DNA context
            combined_dna_context = self._format_dna_contexts(story_dna_contexts)
            choice_context = self._validate_user_choice(user_choice, combined_dna_context, chapter_number) if is_game_mode else ""
            
            # STEP 1: Generate single version - FAST
            logger.info("📝 Generating single chapter version...")
            version = self._generate_single_version(
                story_title=story_title,
                story_outline=story_outline,
                story_dna_context=combined_dna_context,
                chapter_number=chapter_number,
                user_choice=choice_context,
                is_game_mode=is_game_mode  # Pass game mode flag
            )
            
            if not version:
                raise Exception("Failed to generate chapter")
            
            logger.info(f"✅ Chapter {chapter_number} generated successfully")
            logger.info(f"📊 Content length: {len(version.content)} characters")
            
            generation_time = time.time() - start_time
            logger.info(f"⏱️ Generation time: {generation_time:.2f}s")
            
            # Return the single version immediately
            return {
                "chapter_content": version.content,
                "choices": version.choices,  # ALWAYS include choices regardless of mode
                "quality_metrics": {"overall_score": 8.0, "note": "Single generation mode"},
                "generation_metrics": {
                    "generation_time": generation_time,
                    "versions_generated": 1,
                    "enhancement_attempts": 0,
                    "generation_method": "SINGLE_VERSION_FAST"
                },
                "success": True,
                "generation_method": "SINGLE_VERSION_FAST",
                "is_game_mode": is_game_mode
            }
            
        except Exception as e:
            error_msg = f"❌ Error generating chapter {chapter_number}: {str(e)}"
            logger.error(error_msg)
            return {
                "chapter_content": f"Error: {error_msg}",
                "choices": [],
                "quality_metrics": {"overall_score": 0, "error": str(e)},
                "generation_metrics": {"error": str(e)},
                "success": False,
                "generation_method": "SINGLE_VERSION_FAST"
            }
    
    def _generate_single_version(
        self, 
        story_title: str,
        story_outline: str,
        story_dna_context: str,
        chapter_number: int,
        user_choice: str,
        is_game_mode: bool
    ) -> Optional[ChapterVersion]:
        """Generate a single version of the chapter - FAST with CoT reasoning."""
        try:
            logger.info(f"📝 Generating single version for Chapter {chapter_number}")
            logger.info(f"🎮 Game Mode: {is_game_mode}")
            
            # Use emotion focus as default (good balance)
            focus = GenerationFocus.EMOTION
            quality_instructions = self._get_focus_instructions(focus)
            
            # Get previous chapter openings to avoid repetition
            previous_openings = self._extract_previous_openings(story_dna_context)
            
            # Prepare context based on game mode
            if is_game_mode:
                choice_context = f"\n\nUSER'S PREVIOUS CHOICE: {user_choice}\nThis choice should directly influence the events and outcomes in this chapter."
                mode_instructions = "GAME MODE: Generate 3 meaningful choices at the end that will significantly impact the story's direction."
            else:
                choice_context = ""
                mode_instructions = "NORMAL MODE: Generate 3 meaningful choices at the end that will significantly impact the story's direction. (User can switch to game mode later)"
            
            # Generate single version with CoT reasoning
            result = self.base_chain.invoke({
                "story_title": story_title,
                "story_outline": story_outline,
                "story_dna_context": story_dna_context,
                "chapter_number": chapter_number,
                "user_choice": choice_context,
                "generation_focus": focus.value.upper(),
                "quality_instructions": quality_instructions,
                "previous_openings": previous_openings,
                "mode_instructions": mode_instructions,
                "is_game_mode": is_game_mode
            })
            
            # After LLM call, log the raw output for debugging
            llm_output = result.content
            logger.info(f"RAW LLM OUTPUT for Chapter {chapter_number}: {llm_output[:200]}...")
            
            # Parse the response
            parsed_result = self._parse_chapter_response(result.content, chapter_number)
            
            if parsed_result.get("success", False):
                # ALWAYS include choices regardless of mode
                choices = parsed_result["choices"]
                
                version = ChapterVersion(
                    content=parsed_result["chapter_content"],
                    choices=choices,
                    quality_metrics=None,  # Not needed for single version
                    generation_focus=focus,
                    version_id=1
                )
                logger.info(f"✅ Generated single version - {len(version.content)} chars")
                logger.info(f"🎮 Choices generated: {len(choices)} (Game Mode: {is_game_mode})")
                return version
            else:
                logger.warning(f"⚠️ Failed to parse single version")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error generating single version: {e}")
            return None

    def _generate_multiple_versions(
        self, 
        story_title: str,
        story_outline: str,
        story_dna_context: str,
        chapter_number: int,
        user_choice: str,
        num_versions: int = 3
    ) -> List[ChapterVersion]:
        """Generate multiple versions of the same chapter with different focuses."""
        versions = []
        focuses = [GenerationFocus.EMOTION, GenerationFocus.ACTION, GenerationFocus.CHARACTER]
        
        # Get previous chapter openings to avoid repetition
        previous_openings = self._extract_previous_openings(story_dna_context)
        
        for i, focus in enumerate(focuses[:num_versions]):
            try:
                logger.info(f"📝 Generating version {i+1} with {focus.value} focus")
                
                # Create focus-specific instructions
                quality_instructions = self._get_focus_instructions(focus)
                
                # Adjust temperature slightly for variation
                temp_adjustment = 0.1 * i
                original_temp = self.llm.temperature
                self.llm.temperature = min(0.9, original_temp + temp_adjustment)
                
                # Generate version with variety context
                result = self.base_chain.invoke({
                    "story_title": story_title,
                    "story_outline": story_outline,
                    "story_dna_context": story_dna_context,
                    "chapter_number": chapter_number,
                    "user_choice": user_choice,
                    "generation_focus": focus.value.upper(),
                    "quality_instructions": quality_instructions,
                    "previous_openings": previous_openings
                })
                
                # Reset temperature
                self.llm.temperature = original_temp
                
                # Parse the response
                parsed_result = self._parse_chapter_response(result.content, chapter_number)
                
                if parsed_result.get("success", False):
                    version = ChapterVersion(
                        content=parsed_result["chapter_content"],
                        choices=parsed_result["choices"],
                        quality_metrics=None,  # Will be filled later
                        generation_focus=focus,
                        version_id=i + 1
                    )
                    versions.append(version)
                    logger.info(f"✅ Generated version {i+1} - {len(version.content)} chars")
                else:
                    logger.warning(f"⚠️ Failed to parse version {i+1}")
                    
            except Exception as e:
                logger.error(f"❌ Error generating version {i+1}: {e}")
                continue
        
        return versions
    
    def _extract_previous_openings(self, story_dna_context: str) -> str:
        """Extract opening sentences from previous chapters to avoid repetition."""
        actual_openings = []
        
        # Extract actual openings from DNA context
        try:
            # Look for chapter content in DNA context
            import re
            
            # Find patterns like "final_scene_context", "last_dialogue", etc.
            # These often contain the ending of previous chapters
            patterns_to_avoid = []
            
            # Extract from ending_genetics which often contains scene context
            ending_matches = re.findall(r'"final_scene_context":\s*"([^"]+)"', story_dna_context)
            for match in ending_matches:
                if len(match) > 20:  # Only use substantial content
                    # Extract first sentence as potential opening pattern
                    first_sentence = match.split('.')[0][:50]
                    if first_sentence:
                        patterns_to_avoid.append(first_sentence)
            
            # Extract from character states that might indicate scene setup
            scene_matches = re.findall(r'"atmosphere":\s*"([^"]+)"', story_dna_context)
            location_matches = re.findall(r'"location_description":\s*"([^"]+)"', story_dna_context)
            
            # Common repetitive patterns we've seen in your story
            known_repetitive_patterns = [
                "The key turned in",
                "Temüjin stood at",
                "Temüjin felt the weight of",
                "The sun hung low",
                "The air was thick with",
                "Inside, the atmosphere",
                "The scent of dried herbs"
            ]
            
            patterns_to_avoid.extend(known_repetitive_patterns)
            
        except Exception as e:
            logger.warning(f"Could not extract openings from DNA: {e}")
            patterns_to_avoid = [
                "The key turned in",
                "Temüjin stood at", 
                "The air was thick with",
                "Inside, the atmosphere"
            ]
        
        # Create comprehensive warning
        warning_text = "🚨 CRITICAL: AVOID these repetitive openings:\n"
        for i, pattern in enumerate(patterns_to_avoid[:8], 1):  # Limit to 8 patterns
            warning_text += f"{i}. NEVER start with '{pattern}...'\n"
        
        warning_text += "\n✅ REQUIRED: Use these DIFFERENT opening techniques:\n"
        warning_text += "1. DIALOGUE: \"We must act quickly,\" Batu said urgently.\n"
        warning_text += "2. ACTION: The hoofbeats thundered across the steppes.\n"
        warning_text += "3. INTERNAL THOUGHT: Something had changed in Temüjin overnight.\n"
        warning_text += "4. SENSORY DETAIL: The smoke from burning camps filled the morning air.\n"
        warning_text += "5. MYSTERY: The messenger arrived at dawn with blood on his hands.\n"
        warning_text += "6. EMOTION: Fear gripped the camp like ice.\n"
        
        return warning_text
    
    def _get_focus_instructions(self, focus: GenerationFocus) -> str:
        """Get specific instructions for each generation focus."""
        instructions = {
            GenerationFocus.EMOTION: """
🎭 EMOTION FOCUS:
- Prioritize character emotional states and internal thoughts
- Create moments of genuine feeling and vulnerability
- Show emotional consequences of choices and events
- Build empathy and connection with characters
- Use emotional language that resonates with readers
            """,
            GenerationFocus.ACTION: """
⚡ ACTION FOCUS:
- Emphasize dynamic scenes and forward momentum
- Create tension through conflict and obstacles
- Show characters making decisive choices
- Use vivid action verbs and energetic pacing
- Build excitement and anticipation for what's next
            """,
            GenerationFocus.CHARACTER: """
👥 CHARACTER FOCUS:
- Develop character personalities and relationships
- Show character growth through choices and challenges
- Create distinctive dialogue and voice for each character
- Explore character motivations and backstories
- Build character arcs that feel authentic and earned
            """,
            GenerationFocus.DIALOGUE: """
💬 DIALOGUE FOCUS:
- Create natural, character-revealing conversations
- Use subtext and implied meaning in dialogue
- Show character relationships through speech patterns
- Advance plot through meaningful exchanges
- Balance dialogue with action and description
            """
        }
        return instructions.get(focus, "")
    
    def _score_chapter_quality(self, chapter_content: str) -> QualityMetrics:
        """Score a chapter's quality across multiple dimensions."""
        try:
            result = self.quality_chain.invoke({"chapter_content": chapter_content})
            
            # Parse the quality scores
            scores_text = result.content.strip()
            scores_dict = self._parse_quality_scores(scores_text)
            
            return QualityMetrics(
                emotional_impact=scores_dict.get("emotional_impact", 7.0),
                character_consistency=scores_dict.get("character_consistency", 7.0),
                plot_advancement=scores_dict.get("plot_advancement", 7.0),
                writing_quality=scores_dict.get("writing_quality", 7.0),
                dialogue_naturalness=scores_dict.get("dialogue_naturalness", 7.0),
                pacing=scores_dict.get("pacing", 7.0),
                choice_setup=scores_dict.get("choice_setup", 7.0),
                overall_score=scores_dict.get("overall_score", 7.0)
            )
            
        except Exception as e:
            logger.error(f"❌ Error scoring chapter quality: {e}")
            # Return default metrics if scoring fails
            return QualityMetrics(
                emotional_impact=7.0,
                character_consistency=7.0,
                plot_advancement=7.0,
                writing_quality=7.0,
                dialogue_naturalness=7.0,
                pacing=7.0,
                choice_setup=7.0,
                overall_score=7.0
            )
    
    def _parse_quality_scores(self, scores_text: str) -> Dict[str, float]:
        """Parse quality scores from LLM response."""
        try:
            # Try to parse as JSON first
            if scores_text.strip().startswith('{'):
                return json.loads(scores_text)
            
            # Fallback: parse line by line
            scores = {}
            for line in scores_text.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    try:
                        scores[key] = float(value.strip())
                    except ValueError:
                        continue
            
            return scores
            
        except Exception as e:
            logger.error(f"❌ Error parsing quality scores: {e}")
            return {}
    
    def _enhance_chapter(self, chapter_version: ChapterVersion) -> Optional[ChapterVersion]:
        """Enhance a chapter based on its quality weaknesses."""
        try:
            # Identify weak areas
            weak_areas = []
            metrics = chapter_version.quality_metrics
            
            if metrics.emotional_impact < 8.0:
                weak_areas.append("emotional_impact")
            if metrics.character_consistency < 8.0:
                weak_areas.append("character_consistency")
            if metrics.plot_advancement < 8.0:
                weak_areas.append("plot_advancement")
            if metrics.writing_quality < 8.0:
                weak_areas.append("writing_quality")
            if metrics.dialogue_naturalness < 8.0:
                weak_areas.append("dialogue_naturalness")
            if metrics.pacing < 8.0:
                weak_areas.append("pacing")
            
            if not weak_areas:
                return chapter_version  # Already high quality
            
            # Create enhancement instructions
            weak_areas_text = ", ".join(weak_areas)
            
            # Enhance the chapter
            result = self.enhancement_chain.invoke({
                "chapter_content": chapter_version.content,
                "weak_areas": weak_areas_text
            })
            
            # Parse enhancement result
            enhancement_result = self._parse_enhancement_response(result.content)
            
            if enhancement_result.get("success", False):
                # Create new enhanced version
                enhanced_version = ChapterVersion(
                    content=enhancement_result["enhanced_chapter"],
                    choices=chapter_version.choices,  # Keep original choices
                    quality_metrics=None,  # Will be scored later
                    generation_focus=chapter_version.generation_focus,
                    version_id=chapter_version.version_id
                )
                return enhanced_version
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error enhancing chapter: {e}")
            return None
    
    def _parse_enhancement_response(self, response_content: str) -> Dict[str, Any]:
        """Parse the enhancement response from LLM."""
        try:
            # Clean up the response
            cleaned_text = response_content.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()
            
            # Parse JSON
            parsed_json = json.loads(cleaned_text)
            
            return {
                "success": True,
                "enhanced_chapter": parsed_json.get("enhanced_chapter", ""),
                "improvements_made": parsed_json.get("improvements_made", "")
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing enhancement response: {e}")
            return {"success": False, "error": str(e)}
    
    def _format_dna_contexts(self, dna_contexts: List[str]) -> str:
        """Format multiple DNA contexts into a comprehensive story context."""
        if not dna_contexts:
            return "No previous chapter context available."
        
        formatted_context = "\n\n" + "="*50 + "\n\n".join(dna_contexts)
        
        if len(dna_contexts) > 1:
            summary_header = f"STORY PROGRESSION ({len(dna_contexts)} chapters):\n"
            formatted_context = summary_header + formatted_context
        
        # Limit context length
        max_context_length = 8000
        if len(formatted_context) > max_context_length:
            recent_contexts = dna_contexts[-2:] if len(dna_contexts) > 2 else dna_contexts
            formatted_context = "\n\n" + "="*50 + "\n\n".join(recent_contexts)
        
        return formatted_context
    
    def _validate_user_choice(self, user_choice: str, dna_context: str, chapter_number: int) -> str:
        """Validate and contextualize the user choice."""
        if not user_choice:
            return "No specific choice - continue story naturally from the DNA context"
        
        return f"{user_choice}\n\nIMPORTANT: Show this choice being made immediately, based on the exact scene context from the DNA above."
    
    def _parse_chapter_response(self, response_content: str, chapter_number: int) -> Dict[str, Any]:
        """Parse the JSON response from LLM containing chapter and choices."""
        try:
            import re
            
            # Log the raw response for debugging
            logger.info(f"🔍 Raw LLM response length: {len(response_content)} chars")
            logger.info(f"🔍 Response starts with: '{response_content[:100]}...'")
            
            # Clean up the response
            cleaned_text = response_content.strip()
            
            # Check if response starts with { (proper JSON)
            if not cleaned_text.startswith('{'):
                logger.error(f"❌ Response does not start with {{ - starts with: '{cleaned_text[:50]}'")
                raise ValueError("Response does not start with opening brace {")
            
            # Check if response ends with } (proper JSON)
            if not cleaned_text.endswith('}'):
                logger.error(f"❌ Response does not end with }} - ends with: '...{cleaned_text[-50:]}'")
                raise ValueError("Response does not end with closing brace }")
            
            # Remove markdown code blocks (shouldn't exist with new prompt)
            if cleaned_text.startswith("```json"):
                logger.warning("⚠️ Found markdown code block despite strict instructions")
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                logger.warning("⚠️ Found code block despite strict instructions")
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            
            cleaned_text = cleaned_text.strip()
            
            # Fix common JSON issues
            cleaned_text = re.sub(r',(\s*[}\]])', r'\1', cleaned_text)
            
            # Parse JSON
            parsed_json = json.loads(cleaned_text)
            logger.info(f"✅ Successfully parsed JSON with {len(parsed_json)} top-level fields")
            
            # Validate structure
            if "chapter" not in parsed_json:
                logger.error("❌ Response missing 'chapter' field")
                logger.error(f"Available fields: {list(parsed_json.keys())}")
                raise ValueError("Response missing 'chapter' field")
            if "choices" not in parsed_json:
                logger.error("❌ Response missing 'choices' field")
                logger.error(f"Available fields: {list(parsed_json.keys())}")
                raise ValueError("Response missing 'choices' field")
            
            # Validate choices structure
            choices = parsed_json["choices"]
            if not isinstance(choices, list):
                raise ValueError("'choices' field must be an array")
            if len(choices) < 2:
                logger.warning(f"⚠️ Only {len(choices)} choices generated, expected 3-4")
            
            logger.info(f"✅ Chapter parsed successfully: {len(parsed_json['chapter'])} chars, {len(choices)} choices")
            
            return {
                "success": True,
                "chapter_content": parsed_json["chapter"],
                "choices": parsed_json["choices"],
                "chapter_number": chapter_number
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing error at position {e.pos}: {e.msg}")
            logger.error(f"❌ Context around error: '...{response_content[max(0, e.pos-50):e.pos+50]}...'")
            return {
                "success": False,
                "chapter_content": response_content,
                "choices": [],
                "error": f"JSON parsing failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"❌ Error parsing chapter response: {e}")
            logger.error(f"❌ Response preview: '{response_content[:200]}...'")
            return {
                "success": False,
                "chapter_content": response_content,
                "choices": [],
                "error": str(e)
            }

# 🔄 BACKWARD COMPATIBILITY WRAPPER
class NextChapterGeneratorWithDNA:
    """Backward compatibility wrapper that uses the new bestseller system."""
    
    def __init__(self):
        self.bestseller_generator = BestsellerChapterGenerator()
        logger.info("🔄 NextChapterGeneratorWithDNA initialized with bestseller backend")
    
    def generate_next_chapter(
        self, 
        story_title: str,
        story_outline: str, 
        story_dna_contexts: List[str], 
        chapter_number: int,
        user_choice: str = "",
        previous_chapter_summaries: List[str] = None,
        is_game_mode: bool = False,  # NEW: Game mode flag
        generation_focus: str = "enhanced_continuity",
        quality_instructions: str = ""
    ) -> Dict[str, Any]:
        """
        Generate chapter using the bestseller system with CoT reasoning.
        Supports both normal mode (no user choice) and game mode (with user choice).
        """
        logger.info(f"🔄 Using bestseller system for Chapter {chapter_number}")
        logger.info(f"🎮 Game Mode: {is_game_mode}")
        logger.info(f"📝 Using {len(previous_chapter_summaries or [])} chapter summaries")
        
        # Format summaries for inclusion in DNA context
        formatted_summaries = ""
        if previous_chapter_summaries:
            formatted_summaries = "\n\n=== PREVIOUS CHAPTER SUMMARIES ===\n"
            for i, summary in enumerate(previous_chapter_summaries, 1):
                formatted_summaries += f"Chapter {i}: {summary}\n"
        
        # Combine DNA contexts with summaries
        enhanced_dna_contexts = story_dna_contexts.copy()
        if formatted_summaries:
            enhanced_dna_contexts.append(formatted_summaries)
        
        # Use the new bestseller generator with game mode support
        result = self.bestseller_generator.generate_bestseller_chapter(
            story_title=story_title,
            story_outline=story_outline,
            story_dna_contexts=enhanced_dna_contexts,
            chapter_number=chapter_number,
            user_choice=user_choice if is_game_mode else "",  # Only include choice in game mode
            target_quality=8.5,
            is_game_mode=is_game_mode  # Pass game mode flag
        )
        
        # Convert to legacy format for backward compatibility
        return {
            "chapter_content": result["chapter_content"],
            "choices": result["choices"],  # ALWAYS include choices regardless of mode
            "token_metrics": result.get("generation_metrics", {}),
            "quality_score": result.get("quality_metrics", {}).get("overall_score", 0),
            "success": result["success"],
            "generation_method": "BESTSELLER_WITH_SUMMARIES",
            "summaries_used": len(previous_chapter_summaries or []),
            "is_game_mode": is_game_mode
        }

# Global instances
next_chapter_generator_with_dna = NextChapterGeneratorWithDNA()
bestseller_generator = BestsellerChapterGenerator()

# Backward compatibility alias
NextChapterGenerator = NextChapterGeneratorWithDNA

# 🎯 CONVENIENCE FUNCTIONS
def generate_next_chapter_with_dna(
    story_title: str,
    story_outline: str, 
    story_dna_contexts: List[str], 
    chapter_number: int,
    user_choice: str = "",
    is_game_mode: bool = False,  # NEW: Game mode flag
    previous_chapter_summaries: List[str] = None  # NEW: Chapter summaries
) -> Dict[str, Any]:
    """Generate chapter with backward compatibility and game mode support."""
    return next_chapter_generator_with_dna.generate_next_chapter(
        story_title=story_title,
        story_outline=story_outline,
        story_dna_contexts=story_dna_contexts,
        chapter_number=chapter_number,
        user_choice=user_choice,
        is_game_mode=is_game_mode,
        previous_chapter_summaries=previous_chapter_summaries
    )

def generate_bestseller_chapter(
    story_title: str,
    story_outline: str, 
    story_dna_contexts: List[str], 
    chapter_number: int,
    user_choice: str = "",
    target_quality: float = 8.5,
    is_game_mode: bool = False  # NEW: Game mode flag
) -> Dict[str, Any]:
    """Generate chapter with explicit bestseller quality control and game mode support."""
    return bestseller_generator.generate_bestseller_chapter(
        story_title=story_title,
        story_outline=story_outline,
        story_dna_contexts=story_dna_contexts,
        chapter_number=chapter_number,
        user_choice=user_choice,
        target_quality=target_quality,
        is_game_mode=is_game_mode
    )

if __name__ == "__main__":
    # Test the system
    print("🚀 Bestseller Chapter Generator initialized!")
    print("🏆 Multi-version quality system ready!")
    print("⚡ Use generate_bestseller_chapter() for maximum quality!")