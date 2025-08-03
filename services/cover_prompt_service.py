"""
Smart Book Cover Prompt Generation Service

This service creates intelligent, story-specific prompts for AI image generation
by analyzing story data including title, genre, characters, and locations.
"""

import re
from typing import List, Dict, Optional, Tuple
from logger_config import setup_logger

logger = setup_logger(__name__)

class CoverPromptService:
    """
    Service for generating intelligent book cover prompts based on story data.
    """
    
    def __init__(self):
        # Genre-specific visual styles and elements
        self.genre_styles = {
            "fantasy": {
                "elements": ["magical aura", "mystical lighting", "ethereal mists", "ancient runes", "dragon scales", "enchanted forests"],
                "mood": "epic fantasy, magical atmosphere, dramatic lighting",
                "color_palette": "golden and emerald tones, rich purples, mystical blues",
                "composition": "epic wide shot, cinematic fantasy composition"
            },
            "historical fiction": {
                "elements": ["period architecture", "historical weapons", "traditional clothing", "ancient battlefields", "sweeping landscapes"],
                "mood": "historical epic, dramatic period atmosphere, authentic details",
                "color_palette": "earth tones, bronze and gold accents, weathered textures",
                "composition": "cinematic historical composition, epic scale"
            },
            "sci-fi": {
                "elements": ["futuristic technology", "space elements", "neon lighting", "cybernetic details", "alien landscapes"],
                "mood": "futuristic, high-tech atmosphere, cosmic scale",
                "color_palette": "electric blues, neon accents, metallic surfaces, deep space colors",
                "composition": "futuristic composition, technological aesthetics"
            },
            "romance": {
                "elements": ["soft lighting", "elegant details", "romantic atmosphere", "beautiful landscapes", "intimate settings"],
                "mood": "romantic, elegant, emotional atmosphere, soft beauty",
                "color_palette": "warm pastels, rose gold, soft pinks, elegant whites",
                "composition": "romantic composition, emotional focus"
            },
            "mystery": {
                "elements": ["shadowy atmosphere", "noir lighting", "mysterious symbols", "urban settings", "detective elements"],
                "mood": "mysterious, suspenseful, dark atmosphere, intriguing",
                "color_palette": "dark blues, noir shadows, dramatic contrasts, muted tones",
                "composition": "mysterious composition, dramatic shadows"
            },
            "thriller": {
                "elements": ["intense atmosphere", "dramatic tension", "urban decay", "action elements", "high contrast"],
                "mood": "intense, suspenseful, high-energy atmosphere, dramatic tension",
                "color_palette": "high contrast, dramatic reds, stark blacks, intense lighting",
                "composition": "dynamic composition, intense focus"
            },
            "horror": {
                "elements": ["dark atmosphere", "gothic elements", "supernatural imagery", "ominous shadows", "haunting details"],
                "mood": "dark, terrifying, atmospheric horror, spine-chilling",
                "color_palette": "deep blacks, blood reds, gothic purples, haunting grays",
                "composition": "horror composition, ominous atmosphere"
            },
            "adventure": {
                "elements": ["action scenes", "exotic locations", "treasure elements", "exploration gear", "dynamic movement"],
                "mood": "adventurous, exciting, dynamic atmosphere, exploration spirit",
                "color_palette": "vibrant colors, tropical tones, adventure browns, exciting contrasts",
                "composition": "dynamic adventure composition, action-packed"
            },
            "contemporary": {
                "elements": ["modern settings", "urban landscapes", "contemporary fashion", "realistic details", "current technology"],
                "mood": "modern, realistic, contemporary atmosphere, relatable",
                "color_palette": "modern color schemes, urban tones, contemporary aesthetics",
                "composition": "contemporary composition, modern realism"
            }
        }
        
        # Character enhancement patterns
        self.character_enhancements = {
            "warrior": ["battle-worn armor", "wielding weapons", "fierce expression", "commanding presence"],
            "king": ["royal regalia", "crown", "majestic bearing", "throne room setting"],
            "queen": ["elegant gown", "royal crown", "graceful pose", "palace setting"],
            "wizard": ["mystical robes", "magical staff", "arcane symbols", "spellcasting pose"],
            "knight": ["shining armor", "noble sword", "chivalrous stance", "medieval setting"],
            "assassin": ["dark clothing", "hidden weapons", "stealthy pose", "shadowy background"],
            "detective": ["trench coat", "magnifying glass", "investigative pose", "urban setting"],
            "pirate": ["nautical clothing", "cutlass", "ship setting", "adventurous pose"]
        }
        
        # Location enhancement patterns
        self.location_enhancements = {
            "castle": ["imposing walls", "medieval architecture", "dramatic sky", "fortress atmosphere"],
            "forest": ["ancient trees", "dappled sunlight", "mystical atmosphere", "natural beauty"],
            "city": ["urban skyline", "bustling streets", "modern architecture", "city lights"],
            "desert": ["vast dunes", "harsh sunlight", "exotic atmosphere", "endless horizons"],
            "mountain": ["towering peaks", "dramatic vistas", "rugged terrain", "majestic scale"],
            "ocean": ["vast waters", "dramatic waves", "nautical elements", "maritime atmosphere"],
            "battlefield": ["conflict scenes", "dramatic tension", "war elements", "epic scale"],
            "palace": ["ornate architecture", "luxurious details", "royal atmosphere", "grand scale"]
        }
    
    def enhance_character_descriptions(self, characters: List[str]) -> List[str]:
        """
        Enhance character names with visual descriptors based on common patterns.
        """
        enhanced = []
        
        for char in characters[:3]:  # Limit to top 3 characters for prompt clarity
            char_lower = char.lower()
            enhanced_char = char
            
            # Look for character type patterns and enhance
            for char_type, enhancements in self.character_enhancements.items():
                if char_type in char_lower:
                    enhancement = enhancements[0]  # Use primary enhancement
                    enhanced_char = f"{char} ({enhancement})"
                    break
            
            # Special handling for historical figures
            if any(name in char_lower for name in ["khan", "genghis", "caesar", "napoleon", "alexander"]):
                enhanced_char = f"{char} (legendary conqueror)"
            elif any(title in char_lower for title in ["king", "queen", "emperor", "empress"]):
                enhanced_char = f"{char} (royal majesty)"
            
            enhanced.append(enhanced_char)
        
        return enhanced
    
    def enhance_location_descriptions(self, locations: List[str]) -> List[str]:
        """
        Enhance location names with atmospheric descriptors.
        """
        enhanced = []
        
        for loc in locations[:3]:  # Limit to top 3 locations for prompt clarity
            loc_lower = loc.lower()
            enhanced_loc = loc
            
            # Look for location type patterns and enhance
            for loc_type, enhancements in self.location_enhancements.items():
                if loc_type in loc_lower:
                    enhancement = enhancements[0]  # Use primary enhancement
                    enhanced_loc = f"{loc} ({enhancement})"
                    break
            
            # Special handling for specific locations
            if "steppe" in loc_lower:
                enhanced_loc = f"{loc} (vast grasslands under endless sky)"
            elif "camp" in loc_lower:
                enhanced_loc = f"{loc} (bustling with activity)"
            elif "temple" in loc_lower:
                enhanced_loc = f"{loc} (sacred and mysterious)"
            
            enhanced.append(enhanced_loc)
        
        return enhanced
    
    def generate_cover_prompt(
        self, 
        title: str, 
        genre: str, 
        main_characters: List[str], 
        key_locations: List[str],
        tone: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate a comprehensive book cover prompt based on story data.
        
        Returns:
            Dict with 'prompt', 'reasoning', and 'elements' keys
        """
        logger.info(f"🎨 Generating cover prompt for '{title}' ({genre})")
        
        # Clean and normalize inputs
        genre = genre.lower() if genre else "contemporary"
        title = title.strip()
        
        # Get genre-specific styling
        genre_info = self.genre_styles.get(genre, self.genre_styles["contemporary"])
        
        # Enhance characters and locations
        enhanced_characters = self.enhance_character_descriptions(main_characters)
        enhanced_locations = self.enhance_location_descriptions(key_locations)
        
        # Build the main prompt components
        prompt_parts = []
        
        # 1. Base prompt with title and genre
        base = f"Professional book cover for '{title}'"
        prompt_parts.append(base)
        
        # 2. Add enhanced characters
        if enhanced_characters:
            char_desc = f"featuring {', '.join(enhanced_characters)}"
            prompt_parts.append(char_desc)
        
        # 3. Add enhanced locations
        if enhanced_locations:
            loc_desc = f"set in {', '.join(enhanced_locations)}"
            prompt_parts.append(loc_desc)
        
        # 4. Add genre-specific elements
        genre_elements = genre_info["elements"][:2]  # Use top 2 elements
        if genre_elements:
            prompt_parts.append(", ".join(genre_elements))
        
        # 5. Add mood and atmosphere
        prompt_parts.append(genre_info["mood"])
        
        # 6. Add color palette
        prompt_parts.append(genre_info["color_palette"])
        
        # 7. Add composition style
        prompt_parts.append(genre_info["composition"])
        
        # 8. Add quality enhancers
        quality_terms = [
            "masterpiece",
            "award-winning book cover art",
            "professional typography",
            "intricate details",
            "atmospheric depth",
            "book cover design"
        ]
        prompt_parts.append(", ".join(quality_terms))
        
        # Combine all parts
        full_prompt = ": ".join(prompt_parts[:3]) + ", " + ", ".join(prompt_parts[3:])
        
        # Generate reasoning
        reasoning = self._generate_reasoning(title, genre, enhanced_characters, enhanced_locations, genre_info)
        
        # Extract key elements for summary
        elements = {
            "characters": enhanced_characters,
            "locations": enhanced_locations,
            "genre_style": genre_info["mood"],
            "color_palette": genre_info["color_palette"]
        }
        
        result = {
            "prompt": full_prompt,
            "reasoning": reasoning,
            "elements": elements,
            "genre": genre,
            "character_count": len(enhanced_characters),
            "location_count": len(enhanced_locations)
        }
        
        logger.info(f"✅ Generated prompt with {len(enhanced_characters)} characters, {len(enhanced_locations)} locations")
        
        return result
    
    def generate_cover_prompt_for_dalle(
        self, 
        title: str, 
        genre: str, 
        main_characters: List[str], 
        key_locations: List[str],
        tone: Optional[str] = None,
        author_name: str = ""
    ) -> Dict[str, str]:
        """
        Generate a DALL-E 3 optimized book cover prompt with text generation capabilities.
        
        Returns:
            Dict with 'prompt', 'reasoning', 'elements', and 'text_prompt' keys
        """
        logger.info(f"🎨 Generating DALL-E 3 optimized cover prompt for '{title}' ({genre})")
        
        # Clean and normalize inputs
        genre = genre.lower() if genre else "contemporary"
        title = title.strip()
        
        # Get genre-specific styling
        genre_info = self.genre_styles.get(genre, self.genre_styles["contemporary"])
        
        # Enhance characters and locations
        enhanced_characters = self.enhance_character_descriptions(main_characters)
        enhanced_locations = self.enhance_location_descriptions(key_locations)
        
        # Build a SIMPLIFIED prompt optimized for DALL-E 3 text generation
        prompt_parts = []
        
        # 1. Start with clear book cover instruction
        prompt_parts.append("Professional book cover design")
        
        # 2. Add main visual elements (simplified)
        if enhanced_characters:
            char_desc = f"featuring {', '.join(enhanced_characters[:2])}"  # Limit to 2 characters
            prompt_parts.append(char_desc)
        
        if enhanced_locations:
            loc_desc = f"in {enhanced_locations[0]}"  # Use only primary location
            prompt_parts.append(loc_desc)
        
        # 3. Add genre mood (simplified)
        prompt_parts.append(genre_info["mood"])
        
        # 4. Add color palette
        prompt_parts.append(genre_info["color_palette"])
        
        # 5. Add essential quality terms for DALL-E 3
        prompt_parts.append("high quality, detailed artwork, professional typography")
        
        # Combine for base prompt (NO text instructions here)
        base_prompt = " ".join(prompt_parts)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(title, genre, enhanced_characters, enhanced_locations, genre_info)
        
        # Extract key elements for summary
        elements = {
            "characters": enhanced_characters,
            "locations": enhanced_locations,
            "genre_style": genre_info["mood"],
            "color_palette": genre_info["color_palette"]
        }
        
        result = {
            "prompt": base_prompt,  # Return base prompt only - text will be added by dalle_service
            "base_prompt": base_prompt,
            "text_prompt": "",  # Empty - will be handled by dalle_service
            "reasoning": reasoning,
            "elements": elements,
            "genre": genre,
            "character_count": len(enhanced_characters),
            "location_count": len(enhanced_locations),
            "title": title,
            "author_name": author_name
        }
        
        logger.info(f"✅ Generated simplified DALL-E 3 base prompt: {base_prompt[:100]}...")
        
        return result
    
    def _generate_reasoning(
        self, 
        title: str, 
        genre: str, 
        characters: List[str], 
        locations: List[str], 
        genre_info: Dict
    ) -> str:
        """
        Generate reasoning for why this prompt was created.
        """
        reasoning_parts = [
            f"This prompt is designed for '{title}', a {genre} story."
        ]
        
        if characters:
            reasoning_parts.append(f"The main characters ({', '.join(characters)}) are prominently featured to create character recognition.")
        
        if locations:
            reasoning_parts.append(f"The key locations ({', '.join(locations)}) provide atmospheric context and setting.")
        
        reasoning_parts.append(f"The {genre} genre styling includes {genre_info['mood']} to match the story's tone.")
        reasoning_parts.append(f"Color palette ({genre_info['color_palette']}) is chosen to evoke the appropriate emotional response.")
        reasoning_parts.append("Professional quality terms ensure high-standard artistic output suitable for commercial book covers.")
        
        return " ".join(reasoning_parts)

# Global service instance
cover_prompt_service = CoverPromptService() 