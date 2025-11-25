"""Read tools for Story Pilot agent.

These tools allow the agent to read and retrieve information about
worlds, stories, characters, locations, events, and beats.
"""
from typing import Dict, Any, Optional, List
from shinkei.agent.tools.registry import tool, ToolCategory
from shinkei.agent.tools.context import ToolContext
from shinkei.repositories.world import WorldRepository
from shinkei.repositories.story import StoryRepository
from shinkei.repositories.story_beat import StoryBeatRepository
from shinkei.repositories.character import CharacterRepository
from shinkei.repositories.location import LocationRepository
from shinkei.repositories.world_event import WorldEventRepository


# ========================
# WORLD TOOLS
# ========================

@tool(
    name="get_world",
    description="Get details about the current world including its name, description, tone, backdrop, laws, and chronology mode.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    },
    category=ToolCategory.READ
)
async def get_world(context: ToolContext) -> Dict[str, Any]:
    """Get current world details."""
    world_id = context.require_world()

    repo = WorldRepository(context.session)
    world = await repo.get_by_id(world_id)

    if not world:
        return {"error": "World not found"}

    return {
        "id": world.id,
        "name": world.name,
        "description": world.description,
        "tone": world.tone,
        "backdrop": world.backdrop,
        "laws": world.laws,
        "chronology_mode": world.chronology_mode.value if world.chronology_mode else None,
        "created_at": world.created_at.isoformat(),
    }


# ========================
# STORY TOOLS
# ========================

@tool(
    name="get_story",
    description="Get details about a specific story including title, synopsis, status, mode, and tags.",
    parameters={
        "type": "object",
        "properties": {
            "story_id": {
                "type": "string",
                "description": "Story ID. If not provided, uses current story."
            }
        },
        "required": []
    },
    category=ToolCategory.READ
)
async def get_story(context: ToolContext, story_id: Optional[str] = None) -> Dict[str, Any]:
    """Get story details."""
    if not story_id:
        story_id = context.require_story()

    repo = StoryRepository(context.session)
    story = await repo.get_by_id(story_id)

    if not story:
        return {"error": "Story not found"}

    return {
        "id": story.id,
        "world_id": story.world_id,
        "title": story.title,
        "synopsis": story.synopsis,
        "theme": story.theme,
        "status": story.status.value if story.status else None,
        "mode": story.mode.value if story.mode else None,
        "pov_type": story.pov_type.value if story.pov_type else None,
        "tags": story.tags,
        "created_at": story.created_at.isoformat(),
    }


@tool(
    name="list_stories",
    description="List all stories in the current world.",
    parameters={
        "type": "object",
        "properties": {
            "include_archived": {
                "type": "boolean",
                "description": "Include archived stories",
                "default": False
            },
            "tag": {
                "type": "string",
                "description": "Filter by tag"
            }
        },
        "required": []
    },
    category=ToolCategory.READ
)
async def list_stories(
    context: ToolContext,
    include_archived: bool = False,
    tag: Optional[str] = None
) -> Dict[str, Any]:
    """List stories in current world."""
    world_id = context.require_world()

    repo = StoryRepository(context.session)
    stories, total = await repo.list_by_world(
        world_id=world_id,
        include_archived=include_archived,
        tag=tag
    )

    return {
        "stories": [
            {
                "id": s.id,
                "title": s.title,
                "status": s.status.value if s.status else None,
                "mode": s.mode.value if s.mode else None,
                "tags": s.tags,
            }
            for s in stories
        ],
        "total": total
    }


# ========================
# BEAT TOOLS
# ========================

@tool(
    name="get_beat",
    description="Get a specific story beat including its content, type, and metadata.",
    parameters={
        "type": "object",
        "properties": {
            "beat_id": {
                "type": "string",
                "description": "Beat ID to retrieve"
            }
        },
        "required": ["beat_id"]
    },
    category=ToolCategory.READ
)
async def get_beat(context: ToolContext, beat_id: str) -> Dict[str, Any]:
    """Get beat details."""
    repo = StoryBeatRepository(context.session)
    beat = await repo.get_by_id(beat_id)

    if not beat:
        return {"error": "Beat not found"}

    return {
        "id": beat.id,
        "story_id": beat.story_id,
        "content": beat.content,
        "type": beat.type.value if beat.type else None,
        "order_index": beat.order_index,
        "summary": beat.summary,
        "local_time_label": beat.local_time_label,
        "world_event_id": beat.world_event_id,
        "generated_by": beat.generated_by.value if beat.generated_by else None,
        "created_at": beat.created_at.isoformat(),
    }


