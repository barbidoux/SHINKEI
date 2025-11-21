"""World API endpoints."""
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from shinkei.auth.dependencies import get_current_user, get_db_session
from shinkei.models.user import User
from shinkei.models.world import World
from shinkei.schemas.world import WorldCreate, WorldResponse, WorldUpdate, WorldListResponse, WorldLaws, WorldImportData
from shinkei.repositories.world import WorldRepository
from shinkei.repositories.world_event import WorldEventRepository
from shinkei.repositories.story import StoryRepository
from shinkei.repositories.story_beat import StoryBeatRepository
from shinkei.generation.world_templates import get_template, list_templates
from shinkei.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/templates")
async def get_world_templates(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    List all available world templates.

    Returns template IDs with basic information (name, description, tone).
    """
    return {
        "templates": list_templates()
    }


@router.post("/", response_model=WorldResponse, status_code=status.HTTP_201_CREATED)
async def create_world(
    world_in: WorldCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    template_id: Optional[str] = Query(None, description="Optional template ID to initialize world with preset values"),
) -> World:
    """
    Create a new world.

    Optionally provide a template_id to initialize the world with preset values.
    User-provided values will override template defaults.
    """
    # If template_id is provided, merge template with user input
    if template_id:
        template = get_template(template_id)
        if not template:
            raise HTTPException(status_code=400, detail=f"Template '{template_id}' not found")

        # Build laws from template, override with user values if provided
        laws_dict = {}
        if template.laws_physics:
            laws_dict["physics"] = template.laws_physics
        if template.laws_metaphysics:
            laws_dict["metaphysics"] = template.laws_metaphysics
        if template.laws_social:
            laws_dict["social"] = template.laws_social
        if template.laws_forbidden:
            laws_dict["forbidden"] = template.laws_forbidden

        # Override with user-provided laws
        if world_in.laws.physics is not None:
            laws_dict["physics"] = world_in.laws.physics
        if world_in.laws.metaphysics is not None:
            laws_dict["metaphysics"] = world_in.laws.metaphysics
        if world_in.laws.social is not None:
            laws_dict["social"] = world_in.laws.social
        if world_in.laws.forbidden is not None:
            laws_dict["forbidden"] = world_in.laws.forbidden

        # Create merged world data
        merged_data = WorldCreate(
            name=world_in.name or template.name,
            description=world_in.description or template.description,
            tone=world_in.tone or template.tone,
            backdrop=world_in.backdrop or template.backdrop,
            laws=WorldLaws(**laws_dict),
            chronology_mode=world_in.chronology_mode or template.chronology_mode.value
        )
        world_in = merged_data
        logger.info("world_created_from_template", template_id=template_id, user_id=current_user.id)

    repo = WorldRepository(session)
    world = await repo.create(current_user.id, world_in)
    logger.info("world_created", world_id=world.id, user_id=current_user.id)
    return world


@router.get("/", response_model=List[WorldResponse])
async def list_worlds(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    skip: int = 0,
    limit: int = 100,
) -> List[World]:
    """
    List all worlds belonging to the current user.
    """
    repo = WorldRepository(session)
    worlds, total = await repo.list_by_user(current_user.id, skip=skip, limit=limit)
    return worlds


@router.get("/{world_id}", response_model=WorldResponse)
async def get_world(
    world_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> World:
    """
    Get a specific world by ID.
    """
    repo = WorldRepository(session)
    world = await repo.get_by_id(world_id)
    
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
        
    # Verify ownership
    if world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this world")
        
    return world


@router.put("/{world_id}", response_model=WorldResponse)
async def update_world(
    world_id: str,
    world_in: WorldUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> World:
    """
    Update a world.
    """
    repo = WorldRepository(session)
    
    # Check existence and ownership
    world = await repo.get_by_id(world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    if world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this world")
        
    updated_world = await repo.update(world_id, world_in)
    logger.info("world_updated", world_id=world_id)
    return updated_world


@router.delete("/{world_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_world(
    world_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """
    Delete a world.
    """
    repo = WorldRepository(session)

    # Check existence and ownership
    world = await repo.get_by_id(world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    if world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this world")

    await repo.delete(world_id)
    logger.info("world_deleted", world_id=world_id)


@router.get("/{world_id}/export")
async def export_world(
    world_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Export a complete world as JSON including all events, stories, and story beats.

    Returns a comprehensive JSON structure suitable for backup, sharing, or migration.
    The export includes:
    - World metadata (name, description, tone, backdrop, laws, chronology_mode)
    - All world events with dependencies
    - All stories with their story beats

    Format version: 1.0
    """
    # Check existence and ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    if world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to export this world")

    # Fetch all world events
    event_repo = WorldEventRepository(session)
    events, _ = await event_repo.list_by_world(world_id, skip=0, limit=10000)

    # Fetch all stories with their beats
    story_repo = StoryRepository(session)
    stories, _ = await story_repo.list_by_world(world_id, skip=0, limit=10000)

    # For each story, fetch its story beats
    story_beat_repo = StoryBeatRepository(session)
    stories_export = []
    for story in stories:
        beats, _ = await story_beat_repo.list_by_story(story.id, skip=0, limit=10000)
        stories_export.append({
            "id": story.id,
            "title": story.title,
            "synopsis": story.synopsis,
            "status": story.status,
            "pov_type": story.pov_type,
            "mode": story.mode,
            "created_at": story.created_at.isoformat(),
            "updated_at": story.updated_at.isoformat(),
            "story_beats": [
                {
                    "id": beat.id,
                    "seq_in_story": beat.seq_in_story,
                    "world_event_id": beat.world_event_id,
                    "type": beat.type,
                    "text": beat.text,
                    "generated_by": beat.generated_by,
                    "created_at": beat.created_at.isoformat(),
                    "updated_at": beat.updated_at.isoformat(),
                }
                for beat in beats
            ]
        })

    # Build export structure
    export_data = {
        "version": "1.0",
        "exported_at": world.updated_at.isoformat(),
        "world": {
            "id": world.id,
            "name": world.name,
            "description": world.description,
            "tone": world.tone,
            "backdrop": world.backdrop,
            "laws": world.laws,
            "chronology_mode": world.chronology_mode.value,
            "created_at": world.created_at.isoformat(),
            "updated_at": world.updated_at.isoformat(),
        },
        "world_events": [
            {
                "id": event.id,
                "t": event.t,
                "label_time": event.label_time,
                "location_id": event.location_id,
                "type": event.type,
                "summary": event.summary,
                "tags": event.tags,
                "caused_by_ids": event.caused_by_ids,
                "created_at": event.created_at.isoformat(),
                "updated_at": event.updated_at.isoformat(),
            }
            for event in events
        ],
        "stories": stories_export,
    }

    logger.info("world_exported", world_id=world_id, user_id=current_user.id,
                event_count=len(events), story_count=len(stories))

    return JSONResponse(content=export_data)


@router.post("/import", response_model=WorldResponse, status_code=status.HTTP_201_CREATED)
async def import_world(
    import_data: WorldImportData,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> World:
    """
    Import a world from exported JSON data.

    Creates a new world with all events, stories, and story beats from the import.
    All IDs are regenerated, but relationships are preserved.

    Supports format version: 1.0
    """
    import uuid

    # Validate version
    if import_data.version != "1.0":
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported import version: {import_data.version}. Expected: 1.0"
        )

    world_data = import_data.world

    # Create the world
    world_create = WorldCreate(
        name=world_data.get("name", "Imported World"),
        description=world_data.get("description"),
        tone=world_data.get("tone"),
        backdrop=world_data.get("backdrop"),
        laws=WorldLaws(**world_data.get("laws", {})),
        chronology_mode=world_data.get("chronology_mode", "linear")
    )

    world_repo = WorldRepository(session)
    new_world = await world_repo.create(current_user.id, world_create)

    # ID mapping: old_id -> new_id
    event_id_map = {}
    story_id_map = {}

    # Import world events
    event_repo = WorldEventRepository(session)
    for event_data in import_data.world_events:
        old_event_id = event_data["id"]

        # Create event (we'll update caused_by_ids in a second pass)
        from shinkei.schemas.world_event import WorldEventCreate
        event_create = WorldEventCreate(
            t=event_data["t"],
            label_time=event_data["label_time"],
            location_id=event_data.get("location_id"),
            type=event_data["type"],
            summary=event_data["summary"],
            tags=event_data.get("tags", []),
            caused_by_ids=[]  # Will fix in second pass
        )
        new_event = await event_repo.create(new_world.id, event_create)
        event_id_map[old_event_id] = new_event.id

    # Second pass: fix caused_by_ids with remapped IDs
    for event_data in import_data.world_events:
        old_event_id = event_data["id"]
        new_event_id = event_id_map[old_event_id]

        old_caused_by_ids = event_data.get("caused_by_ids", [])
        new_caused_by_ids = [
            event_id_map[old_id]
            for old_id in old_caused_by_ids
            if old_id in event_id_map
        ]

        if new_caused_by_ids:
            event = await event_repo.get_by_id(new_event_id)
            if event:
                event.caused_by_ids = new_caused_by_ids
                await session.commit()

    # Import stories with their beats
    story_repo = StoryRepository(session)
    story_beat_repo = StoryBeatRepository(session)

    for story_data in import_data.stories:
        old_story_id = story_data["id"]

        # Create story
        from shinkei.schemas.story import StoryCreate
        story_create = StoryCreate(
            title=story_data["title"],
            synopsis=story_data.get("synopsis"),
            status=story_data.get("status", "draft"),
            pov_type=story_data.get("pov_type", "first"),
            mode=story_data.get("mode", "manual")
        )
        new_story = await story_repo.create(new_world.id, story_create)
        story_id_map[old_story_id] = new_story.id

        # Create story beats
        for beat_data in story_data.get("story_beats", []):
            # Remap world_event_id if it exists
            old_world_event_id = beat_data.get("world_event_id")
            new_world_event_id = None
            if old_world_event_id and old_world_event_id in event_id_map:
                new_world_event_id = event_id_map[old_world_event_id]

            from shinkei.schemas.story_beat import StoryBeatCreate
            beat_create = StoryBeatCreate(
                seq_in_story=beat_data["seq_in_story"],
                world_event_id=new_world_event_id,
                type=beat_data["type"],
                text=beat_data["text"],
                generated_by=beat_data.get("generated_by")
            )
            await story_beat_repo.create(new_story.id, beat_create)

    await session.commit()

    logger.info("world_imported", world_id=new_world.id, user_id=current_user.id,
                event_count=len(import_data.world_events),
                story_count=len(import_data.stories))

    return new_world


@router.post("/{world_id}/duplicate", response_model=WorldResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_world(
    world_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> World:
    """
    Duplicate a world, creating a complete copy with all events, stories, and story beats.

    The duplicated world will have "(Copy)" appended to its name.
    All IDs are regenerated, but relationships are preserved.
    """
    import uuid

    # Check existence and ownership of source world
    world_repo = WorldRepository(session)
    source_world = await world_repo.get_by_id(world_id)
    if not source_world:
        raise HTTPException(status_code=404, detail="World not found")
    if source_world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to duplicate this world")

    # Fetch all world events
    event_repo = WorldEventRepository(session)
    events, _ = await event_repo.list_by_world(world_id, skip=0, limit=10000)

    # Fetch all stories with their beats
    story_repo = StoryRepository(session)
    stories, _ = await story_repo.list_by_world(world_id, skip=0, limit=10000)

    story_beat_repo = StoryBeatRepository(session)
    stories_data = []
    for story in stories:
        beats, _ = await story_beat_repo.list_by_story(story.id, skip=0, limit=10000)
        stories_data.append({
            "story": story,
            "beats": beats
        })

    # Create the duplicated world with modified name
    duplicate_name = f"{source_world.name} (Copy)"
    world_create = WorldCreate(
        name=duplicate_name,
        description=source_world.description,
        tone=source_world.tone,
        backdrop=source_world.backdrop,
        laws=WorldLaws(**source_world.laws),
        chronology_mode=source_world.chronology_mode.value
    )

    new_world = await world_repo.create(current_user.id, world_create)

    # ID mapping: old_id -> new_id
    event_id_map = {}

    # Duplicate world events
    for event in events:
        old_event_id = event.id

        from shinkei.schemas.world_event import WorldEventCreate
        event_create = WorldEventCreate(
            t=event.t,
            label_time=event.label_time,
            location_id=event.location_id,
            type=event.type,
            summary=event.summary,
            tags=event.tags,
            caused_by_ids=[]  # Will fix in second pass
        )
        new_event = await event_repo.create(new_world.id, event_create)
        event_id_map[old_event_id] = new_event.id

    # Second pass: fix caused_by_ids with remapped IDs
    for event in events:
        old_event_id = event.id
        new_event_id = event_id_map[old_event_id]

        new_caused_by_ids = [
            event_id_map[old_id]
            for old_id in event.caused_by_ids
            if old_id in event_id_map
        ]

        if new_caused_by_ids:
            new_event = await event_repo.get_by_id(new_event_id)
            if new_event:
                new_event.caused_by_ids = new_caused_by_ids
                await session.commit()

    # Duplicate stories with their beats
    for story_data in stories_data:
        story = story_data["story"]
        beats = story_data["beats"]

        from shinkei.schemas.story import StoryCreate
        story_create = StoryCreate(
            title=story.title,
            synopsis=story.synopsis,
            status=story.status,
            pov_type=story.pov_type,
            mode=story.mode
        )
        new_story = await story_repo.create(new_world.id, story_create)

        # Duplicate story beats
        for beat in beats:
            # Remap world_event_id if it exists
            new_world_event_id = None
            if beat.world_event_id and beat.world_event_id in event_id_map:
                new_world_event_id = event_id_map[beat.world_event_id]

            from shinkei.schemas.story_beat import StoryBeatCreate
            beat_create = StoryBeatCreate(
                seq_in_story=beat.seq_in_story,
                world_event_id=new_world_event_id,
                type=beat.type,
                text=beat.text,
                generated_by=beat.generated_by
            )
            await story_beat_repo.create(new_story.id, beat_create)

    await session.commit()

    logger.info("world_duplicated", source_world_id=world_id, new_world_id=new_world.id,
                user_id=current_user.id, event_count=len(events), story_count=len(stories))

    return new_world
