"""
OpenAI DALL-E 3 API Service for AI Image Generation

This service handles communication with OpenAI DALL-E 3 API for generating
high-quality book cover images with text generation capabilities.
"""

import asyncio
import aiohttp
import time
from typing import Dict, Any, Optional, Tuple
from app.core.config import settings
from app.core.logger_config import setup_logger

logger = setup_logger(__name__)

class DalleAPIError(Exception):
    """Custom exception for DALL-E 3 API errors."""
    pass

class DalleService:
    """
    Service for generating book covers using OpenAI DALL-E 3 API.
    
    Handles async image generation with text capabilities for book titles and author names.
    """
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Configuration
        self.timeout = 180  # seconds for API calls
        self.max_retries = 3
        
        if not self.api_key:
            logger.error("❌ OPENAI_API_KEY not found in environment variables")
            raise ValueError("OpenAI API key is required")
        
        logger.info("✅ DALL-E 3 service initialized")
    
    async def generate_image(
        self, 
        prompt: str,
        size: str = "1792x1024",
        quality: str = "hd",
        style: str = "vivid",
        n: int = 1
    ) -> Dict[str, Any]:
        """
        Generate an image using OpenAI DALL-E 3 API.
        
        Args:
            prompt: The text prompt for image generation
            size: Image size (1792x1024 for book covers)
            quality: Image quality (standard or hd)
            style: Image style (vivid or natural)
            n: Number of images to generate (1 for DALL-E 3)
        
        Returns:
            Dict containing image URLs, dimensions, and metadata
        """
        logger.info(f"🎨 Starting DALL-E 3 image generation with size {size}")
        logger.info(f"📝 Prompt: {prompt[:100]}...")
        
        try:
            # Step 1: Submit generation request
            result = await self._submit_generation_request(
                prompt, size, quality, style, n
            )
            
            logger.info(f"✅ Image generation completed successfully with size {size}")
            return result
            
        except Exception as e:
            logger.error(f"❌ DALL-E 3 image generation failed: {str(e)}")
            raise DalleAPIError(f"Image generation failed: {str(e)}")
    
    async def _submit_generation_request(
        self, 
        prompt: str, 
        size: str, 
        quality: str, 
        style: str, 
        n: int
    ) -> Dict[str, Any]:
        """Submit image generation request to DALL-E 3 API."""
        
        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "style": style,
            "n": n
        }
        
        logger.info(f"📤 Submitting generation request to DALL-E 3")
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                    async with session.post(
                        f"{self.base_url}/images/generations",
                        headers=self.headers,
                        json=payload
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            
                            # Extract image data
                            images = data.get("data", [])
                            if not images:
                                raise DalleAPIError("No images returned from DALL-E 3 API")
                            
                            # Get image URL and metadata
                            image_data = images[0]  # DALL-E 3 returns 1 image
                            image_url = image_data.get("url")
                            revised_prompt = data.get("revised_prompt", prompt)
                            
                            if not image_url:
                                raise DalleAPIError("No image URL returned from DALL-E 3 API")
                            
                            # Parse dimensions from size string
                            width, height = map(int, size.split("x"))
                            aspect_ratio = round(width / height, 2)
                            
                            result = {
                                "status": "completed",
                                "generation_id": f"dalle_{int(time.time())}",  # Generate unique ID
                                "images": [{
                                    "url": image_url,
                                    "id": f"dalle_img_{int(time.time())}",
                                    "revised_prompt": revised_prompt
                                }],
                                "primary_image_url": image_url,
                                "image_width": width,
                                "image_height": height,
                                "aspect_ratio": aspect_ratio,
                                "generated_at": time.time(),
                                "revised_prompt": revised_prompt,
                                "model": "dall-e-3",
                                "quality": quality,
                                "style": style
                            }
                            
                            logger.info(f"✅ DALL-E 3 generation successful! Image URL: {image_url}")
                            return result
                        
                        elif response.status == 429:
                            # Rate limit - wait and retry
                            wait_time = 2 ** attempt  # Exponential backoff
                            logger.warning(f"⚠️ Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                            await asyncio.sleep(wait_time)
                            continue
                        
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ DALL-E 3 API request failed: {response.status} - {error_text}")
                            raise DalleAPIError(f"API request failed: {response.status} - {error_text}")
            
            except aiohttp.ClientError as e:
                if attempt == self.max_retries - 1:
                    raise DalleAPIError(f"Network error: {str(e)}")
                logger.warning(f"⚠️ Network error on attempt {attempt + 1}, retrying...")
                await asyncio.sleep(1)
        
        # If we get here, we've exceeded max retries
        raise DalleAPIError("Image generation failed after maximum retries")
    
    async def generate_image_with_text(
        self, 
        prompt: str,
        title: str,
        author_name: str = "",
        size: str = "1792x1024",
        quality: str = "hd",
        style: str = "vivid"
    ) -> Dict[str, Any]:
        """
        Generate an image with text generation for book titles and author names.
        
        Args:
            prompt: The base image prompt
            title: Book title to display on cover
            author_name: Author name to display (optional)
            size: Image size (1792x1024 for book covers)
            quality: Image quality (standard or hd)
            style: Image style (vivid or natural)
        
        Returns:
            Dict containing image URLs, dimensions, and metadata
        """
        logger.info(f"🎨 Starting DALL-E 3 text generation for '{title}'")
        
        # Enhance prompt for text generation
        enhanced_prompt = self._enhance_prompt_for_text(prompt, title, author_name)
        
        return await self.generate_image(
            prompt=enhanced_prompt,
            size=size,
            quality=quality,
            style=style
        )
    
    def _enhance_prompt_for_text(self, base_prompt: str, title: str, author_name: str = "") -> str:
        """
        Enhance the base prompt to include text generation instructions.
        """
        # Clean and format title
        clean_title = title.strip().replace('"', '').replace("'", "")
        
        # Create SIMPLE text instructions for DALL-E 3
        text_instructions = []
        
        # Add title instruction (simplified)
        text_instructions.append(f"large readable title '{clean_title}' at the top")
        
        # Add author name if provided (simplified)
        if author_name:
            clean_author = author_name.strip().replace('"', '').replace("'", "")
            text_instructions.append(f"author name 'By {clean_author}' at the bottom")
        
        # Combine base prompt with simple text instructions
        enhanced_prompt = f"{base_prompt}, with {', '.join(text_instructions)}"
        
        logger.info(f"📝 Enhanced prompt for text generation: {enhanced_prompt[:150]}...")
        
        return enhanced_prompt
    
    async def get_usage_info(self) -> Dict[str, Any]:
        """Get current usage information from OpenAI API."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(
                    f"{self.base_url}/usage",
                    headers=self.headers
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise DalleAPIError(f"Failed to get usage info: {response.status} - {error_text}")
                    
                    data = await response.json()
                    
                    return {
                        "total_usage": data.get("total_usage", 0),
                        "daily_costs": data.get("daily_costs", []),
                        "object": data.get("object", "usage")
                    }
        
        except Exception as e:
            logger.error(f"❌ Failed to get DALL-E 3 usage info: {str(e)}")
            raise DalleAPIError(f"Failed to get usage info: {str(e)}")

# Global service instance
dalle_service = DalleService() 