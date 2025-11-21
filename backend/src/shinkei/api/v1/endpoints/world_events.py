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


async def _would_create_cycle(
    event_id: str,
    new_cause_id: str,
    session: AsyncSession
) -> bool:
    """
    Check if adding new_cause_id as a dependency of event_id would create a cycle.

    Uses DFS to detect if new_cause_id has event_id in its transitive dependencies.

    Args:
        event_id: The event that would have the new dependency
        new_cause_id: The event ID to add as a cause
        session: Database session

    Returns:
        True if adding the dependency would create a cycle, False otherwise
    """
    # Simple self-reference check
    if event_id == new_cause_id:
        return True

    # DFS to find if event_id is reachable from new_cause_id
    repo = WorldEventRepository(session)
    visited = set()
    stack = [new_cause_id]

    while stack:
        current_id = stack.pop()

        if current_id in visited:
            continue

        # If we reach the target event, we found a cycle
        if current_id == event_id:
            return True

        visited.add(current_id)

        # Get current event and its causes
        current_event = await repo.get_by_id(current_id)
        if current_event and current_event.caused_by_ids:
            # Add all causes to the stack
            for cause_id in current_event.caused_by_ids:
                if cause_id not in visited:
                    stack.append(cause_id)

    return False


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


# ===== Event Dependency Endpoints =====

@router.post("/events/{event_id}/dependencies/{cause_event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_event_dependency(
    event_id: str,
    cause_event_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """
    Add a dependency relationship: cause_event_id causes event_id.

    Creates a causal link where cause_event_id is a cause/trigger for event_id.
    """
    repo = WorldEventRepository(session)
    event = await repo.get_by_id(event_id)
    cause_event = await repo.get_by_id(cause_event_id)

    if not event:
        raise HTTPException(status_code=404, detail="Effect event not found")
    if not cause_event:
        raise HTTPException(status_code=404, detail="Cause event not found")

    # Verify both events belong to same world
    if event.world_id != cause_event.world_id:
        raise HTTPException(status_code=400, detail="Events must belong to the same world")

    # Verify ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(event.world_id)
    if not world or world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this world's events")

    # Prevent circular dependencies (full cycle detection)
    if await _would_create_cycle(event_id, cause_event_id, session):
        raise HTTPException(
            status_code=400,
            detail="Adding this dependency would create a circular dependency in the event graph"
        )

    # Add dependency if not already present
    if cause_event_id not in event.caused_by_ids:
        event.caused_by_ids = [*event.caused_by_ids, cause_event_id]
        await session.commit()
        logger.info("event_dependency_added", event_id=event_id, cause_event_id=cause_event_id)


@router.delete("/events/{event_id}/dependencies/{cause_event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_event_dependency(
    event_id: str,
    cause_event_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """
    Remove a dependency relationship between two events.
    """
    repo = WorldEventRepository(session)
    event = await repo.get_by_id(event_id)

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Verify ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(event.world_id)
    if not world or world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this world's events")

    # Remove dependency if present
    if cause_event_id in event.caused_by_ids:
        event.caused_by_ids = [id for id in event.caused_by_ids if id != cause_event_id]
        await session.commit()
        logger.info("event_dependency_removed", event_id=event_id, cause_event_id=cause_event_id)


@router.get("/worlds/{world_id}/events/dependency-graph")
async def get_event_dependency_graph(
    world_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Get the full event dependency graph for a world.

    Returns a graph structure with nodes (events) and edges (dependencies).
    """
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    if world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this world")

    repo = WorldEventRepository(session)
    events, total = await repo.list_by_world(world_id, skip=0, limit=1000)

    # Build graph structure
    nodes = [
        {
            "id": event.id,
            "label": event.label_time,
            "t": event.t,
            "type": event.type,
            "summary": event.summary
        }
        for event in events
    ]

    edges = []
    for event in events:
        for cause_id in event.caused_by_ids:
            edges.append({
                "source": cause_id,  # Cause event
                "target": event.id,  # Effect event
                "type": "causes"
            })

    return {
        "nodes": nodes,
        "edges": edges,
        "world_id": world_id
    }
