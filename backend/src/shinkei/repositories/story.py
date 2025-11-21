"""Story repository for database operations."""
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from shinkei.models.story import Story, StoryStatus
from shinkei.schemas.story import StoryCreate, StoryUpdate
from shinkei.logging_config import get_logger

logger = get_logger(__name__)


class StoryRepository:
    """Repository for Story model database operations."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
    
    async def create(self, world_id: str, story_data: StoryCreate) -> Story:
        """
        Create a new story.

        Args:
            world_id: World UUID
            story_data: Story creation data

        Returns:
            Created story instance
        """
        from shinkei.models.story import AuthoringMode, POVType

        story = Story(
            world_id=world_id,
            title=story_data.title,
            synopsis=story_data.synopsis,
            theme=story_data.theme,
            status=StoryStatus(story_data.status),
            mode=AuthoringMode(story_data.mode),
            pov_type=POVType(story_data.pov_type),
            tags=story_data.tags if story_data.tags else [],
        )

        self.session.add(story)
        await self.session.flush()
        await self.session.refresh(story)

        logger.info("story_created", story_id=story.id, world_id=world_id)
        return story
    
    async def get_by_id(self, story_id: str) -> Optional[Story]:
        """
        Get story by ID.
        
        Args:
            story_id: Story UUID
            
        Returns:
            Story instance or None if not found
        """
        result = await self.session.execute(
            select(Story).where(Story.id == story_id)
        )
        return result.scalar_one_or_none()
    
    async def list_by_world(
        self,
        world_id: str,
        skip: int = 0,
        limit: int = 100,
        include_archived: bool = False
    ) -> tuple[list[Story], int]:
        """
        List stories for a specific world (non-archived by default).

        Args:
            world_id: World UUID
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_archived: If True, include archived stories

        Returns:
            Tuple of (stories list, total count)
        """
        # Build query with archived filter
        query_filter = [Story.world_id == world_id]
        if not include_archived:
            query_filter.append(Story.archived_at.is_(None))

        # Get total count
        count_result = await self.session.execute(
            select(func.count())
            .select_from(Story)
            .where(*query_filter)
        )
        total = count_result.scalar_one()

        # Get stories
        result = await self.session.execute(
            select(Story)
            .where(*query_filter)
            .order_by(Story.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        stories = list(result.scalars().all())

        return stories, total
    
    async def update(
        self,
        story_id: str,
        story_data: StoryUpdate
    ) -> Optional[Story]:
        """
        Update story information.
        
        Args:
            story_id: Story UUID
            story_data: Update data
            
        Returns:
            Updated story instance or None if not found
        """
        story = await self.get_by_id(story_id)
        if not story:
            return None
        
        update_data = story_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "status" and value is not None:
                setattr(story, field, StoryStatus(value))
            elif value is not None:
                setattr(story, field, value)
        
        await self.session.flush()
        await self.session.refresh(story)
        
        logger.info("story_updated", story_id=story.id)
        return story
    
    async def delete(self, story_id: str, soft_delete: bool = True) -> bool:
        """
        Delete a story (soft delete by default).

        Args:
            story_id: Story UUID
            soft_delete: If True, set archived_at (default). If False, hard delete.

        Returns:
            True if deleted, False if not found
        """
        story = await self.get_by_id(story_id)
        if not story:
            return False

        if soft_delete:
            # Soft delete: set archived_at timestamp
            from datetime import datetime, timezone
            story.archived_at = datetime.now(timezone.utc)
            story.status = StoryStatus.ARCHIVED
            await self.session.flush()
            logger.info("story_archived", story_id=story_id)
        else:
            # Hard delete: permanently remove
            await self.session.delete(story)
            await self.session.flush()
            logger.info("story_hard_deleted", story_id=story_id)

        return True

    async def restore(self, story_id: str) -> Optional[Story]:
        """
        Restore an archived story.

        Args:
            story_id: Story UUID

        Returns:
            Restored story instance or None if not found/not archived
        """
        story = await self.get_by_id(story_id)
        if not story or story.archived_at is None:
            return None

        story.archived_at = None
        story.status = StoryStatus.DRAFT
        await self.session.flush()
        await self.session.refresh(story)

        logger.info("story_restored", story_id=story_id)
        return story

    async def list_archived(
        self,
        world_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[Story], int]:
        """
        List only archived stories for a world.

        Args:
            world_id: World UUID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (stories list, total count)
        """
        count_result = await self.session.execute(
            select(func.count())
            .select_from(Story)
            .where(
                Story.world_id == world_id,
                Story.archived_at.isnot(None)
            )
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(Story)
            .where(
                Story.world_id == world_id,
                Story.archived_at.isnot(None)
            )
            .order_by(Story.archived_at.desc())
            .offset(skip)
            .limit(limit)
        )
        stories = list(result.scalars().all())

        return stories, total

    async def list_by_tag(
        self,
        world_id: str,
        tag: str,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[Story], int]:
        """
        List stories by tag (non-archived only).

        Args:
            world_id: World UUID
            tag: Tag to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (stories list, total count)
        """
        count_result = await self.session.execute(
            select(func.count())
            .select_from(Story)
            .where(
                Story.world_id == world_id,
                Story.archived_at.is_(None),
                Story.tags.contains([tag])
            )
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(Story)
            .where(
                Story.world_id == world_id,
                Story.archived_at.is_(None),
                Story.tags.contains([tag])
            )
            .order_by(Story.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        stories = list(result.scalars().all())

        return stories, total

    async def get_all_tags(self, world_id: str) -> list[str]:
        """
        Get all unique tags used in a world's non-archived stories.

        Args:
            world_id: World UUID

        Returns:
            Sorted list of unique tags
        """
        result = await self.session.execute(
            select(Story.tags)
            .where(
                Story.world_id == world_id,
                Story.archived_at.is_(None)
            )
        )
        stories = result.scalars().all()

        all_tags = set()
        for story_tags in stories:
            if story_tags:
                all_tags.update(story_tags)

        return sorted(list(all_tags))

    async def get_statistics(self, story_id: str) -> dict:
        """
        Calculate statistics for a story.

        Args:
            story_id: Story UUID

        Returns:
            Dictionary with statistics
        """
        from shinkei.models.story_beat import StoryBeat, GeneratedBy, BeatType

        result = await self.session.execute(
            select(StoryBeat)
            .where(StoryBeat.story_id == story_id)
            .order_by(StoryBeat.order_index.asc())
        )
        beats = list(result.scalars().all())

        if not beats:
            return {
                "beat_count": 0,
                "word_count": 0,
                "character_count": 0,
                "ai_generated_count": 0,
                "user_generated_count": 0,
                "collaborative_count": 0,
                "latest_beat_date": None,
                "world_event_links": 0,
                "beat_type_distribution": {},
                "estimated_reading_minutes": 0
            }

        beat_count = len(beats)
        word_count = sum(len(beat.content.split()) for beat in beats)
        character_count = sum(len(beat.content) for beat in beats)

        ai_count = sum(1 for b in beats if b.generated_by == GeneratedBy.AI)
        user_count = sum(1 for b in beats if b.generated_by == GeneratedBy.USER)
        collab_count = sum(1 for b in beats if b.generated_by == GeneratedBy.COLLABORATIVE)

        latest_date = max((b.created_at for b in beats), default=None)
        event_links = sum(1 for b in beats if b.world_event_id is not None)

        type_dist = {}
        for beat_type in BeatType:
            count = sum(1 for b in beats if b.type == beat_type)
            if count > 0:
                type_dist[beat_type.value] = count

        reading_minutes = max(1, word_count // 250)

        return {
            "beat_count": beat_count,
            "word_count": word_count,
            "character_count": character_count,
            "ai_generated_count": ai_count,
            "user_generated_count": user_count,
            "collaborative_count": collab_count,
            "latest_beat_date": latest_date,
            "world_event_links": event_links,
            "beat_type_distribution": type_dist,
            "estimated_reading_minutes": reading_minutes
        }
