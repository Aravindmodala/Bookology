from typing import Any


async def get_next_chapter_version_number(story_id: int, chapter_number: int, supabase: Any) -> int:
    """Get the next version number for a chapter (highest + 1)."""
    response = (
        supabase.table("Chapters")
        .select("version_number")
        .eq("story_id", story_id)
        .eq("chapter_number", chapter_number)
        .execute()
    )
    versions = [row["version_number"] for row in response.data] if response.data else []
    return max(versions) + 1 if versions else 1


async def deactivate_previous_chapter_versions(story_id: int, chapter_number: int, supabase: Any) -> None:
    """Set is_active=False for all previous versions of a chapter."""
    (
        supabase.table("Chapters")
        .update({"is_active": False})
        .eq("story_id", story_id)
        .eq("chapter_number", chapter_number)
        .execute()
    )


async def save_choices_for_chapter(
    story_id: int,
    chapter_id: int,
    chapter_number: int,
    choices: list,
    user_id: str,
    supabase: Any,
) -> None:
    """Save choices to the story_choices table for any chapter."""
    for i, choice in enumerate(choices, 1):
        choice_record = {
            "story_id": story_id,
            "chapter_id": chapter_id,
            "chapter_number": chapter_number,
            "choice_id": choice.get("id", f"choice_{i}"),
            "title": choice.get("title", ""),
            "description": choice.get("description", ""),
            "story_impact": choice.get("story_impact", ""),
            "choice_type": choice.get("choice_type", ""),
            "user_id": user_id,
            "is_selected": False,
        }
        supabase.table("story_choices").insert(choice_record).execute()





