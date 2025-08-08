from fastapi import APIRouter, Depends, HTTPException
from logger_config import setup_logger
from dependencies import get_authenticated_user, get_supabase_client
from services.cover_prompt_service import cover_prompt_service
import requests
import uuid
from services.dalle_service import dalle_service, DalleAPIError
import traceback



router = APIRouter()
logger = setup_logger(__name__)

@router.get("/story/{story_id}/cover_prompt_test")
async def test_cover_prompt_endpoint(
    story_id: int,
    user = Depends(get_authenticated_user)
):
    """
    TEST ENDPOINT: Generate and return a cover prompt for a story without actually creating an image.
    This allows us to test and refine prompt quality before implementing DALL-E 3 integration.
    """
    # Get a fresh Supabase client per request
    supabase = get_supabase_client()
    try:
        logger.info(f"[COVER][PROMPT_TEST] start story_id={story_id} user_id={getattr(user, 'id', None)}")
        
        # Fetch story data from database
        logger.info("[COVER][PROMPT_TEST] fetching story from DB…")
        story_response = supabase.table("Stories").select("*").eq("id", story_id).eq("user_id", user.id).execute()
        
        if not story_response.data:
            logger.warning(f"[COVER][PROMPT_TEST] story_not_found story_id={story_id} user_id={user.id}")
            raise HTTPException(status_code=404, detail="Story not found")
        
        story = story_response.data[0]
        
        # Extract story data
        title = story.get("story_title", "Untitled Story")
        genre = story.get("genre", "contemporary")
        tone = story.get("tone", "")
        
        # Parse JSON fields (they might be stored as strings)
        import json
        main_characters = story.get("main_characters", [])
        key_locations = story.get("key_locations", [])
        
        # Handle if they're stored as JSON strings
        if isinstance(main_characters, str):
            try:
                main_characters = json.loads(main_characters)
            except:
                main_characters = []
        
        if isinstance(key_locations, str):
            try:
                key_locations = json.loads(key_locations)
            except:
                key_locations = []
        
        logger.info("[COVER][PROMPT_TEST] story_data title=%s genre=%s tone=%s chars=%d locs=%d",
                    title, genre, tone, len(main_characters or []), len(key_locations or []))
        
        # Generate the prompt using our smart service for DALL-E 3
        logger.info("[COVER][PROMPT_TEST] generating_prompt…")
        prompt_result = cover_prompt_service.generate_cover_prompt_for_dalle(
            title=title,
            genre=genre,
            main_characters=main_characters,
            key_locations=key_locations,
            tone=tone,
            author_name=user.email.split('@')[0] if user.email else ""
        )
        
        logger.info("[COVER][PROMPT_TEST] prompt_ready title=%s prompt_len=%d base_len=%d",
                    title, len(prompt_result.get('prompt','')), len(prompt_result.get('base_prompt','')))
        
        return {
            "success": True,
            "story_id": story_id,
            "story_data": {
                "title": title,
                "genre": genre,
                "tone": tone,
                "main_characters": main_characters,
                "key_locations": key_locations
            },
            "prompt_result": prompt_result,
            "message": "DALL-E 3 cover prompt generated successfully! Review the prompt quality before implementing image generation."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[COVER][PROMPT_TEST] error story_id=%s err=%s\n%s", story_id, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate cover prompt: {str(e)}")

