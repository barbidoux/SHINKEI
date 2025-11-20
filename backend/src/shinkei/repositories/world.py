"""World repository for database operations."""
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from shinkei.models.world import World, ChronologyMode
from shinkei.schemas.world import WorldCreate, WorldUpdate
from shinkei.logging_config import get_logger

logger = get_logger(__name__)


class WorldRepository:
    """Repository for World model database operations."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
    
    async def create(self, user_id: str, world_data: WorldCreate) -> World:
        """
        Create a new world.
        
        Args:
            user_id: Owner user ID
            world_data: World creation data
            
        Returns:
            Created world instance
        """
        world = World(
            user_id=user_id,
            name=world_data.name,
            description=world_data.description,
            tone=world_data.tone,
            backdrop=world_data.backdrop,
            laws=world_data.laws.model_dump(),
            chronology_mode=ChronologyMode(world_data.chronology_mode),
        )
        
        self.session.add(world)
        await self.session.flush()
        await self.session.refresh(world)
        
        logger.info("world_created", world_id=world.id, user_id=user_id)
        return world
    
    async def get_by_id(self, world_id: str) -> Optional[World]:
        """
        Get world by ID.
        
        Args:
            world_id: World UUID
            
        Returns:
            World instance or None if not found
        """
        result = await self.session.execute(
            select(World).where(World.id == world_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_and_id(self, user_id: str, world_id: str) -> Optional[World]:
        """
        Get world by user ID and world ID.
        
        Args:
            user_id: User UUID
            world_id: World UUID
            
        Returns:
            World instance or None if not found or not owned by user
        """
        result = await self.session.execute(
            select(World).where(
                World.id == world_id,
                World.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def list_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[World], int]:
        """
        List worlds owned by a specific user.
        
        Args:
            user_id: User UUID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (worlds list, total count)
        """
        # Get total count
        count_result = await self.session.execute(
            select(func.count())
            .select_from(World)
            .where(World.user_id == user_id)
        )
        total = count_result.scalar_one()
        
        # Get worlds
        result = await self.session.execute(
            select(World)
            .where(World.user_id == user_id)
            .order_by(World.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        worlds = list(result.scalars().all())
        
        return worlds, total
    
    async def update(
        self,
        world_id: str,
        world_data: WorldUpdate
    ) -> Optional[World]:
        """
        Update world information.
        
        Args:
            world_id: World UUID
            world_data: Update data
            
        Returns:
            Updated world instance or None if not found
        """
        world = await self.get_by_id(world_id)
        if not world:
            return None
        
        update_data = world_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "laws" and value is not None:
                setattr(world, field, value.model_dump())
            elif field == "chronology_mode" and value is not None:
                setattr(world, field, ChronologyMode(value))
            elif value is not None:
                setattr(world, field, value)
        
        await self.session.flush()
        await self.session.refresh(world)
        
        logger.info("world_updated", world_id=world.id)
        return world
    
    async def delete(self, world_id: str) -> bool:
        """
        Delete a world.
        
        Args:
            world_id: World UUID
            
        Returns:
            True if deleted, False if not found
        """
        world = await self.get_by_id(world_id)
        if not world:
            return False
        
        await self.session.delete(world)
        await self.session.flush()
        
        logger.info("world_deleted", world_id=world_id)
        return True
    
    async def exists(self, world_id: str) -> bool:
        """
        Check if world exists.
        
        Args:
            world_id: World UUID
            
        Returns:
            True if world exists, False otherwise
        """
        result = await self.session.execute(
            select(func.count()).select_from(World).where(World.id == world_id)
        )
        return result.scalar_one() > 0
