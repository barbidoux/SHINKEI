"""EntityMention repository for database operations."""
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from shinkei.models.entity_mention import EntityMention, EntityType, MentionType, DetectionSource
from shinkei.schemas.entity_mention import EntityMentionCreate, EntityMentionUpdate
from shinkei.logging_config import get_logger

logger = get_logger(__name__)


class EntityMentionRepository:
    """Repository for EntityMention model database operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(self, story_beat_id: str, mention_data: EntityMentionCreate) -> EntityMention:
        """
        Create a new entity mention.

        Args:
            story_beat_id: Story beat ID
            mention_data: Entity mention creation data

        Returns:
            Created entity mention instance
        """
        mention = EntityMention(
            story_beat_id=story_beat_id,
            entity_type=EntityType(mention_data.entity_type),
            entity_id=mention_data.entity_id,
            mention_type=MentionType(mention_data.mention_type),
            confidence=mention_data.confidence,
            context_snippet=mention_data.context_snippet,
            detected_by=DetectionSource(mention_data.detected_by),
        )

        self.session.add(mention)
        await self.session.flush()
        await self.session.refresh(mention)

        logger.info(
            "entity_mention_created",
            mention_id=mention.id,
            beat_id=story_beat_id,
            entity_type=mention_data.entity_type,
            entity_id=mention_data.entity_id
        )
        return mention

    async def bulk_create(self, story_beat_id: str, mentions_data: list[EntityMentionCreate]) -> list[EntityMention]:
        """
        Create multiple entity mentions at once.

        Args:
            story_beat_id: Story beat ID
            mentions_data: List of entity mention creation data

        Returns:
            List of created entity mention instances
        """
        mentions = []
        for mention_data in mentions_data:
            mention = EntityMention(
                story_beat_id=story_beat_id,
                entity_type=EntityType(mention_data.entity_type),
                entity_id=mention_data.entity_id,
                mention_type=MentionType(mention_data.mention_type),
                confidence=mention_data.confidence,
                context_snippet=mention_data.context_snippet,
                detected_by=DetectionSource(mention_data.detected_by),
            )
            mentions.append(mention)

        self.session.add_all(mentions)
        await self.session.flush()

        for mention in mentions:
            await self.session.refresh(mention)

        logger.info("entity_mentions_bulk_created", beat_id=story_beat_id, count=len(mentions))
        return mentions

    async def get_by_id(self, mention_id: str) -> Optional[EntityMention]:
        """
        Get entity mention by ID.

        Args:
            mention_id: Entity mention UUID

        Returns:
            Entity mention instance or None if not found
        """
        result = await self.session.execute(
            select(EntityMention).where(EntityMention.id == mention_id)
        )
        return result.scalar_one_or_none()

    async def list_by_beat(
        self,
        story_beat_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[EntityMention], int]:
        """
        List entity mentions for a story beat.

        Args:
            story_beat_id: Story beat UUID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of mentions, total count)
        """
        query = select(EntityMention).where(EntityMention.story_beat_id == story_beat_id)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Get paginated results ordered by entity type and creation date
        query = query.order_by(EntityMention.entity_type, EntityMention.created_at).offset(skip).limit(limit)
        result = await self.session.execute(query)
        mentions = list(result.scalars().all())

        return mentions, total

    async def list_by_entity(
        self,
        entity_id: str,
        entity_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[EntityMention], int]:
        """
        List all mentions of a specific entity across all story beats.

        Args:
            entity_id: Entity UUID
            entity_type: Entity type (character or location)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of mentions, total count)
        """
        query = select(EntityMention).where(
            EntityMention.entity_id == entity_id,
            EntityMention.entity_type == EntityType(entity_type)
        )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Get paginated results ordered by creation date
        query = query.order_by(EntityMention.created_at).offset(skip).limit(limit)
        result = await self.session.execute(query)
        mentions = list(result.scalars().all())

        return mentions, total

    async def get_timeline_for_entity(self, entity_id: str, entity_type: str) -> list[dict]:
        """
        Get timeline of all appearances for an entity across stories.

        Args:
            entity_id: Entity UUID
            entity_type: Entity type (character or location)

        Returns:
            List of timeline items with story and beat information
        """
        from shinkei.models.story_beat import StoryBeat
        from shinkei.models.story import Story

        result = await self.session.execute(
            select(EntityMention, StoryBeat, Story)
            .join(StoryBeat, EntityMention.story_beat_id == StoryBeat.id)
            .join(Story, StoryBeat.story_id == Story.id)
            .where(
                EntityMention.entity_id == entity_id,
                EntityMention.entity_type == EntityType(entity_type)
            )
            .order_by(Story.created_at, StoryBeat.order_index)
        )

        timeline = []
        for mention, beat, story in result.all():
            timeline.append({
                "mention_id": mention.id,
                "story_beat_id": beat.id,
                "story_id": story.id,
                "story_title": story.title,
                "beat_order_index": beat.order_index,
                "mention_type": mention.mention_type.value,
                "context_snippet": mention.context_snippet,
                "created_at": mention.created_at
            })

        return timeline

    async def update(self, mention_id: str, mention_data: EntityMentionUpdate) -> Optional[EntityMention]:
        """
        Update an entity mention.

        Args:
            mention_id: Entity mention UUID
            mention_data: Entity mention update data

        Returns:
            Updated entity mention instance or None if not found
        """
        mention = await self.get_by_id(mention_id)
        if not mention:
            return None

        update_data = mention_data.model_dump(exclude_unset=True)

        # Convert enums if present
        if "mention_type" in update_data:
            update_data["mention_type"] = MentionType(update_data["mention_type"])
        if "detected_by" in update_data:
            update_data["detected_by"] = DetectionSource(update_data["detected_by"])

        for field, value in update_data.items():
            setattr(mention, field, value)

        await self.session.flush()
        await self.session.refresh(mention)

        logger.info("entity_mention_updated", mention_id=mention.id)
        return mention

    async def delete(self, mention_id: str) -> bool:
        """
        Delete an entity mention.

        Args:
            mention_id: Entity mention UUID

        Returns:
            True if deleted, False if not found
        """
        mention = await self.get_by_id(mention_id)
        if not mention:
            return False

        await self.session.delete(mention)
        await self.session.flush()

        logger.info("entity_mention_deleted", mention_id=mention_id)
        return True

    async def delete_by_beat(self, story_beat_id: str) -> int:
        """
        Delete all entity mentions for a story beat.

        Args:
            story_beat_id: Story beat UUID

        Returns:
            Number of mentions deleted
        """
        result = await self.session.execute(
            select(EntityMention).where(EntityMention.story_beat_id == story_beat_id)
        )
        mentions = list(result.scalars().all())

        for mention in mentions:
            await self.session.delete(mention)

        await self.session.flush()

        logger.info("entity_mentions_deleted_by_beat", beat_id=story_beat_id, count=len(mentions))
        return len(mentions)
