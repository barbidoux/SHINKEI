"""Story API endpoints."""
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shinkei.auth.dependencies import get_current_user, get_db_session
from shinkei.models.user import User
from shinkei.models.story import Story
from shinkei.schemas.story import StoryCreate, StoryResponse, StoryUpdate, StoryStatistics
from shinkei.schemas.story_beat import StoryBeatCreate
from shinkei.repositories.story import StoryRepository
from shinkei.repositories.story_beat import StoryBeatRepository
from shinkei.repositories.world import WorldRepository
from shinkei.generation.story_templates import get_template, list_templates
from shinkei.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/worlds/{world_id}/stories", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
async def create_story(
    world_id: str,
    story_in: StoryCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Story:
    """
    Create a new story in a world.
    """
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    if world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to add stories to this world")

    repo = StoryRepository(session)
    story = await repo.create(world_id, story_in)
    logger.info("story_created", story_id=story.id, world_id=world_id)
    return story


@router.get("/worlds/{world_id}/stories", response_model=List[StoryResponse])
async def list_stories(
    world_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    skip: int = 0,
    limit: int = 100,
    include_archived: bool = Query(False, description="Include archived stories"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
) -> List[Story]:
    """
    List all stories in a world (with optional tag filter).
    """
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    if world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this world")

    repo = StoryRepository(session)

    # Filter by tag if provided
    if tag:
        stories, total = await repo.list_by_tag(world_id, tag, skip=skip, limit=limit)
    else:
        stories, total = await repo.list_by_world(world_id, skip=skip, limit=limit, include_archived=include_archived)

    return stories


@router.get("/stories/{story_id}", response_model=StoryResponse)
async def get_story(
    story_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Story:
    """
    Get a specific story by ID.
    """
    repo = StoryRepository(session)
    story = await repo.get_by_id(story_id)
    
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
        
    # Verify ownership via world
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(story.world_id)
    if not world or world.user_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized to access this story")
        
    return story


@router.put("/stories/{story_id}", response_model=StoryResponse)
async def update_story(
    story_id: str,
    story_in: StoryUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Story:
    """
    Update a story.
    """
    repo = StoryRepository(session)
    story = await repo.get_by_id(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
        
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(story.world_id)
    if not world or world.user_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized to modify this story")

    updated_story = await repo.update(story_id, story_in)
    logger.info("story_updated", story_id=story_id)
    return updated_story


@router.delete("/stories/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_story(
    story_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """
    Delete a story (soft delete by default).
    """
    repo = StoryRepository(session)
    story = await repo.get_by_id(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(story.world_id)
    if not world or world.user_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized to delete this story")

    await repo.delete(story_id, soft_delete=True)
    logger.info("story_archived", story_id=story_id)


# --- New Feature Endpoints ---


@router.get("/stories/templates")
async def get_story_templates() -> dict:
    """
    Get all available story templates.
    """
    return {"templates": list_templates()}


@router.post("/stories/{story_id}/clone", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
async def clone_story(
    story_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Story:
    """
    Clone a story with all its beats.
    """
    story_repo = StoryRepository(session)
    source_story = await story_repo.get_by_id(story_id)
    if not source_story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Verify ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(source_story.world_id)
    if not world or world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to clone this story")

    # Create cloned story
    story_create = StoryCreate(
        title=f"{source_story.title} (Copy)",
        synopsis=source_story.synopsis,
        theme=source_story.theme,
        status=source_story.status.value,
        mode=source_story.mode.value,
        pov_type=source_story.pov_type.value,
        tags=source_story.tags.copy() if source_story.tags else []
    )
    new_story = await story_repo.create(source_story.world_id, story_create)

    # Clone all story beats
    beat_repo = StoryBeatRepository(session)
    beats, _ = await beat_repo.list_by_story(story_id, skip=0, limit=10000)

    for beat in beats:
        beat_create = StoryBeatCreate(
            order_index=beat.order_index,
            content=beat.content,
            type=beat.type.value,
            world_event_id=beat.world_event_id,
            summary=beat.summary,
            local_time_label=beat.local_time_label,
            generated_by=beat.generated_by.value,
            generation_reasoning=beat.generation_reasoning
        )
        await beat_repo.create(new_story.id, beat_create)

    await session.commit()
    logger.info("story_cloned", source_story_id=story_id, new_story_id=new_story.id)
    return new_story


@router.post("/stories/{story_id}/restore", response_model=StoryResponse)
async def restore_story(
    story_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Story:
    """
    Restore an archived story.
    """
    repo = StoryRepository(session)
    story = await repo.get_by_id(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Verify ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(story.world_id)
    if not world or world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to restore this story")

    restored_story = await repo.restore(story_id)
    if not restored_story:
        raise HTTPException(status_code=400, detail="Story is not archived")

    await session.commit()
    logger.info("story_restored", story_id=story_id)
    return restored_story


@router.get("/worlds/{world_id}/stories/archived", response_model=List[StoryResponse])
async def list_archived_stories(
    world_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    skip: int = 0,
    limit: int = 100,
) -> List[Story]:
    """
    List archived stories for a world.
    """
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    if world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this world")

    repo = StoryRepository(session)
    stories, total = await repo.list_archived(world_id, skip=skip, limit=limit)
    return stories


@router.get("/worlds/{world_id}/stories/tags")
async def get_story_tags(
    world_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    """
    Get all unique tags used in a world's stories.
    """
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    if world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this world")

    repo = StoryRepository(session)
    tags = await repo.get_all_tags(world_id)
    return {"tags": tags}


@router.get("/stories/{story_id}/statistics", response_model=StoryStatistics)
async def get_story_statistics(
    story_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    """
    Get statistics for a story.
    """
    repo = StoryRepository(session)
    story = await repo.get_by_id(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Verify ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(story.world_id)
    if not world or world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this story")

    stats = await repo.get_statistics(story_id)
    return {"story_id": story_id, **stats}
