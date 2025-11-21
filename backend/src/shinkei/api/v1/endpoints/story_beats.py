"""StoryBeat API endpoints."""
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shinkei.auth.dependencies import get_current_user, get_db_session
from shinkei.models.user import User
from shinkei.models.story_beat import StoryBeat
from shinkei.schemas.story_beat import (
    StoryBeatCreate,
    StoryBeatResponse,
    StoryBeatUpdate,
    StoryBeatReasoningUpdate,
    StoryBeatReorderRequest
)
from shinkei.repositories.story_beat import StoryBeatRepository
from shinkei.repositories.story import StoryRepository
from shinkei.repositories.world import WorldRepository
from shinkei.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/stories/{story_id}/beats", response_model=StoryBeatResponse, status_code=status.HTTP_201_CREATED)
async def create_story_beat(
    story_id: str,
    beat_in: StoryBeatCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StoryBeat:
    """
    Create a new story beat.
    """
    story_repo = StoryRepository(session)
    story = await story_repo.get_by_id(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
        
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(story.world_id)
    if not world or world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to add beats to this story")

    repo = StoryBeatRepository(session)
    # Ensure story_id in beat matches path if present, or pass it to create
    # Similar to world_events, we'll pass story_id to create method
    
    beat = await repo.create(story_id, beat_in)
    logger.info("story_beat_created", beat_id=beat.id, story_id=story_id)
    return beat


@router.get("/stories/{story_id}/beats", response_model=List[StoryBeatResponse])
async def list_story_beats(
    story_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    skip: int = 0,
    limit: int = 100,
) -> List[StoryBeat]:
    """
    List all beats in a story.
    """
    story_repo = StoryRepository(session)
    story = await story_repo.get_by_id(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(story.world_id)
    if not world or world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this story")

    repo = StoryBeatRepository(session)
    beats, total = await repo.list_by_story(story_id, skip=skip, limit=limit)
    return beats


@router.get("/stories/{story_id}/beats/{beat_id}", response_model=StoryBeatResponse)
async def get_story_beat(
    story_id: str,
    beat_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StoryBeat:
    """
    Get a specific beat from a story.
    """
    repo = StoryBeatRepository(session)
    beat = await repo.get_by_id(beat_id)
    if not beat:
        raise HTTPException(status_code=404, detail="Beat not found")

    # Verify beat belongs to the specified story
    if beat.story_id != story_id:
        raise HTTPException(status_code=404, detail="Beat not found in this story")

    # Verify ownership through story -> world -> user
    story_repo = StoryRepository(session)
    story = await story_repo.get_by_id(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(story.world_id)
    if not world or world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this beat")

    logger.info("story_beat_retrieved", beat_id=beat_id, story_id=story_id)
    return beat


@router.put("/stories/{story_id}/beats/{beat_id}", response_model=StoryBeatResponse)
async def update_story_beat(
    story_id: str,
    beat_id: str,
    beat_in: StoryBeatUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StoryBeat:
    """
    Update a story beat.
    """
    repo = StoryBeatRepository(session)
    beat = await repo.get_by_id(beat_id)
    if not beat:
        raise HTTPException(status_code=404, detail="Beat not found")

    # Verify beat belongs to the specified story
    if beat.story_id != story_id:
        raise HTTPException(status_code=404, detail="Beat not found in this story")

    # Verify ownership through story -> world -> user
    story_repo = StoryRepository(session)
    story = await story_repo.get_by_id(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(story.world_id)
    if not world or world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this beat")

    updated_beat = await repo.update(beat_id, beat_in)
    logger.info("story_beat_updated", beat_id=beat_id, story_id=story_id)
    return updated_beat


@router.patch("/stories/{story_id}/beats/{beat_id}/reasoning", response_model=StoryBeatResponse)
async def update_beat_reasoning(
    story_id: str,
    beat_id: str,
    reasoning_in: StoryBeatReasoningUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StoryBeat:
    """
    Update only the AI reasoning/thoughts for a story beat.

    This endpoint allows users to edit or delete the AI's reasoning
    without affecting the beat's narrative content.
    """
    repo = StoryBeatRepository(session)
    beat = await repo.get_by_id(beat_id)
    if not beat:
        raise HTTPException(status_code=404, detail="Beat not found")

    # Verify beat belongs to the specified story
    if beat.story_id != story_id:
        raise HTTPException(status_code=404, detail="Beat not found in this story")

    # Verify ownership through story -> world -> user
    story_repo = StoryRepository(session)
    story = await story_repo.get_by_id(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(story.world_id)
    if not world or world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this beat")

    # Update only the reasoning field
    updated_beat = await repo.update(beat_id, reasoning_in)
    logger.info(
        "story_beat_reasoning_updated",
        beat_id=beat_id,
        story_id=story_id,
        reasoning_length=len(reasoning_in.generation_reasoning or "")
    )
    return updated_beat


@router.post("/stories/{story_id}/beats/reorder", response_model=List[StoryBeatResponse])
async def reorder_story_beats(
    story_id: str,
    reorder_request: StoryBeatReorderRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> List[StoryBeat]:
    """
    Reorder story beats.

    Accepts a list of beat IDs in the desired order and updates their order_index accordingly.
    """
    # Verify ownership through story -> world -> user
    story_repo = StoryRepository(session)
    story = await story_repo.get_by_id(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(story.world_id)
    if not world or world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to reorder beats in this story")

    # Use repository reorder method
    repo = StoryBeatRepository(session)
    try:
        await repo.reorder(story_id, reorder_request.beat_ids)
        await session.commit()

        # Fetch updated beats
        updated_beats, _ = await repo.list_by_story(story_id)

        logger.info(
            "story_beats_reordered",
            story_id=story_id,
            beat_count=len(reorder_request.beat_ids)
        )

        return updated_beats
    except ValueError as e:
        logger.warning("reorder_failed", error=str(e), story_id=story_id)
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/stories/{story_id}/beats/{beat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_story_beat(
    story_id: str,
    beat_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """
    Delete a story beat.
    """
    repo = StoryBeatRepository(session)
    beat = await repo.get_by_id(beat_id)
    if not beat:
        raise HTTPException(status_code=404, detail="Beat not found")

    # Verify beat belongs to the specified story
    if beat.story_id != story_id:
        raise HTTPException(status_code=404, detail="Beat not found in this story")

    # Verify ownership through story -> world -> user
    story_repo = StoryRepository(session)
    story = await story_repo.get_by_id(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(story.world_id)
    if not world or world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this beat")

    await repo.delete(beat_id)
    logger.info("story_beat_deleted", beat_id=beat_id, story_id=story_id)


# Note: Beat modification endpoints have been moved to narrative.py
# to align with the /narrative prefix used by other AI generation endpoints.