@router.post("/story/{story_id}/generate_cover")
async def generate_cover_endpoint(
    story_id: int,
    user = Depends(get_authenticated_user)
):
    """
    Generate an AI-powered book cover for a story using OpenAI DALL-E 3.
    
    This endpoint:
    1. Fetches story data from database
    2. Generates an intelligent prompt using story context
    3. Calls OpenAI DALL-E 3 API to generate the cover image with text
    4. Saves the image URL and metadata to database
    """
    # Get a fresh Supabase client per request
    supabase = get_supabase_client()
    try:
        logger.info("[COVER] start_generation story_id=%s user_id=%s", story_id, getattr(user, 'id', None))
        
        # Step 1: Fetch and validate story data
        logger.info("[COVER] fetching_story…")
        story_response = supabase.table("Stories").select("*").eq("id", story_id).eq("user_id", user.id).execute()
        
        if not story_response.data:
            logger.warning("[COVER] story_not_found story_id=%s user_id=%s", story_id, user.id)
            raise HTTPException(status_code=404, detail="Story not found")
        
        story = story_response.data[0]
        
        # Check if cover is already being generated
        current_status = story.get("cover_generation_status", "none")
        logger.info("[COVER] current_status=%s", current_status)
        if current_status == "generating":
            logger.info("[COVER] already_generating story_id=%s", story_id)
            return {
                "success": False,
                "message": "Cover generation is already in progress for this story",
                "status": "generating"
            }
        
        # Step 2: Update status to generating
        logger.info("[COVER] set_status_generating story_id=%s", story_id)
        supabase.table("Stories").update({
            "cover_generation_status": "generating"
        }).eq("id", story_id).eq("user_id", user.id).execute()
        
        try:
            # Step 3: Extract story data
            logger.info("[COVER] extract_story_fields…")
            title = story.get("story_title", "Untitled Story")
            genre = story.get("genre", "contemporary")
            tone = story.get("tone", "")
            
            # Parse JSON fields safely
            import json
            main_characters = story.get("main_characters", [])
            key_locations = story.get("key_locations", [])
            
            # Handle if they're stored as JSON strings
            if isinstance(main_characters, str):
                try:
                    main_characters = json.loads(main_characters)
                except:
                    main_characters = []
            
            if isinstance(key_locations, str):
                try:
                    key_locations = json.loads(key_locations)
                except:
                    key_locations = []
            
            logger.info("[COVER] story_fields title=%s genre=%s tone=%s chars=%d locs=%d",
                        title, genre, tone, len(main_characters or []), len(key_locations or []))
            
            # Step 4: Generate intelligent prompt for DALL-E 3
            logger.info("[COVER] generate_prompt…")
            prompt_result = cover_prompt_service.generate_cover_prompt_for_dalle(
                title=title,
                genre=genre,
                main_characters=main_characters,
                key_locations=key_locations,
                tone=tone,
                author_name=user.email.split('@')[0] if user.email else ""  # Use email prefix as author name
            )
            
            prompt = prompt_result["prompt"]
            logger.info("[COVER] prompt_ready len=%d base_len=%d title=%s",
                        len(prompt_result.get('prompt','')), len(prompt_result.get('base_prompt','')), title)
            
            # Step 5: Generate image using DALL-E 3
            logger.info("[COVER] call_dalle size=1024x1792 quality=hd style=vivid")
            dalle_result = await dalle_service.generate_image_with_text(
                prompt=prompt_result["base_prompt"],
                title=prompt_result["title"],
                author_name=prompt_result["author_name"],
                size="1024x1792",  # Book cover aspect ratio
                quality="hd",
                style="vivid"
            )
            
            primary_image_url = dalle_result["primary_image_url"]
            generation_id = dalle_result["generation_id"]
            image_width = dalle_result.get("image_width", 1792)
            image_height = dalle_result.get("image_height", 1024)
            aspect_ratio = dalle_result.get("aspect_ratio", 1.75)
            logger.info("[COVER] dalle_done gen_id=%s url_len=%d dims=%sx%s",
                        generation_id, len(primary_image_url or ''), image_width, image_height)
            
            # ── Make image permanent – upload to Supabase Storage ──
            try:
                # 1) download the temporary Azure / Leonardo image
                logger.info("[COVER] download_temp_image…")
                img_bytes = requests.get(primary_image_url, timeout=60).content

                # 2) choose a unique filename   e.g. 181_8d72a91e.png
                ext       = "png" if primary_image_url.lower().endswith(".png") else "jpg"
                filename  = f"{story_id}_{uuid.uuid4().hex}.{ext}"
                logger.info("[COVER] upload_to_storage filename=%s ext=%s bytes=%d", filename, ext, len(img_bytes or b''))

                # 3) upload to bucket "covers"
                supabase.storage.from_("covers").upload(
                    filename,
                    img_bytes,
                    { "content-type": f"image/{ext}" }
                )

                # 4) get permanent public URL and overwrite old link
                permanent_url   = supabase.storage.from_("covers").get_public_url(filename)
                primary_image_url = permanent_url
                logger.info("[COVER] storage_public_url url=%s", permanent_url)

            except Exception as e:
                # If upload fails keep temp URL (may expire later)
                logger.error("[COVER] storage_upload_failed err=%s\n%s", str(e), traceback.format_exc())
            
            # Step 6: Update database with successful result including dimensions
            update_data = {
                "cover_image_url": primary_image_url,
                "cover_generation_status": "completed",
                "cover_generated_at": "now()",
                "cover_prompt": prompt,
                "cover_image_width": image_width,
                "cover_image_height": image_height,
                "cover_aspect_ratio": aspect_ratio
            }
            
            logger.info("[COVER] update_db_completed story_id=%s", story_id)
            supabase.table("Stories").update(update_data).eq("id", story_id).eq("user_id", user.id).execute()
            
            logger.info("[COVER] done_success story_id=%s url=%s", story_id, primary_image_url)
            
            return {
                "success": True,
                "story_id": story_id,
                "cover_image_url": primary_image_url,
                "image_width": image_width,
                "image_height": image_height,
                "aspect_ratio": aspect_ratio,
                "generation_id": generation_id,
                "prompt": prompt,
                "prompt_reasoning": prompt_result["reasoning"],
                "dalle_result": dalle_result,
                "message": "Cover generated successfully with DALL-E 3!"
            }
            
        except DalleAPIError as e:
            # Handle DALL-E 3 specific errors
            logger.error("[COVER] dalle_api_error story_id=%s err=%s\n%s", story_id, str(e), traceback.format_exc())
            
            # Update status to failed
            supabase.table("Stories").update({
                "cover_generation_status": "failed"
            }).eq("id", story_id).eq("user_id", user.id).execute()
            
            raise HTTPException(
                status_code=503, 
                detail=f"Image generation service error: {str(e)}"
            )
            
        except Exception as e:
            # Handle other errors
            logger.error("[COVER] unexpected_error story_id=%s err=%s\n%s", story_id, str(e), traceback.format_exc())
            
            # Update status to failed
            supabase.table("Stories").update({
                "cover_generation_status": "failed"
            }).eq("id", story_id).eq("user_id", user.id).execute()
            
            raise HTTPException(
                status_code=500, 
                detail=f"Cover generation failed: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[COVER] critical_error story_id=%s err=%s\n%s", story_id, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/story/{story_id}/cover_status")
async def get_cover_status_endpoint(
    story_id: int,
    user = Depends(get_authenticated_user)
):
    """
    Get the current cover generation status for a story.
    
    Returns status and cover URL if available.
    """
    # Get a fresh Supabase client per request
    supabase = get_supabase_client()
    try:
        logger.info("[COVER][STATUS] fetch story_id=%s", story_id)
        story_response = supabase.table("Stories").select(
            "cover_image_url, cover_generation_status, cover_generated_at, cover_image_width, cover_image_height, cover_aspect_ratio"
        ).eq("id", story_id).eq("user_id", user.id).execute()
        
        if not story_response.data:
            logger.warning("[COVER][STATUS] story_not_found story_id=%s user_id=%s", story_id, user.id)
            raise HTTPException(status_code=404, detail="Story not found")
        
        story = story_response.data[0]
        logger.info("[COVER][STATUS] status=%s has_url=%s",
                    story.get("cover_generation_status"), bool(story.get("cover_image_url")))
        
        return {
            "success": True,
            "story_id": story_id,
            "cover_image_url": story.get("cover_image_url"),
            "image_width": story.get("cover_image_width"),
            "image_height": story.get("cover_image_height"),
            "aspect_ratio": story.get("cover_aspect_ratio"),
            "status": story.get("cover_generation_status", "none"),
            "generated_at": story.get("cover_generated_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting cover status for story {story_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get cover status")
