"""Character repository for database operations."""
from typing import Optional
from sqlalchemy import select, func, or_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession
from shinkei.models.character import Character, EntityImportance
from shinkei.schemas.character import CharacterCreate, CharacterUpdate
from shinkei.logging_config import get_logger

logger = get_logger(__name__)


class CharacterRepository:
    """Repository for Character model database operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(self, world_id: str, character_data: CharacterCreate) -> Character:
        """
        Create a new character.

        Args:
            world_id: World ID the character belongs to
            character_data: Character creation data

        Returns:
            Created character instance
        """
        character = Character(
            world_id=world_id,
            name=character_data.name,
            description=character_data.description,
            aliases=character_data.aliases,
            role=character_data.role,
            importance=EntityImportance(character_data.importance),
            first_appearance_beat_id=character_data.first_appearance_beat_id,
            custom_metadata=character_data.custom_metadata,
        )

        self.session.add(character)
        await self.session.flush()
        await self.session.refresh(character)

        logger.info("character_created", character_id=character.id, world_id=world_id, name=character.name)
        return character

    async def get_by_id(self, character_id: str) -> Optional[Character]:
        """
        Get character by ID.

        Args:
            character_id: Character UUID

        Returns:
            Character instance or None if not found
        """
        result = await self.session.execute(
            select(Character).where(Character.id == character_id)
        )
        return result.scalar_one_or_none()

    async def get_by_world_and_id(self, world_id: str, character_id: str) -> Optional[Character]:
        """
        Get character by world ID and character ID.

        Args:
            world_id: World UUID
            character_id: Character UUID

        Returns:
            Character instance or None if not found or not in world
        """
        result = await self.session.execute(
            select(Character).where(
                Character.id == character_id,
                Character.world_id == world_id
            )
        )
        return result.scalar_one_or_none()

    async def list_by_world(
        self,
        world_id: str,
        skip: int = 0,
        limit: int = 100,
        importance: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple[list[Character], int]:
        """
        List characters in a world with pagination and filtering.

        Args:
            world_id: World UUID
            skip: Number of records to skip
            limit: Maximum number of records to return
            importance: Filter by importance level
            search: Search in name, aliases, or description

        Returns:
            Tuple of (list of characters, total count)
        """
        query = select(Character).where(Character.world_id == world_id)

        # Apply importance filter
        if importance:
            query = query.where(Character.importance == EntityImportance(importance))

        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Character.name.ilike(search_pattern),
                    Character.description.ilike(search_pattern),
                    Character.role.ilike(search_pattern)
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Get paginated results ordered by importance then name
        query = query.order_by(Character.importance, Character.name).offset(skip).limit(limit)
        result = await self.session.execute(query)
        characters = list(result.scalars().all())

        return characters, total

    async def update(self, character_id: str, character_data: CharacterUpdate) -> Optional[Character]:
        """
        Update a character.

        Args:
            character_id: Character UUID
            character_data: Character update data

        Returns:
            Updated character instance or None if not found
        """
        character = await self.get_by_id(character_id)
        if not character:
            return None

        update_data = character_data.model_dump(exclude_unset=True)

        # Convert importance to enum if present
        if "importance" in update_data:
            update_data["importance"] = EntityImportance(update_data["importance"])

        for field, value in update_data.items():
            setattr(character, field, value)

        await self.session.flush()
        await self.session.refresh(character)

        logger.info("character_updated", character_id=character.id, world_id=character.world_id)
        return character

    async def delete(self, character_id: str) -> bool:
        """
        Delete a character.

        Args:
            character_id: Character UUID

        Returns:
            True if deleted, False if not found
        """
        character = await self.get_by_id(character_id)
        if not character:
            return False

        await self.session.delete(character)
        await self.session.flush()

        logger.info("character_deleted", character_id=character_id, world_id=character.world_id)
        return True

    async def search_by_name(self, world_id: str, name: str) -> list[Character]:
        """
        Search characters by name (exact or partial match).

        Args:
            world_id: World UUID
            name: Character name to search for

        Returns:
            List of matching characters
        """
        result = await self.session.execute(
            select(Character).where(
                Character.world_id == world_id,
                Character.name.ilike(f"%{name}%")
            ).order_by(Character.name)
        )
        return list(result.scalars().all())

    async def get_with_mention_count(self, character_id: str) -> Optional[tuple[Character, int]]:
        """
        Get character with count of their mentions in story beats.

        Args:
            character_id: Character UUID

        Returns:
            Tuple of (Character, mention_count) or None if not found
        """
        from shinkei.models.entity_mention import EntityMention, EntityType

        character = await self.get_by_id(character_id)
        if not character:
            return None

        count_result = await self.session.execute(
            select(func.count()).where(
                EntityMention.entity_id == character_id,
                cast(EntityMention.entity_type, String) == "character"
            )
        )
        mention_count = count_result.scalar_one()

        return character, mention_count
