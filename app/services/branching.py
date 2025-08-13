from typing import Any, Optional


async def get_main_branch_id(story_id: int) -> Optional[int]:
    """Proxy to main.get_main_branch_id if present. Replace with real impl later."""
    try:
        from main import get_main_branch_id as _impl  # type: ignore
        return await _impl(story_id)  # pragma: no cover
    except Exception:
        return None


async def create_new_branch(
    story_id: int, parent_branch_id: Optional[int], branched_from_chapter: int, branch_name: str
) -> int:
    """Proxy to main.create_new_branch if present. Replace with real impl later."""
    from main import create_new_branch as _impl  # type: ignore
    return await _impl(story_id, parent_branch_id, branched_from_chapter, branch_name)  # pragma: no cover


async def copy_chapters_to_branch(
    story_id: int, from_branch_id: Optional[int], to_branch_id: int, up_to_chapter: int
) -> None:
    """Proxy to main.copy_chapters_to_branch if present. Replace with real impl later."""
    from main import copy_chapters_to_branch as _impl  # type: ignore
    return await _impl(story_id, from_branch_id, to_branch_id, up_to_chapter)  # pragma: no cover





