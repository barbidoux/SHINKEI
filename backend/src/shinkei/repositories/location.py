"""Location repository for database operations."""
from typing import Optional
from sqlalchemy import select, func, or_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from shinkei.models.location import Location
from shinkei.schemas.location import LocationCreate, LocationUpdate
from shinkei.logging_config import get_logger

logger = get_logger(__name__)


class LocationRepository:
    """Repository for Location model database operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(self, world_id: str, location_data: LocationCreate) -> Location:
        """
        Create a new location.

        Args:
            world_id: World ID the location belongs to
            location_data: Location creation data

        Returns:
            Created location instance
        """
        location = Location(
            world_id=world_id,
            name=location_data.name,
            description=location_data.description,
            location_type=location_data.location_type,
            parent_location_id=location_data.parent_location_id,
            significance=location_data.significance,
            first_appearance_beat_id=location_data.first_appearance_beat_id,
            coordinates=location_data.coordinates,
            custom_metadata=location_data.custom_metadata,
        )

        self.session.add(location)
        await self.session.flush()
        await self.session.refresh(location)

        logger.info("location_created", location_id=location.id, world_id=world_id, name=location.name)
        return location

    async def get_by_id(self, location_id: str) -> Optional[Location]:
        """
        Get location by ID.

        Args:
            location_id: Location UUID

        Returns:
            Location instance or None if not found
        """
        result = await self.session.execute(
            select(Location).where(Location.id == location_id)
        )
        return result.scalar_one_or_none()

    async def get_by_world_and_id(self, world_id: str, location_id: str) -> Optional[Location]:
        """
        Get location by world ID and location ID.

        Args:
            world_id: World UUID
            location_id: Location UUID

        Returns:
            Location instance or None if not found or not in world
        """
        result = await self.session.execute(
            select(Location).where(
                Location.id == location_id,
                Location.world_id == world_id
            )
        )
        return result.scalar_one_or_none()

    async def get_with_hierarchy(self, location_id: str) -> Optional[Location]:
        """
        Get location with parent and children loaded.

        Args:
            location_id: Location UUID

        Returns:
            Location with hierarchy loaded or None if not found
        """
        result = await self.session.execute(
            select(Location)
            .options(
                selectinload(Location.parent_location),
                selectinload(Location.child_locations)
            )
            .where(Location.id == location_id)
        )
        return result.scalar_one_or_none()

    async def list_by_world(
        self,
        world_id: str,
        skip: int = 0,
        limit: int = 100,
        location_type: Optional[str] = None,
        parent_location_id: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple[list[Location], int]:
        """
        List locations in a world with pagination and filtering.

        Args:
            world_id: World UUID
            skip: Number of records to skip
            limit: Maximum number of records to return
            location_type: Filter by location type
            parent_location_id: Filter by parent location (use "null" for root locations)
            search: Search in name or description

        Returns:
            Tuple of (list of locations, total count)
        """
        query = select(Location).where(Location.world_id == world_id)

        # Apply location type filter
        if location_type:
            query = query.where(Location.location_type == location_type)

        # Apply parent location filter
        if parent_location_id == "null":
            query = query.where(Location.parent_location_id.is_(None))
        elif parent_location_id:
            query = query.where(Location.parent_location_id == parent_location_id)

        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Location.name.ilike(search_pattern),
                    Location.description.ilike(search_pattern)
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Get paginated results ordered by name
        query = query.order_by(Location.name).offset(skip).limit(limit)
        result = await self.session.execute(query)
        locations = list(result.scalars().all())

        return locations, total

    async def get_root_locations(self, world_id: str) -> list[Location]:
        """
        Get all root locations (locations with no parent) in a world.

        Args:
            world_id: World UUID

        Returns:
            List of root locations
        """
        result = await self.session.execute(
            select(Location).where(
                Location.world_id == world_id,
                Location.parent_location_id.is_(None)
            ).order_by(Location.name)
        )
        return list(result.scalars().all())

    async def get_children(self, location_id: str) -> list[Location]:
        """
        Get all direct children of a location.

        Args:
            location_id: Parent location UUID

        Returns:
            List of child locations
        """
        result = await self.session.execute(
            select(Location).where(
                Location.parent_location_id == location_id
            ).order_by(Location.name)
        )
        return list(result.scalars().all())

    async def update(self, location_id: str, location_data: LocationUpdate) -> Optional[Location]:
        """
        Update a location.

        Args:
            location_id: Location UUID
            location_data: Location update data

        Returns:
            Updated location instance or None if not found
        """
        location = await self.get_by_id(location_id)
        if not location:
            return None

        update_data = location_data.model_dump(exclude_unset=True)

        # Prevent circular parent references
        if "parent_location_id" in update_data:
            parent_id = update_data["parent_location_id"]
            if parent_id == location_id:
                logger.warning("attempted_circular_location_parent", location_id=location_id)
                raise ValueError("A location cannot be its own parent")

        for field, value in update_data.items():
            setattr(location, field, value)

        await self.session.flush()
        await self.session.refresh(location)

        logger.info("location_updated", location_id=location.id, world_id=location.world_id)
        return location

    async def delete(self, location_id: str) -> bool:
        """
        Delete a location.

        Args:
            location_id: Location UUID

        Returns:
            True if deleted, False if not found
        """
        location = await self.get_by_id(location_id)
        if not location:
            return False

        await self.session.delete(location)
        await self.session.flush()

        logger.info("location_deleted", location_id=location_id, world_id=location.world_id)
        return True

    async def get_with_mention_count(self, location_id: str) -> Optional[tuple[Location, int]]:
        """
        Get location with count of their mentions in story beats.

        Args:
            location_id: Location UUID

        Returns:
            Tuple of (Location, mention_count) or None if not found
        """
        from shinkei.models.entity_mention import EntityMention, EntityType

        location = await self.get_by_id(location_id)
        if not location:
            return None

        count_result = await self.session.execute(
            select(func.count()).where(
                EntityMention.entity_id == location_id,
                cast(EntityMention.entity_type, String) == "location"
            )
        )
        mention_count = count_result.scalar_one()

        return location, mention_count
