"""Write tools for Story Pilot agent.

These tools allow the agent to create and modify world data.
All write tools require approval in Ask mode.
"""
from typing import Dict, Any, Optional, List
from shinkei.agent.tools.registry import tool, ToolCategory
from shinkei.agent.tools.context import ToolContext
from shinkei.repositories.story_beat import StoryBeatRepository
from shinkei.repositories.character import CharacterRepository
from shinkei.repositories.location import LocationRepository
from shinkei.repositories.world_event import WorldEventRepository
from shinkei.schemas.story_beat import StoryBeatCreate
from shinkei.schemas.character import CharacterCreate, CharacterUpdate
from shinkei.schemas.location import LocationCreate, LocationUpdate


# ========================
# BEAT TOOLS
# ========================

@tool(
    name="create_beat",
    description="Create a new story beat with content. This adds a new narrative segment to the story.",
    parameters={
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The narrative content of the beat"
            },
            "story_id": {
                "type": "string",
                "description": "Story ID. If not provided, uses current story."
            },
            "beat_type": {
                "type": "string",
                "description": "Type of beat: scene, log, memory, dialogue, or description",
                "enum": ["scene", "log", "memory", "dialogue", "description"],
                "default": "scene"
            },
            "summary": {
                "type": "string",
                "description": "Brief summary of the beat"
            },
            "local_time_label": {
                "type": "string",
                "description": "In-world time label (e.g., 'Day 3, Morning')"
            },
            "world_event_id": {
                "type": "string",
                "description": "Link to a world event if applicable"
            },
            "insert_after_beat_id": {
                "type": "string",
                "description": "Insert after this beat ID (for mid-story insertion)"
            }
        },
        "required": ["content"]
    },
    requires_approval=True,
    category=ToolCategory.WRITE
)
async def create_beat(
    context: ToolContext,
    content: str,
    story_id: Optional[str] = None,
    beat_type: str = "scene",
    summary: Optional[str] = None,
    local_time_label: Optional[str] = None,
    world_event_id: Optional[str] = None,
    insert_after_beat_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new story beat."""
    if not story_id:
        story_id = context.require_story()

    repo = StoryBeatRepository(context.session)

    # Determine order_index
    if insert_after_beat_id:
        after_beat = await repo.get_by_id(insert_after_beat_id)
        if after_beat:
            order_index = after_beat.order_index + 1
            # Shift subsequent beats
            await repo.shift_beats_after(story_id, order_index)
        else:
            # Append to end
            beats, _ = await repo.list_by_story(story_id)
            order_index = len(beats)
    else:
        # Append to end
        beats, _ = await repo.list_by_story(story_id)
        order_index = len(beats)

    beat_data = StoryBeatCreate(
        story_id=story_id,
        content=content,
        type=beat_type,
        order_index=order_index,
        summary=summary,
        local_time_label=local_time_label,
        world_event_id=world_event_id,
        generated_by="ai"
    )

    beat = await repo.create(beat_data)

    return {
        "success": True,
        "beat_id": beat.id,
        "order_index": beat.order_index,
        "message": f"Created beat at position {beat.order_index}"
    }


@tool(
    name="update_beat",
    description="Update an existing story beat's content or metadata.",
    parameters={
        "type": "object",
        "properties": {
            "beat_id": {
                "type": "string",
                "description": "Beat ID to update"
            },
            "content": {
                "type": "string",
                "description": "New content (optional)"
            },
            "summary": {
                "type": "string",
                "description": "New summary (optional)"
            },
            "local_time_label": {
                "type": "string",
                "description": "New time label (optional)"
            }
        },
        "required": ["beat_id"]
    },
    requires_approval=True,
    category=ToolCategory.WRITE
)
async def update_beat(
    context: ToolContext,
    beat_id: str,
    content: Optional[str] = None,
    summary: Optional[str] = None,
    local_time_label: Optional[str] = None
) -> Dict[str, Any]:
    """Update an existing beat."""
    repo = StoryBeatRepository(context.session)

    beat = await repo.get_by_id(beat_id)
    if not beat:
        return {"error": "Beat not found"}

    update_data = {}
    if content is not None:
        update_data["content"] = content
    if summary is not None:
        update_data["summary"] = summary
    if local_time_label is not None:
        update_data["local_time_label"] = local_time_label

    if not update_data:
        return {"error": "No updates provided"}

    from shinkei.schemas.story_beat import StoryBeatUpdate
    updated = await repo.update(beat_id, StoryBeatUpdate(**update_data))

    return {
        "success": True,
        "beat_id": beat_id,
        "updated_fields": list(update_data.keys())
    }


@tool(
    name="delete_beat",
    description="Delete a story beat. This action cannot be undone.",
    parameters={
        "type": "object",
        "properties": {
            "beat_id": {
                "type": "string",
                "description": "Beat ID to delete"
            }
        },
        "required": ["beat_id"]
    },
    requires_approval=True,
    category=ToolCategory.WRITE
)
async def delete_beat(context: ToolContext, beat_id: str) -> Dict[str, Any]:
    """Delete a story beat."""
    repo = StoryBeatRepository(context.session)

    deleted = await repo.delete(beat_id)
    if not deleted:
        return {"error": "Beat not found"}

    return {"success": True, "message": f"Beat {beat_id} deleted"}


# ========================
# CHARACTER TOOLS
# ========================

@tool(
    name="create_character",
    description="Create a new character in the current world.",
    parameters={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Character name"
            },
            "description": {
                "type": "string",
                "description": "Character description and background"
            },
            "role": {
                "type": "string",
                "description": "Character's role in the story (e.g., protagonist, antagonist, mentor)"
            },
            "importance": {
                "type": "string",
                "description": "Character importance level",
                "enum": ["major", "minor", "background"],
                "default": "minor"
            },
            "aliases": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Alternative names or nicknames"
            }
        },
        "required": ["name"]
    },
    requires_approval=True,
    category=ToolCategory.WRITE
)
async def create_character(
    context: ToolContext,
    name: str,
    description: Optional[str] = None,
    role: Optional[str] = None,
    importance: str = "minor",
    aliases: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create a new character."""
    world_id = context.require_world()

    repo = CharacterRepository(context.session)

    # Check if character with same name exists
    existing = await repo.search_by_name(world_id, name)
    exact_match = [c for c in existing if c.name.lower() == name.lower()]
    if exact_match:
        return {"error": f"Character '{name}' already exists in this world"}

    character_data = CharacterCreate(
        name=name,
        description=description,
        role=role,
        importance=importance,
        aliases=aliases,
    )

    character = await repo.create(world_id, character_data)

    return {
        "success": True,
        "character_id": character.id,
        "name": character.name,
        "message": f"Created character '{name}'"
    }


@tool(
    name="update_character",
    description="Update an existing character's information.",
    parameters={
        "type": "object",
        "properties": {
            "character_id": {
                "type": "string",
                "description": "Character ID to update"
            },
            "name": {
                "type": "string",
                "description": "New name (optional)"
            },
            "description": {
                "type": "string",
                "description": "New description (optional)"
            },
            "role": {
                "type": "string",
                "description": "New role (optional)"
            },
            "importance": {
                "type": "string",
                "description": "New importance level",
                "enum": ["major", "minor", "background"]
            }
        },
        "required": ["character_id"]
    },
    requires_approval=True,
    category=ToolCategory.WRITE
)
async def update_character(
    context: ToolContext,
    character_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    role: Optional[str] = None,
    importance: Optional[str] = None
) -> Dict[str, Any]:
    """Update a character."""
    repo = CharacterRepository(context.session)

    update_data = {}
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description
    if role is not None:
        update_data["role"] = role
    if importance is not None:
        update_data["importance"] = importance

    if not update_data:
        return {"error": "No updates provided"}

    updated = await repo.update(character_id, CharacterUpdate(**update_data))
    if not updated:
        return {"error": "Character not found"}

    return {
        "success": True,
        "character_id": character_id,
        "updated_fields": list(update_data.keys())
    }


# ========================
# LOCATION TOOLS
# ========================

@tool(
    name="create_location",
    description="Create a new location in the current world.",
    parameters={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Location name"
            },
            "description": {
                "type": "string",
                "description": "Location description"
            },
            "parent_id": {
                "type": "string",
                "description": "Parent location ID for hierarchical locations"
            },
            "importance": {
                "type": "string",
                "description": "Location importance level",
                "enum": ["major", "minor", "background"],
                "default": "minor"
            }
        },
        "required": ["name"]
    },
    requires_approval=True,
    category=ToolCategory.WRITE
)
async def create_location(
    context: ToolContext,
    name: str,
    description: Optional[str] = None,
    parent_id: Optional[str] = None,
    importance: str = "minor"
) -> Dict[str, Any]:
    """Create a new location."""
    world_id = context.require_world()

    repo = LocationRepository(context.session)

    location_data = LocationCreate(
        name=name,
        description=description,
        parent_id=parent_id,
        importance=importance,
    )

    location = await repo.create(world_id, location_data)

    return {
        "success": True,
        "location_id": location.id,
        "name": location.name,
        "message": f"Created location '{name}'"
    }


