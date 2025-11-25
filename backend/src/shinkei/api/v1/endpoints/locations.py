"""Location API endpoints."""
from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from shinkei.auth.dependencies import get_current_user, get_db_session
from shinkei.models.user import User
from shinkei.models.location import Location
from shinkei.schemas.location import (
    LocationCreate,
    LocationUpdate,
    LocationResponse,
    LocationListResponse,
    LocationHierarchyResponse,
    LocationWithMentionsResponse
)
from shinkei.repositories.location import LocationRepository
from shinkei.repositories.world import WorldRepository
from shinkei.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/{world_id}/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    world_id: str,
    location_in: LocationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Location:
    """
    Create a new location in a world.

    Requires ownership of the world.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Create location
    loc_repo = LocationRepository(session)
    location = await loc_repo.create(world_id, location_in)
    await session.commit()

    logger.info("location_created", location_id=location.id, world_id=world_id, user_id=current_user.id)
    return location


@router.get("/{world_id}/locations", response_model=LocationListResponse)
async def list_locations(
    world_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    location_type: Optional[str] = Query(None, max_length=50),
    parent_location_id: Optional[str] = Query(None, description="Use 'null' for root locations only"),
    search: Optional[str] = Query(None, max_length=200),
):
    """
    List all locations in a world with optional filtering.

    Supports filtering by location_type, parent_location_id, and text search.
    Use parent_location_id='null' to get only root locations.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Get locations
    loc_repo = LocationRepository(session)
    locations, total = await loc_repo.list_by_world(
        world_id=world_id,
        skip=skip,
        limit=limit,
        location_type=location_type,
        parent_location_id=parent_location_id,
        search=search
    )

    return LocationListResponse(
        locations=locations,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/{world_id}/locations/roots", response_model=List[LocationResponse])
async def get_root_locations(
    world_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Get all root locations (locations with no parent) in a world.

    Useful for building hierarchical tree structures.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Get root locations
    loc_repo = LocationRepository(session)
    root_locations = await loc_repo.get_root_locations(world_id)

    return root_locations


@router.get("/{world_id}/locations/{location_id}", response_model=LocationWithMentionsResponse)
async def get_location(
    world_id: str,
    location_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Get a specific location by ID with mention count.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Get location
    loc_repo = LocationRepository(session)
    result = await loc_repo.get_with_mention_count(location_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location {location_id} not found"
        )

    location, mention_count = result

    # Verify location belongs to world
    if location.world_id != world_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location {location_id} not found in world {world_id}"
        )

    return LocationWithMentionsResponse(
        **location.__dict__,
        mention_count=mention_count
    )


@router.get("/{world_id}/locations/{location_id}/hierarchy", response_model=LocationHierarchyResponse)
async def get_location_hierarchy(
    world_id: str,
    location_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Get a location with its full hierarchy (parent and children).

    Returns the location with parent_location and child_locations loaded.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Get location with hierarchy
    loc_repo = LocationRepository(session)
    location = await loc_repo.get_with_hierarchy(location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location {location_id} not found"
        )

    # Verify location belongs to world
    if location.world_id != world_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location {location_id} not found in world {world_id}"
        )

    return location


@router.get("/{world_id}/locations/{location_id}/children", response_model=List[LocationResponse])
async def get_location_children(
    world_id: str,
    location_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Get all direct children of a location.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Verify location exists and belongs to world
    loc_repo = LocationRepository(session)
    location = await loc_repo.get_by_world_and_id(world_id, location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location {location_id} not found in world {world_id}"
        )

    # Get children
    children = await loc_repo.get_children(location_id)
    return children


@router.put("/{world_id}/locations/{location_id}", response_model=LocationResponse)
async def update_location(
    world_id: str,
    location_id: str,
    location_in: LocationUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Update a location.

    Requires ownership of the world. Prevents circular parent references.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Get and verify location
    loc_repo = LocationRepository(session)
    location = await loc_repo.get_by_world_and_id(world_id, location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location {location_id} not found in world {world_id}"
        )

    # Update location (repository will prevent circular parents)
    try:
        updated_location = await loc_repo.update(location_id, location_in)
        await session.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    logger.info("location_updated", location_id=location_id, world_id=world_id, user_id=current_user.id)
    return updated_location


@router.delete("/{world_id}/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    world_id: str,
    location_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Delete a location.

    Requires ownership of the world. Cascade deletes all children and mentions.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Get and verify location
    loc_repo = LocationRepository(session)
    location = await loc_repo.get_by_world_and_id(world_id, location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location {location_id} not found in world {world_id}"
        )

    # Delete location
    await loc_repo.delete(location_id)
    await session.commit()

    logger.info("location_deleted", location_id=location_id, world_id=world_id, user_id=current_user.id)
    return None
