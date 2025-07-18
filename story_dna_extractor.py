"""
Story DNA Extractor - LLM-Powered Version
Replaces broken regex extraction with intelligent LLM-based DNA extraction
"""

import json
import re
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from logger_config import setup_logger

# Load environment variables
load_dotenv()

logger = setup_logger(__name__)

class LLMStoryDNAExtractor:
    """
    LLM-powered DNA extractor that intelligently extracts story genetics
    instead of relying on broken regex patterns.
    """
    
    def __init__(self):
        # Use a focused LLM for DNA extraction
        self.dna_llm = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"), 
            model_name='gpt-4o-mini', 
            temperature=0.2,  # Lower temperature for consistent extraction
            max_tokens=800
        )
        logger.info("🧬 LLM-Powered DNA Extractor initialized")
    
    def extract_chapter_dna(self, chapter_content: str, chapter_number: int) -> Dict[str, Any]:
        """
        Extract story DNA using LLM intelligence instead of regex patterns.
        
        Args:
            chapter_content: Full chapter text
            chapter_number: Chapter number for context
            
        Returns:
            Dict containing intelligently extracted story DNA
        """
        logger.info(f"🧬 Extracting DNA from Chapter {chapter_number} using LLM")
        
        try:
            # Use LLM to extract comprehensive DNA
            story_dna = self._extract_dna_with_llm(chapter_content, chapter_number)
            
            # Add metadata
            story_dna["chapter_number"] = chapter_number
            story_dna["extraction_method"] = "LLM"
            story_dna["dna_version"] = "2.0"
            
            logger.info(f"✅ Chapter {chapter_number} DNA extracted: {len(str(story_dna))} chars")
            return story_dna
            
        except Exception as e:
            logger.error(f"❌ Error extracting DNA from Chapter {chapter_number}: {e}")
            return self._create_fallback_dna(chapter_content, chapter_number)
    
    def _extract_dna_with_llm(self, chapter_content: str, chapter_number: int) -> Dict[str, Any]:
        """Use LLM to intelligently extract story DNA."""
        
        # Create focused extraction prompt
        extraction_prompt = f"""
Extract the essential story DNA from this chapter for perfect story continuity. Be precise and avoid repetitive descriptions.

CHAPTER {chapter_number}:
{chapter_content}

Extract the following information and return as JSON:

{{
    "scene_genetics": {{
        "location_type": "general location type (forest/village/castle/etc - use variety, not exact phrases)",
        "location_description": "brief varied description (avoid repeating 'edge of ancient forest' - use alternatives like 'woodland area', 'forest clearing', 'among the trees')",
        "time_context": "time of day or temporal context",
        "atmosphere": "emotional atmosphere of the scene"
    }},
    "character_genetics": {{
        "active_characters": ["only real character names - exclude common words like 'You', 'Each', 'With', 'This'"],
        "character_states": {{"character_name": "current emotional/physical state"}},
        "character_relationships": {{"character1_character2": "relationship description"}}
    }},
    "emotional_genetics": {{
        "dominant_emotions": ["primary emotions present in chapter"],
        "emotional_momentum": "rising/falling/stable/shifting",
        "tension_level": "high/medium/low"
    }},
    "plot_genetics": {{
        "pending_decisions": ["any choices or questions awaiting resolution"],
        "active_conflicts": ["ongoing tensions or problems"],
        "conversation_threads": ["key dialogue topics that might continue"]
    }},
    "ending_genetics": {{
        "final_scene_context": "what is happening at the very end of the chapter (last 2-3 sentences)",
        "last_dialogue": "final spoken words if any",
        "last_action": "final significant action taken",
        "scene_status": "ongoing/complete/transitional",
        "cliffhanger_type": "question/decision/suspense/none"
    }},
    "continuity_anchors": ["critical facts that must remain consistent (character backgrounds, established relationships, important objects, etc)"]
}}

CRITICAL REQUIREMENTS:
1. For location: Use VARIED descriptions even for same place (forest setting, woodland area, among trees, forest clearing)
2. For characters: ONLY include actual character names, not pronouns or common words
3. For final scene: Focus on immediate context needed for next chapter
4. Keep descriptions brief but unique
5. Ensure all extracted information is directly from the chapter text

Return ONLY the JSON object, no additional text.
"""

        try:
            # Get LLM response
            response = self.dna_llm.invoke([{"role": "user", "content": extraction_prompt}])
            
            # Parse JSON response
            dna_dict = self._parse_llm_response(response.content)
            
            # Validate and clean the extracted DNA
            validated_dna = self._validate_and_clean_dna(dna_dict)
            
            return validated_dna
            
        except Exception as e:
            logger.error(f"❌ LLM DNA extraction failed: {e}")
            raise
    
    def _parse_llm_response(self, response_content: str) -> Dict[str, Any]:
        """Parse and clean LLM JSON response."""
        
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
            
            cleaned_text = cleaned_text.strip()
            
            # Fix common JSON issues
            cleaned_text = re.sub(r',(\s*[}\]])', r'\1', cleaned_text)
            
            # Parse JSON
            parsed_json = json.loads(cleaned_text)
            
            return parsed_json
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse LLM DNA response: {e}")
            # Try to extract partial information
            return self._extract_partial_dna_from_text(response_content)
    
    def _validate_and_clean_dna(self, dna_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted DNA to ensure quality."""
        
        # Clean character list - remove common words that aren't character names
        common_words = {
            'You', 'Each', 'With', 'This', 'Then', 'Where', 'When', 'Why', 
            'How', 'Now', 'Here', 'There', 'Today', 'Festival', 'Secrets',
            'Memories', 'Shadows', 'Light', 'Dark', 'Magic', 'Power', 'Key',
            'Door', 'Time', 'Moment', 'Voice', 'Sound', 'Suddenly'
        }
        
        if "character_genetics" in dna_dict and "active_characters" in dna_dict["character_genetics"]:
            original_chars = dna_dict["character_genetics"]["active_characters"]
            cleaned_chars = [char for char in original_chars if char not in common_words and len(char) > 2]
            dna_dict["character_genetics"]["active_characters"] = cleaned_chars[:5]  # Limit to 5
        
        # Clean location description to avoid repetitive phrases
        if "scene_genetics" in dna_dict and "location_description" in dna_dict["scene_genetics"]:
            location_desc = dna_dict["scene_genetics"]["location_description"]
            
            # Replace repetitive phrases with varied alternatives
            if "edge of the ancient forest" in location_desc.lower():
                alternatives = ["woodland setting", "forest area", "among the trees", "forest clearing"]
                import random
                dna_dict["scene_genetics"]["location_description"] = random.choice(alternatives)
            
            elif "edge of" in location_desc.lower():
                dna_dict["scene_genetics"]["location_description"] = location_desc.replace("edge of", "area near")
        
        # Ensure all required sections exist
        required_sections = ["scene_genetics", "character_genetics", "emotional_genetics", "plot_genetics", "ending_genetics"]
        for section in required_sections:
            if section not in dna_dict:
                dna_dict[section] = {}
        
        return dna_dict
    
    def _extract_partial_dna_from_text(self, response_text: str) -> Dict[str, Any]:
        """Extract what we can from malformed LLM response."""
        
        # Basic fallback extraction
        return {
            "scene_genetics": {
                "location_type": "unknown",
                "location_description": "continuing scene",
                "atmosphere": "neutral"
            },
            "character_genetics": {
                "active_characters": [],
                "character_states": {},
                "character_relationships": {}
            },
            "emotional_genetics": {
                "dominant_emotions": [],
                "emotional_momentum": "stable",
                "tension_level": "medium"
            },
            "plot_genetics": {
                "pending_decisions": [],
                "active_conflicts": [],
                "conversation_threads": []
            },
            "ending_genetics": {
                "final_scene_context": response_text[:200],
                "last_dialogue": "",
                "last_action": "",
                "scene_status": "ongoing",
                "cliffhanger_type": "none"
            },
            "continuity_anchors": [],
            "extraction_status": "partial_fallback"
        }
    
    def _create_fallback_dna(self, content: str, chapter_number: int) -> Dict[str, Any]:
        """Create minimal DNA if LLM extraction completely fails."""
        
        # Simple regex backup for critical information
        words = content.split()
        ending_words = ' '.join(words[-100:]) if len(words) > 100 else content
        
        # Extract character names with simple pattern
        name_pattern = r'\b[A-Z][a-z]{2,}\b'
        potential_names = re.findall(name_pattern, content)
        common_words = {'The', 'And', 'But', 'She', 'He', 'Her', 'His', 'You', 'This', 'That'}
        character_names = [name for name in set(potential_names) if name not in common_words][:3]
        
        return {
            "chapter_number": chapter_number,
            "scene_genetics": {
                "location_type": "continuing",
                "location_description": "scene continues",
                "atmosphere": "neutral"
            },
            "character_genetics": {
                "active_characters": character_names,
                "character_states": {},
                "character_relationships": {}
            },
            "emotional_genetics": {
                "dominant_emotions": [],
                "emotional_momentum": "stable",
                "tension_level": "medium"
            },
            "plot_genetics": {
                "pending_decisions": [],
                "active_conflicts": [],
                "conversation_threads": []
            },
            "ending_genetics": {
                "final_scene_context": ending_words,
                "last_dialogue": "",
                "last_action": "",
                "scene_status": "ongoing",
                "cliffhanger_type": "none"
            },
            "continuity_anchors": [],
            "extraction_status": "fallback",
            "fallback_reason": "LLM extraction failed"
        }
    
    def format_dna_for_prompt(self, story_dna: Dict[str, Any]) -> str:
        """Format intelligently extracted DNA for story generation prompt."""
        
        if story_dna.get('extraction_status') == 'fallback':
            return f"FALLBACK DNA: {story_dna.get('ending_genetics', {}).get('final_scene_context', '')}"
        
        # Extract sections
        scene = story_dna.get('scene_genetics', {})
        chars = story_dna.get('character_genetics', {})
        emotional = story_dna.get('emotional_genetics', {})
        plot = story_dna.get('plot_genetics', {})
        ending = story_dna.get('ending_genetics', {})
        anchors = story_dna.get('continuity_anchors', [])
        
        # Format DNA for generation prompt
        dna_string = f"""CHAPTER {story_dna.get('chapter_number', 'X')} DNA (LLM-Extracted):

🏞️ SCENE: {scene.get('location_description', 'unknown location')} - {scene.get('atmosphere', 'neutral')} atmosphere
👥 CHARACTERS: {', '.join(chars.get('active_characters', []))}
💭 EMOTIONS: {', '.join(emotional.get('dominant_emotions', []))} (tension: {emotional.get('tension_level', 'medium')})
🎯 ENDING: {ending.get('scene_status', 'ongoing')} scene
💬 LAST DIALOGUE: {ending.get('last_dialogue', 'none')}
🎪 CLIFFHANGER: {ending.get('cliffhanger_type', 'none')}
⚓ CONTINUITY: {'; '.join(anchors[:3]) if anchors else 'none'}

FINAL SCENE CONTEXT: {ending.get('final_scene_context', 'Scene continues from previous chapter')}"""
        
        return dna_string
    
    def extract_variety_safe_dna(self, chapter_content: str, chapter_number: int, previous_extractions: List[Dict] = None) -> Dict[str, Any]:
        """
        Extract DNA with automatic variety enforcement to prevent repetitive descriptions.
        
        Args:
            chapter_content: Chapter content to extract from
            chapter_number: Current chapter number
            previous_extractions: List of previous DNA extractions to avoid repetition
        """
        
        # Get base DNA
        base_dna = self.extract_chapter_dna(chapter_content, chapter_number)
        
        # If we have previous extractions, enforce variety
        if previous_extractions:
            base_dna = self._enforce_variety(base_dna, previous_extractions)
        
        return base_dna
    
    def _enforce_variety(self, current_dna: Dict[str, Any], previous_extractions: List[Dict]) -> Dict[str, Any]:
        """Ensure variety in location descriptions across chapters."""
        
        # Check for repetitive location descriptions
        current_location = current_dna.get('scene_genetics', {}).get('location_description', '')
        
        # Collect previous location descriptions
        previous_locations = []
        for prev_dna in previous_extractions[-3:]:  # Check last 3 chapters
            prev_location = prev_dna.get('scene_genetics', {}).get('location_description', '')
            if prev_location:
                previous_locations.append(prev_location.lower())
        
        # If current location is too similar to previous ones, vary it
        if current_location and any(current_location.lower() in prev for prev in previous_locations):
            logger.info(f"🔄 Enforcing variety - location '{current_location}' too similar to previous")
            
            # Generate varied alternatives based on location type
            location_type = current_dna.get('scene_genetics', {}).get('location_type', '')
            varied_description = self._get_varied_location_description(location_type, previous_locations)
            
            current_dna['scene_genetics']['location_description'] = varied_description
            logger.info(f"🎨 Varied location description: '{varied_description}'")
        
        return current_dna
    
    def _get_varied_location_description(self, location_type: str, avoid_phrases: List[str]) -> str:
        """Generate varied location descriptions."""
        
        variety_map = {
            'forest': [
                'woodland setting', 'forest area', 'among the trees', 'forest clearing',
                'wooded environment', 'tree-lined space', 'sylvan setting', 'forest grove'
            ],
            'village': [
                'village area', 'settlement', 'community space', 'village center',
                'town square', 'village setting', 'local community', 'village grounds'
            ],
            'castle': [
                'castle grounds', 'fortress area', 'castle setting', 'stronghold',
                'palace area', 'castle environment', 'fortress grounds', 'royal setting'
            ]
        }
        
        # Get possible variations
        variations = variety_map.get(location_type.lower(), ['continuing scene', 'current setting'])
        
        # Filter out phrases that are too similar to previous ones
        available_variations = []
        for variation in variations:
            if not any(variation.lower() in avoid.lower() for avoid in avoid_phrases):
                available_variations.append(variation)
        
        # Return a varied description
        if available_variations:
            import random
            return random.choice(available_variations)
        else:
            return f"{location_type} environment"

# Global LLM DNA extractor instance
llm_dna_extractor = LLMStoryDNAExtractor()

# Updated convenience functions
def extract_chapter_dna(chapter_content: str, chapter_number: int) -> Dict[str, Any]:
    """
    Extract story DNA using intelligent LLM analysis.
    
    Args:
        chapter_content: Full chapter text
        chapter_number: Chapter number
        
    Returns:
        Intelligently extracted story DNA dictionary
    """
    return llm_dna_extractor.extract_chapter_dna(chapter_content, chapter_number)

def format_dna_for_llm(story_dna: Dict[str, Any]) -> str:
    """
    Format story DNA for LLM prompt.
    
    Args:
        story_dna: Story DNA dictionary
        
    Returns:
        Formatted DNA string for prompt
    """
    return llm_dna_extractor.format_dna_for_prompt(story_dna)

def extract_variety_safe_dna(chapter_content: str, chapter_number: int, previous_extractions: List[Dict] = None) -> Dict[str, Any]:
    """
    Extract DNA with automatic variety enforcement.
    
    Args:
        chapter_content: Chapter content
        chapter_number: Chapter number  
        previous_extractions: Previous DNA extractions to ensure variety
        
    Returns:
        DNA with variety enforcement applied
    """
    return llm_dna_extractor.extract_variety_safe_dna(chapter_content, chapter_number, previous_extractions)

# Backward compatibility - keep the old class name but use LLM backend
class StoryDNAExtractor:
    """Backward compatibility wrapper - now uses LLM backend."""
    
    def __init__(self):
        self.llm_extractor = LLMStoryDNAExtractor()
        logger.info("🔄 Legacy StoryDNAExtractor now using LLM backend")
    
    def extract_chapter_dna(self, chapter_content: str, chapter_number: int) -> Dict[str, Any]:
        return self.llm_extractor.extract_chapter_dna(chapter_content, chapter_number)
    
    def format_dna_for_prompt(self, story_dna: Dict[str, Any]) -> str:
        return self.llm_extractor.format_dna_for_prompt(story_dna)

# Keep the old global instance for compatibility
dna_extractor = StoryDNAExtractor()

if __name__ == "__main__":
    print("🧬 LLM-Powered Story DNA Extractor loaded!")
    print("✅ Intelligent context-aware DNA extraction enabled")
    print("🎯 Automatic variety enforcement active")
    print("🔄 Backward compatibility maintained")