@tool(
    name="update_location",
    description="Update an existing location's information.",
    parameters={
        "type": "object",
        "properties": {
            "location_id": {
                "type": "string",
                "description": "Location ID to update"
            },
            "name": {
                "type": "string",
                "description": "New name (optional)"
            },
            "description": {
                "type": "string",
                "description": "New description (optional)"
            },
            "parent_id": {
                "type": "string",
                "description": "New parent location ID (optional)"
            },
            "importance": {
                "type": "string",
                "description": "New importance level",
                "enum": ["major", "minor", "background"]
            }
        },
        "required": ["location_id"]
    },
    requires_approval=True,
    category=ToolCategory.WRITE
)
async def update_location(
    context: ToolContext,
    location_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    parent_id: Optional[str] = None,
    importance: Optional[str] = None
) -> Dict[str, Any]:
    """Update a location."""
    repo = LocationRepository(context.session)

    update_data = {}
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description
    if parent_id is not None:
        update_data["parent_id"] = parent_id
    if importance is not None:
        update_data["importance"] = importance

    if not update_data:
        return {"error": "No updates provided"}

    updated = await repo.update(location_id, LocationUpdate(**update_data))
    if not updated:
        return {"error": "Location not found"}

    return {
        "success": True,
        "location_id": location_id,
        "updated_fields": list(update_data.keys())
    }


