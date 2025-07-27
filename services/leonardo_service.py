"""
Leonardo.ai API Service for AI Image Generation

This service handles communication with Leonardo.ai API for generating
high-quality book cover images using intelligent prompts.
"""

import asyncio
import aiohttp
import time
from typing import Dict, Any, Optional, Tuple
from config import settings
from logger_config import setup_logger

logger = setup_logger(__name__)

class LeonardoAPIError(Exception):
    """Custom exception for Leonardo API errors."""
    pass

class LeonardoService:
    """
    Service for generating book covers using Leonardo.ai API.
    
    Handles async image generation, polling for completion, and error recovery.
    """
    
    def __init__(self):
        self.api_key = settings.LEONARDO_API_KEY
        self.base_url = "https://cloud.leonardo.ai/api/rest/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Configuration
        self.max_poll_attempts = 60  # 5 minutes max (5s intervals)
        self.poll_interval = 5  # seconds
        self.timeout = 30  # seconds for API calls
        
        if not self.api_key:
            logger.error("❌ LEONARDO_API_KEY not found in environment variables")
            raise ValueError("Leonardo API key is required")
        
        logger.info("✅ Leonardo.ai service initialized")
    
    async def generate_image(
        self, 
        prompt: str, 
        model_id: str = "ac614f96-1082-45bf-be9d-757f2d31c174",  # DreamShaper v7
        width: int = 832,
        height: int = 1216,
        num_images: int = 1
    ) -> Dict[str, Any]:
        """
        Generate an image using Leonardo.ai API.
        
        Args:
            prompt: The text prompt for image generation
            model_id: Leonardo model ID to use
            width: Image width (must be multiple of 8)
            height: Image height (must be multiple of 8)
            num_images: Number of images to generate (1-4)
        
        Returns:
            Dict containing image URLs, dimensions, and metadata
        """
        logger.info(f"🎨 Starting Leonardo.ai image generation with dimensions {width}x{height}")
        logger.info(f"📝 Prompt: {prompt[:100]}...")
        
        try:
            # Step 1: Submit generation request
            generation_id = await self._submit_generation_request(
                prompt, model_id, width, height, num_images
            )
            
            # Step 2: Poll for completion
            result = await self._poll_for_completion(generation_id, width, height)
            
            logger.info(f"✅ Image generation completed successfully with dimensions {width}x{height}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Leonardo.ai image generation failed: {str(e)}")
            raise LeonardoAPIError(f"Image generation failed: {str(e)}")
    
    async def _submit_generation_request(
        self, 
        prompt: str, 
        model_id: str, 
        width: int, 
        height: int, 
        num_images: int
    ) -> str:
        """Submit image generation request to Leonardo.ai."""
        
        payload = {
            "prompt": prompt,
            "modelId": model_id,
            "width": width,
            "height": height,
            "num_images": num_images,
            "guidance_scale": 7,  # How closely to follow the prompt (1-20)
            "num_inference_steps": 30,  # Quality vs speed tradeoff
            "scheduler": "LEONARDO",  # Leonardo's proprietary scheduler
            "presetStyle": "LEONARDO",  # Use Leonardo's style preset
            "public": False,  # Keep images private
            "promptMagic": True,  # Enhance prompt automatically
            "alchemy": True,  # Use Alchemy for higher quality
            "photoReal": False,  # We want artistic style, not photorealistic
            "contrastRatio": 1.0  # Balanced contrast (float value)
        }
        
        logger.info(f"📤 Submitting generation request to Leonardo.ai")
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            async with session.post(
                f"{self.base_url}/generations",
                headers=self.headers,
                json=payload
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ Leonardo API request failed: {response.status} - {error_text}")
                    raise LeonardoAPIError(f"API request failed: {response.status} - {error_text}")
                
                data = await response.json()
                generation_id = data.get("sdGenerationJob", {}).get("generationId")
                
                if not generation_id:
                    logger.error(f"❌ No generation ID returned from Leonardo API")
                    raise LeonardoAPIError("No generation ID returned from API")
                
                logger.info(f"✅ Generation request submitted. ID: {generation_id}")
                return generation_id
    
    async def _poll_for_completion(self, generation_id: str, width: int, height: int) -> Dict[str, Any]:
        """Poll Leonardo.ai API until image generation is complete."""
        
        logger.info(f"⏳ Polling for completion of generation {generation_id}")
        
        for attempt in range(self.max_poll_attempts):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                    async with session.get(
                        f"{self.base_url}/generations/{generation_id}",
                        headers=self.headers
                    ) as response:
                        
                        if response.status != 200:
                            error_text = await response.text()
                            logger.warning(f"⚠️ Polling attempt {attempt + 1} failed: {response.status}")
                            
                            if attempt == self.max_poll_attempts - 1:
                                raise LeonardoAPIError(f"Polling failed: {response.status} - {error_text}")
                            
                            await asyncio.sleep(self.poll_interval)
                            continue
                        
                        data = await response.json()
                        generations = data.get("generations_by_pk", {}).get("generated_images", [])
                        status = data.get("generations_by_pk", {}).get("status")
                        
                        logger.info(f"📊 Generation status: {status} (attempt {attempt + 1}/{self.max_poll_attempts})")
                        
                        if status == "COMPLETE" and generations:
                            # Extract image URLs
                            image_urls = []
                            for img in generations:
                                if img.get("url"):
                                    image_urls.append({
                                        "url": img["url"],
                                        "id": img.get("id"),
                                        "seed": img.get("seed")
                                    })
                            
                            if image_urls:
                                result = {
                                    "status": "completed",
                                    "generation_id": generation_id,
                                    "images": image_urls,
                                    "primary_image_url": image_urls[0]["url"],  # Use first image as primary
                                    "image_width": width,
                                    "image_height": height,
                                    "aspect_ratio": round(width / height, 2),
                                    "generated_at": time.time()
                                }
                                
                                logger.info(f"✅ Generation completed! Generated {len(image_urls)} images at {width}x{height}")
                                return result
                        
                        elif status in ["FAILED", "CANCELLED"]:
                            error_msg = f"Generation {status.lower()}"
                            logger.error(f"❌ {error_msg}")
                            raise LeonardoAPIError(error_msg)
                        
                        # Status is still PENDING, continue polling
                        await asyncio.sleep(self.poll_interval)
            
            except aiohttp.ClientError as e:
                logger.warning(f"⚠️ Network error during polling attempt {attempt + 1}: {str(e)}")
                if attempt == self.max_poll_attempts - 1:
                    raise LeonardoAPIError(f"Network error during polling: {str(e)}")
                await asyncio.sleep(self.poll_interval)
        
        # If we get here, we've exceeded max attempts
        logger.error(f"❌ Generation timed out after {self.max_poll_attempts} attempts")
        raise LeonardoAPIError("Image generation timed out")
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get user information and remaining credits."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(
                    f"{self.base_url}/me",
                    headers=self.headers
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise LeonardoAPIError(f"Failed to get user info: {response.status} - {error_text}")
                    
                    data = await response.json()
                    user_details = data.get("user_details", [{}])[0]
                    
                    return {
                        "user_id": user_details.get("user", {}).get("id"),
                        "username": user_details.get("user", {}).get("username"),
                        "token_renewal_date": user_details.get("tokenRenewalDate"),
                        "subscription_tokens": user_details.get("subscriptionTokens", 0),
                        "subscription_gpt_tokens": user_details.get("subscriptionGptTokens", 0)
                    }
        
        except Exception as e:
            logger.error(f"❌ Failed to get Leonardo user info: {str(e)}")
            raise LeonardoAPIError(f"Failed to get user info: {str(e)}")

# Global service instance
leonardo_service = LeonardoService() 