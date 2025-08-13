"""
Chat-related data models.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from enum import Enum

class IntentType(Enum):
    """Chat intent types."""
    QUERY = "query"
    MODIFY = "modify"
    MULTIVERSE = "multiverse"
    OTHER = "other"

class ChatMessage(BaseModel):
    """Represents a chat message."""
    
    user_id: str
    story_id: str
    message: str
    session_id: Optional[str] = None
    
    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    """Represents a chat response."""
    
    type: str
    content: str
    intent: Optional[str] = None
    sources: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True





