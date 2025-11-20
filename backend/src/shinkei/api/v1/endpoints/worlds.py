"""World API endpoints."""
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shinkei.auth.dependencies import get_current_user, get_db_session
from shinkei.models.user import User
from shinkei.models.world import World
from shinkei.schemas.world import WorldCreate, WorldResponse, WorldUpdate, WorldListResponse
from shinkei.repositories.world import WorldRepository
from shinkei.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/", response_model=WorldResponse, status_code=status.HTTP_201_CREATED)
async def create_world(
    world_in: WorldCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> World:
    """
    Create a new world.
    """
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
