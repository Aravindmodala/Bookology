"""
Story-related data models.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class Story(BaseModel):
    """Unified story model that works with both table schemas."""
    
    id: int
    user_id: uuid.UUID
    title: str
    outline: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    total_chapters: Optional[int] = None
    current_chapter: Optional[int] = None
    source_table: str = "Stories"  # Track which table this came from
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_Stories_table(cls, data: Dict[str, Any]) -> "Story":
        """Create Story from capitalized 'Stories' table."""
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            title=data["story_title"],
            outline=data.get("story_outline"),
            created_at=data["created_at"],
            updated_at=data.get("updated_at"),
            total_chapters=data.get("total_chapters"),
            current_chapter=data.get("current_chapter"),
            source_table="Stories"
        )
    
    @classmethod
    def from_Stories_lowercase(cls, data: Dict[str, Any]) -> "Story":
        """Create Story from lowercase 'Stories' table."""
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            title=data["title"],
            outline=data.get("outline"),
            created_at=data["created_at"],
            updated_at=data.get("updated_at"),
            source_table="Stories"
        )

class Chapter(BaseModel):
    """Unified chapter model."""
    
    id: int
    story_id: int
    chapter_number: int
    title: Optional[str] = None
    content: str
    summary: Optional[str] = None
    dna: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    source_table: str = "Chapters"
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_Chapters_table(cls, data: Dict[str, Any]) -> "Chapter":
        """Create Chapter from capitalized 'Chapters' table."""
        return cls(
            id=data["id"],
            story_id=data["story_id"],
            chapter_number=data["chapter_number"],
            title=data.get("title"),
            content=data["content"],
            summary=data.get("summary"),
            dna=data.get("dna"),
            created_at=data["created_at"],
            updated_at=data.get("updated_at"),
            source_table="Chapters"
        )
    
    @classmethod
    def from_Chapters_lowercase(cls, data: Dict[str, Any]) -> "Chapter":
        """Create Chapter from lowercase 'Chapters' table."""
        return cls(
            id=data["id"],
            story_id=data["story_id"],
            chapter_number=data["chapter_number"],
            title=data.get("title"),
            content=data["content"],
            summary=data.get("summary"),
            dna=data.get("dna"),
            created_at=data["created_at"],
            updated_at=data.get("updated_at"),
            source_table="Chapters"
        )

class StoryWithChapters(BaseModel):
    """Story combined with its Chapters."""
    
    story: Story
    Chapters: List[Chapter] = Field(default_factory=list)
    
    @property
    def total_content_length(self) -> int:
        """Total character count across all Chapters."""
        return sum(len(chapter.content) for chapter in self.Chapters)
    
    @property
    def chapter_count(self) -> int:
        """Number of Chapters."""
        return len(self.Chapters)

class EmbeddingChunk(BaseModel):
    """Represents an embedded text chunk."""
    
    chunk_id: str
    story_id: int
    chapter_id: int
    chapter_number: int
    content: str
    chunk_index: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True