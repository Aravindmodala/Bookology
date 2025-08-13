"""
Enhanced Story DNA Extractor - Plot Thread Aware Version
Includes active plot tracking, choice context, and continuity preservation
"""

import json
import re
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class EnhancedLLMStoryDNAExtractor:
    """
    Enhanced DNA extractor that tracks plot threads, choices, and continuity anchors
    """
    
    def __init__(self):
        # Use a focused LLM for DNA extraction
        self.dna_llm = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"), 
            model_name='gpt-4o-mini', 
            temperature=0.1,  # Even lower for precise extraction
            max_tokens=1200   # More tokens for detailed extraction
        )
        print("🧬 Enhanced LLM-Powered DNA Extractor initialized")
    
    def extract_chapter_dna(
        self, 
        chapter_content: str, 
        chapter_number: int,
        previous_dna_list: List[Dict] = None,
        user_choice_made: str = "",
        choice_options: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Extract comprehensive story DNA with plot thread tracking.
        
        Args:
            chapter_content: Full chapter text
            chapter_number: Chapter number for context
            previous_dna_list: List of DNA from previous chapters
            user_choice_made: The choice the user made (if any)
            choice_options: The choices that were available
            
        Returns:
            Dict containing enhanced story DNA with plot tracking
        """
        print(f"🧬 Extracting Enhanced DNA from Chapter {chapter_number}")
        
        try:
            # Build context from previous chapters
            previous_context = self._build_previous_context(previous_dna_list)
            choice_context = self._build_choice_context(user_choice_made, choice_options)
            
            # Use enhanced LLM extraction
            story_dna = self._extract_enhanced_dna_with_llm(
                chapter_content, 
                chapter_number,
                previous_context,
                choice_context
            )
            
            # Add metadata
            story_dna["chapter_number"] = chapter_number
            story_dna["extraction_method"] = "ENHANCED_LLM"
            story_dna["dna_version"] = "3.0"
            
            # Track plot thread evolution
            if previous_dna_list:
                story_dna = self._track_plot_evolution(story_dna, previous_dna_list)
            
            print(f"✅ Enhanced Chapter {chapter_number} DNA extracted: {len(str(story_dna))} chars")
            return story_dna
            
        except Exception as e:
            print(f"❌ Error extracting enhanced DNA from Chapter {chapter_number}: {e}")
            return self._create_fallback_dna(chapter_content, chapter_number)
    
    def _extract_enhanced_dna_with_llm(
        self, 
        chapter_content: str, 
        chapter_number: int,
        previous_context: str,
        choice_context: str
    ) -> Dict[str, Any]:
        """Use LLM to extract enhanced DNA with plot tracking."""
        
        extraction_prompt = f"""
You are extracting COMPREHENSIVE story DNA for perfect continuity in a choice-driven story.

PREVIOUS STORY CONTEXT:
{previous_context}

USER CHOICE CONTEXT:
{choice_context}

CURRENT CHAPTER {chapter_number}:
{chapter_content}

Extract ALL essential story elements and return as JSON:

{{
    "scene_genetics": {{
        "location_type": "specific location type",
        "location_description": "brief but distinctive description",
        "time_context": "time of day/duration",
        "atmosphere": "emotional atmosphere",
        "setting_continuity": "how this connects to previous scene"
    }},
    "character_genetics": {{
        "active_characters": ["actual character names only"],
        "character_states": {{"character_name": "current physical/emotional state"}},
        "character_relationships": {{"char1_char2": "relationship status/changes"}},
        "character_development": {{"character_name": "any growth/change this chapter"}}
    }},
    "plot_genetics": {{
        "active_plot_threads": [
            {{
                "thread_id": "unique_identifier",
                "description": "what this plot thread is about",
                "status": "introduced/ongoing/resolved/escalated",
                "next_action_needed": "what needs to happen next"
            }}
        ],
        "pending_decisions": ["specific choices/questions awaiting resolution"],
        "active_conflicts": ["ongoing tensions with specific details"],
        "conversation_threads": ["dialogue topics that could continue"],
        "established_facts": ["important facts established this chapter"],
        "promises_made": ["any commitments or promises made"],
        "deadlines_mentioned": ["any time pressures or deadlines"]
    }},
    "choice_genetics": {{
        "choice_made": "the choice that led to this chapter",
        "choice_consequences": ["how the choice played out"],
        "choice_fulfillment": "did the chapter deliver on choice expectations?",
        "new_choice_setups": ["situations that could lead to new choices"]
    }},
    "emotional_genetics": {{
        "dominant_emotions": ["primary emotions present"],
        "emotional_momentum": "rising/falling/stable/shifting",
        "tension_level": "high/medium/low",
        "emotional_arcs": {{"character_name": "emotional journey this chapter"}}
    }},
    "ending_genetics": {{
        "final_scene_context": "detailed description of chapter ending",
        "last_dialogue": "final spoken words with speaker",
        "last_action": "final significant action with who did it",
        "immediate_situation": "what situation characters are in RIGHT NOW",
        "scene_status": "ongoing/complete/transitional",
        "cliffhanger_type": "question/decision/suspense/revelation/none",
        "urgent_needs": ["what characters urgently need to address next"]
    }},
    "continuity_anchors": [
        {{
            "type": "character_fact/relationship/object/location/rule",
            "description": "the specific fact that must remain consistent",
            "importance": "critical/important/minor"
        }}
    ],
    "world_building": {{
        "locations_mentioned": ["any places referenced"],
        "objects_introduced": ["important items introduced"],
        "rules_established": ["world rules or constraints mentioned"],
        "backstory_revealed": ["any character/world history revealed"]
    }}
}}

CRITICAL EXTRACTION REQUIREMENTS:
1. **PLOT THREADS**: Identify ALL ongoing storylines, especially job offers, financial problems, relationship issues
2. **CHOICE TRACKING**: Note how user choices affected the story and what they led to
3. **SPECIFIC DETAILS**: Include names, numbers, specific commitments, exact situations
4. **CONTINUITY FACTS**: Extract facts that MUST remain consistent (ages, jobs, relationships, past events)
5. **IMMEDIATE CONTEXT**: Focus on where characters are RIGHT NOW and what they need to do NEXT

Return ONLY the JSON object, no additional text.
"""

        try:
            # Get LLM response
            response = self.dna_llm.invoke([{"role": "user", "content": extraction_prompt}])
            
            # Parse JSON response
            dna_dict = self._parse_llm_response(response.content)
            
            # Validate and enhance the extracted DNA
            validated_dna = self._validate_and_enhance_dna(dna_dict)
            
            return validated_dna
            
        except Exception as e:
            print(f"❌ Enhanced LLM DNA extraction failed: {e}")
            raise
    
    def _build_previous_context(self, previous_dna_list: List[Dict]) -> str:
        """Build context from previous chapter DNA."""
        if not previous_dna_list:
            return "This is the first chapter - no previous context."
        
        context_parts = []
        
        # Get the most recent chapters (last 2-3)
        recent_chapters = previous_dna_list[-3:] if len(previous_dna_list) > 3 else previous_dna_list
        
        for dna in recent_chapters:
            chapter_num = dna.get('chapter_number', 'Unknown')
            
            # Extract key plot threads
            plot_threads = []
            if 'plot_genetics' in dna:
                plot_data = dna['plot_genetics']
                if 'active_plot_threads' in plot_data:
                    plot_threads = [t.get('description', str(t)) for t in plot_data.get('active_plot_threads', [])]
                elif 'pending_decisions' in plot_data:
                    plot_threads = plot_data.get('pending_decisions', [])
            
            # Extract ending context
            ending_context = ""
            if 'ending_genetics' in dna:
                ending_context = dna['ending_genetics'].get('final_scene_context', '')
            
            # Extract continuity anchors
            anchors = dna.get('continuity_anchors', [])
            if isinstance(anchors, list) and anchors:
                anchor_text = '; '.join([str(a) for a in anchors[:3]])
            else:
                anchor_text = "None"
            
            context_parts.append(f"""
CHAPTER {chapter_num} SUMMARY:
- Plot Threads: {'; '.join(plot_threads) if plot_threads else 'None'}
- Ending: {ending_context}
- Key Facts: {anchor_text}
""")
        
        return "\n".join(context_parts)
    
    def _build_choice_context(self, user_choice_made: str, choice_options: List[Dict]) -> str:
        """Build context about the choice that led to this chapter."""
        if not user_choice_made:
            return "No specific choice led to this chapter."
        
        context = f"USER CHOICE MADE: {user_choice_made}\n"
        
        if choice_options:
            for choice in choice_options:
                if choice.get('title', '').lower() in user_choice_made.lower() or \
                   choice.get('description', '').lower() in user_choice_made.lower():
                    context += f"CHOICE IMPACT EXPECTED: {choice.get('story_impact', 'Unknown')}\n"
                    break
        
        context += "REQUIREMENT: This chapter MUST show the consequences of this choice."
        return context
    
    def _track_plot_evolution(self, current_dna: Dict, previous_dna_list: List[Dict]) -> Dict:
        """Track how plot threads evolved from previous chapters."""
        
        # Get previous plot threads
        previous_threads = set()
        for prev_dna in previous_dna_list:
            plot_genetics = prev_dna.get('plot_genetics', {})
            
            # From old format
            if 'pending_decisions' in plot_genetics:
                previous_threads.update(plot_genetics['pending_decisions'])
            if 'active_conflicts' in plot_genetics:
                previous_threads.update(plot_genetics['active_conflicts'])
            
            # From new format
            if 'active_plot_threads' in plot_genetics:
                for thread in plot_genetics['active_plot_threads']:
                    if isinstance(thread, dict):
                        previous_threads.add(thread.get('description', ''))
                    else:
                        previous_threads.add(str(thread))
        
        # Check if important threads were dropped
        current_threads = set()
        current_plot = current_dna.get('plot_genetics', {})
        
        if 'active_plot_threads' in current_plot:
            for thread in current_plot['active_plot_threads']:
                if isinstance(thread, dict):
                    current_threads.add(thread.get('description', ''))
                else:
                    current_threads.add(str(thread))
        
        # Add tracking metadata
        current_dna['plot_evolution'] = {
            'threads_continued': len(current_threads.intersection(previous_threads)),
            'threads_dropped': list(previous_threads - current_threads),
            'threads_new': list(current_threads - previous_threads)
        }
        
        return current_dna
    
    def _validate_and_enhance_dna(self, dna_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance extracted DNA."""
        
        # Ensure all required sections exist
        required_sections = [
            "scene_genetics", "character_genetics", "plot_genetics", 
            "choice_genetics", "emotional_genetics", "ending_genetics",
            "continuity_anchors", "world_building"
        ]
        
        for section in required_sections:
            if section not in dna_dict:
                dna_dict[section] = {}
        
        # Clean character list
        if "character_genetics" in dna_dict and "active_characters" in dna_dict["character_genetics"]:
            common_words = {
                'You', 'Each', 'With', 'This', 'Then', 'Where', 'When', 'Why', 
                'How', 'Now', 'Here', 'There', 'Today', 'Everyone', 'Someone'
            }
            original_chars = dna_dict["character_genetics"]["active_characters"]
            cleaned_chars = [char for char in original_chars if char not in common_words and len(char) > 2]
            dna_dict["character_genetics"]["active_characters"] = cleaned_chars[:6]
        
        # Ensure plot threads are properly formatted
        if "plot_genetics" in dna_dict and "active_plot_threads" in dna_dict["plot_genetics"]:
            threads = dna_dict["plot_genetics"]["active_plot_threads"]
            formatted_threads = []
            
            for i, thread in enumerate(threads):
                if isinstance(thread, str):
                    # Convert string to proper format
                    formatted_threads.append({
                        "thread_id": f"thread_{i+1}",
                        "description": thread,
                        "status": "ongoing",
                        "next_action_needed": "continue development"
                    })
                elif isinstance(thread, dict):
                    # Ensure proper keys
                    if "thread_id" not in thread:
                        thread["thread_id"] = f"thread_{i+1}"
                    if "status" not in thread:
                        thread["status"] = "ongoing"
                    formatted_threads.append(thread)
            
            dna_dict["plot_genetics"]["active_plot_threads"] = formatted_threads
        
        return dna_dict
    
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
            print(f"❌ Failed to parse enhanced DNA response: {e}")
            return self._extract_fallback_from_text(response_content)
    
    def _extract_fallback_from_text(self, response_text: str) -> Dict[str, Any]:
        """Extract what we can from malformed response."""
        return {
            "scene_genetics": {"location_description": "continuing scene"},
            "character_genetics": {"active_characters": []},
            "plot_genetics": {"active_plot_threads": []},
            "choice_genetics": {"choice_fulfillment": "unknown"},
            "emotional_genetics": {"dominant_emotions": []},
            "ending_genetics": {"final_scene_context": response_text[:200]},
            "continuity_anchors": [],
            "world_building": {},
            "extraction_status": "partial_fallback"
        }
    
    def _create_fallback_dna(self, content: str, chapter_number: int) -> Dict[str, Any]:
        """Create minimal DNA if extraction fails completely."""
        words = content.split()
        ending_words = ' '.join(words[-100:]) if len(words) > 100 else content
        
        return {
            "chapter_number": chapter_number,
            "scene_genetics": {"location_description": "scene continues"},
            "character_genetics": {"active_characters": []},
            "plot_genetics": {"active_plot_threads": []},
            "choice_genetics": {"choice_fulfillment": "unknown"},
            "emotional_genetics": {"dominant_emotions": []},
            "ending_genetics": {"final_scene_context": ending_words},
            "continuity_anchors": [],
            "world_building": {},
            "extraction_status": "fallback",
            "fallback_reason": "Complete extraction failure"
        }
    
    def format_enhanced_dna_for_prompt(self, story_dna: Dict[str, Any]) -> str:
        """Format enhanced DNA for story generation."""
        
        if story_dna.get('extraction_status') == 'fallback':
            return f"FALLBACK DNA: {story_dna.get('ending_genetics', {}).get('final_scene_context', '')}"
        
        # Extract all sections
        scene = story_dna.get('scene_genetics', {})
        chars = story_dna.get('character_genetics', {})
        plot = story_dna.get('plot_genetics', {})
        choice = story_dna.get('choice_genetics', {})
        emotional = story_dna.get('emotional_genetics', {})
        ending = story_dna.get('ending_genetics', {})
        anchors = story_dna.get('continuity_anchors', [])
        
        # Format active plot threads
        plot_threads_text = ""
        if 'active_plot_threads' in plot:
            for thread in plot['active_plot_threads']:
                if isinstance(thread, dict):
                    plot_threads_text += f"  • {thread.get('description', 'Unknown thread')} [{thread.get('status', 'ongoing')}]\n"
                else:
                    plot_threads_text += f"  • {thread}\n"
        
        # Format continuity anchors
        anchors_text = ""
        for anchor in anchors[:5]:
            if isinstance(anchor, dict):
                anchors_text += f"  • {anchor.get('description', 'Unknown anchor')}\n"
            else:
                anchors_text += f"  • {anchor}\n"
        
        dna_string = f"""CHAPTER {story_dna.get('chapter_number', 'X')} ENHANCED DNA:

🏞️ SCENE: {scene.get('location_description', 'unknown')} - {scene.get('atmosphere', 'neutral')} atmosphere
👥 CHARACTERS: {', '.join(chars.get('active_characters', []))}
💭 EMOTIONS: {', '.join(emotional.get('dominant_emotions', []))} (tension: {emotional.get('tension_level', 'medium')})

🎯 ACTIVE PLOT THREADS:
{plot_threads_text or '  • None identified'}

🔄 PREVIOUS CHOICE: {choice.get('choice_made', 'None')}
✅ CHOICE FULFILLED: {choice.get('choice_fulfillment', 'Unknown')}

📋 PENDING DECISIONS: {'; '.join(plot.get('pending_decisions', []))}
⚡ ACTIVE CONFLICTS: {'; '.join(plot.get('active_conflicts', []))}

🎪 ENDING: {ending.get('scene_status', 'ongoing')} scene
💬 LAST DIALOGUE: {ending.get('last_dialogue', 'none')}
🚨 URGENT NEEDS: {'; '.join(ending.get('urgent_needs', []))}

⚓ CONTINUITY ANCHORS (CRITICAL):
{anchors_text or '  • None identified'}

🎬 FINAL SCENE CONTEXT: {ending.get('final_scene_context', 'Scene continues')}
📍 IMMEDIATE SITUATION: {ending.get('immediate_situation', 'Characters in current scene')}"""
        
        return dna_string

# Create enhanced global instance
enhanced_dna_extractor = EnhancedLLMStoryDNAExtractor()

# Enhanced convenience function
def extract_enhanced_chapter_dna(
    chapter_content: str, 
    chapter_number: int,
    previous_dna_list: List[Dict] = None,
    user_choice_made: str = "",
    choice_options: List[Dict] = None
) -> Dict[str, Any]:
    """Extract enhanced DNA with plot tracking."""
    return enhanced_dna_extractor.extract_chapter_dna(
        chapter_content, 
        chapter_number,
        previous_dna_list,
        user_choice_made,
        choice_options
    )

def format_enhanced_dna_for_llm(story_dna: Dict[str, Any]) -> str:
    """Format enhanced DNA for prompt."""
    return enhanced_dna_extractor.format_enhanced_dna_for_prompt(story_dna)

if __name__ == "__main__":
    print("🚀 Enhanced Story DNA Extractor loaded!")
    print("🧬 Plot thread tracking enabled")
    print("🎯 Choice consequence validation active")
    print("⚓ Advanced continuity preservation ready")





