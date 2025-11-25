"""Character API endpoints."""
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from shinkei.auth.dependencies import get_current_user, get_db_session
from shinkei.models.user import User
from shinkei.models.character import Character
from shinkei.schemas.character import (
    CharacterCreate,
    CharacterUpdate,
    CharacterResponse,
    CharacterListResponse,
    CharacterWithMentionsResponse,
    CharacterSearchResponse
)
from shinkei.repositories.character import CharacterRepository
from shinkei.repositories.world import WorldRepository
from shinkei.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/{world_id}/characters", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
async def create_character(
    world_id: str,
    character_in: CharacterCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Character:
    """
    Create a new character in a world.

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

    # Create character
    char_repo = CharacterRepository(session)
    character = await char_repo.create(world_id, character_in)
    await session.commit()

    logger.info("character_created", character_id=character.id, world_id=world_id, user_id=current_user.id)
    return character


@router.get("/{world_id}/characters", response_model=CharacterListResponse)
async def list_characters(
    world_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    importance: Optional[str] = Query(None, regex="^(major|minor|background)$"),
    search: Optional[str] = Query(None, max_length=200),
):
    """
    List all characters in a world with optional filtering.

    Supports filtering by importance and text search in name/description/role.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Get characters
    char_repo = CharacterRepository(session)
    characters, total = await char_repo.list_by_world(
        world_id=world_id,
        skip=skip,
        limit=limit,
        importance=importance,
        search=search
    )

    return CharacterListResponse(
        characters=characters,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/{world_id}/characters/search", response_model=CharacterSearchResponse)
async def search_characters(
    world_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    name: str = Query(..., min_length=1, max_length=200),
):
    """
    Search for characters by name in a world.

    Returns characters with mention counts.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Search characters
    char_repo = CharacterRepository(session)
    characters = await char_repo.search_by_name(world_id, name)

    # Get mention counts for each character
    characters_with_mentions = []
    for char in characters:
        result = await char_repo.get_with_mention_count(char.id)
        if result:
            char_obj, mention_count = result
            characters_with_mentions.append(
                CharacterWithMentionsResponse(
                    **char_obj.__dict__,
                    mention_count=mention_count
                )
            )

    return CharacterSearchResponse(
        characters=characters_with_mentions,
        total=len(characters_with_mentions)
    )


@router.get("/{world_id}/characters/{character_id}", response_model=CharacterWithMentionsResponse)
async def get_character(
    world_id: str,
    character_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Get a specific character by ID with mention count.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Get character
    char_repo = CharacterRepository(session)
    result = await char_repo.get_with_mention_count(character_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character {character_id} not found"
        )

    character, mention_count = result

    # Verify character belongs to world
    if character.world_id != world_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character {character_id} not found in world {world_id}"
        )

    return CharacterWithMentionsResponse(
        **character.__dict__,
        mention_count=mention_count
    )


@router.put("/{world_id}/characters/{character_id}", response_model=CharacterResponse)
async def update_character(
    world_id: str,
    character_id: str,
    character_in: CharacterUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Update a character.

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

    # Get and verify character
    char_repo = CharacterRepository(session)
    character = await char_repo.get_by_world_and_id(world_id, character_id)
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character {character_id} not found in world {world_id}"
        )

    # Update character
    updated_character = await char_repo.update(character_id, character_in)
    await session.commit()

    logger.info("character_updated", character_id=character_id, world_id=world_id, user_id=current_user.id)
    return updated_character


@router.delete("/{world_id}/characters/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(
    world_id: str,
    character_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Delete a character.

    Requires ownership of the world. Cascade deletes all mentions and relationships.
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

    # Delete character
    await char_repo.delete(character_id)
    await session.commit()

    logger.info("character_deleted", character_id=character_id, world_id=world_id, user_id=current_user.id)
    return None
