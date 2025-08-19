from typing import Any, Optional
from app.dependencies.supabase import get_supabase_client, get_supabase_async
from app.core.logger_config import setup_logger
from app.core.concurrency import DB_SEMAPHORE

logger = setup_logger(__name__)


async def get_main_branch_id(story_id: int) -> Optional[int]:
    """Get the main branch ID for a story. Returns None if no main branch exists."""
    try:
        # Use async client with concurrency control
        async with DB_SEMAPHORE:
            supabase = await get_supabase_async()
            
            # Query for the main branch (usually branch_id=1 or the first branch created)
            # For now, we'll implement a simple logic - return 1 as the main branch
            # In a full implementation, this would query a branches table
            
            # Check if story exists and has chapters with branch_id
            chapters_response = await supabase.table("Chapters").select("branch_id").eq("story_id", story_id).limit(1).execute()
            
            if chapters_response.data:
                # Return the first branch_id found, or default to 1
                first_branch = chapters_response.data[0].get("branch_id")
                return first_branch if first_branch is not None else 1
            
            # Default to main branch ID = 1
            return 1
        
    except Exception as e:
        logger.error(f"Error getting main branch ID for story {story_id}: {e}")
        return None


async def create_new_branch(
    story_id: int, parent_branch_id: Optional[int], branched_from_chapter: int, branch_name: str
) -> int:
    """Create a new branch for a story. Returns the new branch ID."""
    try:
        async with DB_SEMAPHORE:
            supabase = await get_supabase_async()
            
            # For now, we'll use a simple incrementing branch ID system
            # In a full implementation, this would insert into a branches table
            
            # Get the highest existing branch_id for this story
            branches_response = await supabase.table("Chapters").select("branch_id").eq("story_id", story_id).execute()
            
            existing_branch_ids = [row.get("branch_id", 1) for row in branches_response.data if row.get("branch_id") is not None]
            
            if existing_branch_ids:
                new_branch_id = max(existing_branch_ids) + 1
            else:
                new_branch_id = 2  # Start with 2, assuming 1 is the main branch
            
            logger.info(f"Created new branch {new_branch_id} for story {story_id} from chapter {branched_from_chapter}")
            return new_branch_id
        
    except Exception as e:
        logger.error(f"Error creating new branch for story {story_id}: {e}")
        raise


async def copy_chapters_to_branch(
    story_id: int, from_branch_id: Optional[int], to_branch_id: int, up_to_chapter: int
) -> None:
    """Copy chapters from one branch to another up to a specific chapter number."""
    try:
        supabase = get_supabase_client()
        
        # Get all chapters from the source branch up to the specified chapter
        query = supabase.table("Chapters").select("*").eq("story_id", story_id).lte("chapter_number", up_to_chapter)
        
        if from_branch_id is not None:
            query = query.eq("branch_id", from_branch_id)
        
        chapters_response = query.order("chapter_number").execute()
        chapters_to_copy = chapters_response.data
        
        # Copy each chapter to the new branch
        for chapter in chapters_to_copy:
            # Create a copy with the new branch_id
            new_chapter = dict(chapter)
            del new_chapter["id"]  # Remove the original ID
            new_chapter["branch_id"] = to_branch_id
            new_chapter["is_active"] = True
            
            # Insert the copied chapter
            supabase.table("Chapters").insert(new_chapter).execute()
        
        # Also copy choices for these chapters
        choices_query = supabase.table("story_choices").select("*").eq("story_id", story_id).lte("chapter_number", up_to_chapter)
        
        if from_branch_id is not None:
            choices_query = choices_query.eq("branch_id", from_branch_id)
            
        choices_response = choices_query.execute()
        choices_to_copy = choices_response.data
        
        for choice in choices_to_copy:
            # Create a copy with the new branch_id
            new_choice = dict(choice)
            del new_choice["id"]  # Remove the original ID
            new_choice["branch_id"] = to_branch_id
            
            # Insert the copied choice
            supabase.table("story_choices").insert(new_choice).execute()
        
        logger.info(f"Copied {len(chapters_to_copy)} chapters and {len(choices_to_copy)} choices to branch {to_branch_id}")
        
    except Exception as e:
        logger.error(f"Error copying chapters to branch {to_branch_id}: {e}")
        raise





