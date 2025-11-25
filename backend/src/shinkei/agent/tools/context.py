"""Tool execution context for Story Pilot agent.

This module provides the context object passed to all tool handlers,
giving them access to the database session, user info, and current
navigation context.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class NavigationContext:
    """
    Current navigation context - where the user is in the app.

    Attributes:
        world_id: Current world ID (if any)
        story_id: Current story ID (if any)
        beat_id: Current beat ID (if any)
        character_id: Current character ID (if any)
        location_id: Current location ID (if any)
    """
    world_id: Optional[str] = None
    story_id: Optional[str] = None
    beat_id: Optional[str] = None
    character_id: Optional[str] = None
    location_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Convert to dictionary."""
        return {
            "world_id": self.world_id,
            "story_id": self.story_id,
            "beat_id": self.beat_id,
            "character_id": self.character_id,
            "location_id": self.location_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NavigationContext":
        """Create from dictionary."""
        return cls(
            world_id=data.get("world_id"),
            story_id=data.get("story_id"),
            beat_id=data.get("beat_id"),
            character_id=data.get("character_id"),
            location_id=data.get("location_id"),
        )


@dataclass
class ToolContext:
    """
    Execution context for tool handlers.

    Provides tools with access to the database session, user information,
    and current navigation context.

    Attributes:
        session: SQLAlchemy async database session
        user_id: Current user's ID
        conversation_id: Current conversation ID
        navigation: Current navigation context
        extra: Additional context data
    """
    session: AsyncSession
    user_id: str
    conversation_id: str
    navigation: NavigationContext = field(default_factory=NavigationContext)
    extra: Dict[str, Any] = field(default_factory=dict)

    @property
    def world_id(self) -> Optional[str]:
        """Shortcut to navigation.world_id."""
        return self.navigation.world_id

    @property
    def story_id(self) -> Optional[str]:
        """Shortcut to navigation.story_id."""
        return self.navigation.story_id

    @property
    def beat_id(self) -> Optional[str]:
        """Shortcut to navigation.beat_id."""
        return self.navigation.beat_id

    def require_world(self) -> str:
        """
        Require that a world is selected.

        Returns:
            World ID

        Raises:
            ValueError: If no world is selected
        """
        if not self.navigation.world_id:
            raise ValueError("No world selected. Please navigate to a world first.")
        return self.navigation.world_id

    def require_story(self) -> str:
        """
        Require that a story is selected.

        Returns:
            Story ID

        Raises:
            ValueError: If no story is selected
        """
        if not self.navigation.story_id:
            raise ValueError("No story selected. Please navigate to a story first.")
        return self.navigation.story_id