# ========================
# WORLD EVENT TOOLS
# ========================

@tool(
    name="create_event",
    description="Create a new world event on the global timeline.",
    parameters={
        "type": "object",
        "properties": {
            "t": {
                "type": "number",
                "description": "Objective time value on the world timeline"
            },
            "label_time": {
                "type": "string",
                "description": "Human-readable time label (e.g., 'Year 1042, Summer')"
            },
            "summary": {
                "type": "string",
                "description": "Summary of what happened"
            },
            "event_type": {
                "type": "string",
                "description": "Type of event",
                "enum": ["historical", "plot", "character", "world", "minor"]
            },
            "location_id": {
                "type": "string",
                "description": "Location where the event occurred"
            }
        },
        "required": ["t", "summary"]
    },
    requires_approval=True,
    category=ToolCategory.WRITE
)
async def create_event(
    context: ToolContext,
    t: float,
    summary: str,
    label_time: Optional[str] = None,
    event_type: Optional[str] = None,
    location_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new world event."""
    world_id = context.require_world()

    repo = WorldEventRepository(context.session)

    from shinkei.schemas.world_event import WorldEventCreate
    event_data = WorldEventCreate(
        t=t,
        label_time=label_time,
        summary=summary,
        event_type=event_type,
        location_id=location_id,
    )

    event = await repo.create(world_id, event_data)

    return {
        "success": True,
        "event_id": event.id,
        "t": event.t,
        "message": f"Created event at t={t}"
    }


# ========================
# ENTITY MENTION TOOLS
# ========================

@tool(
    name="add_entity_mention",
    description="Record that an entity (character or location) appears in a beat.",
    parameters={
        "type": "object",
        "properties": {
            "beat_id": {
                "type": "string",
                "description": "Beat ID where the entity appears"
            },
            "entity_type": {
                "type": "string",
                "description": "Type of entity",
                "enum": ["character", "location"]
            },
            "entity_id": {
                "type": "string",
                "description": "ID of the entity (character_id or location_id)"
            },
            "mention_type": {
                "type": "string",
                "description": "How the entity is mentioned",
                "enum": ["explicit", "implicit", "referenced"],
                "default": "explicit"
            },
            "context_snippet": {
                "type": "string",
                "description": "Text snippet where entity appears"
            }
        },
        "required": ["beat_id", "entity_type", "entity_id"]
    },
    requires_approval=True,
    category=ToolCategory.WRITE
)
async def add_entity_mention(
    context: ToolContext,
    beat_id: str,
    entity_type: str,
    entity_id: str,
    mention_type: str = "explicit",
    context_snippet: Optional[str] = None
) -> Dict[str, Any]:
    """Add an entity mention to a beat."""
    from shinkei.repositories.entity_mention import EntityMentionRepository
    from shinkei.schemas.entity_mention import EntityMentionCreate

    repo = EntityMentionRepository(context.session)

    mention_data = EntityMentionCreate(
        story_beat_id=beat_id,
        entity_type=entity_type,
        entity_id=entity_id,
        mention_type=mention_type,
        context_snippet=context_snippet,
        detected_by="ai"
    )

    mention = await repo.create(mention_data)

    return {
        "success": True,
        "mention_id": mention.id,
        "message": f"Added {entity_type} mention to beat"
    }
