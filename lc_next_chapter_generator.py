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
- NEVER start with "Eli stood at the edge of..."
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

📌 OUTPUT FORMAT (CRITICAL):
Return ONLY valid JSON:
{{
  "chapter": "Full immersive chapter content (2500+ words)",
  "choices": [
    {{
      "id": "choice_1",
      "title": "Brief compelling title",
      "description": "Detailed description of choice and immediate consequences",
      "story_impact": "How this choice affects character development and story direction",
      "choice_type": "action/emotional/strategic/dialogue",
      "emotional_weight": "high/medium/low"
    }},
    // ... 3-4 more choices
  ]
}}

Write a chapter that readers will remember and discuss with friends."""
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
        max_enhancement_attempts: int = 2
    ) -> Dict[str, Any]:
        """
        🏆 Generate a bestseller-quality chapter with multi-version selection and enhancement.
        
        Args:
            story_title: The title of the story
            story_outline: The original story outline
            story_dna_contexts: List of DNA contexts from all previous chapters
            chapter_number: The chapter number to generate
            user_choice: The user's selected choice from the previous chapter
            target_quality: Minimum quality score required (8.5 = bestseller level)
            max_enhancement_attempts: Maximum number of enhancement iterations
            
        Returns:
            Dict containing the best chapter content, choices, and quality metrics
        """
        start_time = time.time()
        logger.info(f"🏆 Generating BESTSELLER Chapter {chapter_number} for '{story_title}'")
        logger.info(f"🎯 Target quality: {target_quality}/10")
        
        try:
            # Format DNA context
            combined_dna_context = self._format_dna_contexts(story_dna_contexts)
            choice_context = self._validate_user_choice(user_choice, combined_dna_context, chapter_number)
            
            # STEP 1: Generate multiple versions with different focuses
            logger.info("📝 Generating multiple chapter versions...")
            versions = self._generate_multiple_versions(
                story_title=story_title,
                story_outline=story_outline,
                story_dna_context=combined_dna_context,
                chapter_number=chapter_number,
                user_choice=choice_context
            )
            
            if not versions:
                raise Exception("Failed to generate any valid chapter versions")
            
            # STEP 2: Score each version
            logger.info("📊 Scoring chapter versions...")
            scored_versions = []
            for version in versions:
                try:
                    quality_metrics = self._score_chapter_quality(version.content)
                    version.quality_metrics = quality_metrics
                    scored_versions.append(version)
                    logger.info(f"✅ Version {version.version_id} ({version.generation_focus.value}): {quality_metrics.overall_score:.1f}/10")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to score version {version.version_id}: {e}")
                    continue
            
            if not scored_versions:
                raise Exception("Failed to score any chapter versions")
            
            # STEP 3: Select best version
            best_version = max(scored_versions, key=lambda v: v.quality_metrics.overall_score)
            logger.info(f"🏆 Best version: {best_version.version_id} ({best_version.generation_focus.value}) - {best_version.quality_metrics.overall_score:.1f}/10")
            
            # STEP 4: Enhance if below target quality
            enhancement_attempts = 0
            while best_version.quality_metrics.overall_score < target_quality and enhancement_attempts < max_enhancement_attempts:
                logger.info(f"🔧 Enhancing chapter (attempt {enhancement_attempts + 1}/{max_enhancement_attempts})")
                
                enhanced_version = self._enhance_chapter(best_version)
                if enhanced_version:
                    # Re-score the enhanced version
                    try:
                        enhanced_quality = self._score_chapter_quality(enhanced_version.content)
                        if enhanced_quality.overall_score > best_version.quality_metrics.overall_score:
                            best_version = enhanced_version
                            best_version.quality_metrics = enhanced_quality
                            logger.info(f"✅ Enhanced to {enhanced_quality.overall_score:.1f}/10")
                        else:
                            logger.info("⚠️ Enhancement didn't improve quality, keeping original")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to score enhanced version: {e}")
                
                enhancement_attempts += 1
            
            # STEP 5: Final validation
            final_quality = best_version.quality_metrics.overall_score
            if final_quality < target_quality:
                logger.warning(f"⚠️ Final quality {final_quality:.1f}/10 below target {target_quality}/10")
            else:
                logger.info(f"🎉 BESTSELLER QUALITY ACHIEVED: {final_quality:.1f}/10")
            
            generation_time = time.time() - start_time
            logger.info(f"⏱️ Total generation time: {generation_time:.2f}s")
            
            # Calculate comprehensive metrics
            total_input_tokens = sum(len(v.content.split()) * 1.33 for v in versions)
            total_output_tokens = len(best_version.content.split()) * 1.33
            
            return {
                "chapter_content": best_version.content,
                "choices": best_version.choices,
                "quality_metrics": {
                    "emotional_impact": best_version.quality_metrics.emotional_impact,
                    "character_consistency": best_version.quality_metrics.character_consistency,
                    "plot_advancement": best_version.quality_metrics.plot_advancement,
                    "writing_quality": best_version.quality_metrics.writing_quality,
                    "dialogue_naturalness": best_version.quality_metrics.dialogue_naturalness,
                    "pacing": best_version.quality_metrics.pacing,
                    "choice_setup": best_version.quality_metrics.choice_setup,
                    "overall_score": best_version.quality_metrics.overall_score,
                    "target_quality": target_quality,
                    "quality_achieved": final_quality >= target_quality
                },
                "generation_metrics": {
                    "versions_generated": len(versions),
                    "versions_scored": len(scored_versions),
                    "enhancement_attempts": enhancement_attempts,
                    "generation_time": generation_time,
                    "best_version_focus": best_version.generation_focus.value,
                    "estimated_input_tokens": int(total_input_tokens),
                    "estimated_output_tokens": int(total_output_tokens),
                    "model_used": self.llm.model_name
                },
                "success": True,
                "generation_method": "BESTSELLER_MULTI_VERSION"
            }
            
        except Exception as e:
            error_msg = f"❌ Error generating bestseller chapter {chapter_number}: {str(e)}"
            logger.error(error_msg)
            return {
                "chapter_content": f"Error: {error_msg}",
                "choices": [],
                "quality_metrics": {"overall_score": 0, "error": str(e)},
                "generation_metrics": {"error": str(e)},
                "success": False,
                "generation_method": "BESTSELLER_MULTI_VERSION"
            }
    
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
        openings = []
        
        # Common repetitive patterns we've seen
        repetitive_patterns = [
            "Eli stood at the edge of",
            "Eli found himself",
            "Eli hesitated for",
            "Eli felt the weight of",
            "The ancient forest",
            "The shadows danced"
        ]
        
        # Extract from DNA context if available
        if "CHAPTER" in story_dna_context:
            # This would ideally parse actual previous openings
            # For now, we'll use known patterns
            pass
        
        # Create warning about known repetitive patterns
        warning_text = "AVOID these repetitive openings:\n"
        for pattern in repetitive_patterns:
            warning_text += f"- Never start with '{pattern}...'\n"
        
        warning_text += "\nInstead, use:\n"
        warning_text += "- Start with dialogue: '\"We need to move,\" Eli said...'\n"
        warning_text += "- Start with action: 'The key turned in Eli's hand...'\n"
        warning_text += "- Start with thought: 'Something was wrong...'\n"
        warning_text += "- Start with sensory: 'The smell of magic filled the air...'\n"
        
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
            
            # Clean up the response
            cleaned_text = response_content.strip()
            
            # Remove markdown code blocks
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            
            cleaned_text = cleaned_text.strip()
            
            # Fix common JSON issues
            cleaned_text = re.sub(r',(\s*[}\]])', r'\1', cleaned_text)
            
            # Parse JSON
            parsed_json = json.loads(cleaned_text)
            
            # Validate structure
            if "chapter" not in parsed_json:
                raise ValueError("Response missing 'chapter' field")
            if "choices" not in parsed_json:
                raise ValueError("Response missing 'choices' field")
            
            return {
                "success": True,
                "chapter_content": parsed_json["chapter"],
                "choices": parsed_json["choices"],
                "chapter_number": chapter_number
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing chapter response: {e}")
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
        user_choice: str = ""
    ) -> Dict[str, Any]:
        """Generate chapter using the new bestseller system."""
        logger.info(f"🔄 Using bestseller system for Chapter {chapter_number}")
        
        # Use the new bestseller generator
        result = self.bestseller_generator.generate_bestseller_chapter(
            story_title=story_title,
            story_outline=story_outline,
            story_dna_contexts=story_dna_contexts,
            chapter_number=chapter_number,
            user_choice=user_choice,
            target_quality=8.5  # Bestseller quality threshold
        )
        
        # Convert to legacy format for backward compatibility
        return {
            "chapter_content": result["chapter_content"],
            "choices": result["choices"],
            "token_metrics": result.get("generation_metrics", {}),
            "quality_score": result.get("quality_metrics", {}).get("overall_score", 0),
            "success": result["success"],
            "generation_method": "BESTSELLER"
        }

# Global instances
next_chapter_generator_with_dna = NextChapterGeneratorWithDNA()
bestseller_generator = BestsellerChapterGenerator()

# 🎯 CONVENIENCE FUNCTIONS
def generate_next_chapter_with_dna(
    story_title: str,
    story_outline: str, 
    story_dna_contexts: List[str], 
    chapter_number: int,
    user_choice: str = ""
) -> Dict[str, Any]:
    """Generate chapter with backward compatibility."""
    return next_chapter_generator_with_dna.generate_next_chapter(
        story_title=story_title,
        story_outline=story_outline,
        story_dna_contexts=story_dna_contexts,
        chapter_number=chapter_number,
        user_choice=user_choice
    )

def generate_bestseller_chapter(
    story_title: str,
    story_outline: str, 
    story_dna_contexts: List[str], 
    chapter_number: int,
    user_choice: str = "",
    target_quality: float = 8.5
) -> Dict[str, Any]:
    """Generate chapter with explicit bestseller quality control."""
    return bestseller_generator.generate_bestseller_chapter(
        story_title=story_title,
        story_outline=story_outline,
        story_dna_contexts=story_dna_contexts,
        chapter_number=chapter_number,
        user_choice=user_choice,
        target_quality=target_quality
    )

if __name__ == "__main__":
    # Test the system
    print("🚀 Bestseller Chapter Generator initialized!")
    print("🏆 Multi-version quality system ready!")
    print("⚡ Use generate_bestseller_chapter() for maximum quality!")