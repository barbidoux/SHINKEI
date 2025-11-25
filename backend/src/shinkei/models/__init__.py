"""SQLAlchemy models package.

Import all models here to ensure proper relationship configuration.
Models must be imported in dependency order to avoid circular imports.
"""

# Base models (no dependencies)
from shinkei.models.user import User
from shinkei.models.world import World

# Dependent models
from shinkei.models.world_event import WorldEvent
from shinkei.models.story import Story
from shinkei.models.story_beat import StoryBeat
from shinkei.models.beat_modification import BeatModification
from shinkei.models.conversation import Conversation, ConversationMessage

# Entity models (Phase 6)
from shinkei.models.character import Character
from shinkei.models.location import Location
from shinkei.models.entity_mention import EntityMention
from shinkei.models.character_relationship import CharacterRelationship

__all__ = [
    "User",
    "World",
    "WorldEvent",
    "Story",
    "StoryBeat",
    "BeatModification",
    "Conversation",
    "ConversationMessage",
    "Character",
    "Location",
    "EntityMention",
    "CharacterRelationship",
]
