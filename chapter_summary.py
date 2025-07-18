import os
import json
from typing import Dict, Any, List, Optional
from openai import OpenAI
import logging

# Setup logging
from logger_config import setup_summary_logger
logger = setup_summary_logger()

class EnhancedChapterSummarizer:
    """
    CORE CHAPTER SUMMARIZATION ENGINE
    
    Focus: Create perfect, detailed chapter summaries optimized for story continuity.
    Responsibility: Single chapter analysis and summarization only.
    """
    
    def __init__(self):
        """Initialize with optimized settings for detailed summarization."""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"
        self.temperature = 0.3
        self.max_tokens = 1500
        
    def create_detailed_summary(
        self,
        chapter_content: str,
        chapter_number: int = 1,
        story_title: str = "Untitled Story",
        minimal_context: str = ""  # Only basic story context, not previous chapters
    ) -> Dict[str, Any]:
        """
        Create a comprehensive chapter summary optimized for future chapter writing.
        
        OUTPUT: 400-600 word detailed summary with all essential continuity elements.
        """
        try:
            logger.info(f"📖 CHAPTER SUMMARY: Starting detailed analysis for Chapter {chapter_number}")
            
            # Build minimal context (story outline only, no previous chapters)
            context_section = ""
            if minimal_context:
                context_section = f"STORY CONTEXT:\n{minimal_context[:500]}\n\n"
            
            # Enhanced prompt for maximum detail and continuity
            summary_prompt = f"""You are an expert story continuity analyst. Create a COMPREHENSIVE chapter summary that will be perfect for writing future chapters.

{context_section}STORY: {story_title}
CHAPTER {chapter_number} TO ANALYZE:
{chapter_content}

Create a detailed summary (400-600 words) that captures EVERY element important for story continuity:

PLOT PROGRESSION:
- What happens in this chapter (complete sequence of events)
- How conflicts develop or resolve
- New plot threads introduced
- Consequences and their implications

CHARACTER DEVELOPMENT:
- Emotional states at start vs end of chapter
- Character decisions and motivations
- Dialogue that reveals character growth
- Relationship dynamics and changes
- Internal conflicts and revelations

WORLD & SETTING:
- Location details and atmosphere
- Time progression and pacing
- World-building elements introduced
- Environmental factors affecting story

CONTINUITY ELEMENTS:
- Information that will be referenced later
- Setups for future payoffs
- Unresolved questions and mysteries
- Cliffhangers and hooks
- Details that affect character motivations going forward

EMOTIONAL TONE:
- Chapter's emotional arc
- Mood and atmosphere shifts
- Tension levels and releases

Format as a flowing, comprehensive summary that reads naturally while including ALL essential details. This summary will be used to write future chapters, so completeness is crucial."""

            # Generate detailed summary
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert story analyst who creates comprehensive summaries for perfect story continuity."},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            summary_text = response.choices[0].message.content.strip()
            
            # Calculate metrics
            original_words = len(chapter_content.split())
            summary_words = len(summary_text.split())
            compression_ratio = round((summary_words / original_words) * 100, 1)
            
            # Quality validation
            quality_score = self._validate_summary_quality(chapter_content, summary_text)
            
            logger.info(f"✅ CHAPTER SUMMARY: Generated {summary_words} words (quality: {quality_score}/10)")
            
            return {
                "success": True,
                "chapter_number": chapter_number,
                "summary": summary_text,
                "metadata": {
                    "story_title": story_title,
                    "original_word_count": original_words,
                    "summary_word_count": summary_words,
                    "compression_ratio": compression_ratio,
                    "quality_score": quality_score,
                    "summary_type": "detailed_continuity"
                },
                "usage_metrics": {
                    "model_used": self.model,
                    "temperature_used": self.temperature,
                    "max_tokens_used": self.max_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"❌ CHAPTER SUMMARY: Failed for Chapter {chapter_number}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "chapter_number": chapter_number,
                "summary": "",
                "metadata": {"error": str(e)}
            }
    
    def extract_story_elements(
        self,
        chapter_content: str,
        chapter_number: int
    ) -> Dict[str, Any]:
        """
        Extract structured story elements for hierarchical system integration.
        
        OUTPUT: Character states, plot threads, world changes for DNA building.
        """
        try:
            logger.info(f"🧬 ELEMENT EXTRACTION: Analyzing Chapter {chapter_number}")
            
            extraction_prompt = f"""Analyze Chapter {chapter_number} and extract structured story elements:

CHAPTER CONTENT:
{chapter_content}

Extract the following in JSON format:
{{
    "characters": [
        {{
            "name": "Character Name",
            "emotional_state": "current emotional state",
            "key_actions": ["action1", "action2"],
            "relationships": {{"other_char": "relationship_status"}},
            "character_development": "how they changed this chapter",
            "future_motivation": "what drives them going forward"
        }}
    ],
    "plot_threads": [
        {{
            "thread_name": "plot thread name",
            "description": "what's happening with this thread",
            "status": "introduced/developed/resolved",
            "importance": "high/medium/low",
            "connections": ["related threads or characters"]
        }}
    ],
    "world_building": {{
        "setting_details": "location and environment details",
        "time_progression": "time-related information",
        "atmosphere": "mood and tone",
        "new_world_info": "any new world-building revealed"
    }},
    "continuity_hooks": [
        "detail that will be important later",
        "setup for future chapters",
        "unresolved question or mystery"
    ],
    "major_events": [
        "significant event that shapes the story",
        "key decision or revelation"
    ]
}}

Focus only on information explicitly present in the chapter."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a story element extractor. Extract structured data for story continuity systems."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.2,  # Lower temperature for structured extraction
                max_tokens=600
            )
            
            # Parse JSON response
            story_elements = json.loads(response.choices[0].message.content)
            
            logger.info(f"✅ ELEMENT EXTRACTION: Found {len(story_elements.get('characters', []))} characters, {len(story_elements.get('plot_threads', []))} threads")
            
            return {
                "success": True,
                "chapter_number": chapter_number,
                "story_elements": story_elements
            }
            
        except Exception as e:
            logger.error(f"❌ ELEMENT EXTRACTION: Failed for Chapter {chapter_number}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "chapter_number": chapter_number,
                "story_elements": {}
            }
    
    def _validate_summary_quality(
        self,
        original_content: str,
        summary: str
    ) -> int:
        """
        Validate summary quality on a scale of 1-10.
        
        Focused on continuity completeness and detail level.
        """
        score = 10
        
        # Length validation (should be comprehensive)
        summary_words = len(summary.split())
        if summary_words < 300:
            score -= 3  # Too short for comprehensive summary
        elif summary_words < 400:
            score -= 1  # Could be more detailed
        elif summary_words > 700:
            score -= 1  # Might be too verbose
        
        # Content coverage check
        original_lower = original_content.lower()
        summary_lower = summary.lower()
        
        # Check for key story elements
        story_indicators = [
            "character", "emotion", "conflict", "setting", "dialogue",
            "relationship", "motivation", "consequence", "decision"
        ]
        
        covered_elements = sum(1 for indicator in story_indicators 
                             if indicator in summary_lower)
        
        if covered_elements < 6:
            score -= 2  # Missing important story elements
        
        # Check for continuity language
        continuity_words = [
            "will", "future", "later", "consequences", "affects", 
            "leads", "results", "develops", "continues"
        ]
        
        continuity_score = sum(1 for word in continuity_words 
                             if word in summary_lower)
        
        if continuity_score < 3:
            score -= 2  # Lacks future-focused language
        
        return max(1, min(10, score))

# Convenience function for easy integration
def generate_chapter_summary(
    chapter_content: str,
    chapter_number: int = 1,
    story_title: str = "Untitled Story",
    story_context: str = ""
) -> Dict[str, Any]:
    """
    SIMPLE INTERFACE: Generate a detailed chapter summary.
    
    This function focuses ONLY on creating the best possible summary
    of a single chapter. Hierarchical management is handled separately.
    """
    summarizer = EnhancedChapterSummarizer()
    return summarizer.create_detailed_summary(
        chapter_content=chapter_content,
        chapter_number=chapter_number,
        story_title=story_title,
        minimal_context=story_context
    )

def extract_chapter_elements(
    chapter_content: str,
    chapter_number: int
) -> Dict[str, Any]:
    """
    SIMPLE INTERFACE: Extract story elements for hierarchical system.
    """
    summarizer = EnhancedChapterSummarizer()
    return summarizer.extract_story_elements(
        chapter_content=chapter_content,
        chapter_number=chapter_number
    )