@tool(
    name="list_beats",
    description="List story beats in a story, ordered by their sequence.",
    parameters={
        "type": "object",
        "properties": {
            "story_id": {
                "type": "string",
                "description": "Story ID. If not provided, uses current story."
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of beats to return",
                "default": 20
            }
        },
        "required": []
    },
    category=ToolCategory.READ
)
async def list_beats(
    context: ToolContext,
    story_id: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """List beats in a story."""
    if not story_id:
        story_id = context.require_story()

    repo = StoryBeatRepository(context.session)
    beats, total = await repo.list_by_story(story_id=story_id, limit=limit)

    return {
        "beats": [
            {
                "id": b.id,
                "order_index": b.order_index,
                "type": b.type.value if b.type else None,
                "summary": b.summary,
                "local_time_label": b.local_time_label,
                "content_preview": b.content[:200] + "..." if len(b.content) > 200 else b.content,
            }
            for b in beats
        ],
        "total": total
    }


@tool(
    name="get_recent_beats",
    description="Get the most recent beats in the current story for context.",
    parameters={
        "type": "object",
        "properties": {
            "count": {
                "type": "integer",
                "description": "Number of recent beats to retrieve",
                "default": 5
            }
        },
        "required": []
    },
    category=ToolCategory.READ
)
async def get_recent_beats(context: ToolContext, count: int = 5) -> Dict[str, Any]:
    """Get recent beats for context."""
    story_id = context.require_story()

    repo = StoryBeatRepository(context.session)
    beats, _ = await repo.list_by_story(story_id=story_id, limit=count)

    # Get the last N beats (they're ordered by order_index)
    recent = beats[-count:] if len(beats) > count else beats

    return {
        "beats": [
            {
                "id": b.id,
                "order_index": b.order_index,
                "content": b.content,
                "type": b.type.value if b.type else None,
                "summary": b.summary,
            }
            for b in recent
        ]
    }


# ========================
# CHARACTER TOOLS
# ========================

@tool(
    name="get_character",
    description="Get details about a character including name, description, role, and importance.",
    parameters={
        "type": "object",
        "properties": {
            "character_id": {
                "type": "string",
                "description": "Character ID to retrieve"
            }
        },
        "required": ["character_id"]
    },
    category=ToolCategory.READ
)
async def get_character(context: ToolContext, character_id: str) -> Dict[str, Any]:
    """Get character details."""
    repo = CharacterRepository(context.session)
    result = await repo.get_with_mention_count(character_id)

    if not result:
        return {"error": "Character not found"}

    character, mention_count = result

    return {
        "id": character.id,
        "world_id": character.world_id,
        "name": character.name,
        "description": character.description,
        "aliases": character.aliases,
        "role": character.role,
        "importance": character.importance.value if character.importance else None,
        "mention_count": mention_count,
        "metadata": character.custom_metadata,
    }


@tool(
    name="list_characters",
    description="List characters in the current world with optional filtering.",
    parameters={
        "type": "object",
        "properties": {
            "importance": {
                "type": "string",
                "description": "Filter by importance: major, minor, or background",
                "enum": ["major", "minor", "background"]
            },
            "search": {
                "type": "string",
                "description": "Search term for name/description"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results",
                "default": 50
            }
        },
        "required": []
    },
    category=ToolCategory.READ
)
async def list_characters(
    context: ToolContext,
    importance: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """List characters in current world."""
    world_id = context.require_world()

    repo = CharacterRepository(context.session)
    characters, total = await repo.list_by_world(
        world_id=world_id,
        importance=importance,
        search=search,
        limit=limit
    )

    return {
        "characters": [
            {
                "id": c.id,
                "name": c.name,
                "role": c.role,
                "importance": c.importance.value if c.importance else None,
            }
            for c in characters
        ],
        "total": total
    }


@tool(
    name="search_characters",
    description="Search for characters by name.",
    parameters={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Character name to search for"
            }
        },
        "required": ["name"]
    },
    category=ToolCategory.READ
)
async def search_characters(context: ToolContext, name: str) -> Dict[str, Any]:
    """Search characters by name."""
    world_id = context.require_world()

    repo = CharacterRepository(context.session)
    characters = await repo.search_by_name(world_id, name)

    return {
        "matches": [
            {
                "id": c.id,
                "name": c.name,
                "role": c.role,
                "importance": c.importance.value if c.importance else None,
            }
            for c in characters
        ]
    }


