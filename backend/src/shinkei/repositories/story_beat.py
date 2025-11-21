"""StoryBeat repository for database operations."""
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from shinkei.models.story_beat import StoryBeat, BeatType
from shinkei.models.story import Story
from shinkei.schemas.story_beat import StoryBeatCreate, StoryBeatUpdate
from shinkei.logging_config import get_logger

logger = get_logger(__name__)


class StoryBeatRepository:
    """Repository for StoryBeat model database operations."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
    
    async def create(self, story_id: str, beat_data: StoryBeatCreate) -> StoryBeat:
        """
        Create a new story beat.

        If order_index is 0 (default), automatically append to end of story.

        Args:
            story_id: Story UUID
            beat_data: Beat creation data

        Returns:
            Created story beat instance
        """
        # If order_index is 0 (default), append to end
        order_index = beat_data.order_index
        if order_index == 0:
            order_index = await self.get_last_order_index(story_id) + 1

        beat = StoryBeat(
            story_id=story_id,
            order_index=order_index,
            content=beat_data.content,
            type=BeatType(beat_data.type),
            world_event_id=beat_data.world_event_id,
            summary=beat_data.summary,
            local_time_label=beat_data.local_time_label,
            generated_by=beat_data.generated_by,
            generation_reasoning=beat_data.generation_reasoning,
        )

        self.session.add(beat)
        await self.session.flush()
        await self.session.refresh(beat)

        logger.info("story_beat_created", beat_id=beat.id, story_id=story_id, order_index=order_index)
        return beat
    
    async def get_by_id(self, beat_id: str) -> Optional[StoryBeat]:
        """
        Get story beat by ID.
        
        Args:
            beat_id: StoryBeat UUID
            
        Returns:
            StoryBeat instance or None if not found
        """
        result = await self.session.execute(
            select(StoryBeat).where(StoryBeat.id == beat_id)
        )
        return result.scalar_one_or_none()
    
    async def list_by_story(
        self,
        story_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[StoryBeat], int]:
        """
        List beats for a specific story.
        
        Args:
            story_id: Story UUID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (beats list, total count)
        """
        # Get total count
        count_result = await self.session.execute(
            select(func.count())
            .select_from(StoryBeat)
            .where(StoryBeat.story_id == story_id)
        )
        total = count_result.scalar_one()
        
        # Get beats ordered by index
        result = await self.session.execute(
            select(StoryBeat)
            .where(StoryBeat.story_id == story_id)
            .order_by(StoryBeat.order_index.asc())
            .offset(skip)
            .limit(limit)
        )
        beats = list(result.scalars().all())
        
        return beats, total
    
    async def update(
        self,
        beat_id: str,
        beat_data: StoryBeatUpdate
    ) -> Optional[StoryBeat]:
        """
        Update story beat information.
        
        Args:
            beat_id: StoryBeat UUID
            beat_data: Update data
            
        Returns:
            Updated story beat instance or None if not found
        """
        beat = await self.get_by_id(beat_id)
        if not beat:
            return None
        
        update_data = beat_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "type" and value is not None:
                setattr(beat, field, BeatType(value))
            elif value is not None:
                setattr(beat, field, value)
        
        await self.session.flush()
        await self.session.refresh(beat)
        
        logger.info("story_beat_updated", beat_id=beat.id)
        return beat
    
    async def delete(self, beat_id: str) -> bool:
        """
        Delete a story beat.
        
        Args:
            beat_id: StoryBeat UUID
            
        Returns:
            True if deleted, False if not found
        """
        beat = await self.get_by_id(beat_id)
        if not beat:
            return False
        
        await self.session.delete(beat)
        await self.session.flush()
        
        logger.info("story_beat_deleted", beat_id=beat_id)
        return True
    
    async def reorder(self, story_id: str, beat_ids: list[str]) -> bool:
        """
        Reorder beats in a story.

        Args:
            story_id: Story UUID
            beat_ids: List of beat IDs in new order

        Returns:
            True if successful
        """
        # This is a simplified implementation. In a real app, we'd want to be more careful
        # about concurrency and ensuring all IDs belong to the story.
        for index, beat_id in enumerate(beat_ids):
            beat = await self.get_by_id(beat_id)
            if beat and beat.story_id == story_id:
                beat.order_index = index + 1

        await self.session.flush()
        return True

    async def get_beat_order_index(self, beat_id: str) -> Optional[int]:
        """
        Get the order_index of a specific beat.

        Args:
            beat_id: StoryBeat UUID

        Returns:
            order_index value or None if beat not found
        """
        beat = await self.get_by_id(beat_id)
        return beat.order_index if beat else None

    async def get_last_order_index(self, story_id: str) -> int:
        """
        Get the highest order_index in a story.

        Args:
            story_id: Story UUID

        Returns:
            Highest order_index value, or 0 if story has no beats
        """
        result = await self.session.execute(
            select(func.max(StoryBeat.order_index))
            .where(StoryBeat.story_id == story_id)
        )
        max_index = result.scalar_one_or_none()
        return max_index if max_index is not None else 0

    async def insert_at_position(
        self,
        story_id: str,
        position: int,
        beat_data: StoryBeatCreate
    ) -> StoryBeat:
        """
        Insert a beat at a specific position, reindexing subsequent beats.

        This method:
        1. Increments order_index of all beats at position and above
        2. Inserts the new beat at the specified position
        3. Ensures consistent ordering

        Args:
            story_id: Story UUID
            position: 1-based position to insert at (1 = first beat)
            beat_data: Beat creation data

        Returns:
            Created story beat instance

        Raises:
            ValueError: If position is invalid (<1)
        """
        if position < 1:
            raise ValueError(f"Position must be >= 1, got {position}")

        # Get all beats at or after the insertion position
        result = await self.session.execute(
            select(StoryBeat)
            .where(
                StoryBeat.story_id == story_id,
                StoryBeat.order_index >= position
            )
            .order_by(StoryBeat.order_index.asc())
        )
        beats_to_reindex = list(result.scalars().all())

        # Increment order_index of all affected beats
        for beat in beats_to_reindex:
            beat.order_index += 1

        await self.session.flush()

        # Create new beat at the specified position
        beat = StoryBeat(
            story_id=story_id,
            order_index=position,
            content=beat_data.content,
            type=BeatType(beat_data.type),
            world_event_id=beat_data.world_event_id,
            summary=beat_data.summary,
            local_time_label=beat_data.local_time_label,
            generated_by=beat_data.generated_by,
            generation_reasoning=beat_data.generation_reasoning
        )

        self.session.add(beat)
        await self.session.flush()
        await self.session.refresh(beat)

        logger.info(
            "story_beat_inserted",
            beat_id=beat.id,
            story_id=story_id,
            position=position,
            reindexed_count=len(beats_to_reindex)
        )

        return beat

    async def list_by_world_event(self, event_id: str) -> list[StoryBeat]:
        """
        List all beats linked to a specific world event, with story information loaded.

        Args:
            event_id: WorldEvent UUID

        Returns:
            List of story beats with story relationship loaded
        """
        result = await self.session.execute(
            select(StoryBeat)
            .options(selectinload(StoryBeat.story))
            .where(StoryBeat.world_event_id == event_id)
            .order_by(StoryBeat.created_at.asc())
        )
        beats = list(result.scalars().all())

        logger.info("beats_fetched_by_event", event_id=event_id, count=len(beats))
        return beats
