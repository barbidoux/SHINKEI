"""CharacterRelationship API endpoints."""
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from shinkei.auth.dependencies import get_current_user, get_db_session
from shinkei.models.user import User
from shinkei.models.character_relationship import CharacterRelationship
from shinkei.schemas.character_relationship import (
    CharacterRelationshipCreate,
    CharacterRelationshipUpdate,
    CharacterRelationshipResponse,
    CharacterRelationshipListResponse,
    CharacterWithRelationshipsResponse,
    RelationshipNetworkResponse
)
from shinkei.repositories.character_relationship import CharacterRelationshipRepository
from shinkei.repositories.character import CharacterRepository
from shinkei.repositories.world import WorldRepository
from shinkei.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/{world_id}/character-relationships", response_model=CharacterRelationshipResponse, status_code=status.HTTP_201_CREATED)
async def create_character_relationship(
    world_id: str,
    relationship_in: CharacterRelationshipCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CharacterRelationship:
    """
    Create a new character relationship in a world.

    Requires ownership of the world. Both characters must exist in the same world.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Verify both characters exist in this world
    char_repo = CharacterRepository(session)
    char_a = await char_repo.get_by_world_and_id(world_id, relationship_in.character_a_id)
    if not char_a:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character {relationship_in.character_a_id} not found in world {world_id}"
        )

    char_b = await char_repo.get_by_world_and_id(world_id, relationship_in.character_b_id)
    if not char_b:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character {relationship_in.character_b_id} not found in world {world_id}"
        )

    # Create relationship
    rel_repo = CharacterRelationshipRepository(session)
    relationship = await rel_repo.create(world_id, relationship_in)
    await session.commit()

    logger.info("character_relationship_created", relationship_id=relationship.id, world_id=world_id)
    return relationship


@router.get("/{world_id}/character-relationships", response_model=CharacterRelationshipListResponse)
async def list_character_relationships(
    world_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    strength: Optional[str] = Query(None, regex="^(strong|moderate|weak)$"),
    relationship_type: Optional[str] = Query(None, max_length=100),
):
    """
    List all character relationships in a world with optional filtering.

    Supports filtering by strength and relationship_type.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Get relationships
    rel_repo = CharacterRelationshipRepository(session)
    relationships, total = await rel_repo.list_by_world(
        world_id=world_id,
        skip=skip,
        limit=limit,
        strength=strength,
        relationship_type=relationship_type
    )

    return CharacterRelationshipListResponse(
        relationships=relationships,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/{world_id}/character-relationships/network", response_model=RelationshipNetworkResponse)
async def get_relationship_network(
    world_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Get relationship network graph data for visualization.

    Returns nodes (characters) and edges (relationships) for the entire world.
    Useful for generating network graphs.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Get network data
    rel_repo = CharacterRelationshipRepository(session)
    network_data = await rel_repo.get_network_data(world_id)

    return RelationshipNetworkResponse(
        world_id=world_id,
        **network_data
    )


@router.get("/{world_id}/characters/{character_id}/relationships", response_model=CharacterWithRelationshipsResponse)
async def get_character_relationships(
    world_id: str,
    character_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Get all relationships for a specific character.

    Returns the character with all relationships where they are either character A or B.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Get and verify character
    char_repo = CharacterRepository(session)
    character = await char_repo.get_by_world_and_id(world_id, character_id)
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character {character_id} not found in world {world_id}"
        )

    # Get relationships
    rel_repo = CharacterRelationshipRepository(session)
    relationships = await rel_repo.list_by_character(character_id)

    return CharacterWithRelationshipsResponse(
        character=character,
        relationships=relationships,
        total_relationships=len(relationships)
    )


@router.get("/{world_id}/character-relationships/{relationship_id}", response_model=CharacterRelationshipResponse)
async def get_character_relationship(
    world_id: str,
    relationship_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Get a specific character relationship by ID.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Get relationship
    rel_repo = CharacterRelationshipRepository(session)
    relationship = await rel_repo.get_by_world_and_id(world_id, relationship_id)
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relationship {relationship_id} not found in world {world_id}"
        )

    return relationship


@router.put("/{world_id}/character-relationships/{relationship_id}", response_model=CharacterRelationshipResponse)
async def update_character_relationship(
    world_id: str,
    relationship_id: str,
    relationship_in: CharacterRelationshipUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Update a character relationship.

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

    # Get and verify relationship
    rel_repo = CharacterRelationshipRepository(session)
    relationship = await rel_repo.get_by_world_and_id(world_id, relationship_id)
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relationship {relationship_id} not found in world {world_id}"
        )

    # Update relationship
    updated_relationship = await rel_repo.update(relationship_id, relationship_in)
    await session.commit()

    logger.info("character_relationship_updated", relationship_id=relationship_id, world_id=world_id)
    return updated_relationship


@router.delete("/{world_id}/character-relationships/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character_relationship(
    world_id: str,
    relationship_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Delete a character relationship.

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

    # Get and verify relationship
    rel_repo = CharacterRelationshipRepository(session)
    relationship = await rel_repo.get_by_world_and_id(world_id, relationship_id)
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relationship {relationship_id} not found in world {world_id}"
        )

    # Delete relationship
    await rel_repo.delete(relationship_id)
    await session.commit()

    logger.info("character_relationship_deleted", relationship_id=relationship_id, world_id=world_id)
    return None
