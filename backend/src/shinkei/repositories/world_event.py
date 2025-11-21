"""WorldEvent repository for database operations."""
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from shinkei.models.world_event import WorldEvent
from shinkei.schemas.world_event import WorldEventCreate, WorldEventUpdate
from shinkei.logging_config import get_logger

logger = get_logger(__name__)


class WorldEventRepository:
    """Repository for WorldEvent model database operations."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
    
    async def create(self, world_id: str, event_data: WorldEventCreate) -> WorldEvent:
        """
        Create a new world event.
        
        Args:
            world_id: World UUID
            event_data: Event creation data
            
        Returns:
            Created world event instance
        """
        event = WorldEvent(
            world_id=world_id,
            t=event_data.t,
            label_time=event_data.label_time,
            location_id=event_data.location_id,
            type=event_data.type,
            summary=event_data.summary,
            tags=event_data.tags,
            caused_by_ids=event_data.caused_by_ids,
        )
        
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        
        logger.info("world_event_created", event_id=event.id, world_id=world_id)
        return event
    
    async def get_by_id(self, event_id: str) -> Optional[WorldEvent]:
        """
        Get world event by ID.
        
        Args:
            event_id: WorldEvent UUID
            
        Returns:
            WorldEvent instance or None if not found
        """
        result = await self.session.execute(
            select(WorldEvent).where(WorldEvent.id == event_id)
        )
        return result.scalar_one_or_none()
    
    async def list_by_world(
        self,
        world_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[WorldEvent], int]:
        """
        List events for a specific world.
        
        Args:
            world_id: World UUID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (events list, total count)
        """
        # Get total count
        count_result = await self.session.execute(
            select(func.count())
            .select_from(WorldEvent)
            .where(WorldEvent.world_id == world_id)
        )
        total = count_result.scalar_one()
        
        # Get events ordered by time t
        result = await self.session.execute(
            select(WorldEvent)
            .where(WorldEvent.world_id == world_id)
            .order_by(WorldEvent.t.asc())
            .offset(skip)
            .limit(limit)
        )
        events = list(result.scalars().all())
        
        return events, total
    
    async def update(
        self,
        event_id: str,
        event_data: WorldEventUpdate
    ) -> Optional[WorldEvent]:
        """
        Update world event information.
        
        Args:
            event_id: WorldEvent UUID
            event_data: Update data
            
        Returns:
            Updated world event instance or None if not found
        """
        event = await self.get_by_id(event_id)
        if not event:
            return None
        
        update_data = event_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                setattr(event, field, value)
        
        await self.session.flush()
        await self.session.refresh(event)
        
        logger.info("world_event_updated", event_id=event.id)
        return event
    
    async def delete(self, event_id: str) -> bool:
        """
        Delete a world event.
        
        Args:
            event_id: WorldEvent UUID
            
        Returns:
            True if deleted, False if not found
        """
        event = await self.get_by_id(event_id)
        if not event:
            return False
        
        await self.session.delete(event)
        await self.session.flush()
        
        logger.info("world_event_deleted", event_id=event_id)
        return True
