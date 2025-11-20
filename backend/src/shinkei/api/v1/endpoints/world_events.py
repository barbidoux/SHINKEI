"""WorldEvent API endpoints."""
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shinkei.auth.dependencies import get_current_user, get_db_session
from shinkei.models.user import User
from shinkei.models.world_event import WorldEvent
from shinkei.models.story_beat import StoryBeat
from shinkei.schemas.world_event import WorldEventCreate, WorldEventResponse, WorldEventUpdate
from shinkei.schemas.story_beat import BeatWithStoryResponse
from shinkei.repositories.world_event import WorldEventRepository
from shinkei.repositories.world import WorldRepository
from shinkei.repositories.story_beat import StoryBeatRepository
from shinkei.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/worlds/{world_id}/events", response_model=WorldEventResponse, status_code=status.HTTP_201_CREATED)
async def create_world_event(
    world_id: str,
    event_in: WorldEventCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorldEvent:
    """
    Create a new world event.
    """
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    if world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to add events to this world")

    repo = WorldEventRepository(session)
    event = await repo.create(world_id, event_in)
    logger.info("world_event_created", event_id=event.id, world_id=world_id)
    return event


@router.get("/worlds/{world_id}/events", response_model=List[WorldEventResponse])
async def list_world_events(
    world_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    skip: int = 0,
    limit: int = 100,
) -> List[WorldEvent]:
    """
    List all events for a specific world.
    """
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    if world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this world")

    repo = WorldEventRepository(session)
    events, total = await repo.list_by_world(world_id, skip=skip, limit=limit)
    return events


@router.get("/events/{event_id}", response_model=WorldEventResponse)
async def get_world_event(
    event_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorldEvent:
    """
    Get a specific world event by ID.
    """
    repo = WorldEventRepository(session)
    event = await repo.get_by_id(event_id)

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Verify ownership via world
    # We need to fetch the world to check ownership, or join.
    # For simplicity, let's fetch the world.
    # Ideally repository should handle this or return world_id.
    # event.world should be loaded if we use lazy loading or explicit join.
    # Let's assume we can access event.world_id and fetch world.

    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(event.world_id)
    if not world or world.user_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized to access this event")

    return event


@router.get("/events/{event_id}/beats", response_model=List[BeatWithStoryResponse])
async def get_event_beats(
    event_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> List[StoryBeat]:
    """
    Get all story beats linked to a specific world event.

    This shows story intersection - which stories have beats at this canonical event.
    """
    # First verify event exists and user has access
    event_repo = WorldEventRepository(session)
    event = await event_repo.get_by_id(event_id)

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Verify ownership via world
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(event.world_id)
    if not world or world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this event")

    # Fetch all beats linked to this event
    beat_repo = StoryBeatRepository(session)
    beats = await beat_repo.list_by_world_event(event_id)

    logger.info("event_beats_fetched", event_id=event_id, beat_count=len(beats))
    return beats


@router.put("/events/{event_id}", response_model=WorldEventResponse)
async def update_world_event(
    event_id: str,
    event_in: WorldEventUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorldEvent:
    """
    Update a world event.
    """
    repo = WorldEventRepository(session)
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(event.world_id)
    if not world or world.user_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized to modify this event")

    updated_event = await repo.update(event_id, event_in)
    logger.info("world_event_updated", event_id=event_id)
    return updated_event


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_world_event(
    event_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """
    Delete a world event.
    """
    repo = WorldEventRepository(session)
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(event.world_id)
    if not world or world.user_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized to delete this event")
        
    await repo.delete(event_id)
    logger.info("world_event_deleted", event_id=event_id)
