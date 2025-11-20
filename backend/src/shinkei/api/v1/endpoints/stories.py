"""Story API endpoints."""
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shinkei.auth.dependencies import get_current_user, get_db_session
from shinkei.models.user import User
from shinkei.models.story import Story
from shinkei.schemas.story import StoryCreate, StoryResponse, StoryUpdate
from shinkei.repositories.story import StoryRepository
from shinkei.repositories.world import WorldRepository
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
) -> List[Story]:
    """
    List all stories in a world.
    """
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    if world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this world")

    repo = StoryRepository(session)
    stories, total = await repo.list_by_world(world_id, skip=skip, limit=limit)
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
    Delete a story.
    """
    repo = StoryRepository(session)
    story = await repo.get_by_id(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
        
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(story.world_id)
    if not world or world.user_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized to delete this story")
        
    await repo.delete(story_id)
    logger.info("story_deleted", story_id=story_id)
