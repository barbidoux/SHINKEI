"""EntityMention API endpoints."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from shinkei.auth.dependencies import get_current_user, get_db_session
from shinkei.models.user import User
from shinkei.models.entity_mention import EntityMention
from shinkei.schemas.entity_mention import (
    EntityMentionCreate,
    EntityMentionUpdate,
    EntityMentionResponse,
    EntityMentionListResponse,
    EntityTimelineResponse,
    BulkEntityMentionCreate
)
from shinkei.repositories.entity_mention import EntityMentionRepository
from shinkei.repositories.story_beat import StoryBeatRepository
from shinkei.repositories.story import StoryRepository
from shinkei.repositories.world import WorldRepository
from shinkei.repositories.character import CharacterRepository
from shinkei.repositories.location import LocationRepository
from shinkei.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/stories/{story_id}/beats/{beat_id}/mentions", response_model=EntityMentionResponse, status_code=status.HTTP_201_CREATED)
async def create_entity_mention(
    story_id: str,
    beat_id: str,
    mention_in: EntityMentionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> EntityMention:
    """
    Create a new entity mention in a story beat.

    Requires ownership of the story's world.
    """
    # Verify story ownership through world
    story_repo = StoryRepository(session)
    story = await story_repo.get_by_id(story_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Story {story_id} not found"
        )

    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, story.world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found or access denied"
        )

    # Verify beat belongs to story
    beat_repo = StoryBeatRepository(session)
    beat = await beat_repo.get_by_id(beat_id)
    if not beat or beat.story_id != story_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Beat {beat_id} not found in story {story_id}"
        )

    # Verify entity exists in the same world
    if mention_in.entity_type == "character":
        char_repo = CharacterRepository(session)
        entity = await char_repo.get_by_world_and_id(story.world_id, mention_in.entity_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Character {mention_in.entity_id} not found in world {story.world_id}"
            )
    elif mention_in.entity_type == "location":
        loc_repo = LocationRepository(session)
        entity = await loc_repo.get_by_world_and_id(story.world_id, mention_in.entity_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location {mention_in.entity_id} not found in world {story.world_id}"
            )

    # Create mention
    mention_repo = EntityMentionRepository(session)
    mention = await mention_repo.create(beat_id, mention_in)
    await session.commit()

    logger.info("entity_mention_created", mention_id=mention.id, beat_id=beat_id, entity_type=mention_in.entity_type)
    return mention


@router.post("/stories/{story_id}/beats/{beat_id}/mentions/bulk", response_model=list[EntityMentionResponse], status_code=status.HTTP_201_CREATED)
async def create_bulk_entity_mentions(
    story_id: str,
    beat_id: str,
    bulk_mentions: BulkEntityMentionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Create multiple entity mentions at once for a story beat.

    Useful for AI auto-detection of multiple entities.
    """
    # Verify story ownership
    story_repo = StoryRepository(session)
    story = await story_repo.get_by_id(story_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Story {story_id} not found"
        )

    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, story.world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found or access denied"
        )

    # Verify beat
    beat_repo = StoryBeatRepository(session)
    beat = await beat_repo.get_by_id(beat_id)
    if not beat or beat.story_id != story_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Beat {beat_id} not found in story {story_id}"
        )

    # Create all mentions
    mention_repo = EntityMentionRepository(session)
    mentions = await mention_repo.bulk_create(beat_id, bulk_mentions.mentions)
    await session.commit()

    logger.info("entity_mentions_bulk_created", beat_id=beat_id, count=len(mentions))
    return mentions


@router.get("/stories/{story_id}/beats/{beat_id}/mentions", response_model=EntityMentionListResponse)
async def list_beat_entity_mentions(
    story_id: str,
    beat_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    List all entity mentions for a story beat.
    """
    # Verify story ownership
    story_repo = StoryRepository(session)
    story = await story_repo.get_by_id(story_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Story {story_id} not found"
        )

    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, story.world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found or access denied"
        )

    # Verify beat
    beat_repo = StoryBeatRepository(session)
    beat = await beat_repo.get_by_id(beat_id)
    if not beat or beat.story_id != story_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Beat {beat_id} not found in story {story_id}"
        )

    # Get mentions
    mention_repo = EntityMentionRepository(session)
    mentions, total = await mention_repo.list_by_beat(beat_id, skip, limit)

    return EntityMentionListResponse(
        mentions=mentions,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/entities/{entity_type}/{entity_id}/timeline", response_model=EntityTimelineResponse)
async def get_entity_timeline(
    entity_type: str,
    entity_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Get timeline of all appearances for an entity across all stories.

    Shows where the character or location appears chronologically.
    """
    # Validate entity type
    if entity_type not in ["character", "location"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="entity_type must be 'character' or 'location'"
        )

    # Get entity and verify ownership
    if entity_type == "character":
        char_repo = CharacterRepository(session)
        entity = await char_repo.get_by_id(entity_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Character {entity_id} not found"
            )
        world_id = entity.world_id
        entity_name = entity.name
    else:  # location
        loc_repo = LocationRepository(session)
        entity = await loc_repo.get_by_id(entity_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location {entity_id} not found"
            )
        world_id = entity.world_id
        entity_name = entity.name

    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity not found or access denied"
        )

    # Get timeline
    mention_repo = EntityMentionRepository(session)
    timeline_items = await mention_repo.get_timeline_for_entity(entity_id, entity_type)

    return EntityTimelineResponse(
        entity_id=entity_id,
        entity_type=entity_type,
        entity_name=entity_name,
        mentions=timeline_items,
        total_mentions=len(timeline_items)
    )


@router.put("/stories/{story_id}/beats/{beat_id}/mentions/{mention_id}", response_model=EntityMentionResponse)
async def update_entity_mention(
    story_id: str,
    beat_id: str,
    mention_id: str,
    mention_in: EntityMentionUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Update an entity mention.
    """
    # Verify story ownership
    story_repo = StoryRepository(session)
    story = await story_repo.get_by_id(story_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Story {story_id} not found"
        )

    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, story.world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found or access denied"
        )

    # Get and verify mention
    mention_repo = EntityMentionRepository(session)
    mention = await mention_repo.get_by_id(mention_id)
    if not mention or mention.story_beat_id != beat_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mention {mention_id} not found in beat {beat_id}"
        )

    # Update mention
    updated_mention = await mention_repo.update(mention_id, mention_in)
    await session.commit()

    logger.info("entity_mention_updated", mention_id=mention_id)
    return updated_mention


@router.delete("/stories/{story_id}/beats/{beat_id}/mentions/{mention_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity_mention(
    story_id: str,
    beat_id: str,
    mention_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Delete an entity mention.
    """
    # Verify story ownership
    story_repo = StoryRepository(session)
    story = await story_repo.get_by_id(story_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Story {story_id} not found"
        )

    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, story.world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found or access denied"
        )

    # Get and verify mention
    mention_repo = EntityMentionRepository(session)
    mention = await mention_repo.get_by_id(mention_id)
    if not mention or mention.story_beat_id != beat_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mention {mention_id} not found in beat {beat_id}"
        )

    # Delete mention
    await mention_repo.delete(mention_id)
    await session.commit()

    logger.info("entity_mention_deleted", mention_id=mention_id)
    return None