# ========================
# LOCATION TOOLS
# ========================

@tool(
    name="get_location",
    description="Get details about a location including name, description, and hierarchy.",
    parameters={
        "type": "object",
        "properties": {
            "location_id": {
                "type": "string",
                "description": "Location ID to retrieve"
            }
        },
        "required": ["location_id"]
    },
    category=ToolCategory.READ
)
async def get_location(context: ToolContext, location_id: str) -> Dict[str, Any]:
    """Get location details."""
    repo = LocationRepository(context.session)
    location = await repo.get_by_id(location_id)

    if not location:
        return {"error": "Location not found"}

    return {
        "id": location.id,
        "world_id": location.world_id,
        "name": location.name,
        "description": location.description,
        "parent_id": location.parent_id,
        "importance": location.importance.value if location.importance else None,
        "metadata": location.custom_metadata,
    }


@tool(
    name="list_locations",
    description="List locations in the current world.",
    parameters={
        "type": "object",
        "properties": {
            "parent_id": {
                "type": "string",
                "description": "Filter by parent location (for hierarchy)"
            },
            "search": {
                "type": "string",
                "description": "Search term for name/description"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results",
                "default": 50
            }
        },
        "required": []
    },
    category=ToolCategory.READ
)
async def list_locations(
    context: ToolContext,
    parent_id: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """List locations in current world."""
    world_id = context.require_world()

    repo = LocationRepository(context.session)
    locations, total = await repo.list_by_world(
        world_id=world_id,
        parent_id=parent_id,
        search=search,
        limit=limit
    )

    return {
        "locations": [
            {
                "id": loc.id,
                "name": loc.name,
                "parent_id": loc.parent_id,
                "importance": loc.importance.value if loc.importance else None,
            }
            for loc in locations
        ],
        "total": total
    }


# ========================
# WORLD EVENT TOOLS
# ========================

@tool(
    name="get_event",
    description="Get details about a world event on the timeline.",
    parameters={
        "type": "object",
        "properties": {
            "event_id": {
                "type": "string",
                "description": "Event ID to retrieve"
            }
        },
        "required": ["event_id"]
    },
    category=ToolCategory.READ
)
async def get_event(context: ToolContext, event_id: str) -> Dict[str, Any]:
    """Get world event details."""
    repo = WorldEventRepository(context.session)
    event = await repo.get_by_id(event_id)

    if not event:
        return {"error": "Event not found"}

    return {
        "id": event.id,
        "world_id": event.world_id,
        "t": event.t,
        "label_time": event.label_time,
        "event_type": event.event_type.value if event.event_type else None,
        "summary": event.summary,
        "location_id": event.location_id,
        "caused_by_ids": event.caused_by_ids,
    }


@tool(
    name="list_events",
    description="List world events in chronological order.",
    parameters={
        "type": "object",
        "properties": {
            "event_type": {
                "type": "string",
                "description": "Filter by event type"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results",
                "default": 50
            }
        },
        "required": []
    },
    category=ToolCategory.READ
)
async def list_events(
    context: ToolContext,
    event_type: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """List world events."""
    world_id = context.require_world()

    repo = WorldEventRepository(context.session)
    events, total = await repo.list_by_world(
        world_id=world_id,
        event_type=event_type,
        limit=limit
    )

    return {
        "events": [
            {
                "id": e.id,
                "t": e.t,
                "label_time": e.label_time,
                "event_type": e.event_type.value if e.event_type else None,
                "summary": e.summary,
            }
            for e in events
        ],
        "total": total
    }
