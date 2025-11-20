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
        story = Story(
            world_id=world_id,
            title=story_data.title,
            synopsis=story_data.synopsis,
            theme=story_data.theme,
            status=StoryStatus(story_data.status),
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
        limit: int = 100
    ) -> tuple[list[Story], int]:
        """
        List stories for a specific world.
        
        Args:
            world_id: World UUID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (stories list, total count)
        """
        # Get total count
        count_result = await self.session.execute(
            select(func.count())
            .select_from(Story)
            .where(Story.world_id == world_id)
        )
        total = count_result.scalar_one()
        
        # Get stories
        result = await self.session.execute(
            select(Story)
            .where(Story.world_id == world_id)
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
    
    async def delete(self, story_id: str) -> bool:
        """
        Delete a story.
        
        Args:
            story_id: Story UUID
            
        Returns:
            True if deleted, False if not found
        """
        story = await self.get_by_id(story_id)
        if not story:
            return False
        
        await self.session.delete(story)
        await self.session.flush()
        
        logger.info("story_deleted", story_id=story_id)
        return True
