"""CharacterRelationship repository for database operations."""
from typing import Optional
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from shinkei.models.character_relationship import CharacterRelationship, RelationshipStrength
from shinkei.schemas.character_relationship import CharacterRelationshipCreate, CharacterRelationshipUpdate
from shinkei.logging_config import get_logger

logger = get_logger(__name__)


class CharacterRelationshipRepository:
    """Repository for CharacterRelationship model database operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(self, world_id: str, relationship_data: CharacterRelationshipCreate) -> CharacterRelationship:
        """
        Create a new character relationship.

        Args:
            world_id: World ID the relationship belongs to
            relationship_data: Character relationship creation data

        Returns:
            Created character relationship instance
        """
        relationship = CharacterRelationship(
            world_id=world_id,
            character_a_id=relationship_data.character_a_id,
            character_b_id=relationship_data.character_b_id,
            relationship_type=relationship_data.relationship_type,
            description=relationship_data.description,
            strength=RelationshipStrength(relationship_data.strength),
            first_established_beat_id=relationship_data.first_established_beat_id,
        )

        self.session.add(relationship)
        await self.session.flush()
        await self.session.refresh(relationship)

        logger.info(
            "character_relationship_created",
            relationship_id=relationship.id,
            world_id=world_id,
            type=relationship_data.relationship_type
        )
        return relationship

    async def get_by_id(self, relationship_id: str) -> Optional[CharacterRelationship]:
        """
        Get character relationship by ID.

        Args:
            relationship_id: Character relationship UUID

        Returns:
            Character relationship instance or None if not found
        """
        result = await self.session.execute(
            select(CharacterRelationship).where(CharacterRelationship.id == relationship_id)
        )
        return result.scalar_one_or_none()

    async def get_by_world_and_id(self, world_id: str, relationship_id: str) -> Optional[CharacterRelationship]:
        """
        Get character relationship by world ID and relationship ID.

        Args:
            world_id: World UUID
            relationship_id: Character relationship UUID

        Returns:
            Character relationship instance or None if not found or not in world
        """
        result = await self.session.execute(
            select(CharacterRelationship).where(
                CharacterRelationship.id == relationship_id,
                CharacterRelationship.world_id == world_id
            )
        )
        return result.scalar_one_or_none()

    async def list_by_world(
        self,
        world_id: str,
        skip: int = 0,
        limit: int = 100,
        strength: Optional[str] = None,
        relationship_type: Optional[str] = None
    ) -> tuple[list[CharacterRelationship], int]:
        """
        List character relationships in a world with pagination and filtering.

        Args:
            world_id: World UUID
            skip: Number of records to skip
            limit: Maximum number of records to return
            strength: Filter by relationship strength
            relationship_type: Filter by relationship type

        Returns:
            Tuple of (list of relationships, total count)
        """
        query = select(CharacterRelationship).where(CharacterRelationship.world_id == world_id)

        # Apply strength filter
        if strength:
            query = query.where(CharacterRelationship.strength == RelationshipStrength(strength))

        # Apply relationship type filter
        if relationship_type:
            query = query.where(CharacterRelationship.relationship_type.ilike(f"%{relationship_type}%"))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Get paginated results ordered by strength then type
        query = query.order_by(CharacterRelationship.strength, CharacterRelationship.relationship_type).offset(skip).limit(limit)
        result = await self.session.execute(query)
        relationships = list(result.scalars().all())

        return relationships, total

    async def list_by_character(self, character_id: str) -> list[CharacterRelationship]:
        """
        Get all relationships for a specific character.

        Args:
            character_id: Character UUID

        Returns:
            List of relationships where character is either A or B
        """
        result = await self.session.execute(
            select(CharacterRelationship)
            .options(
                joinedload(CharacterRelationship.character_a),
                joinedload(CharacterRelationship.character_b)
            )
            .where(
                or_(
                    CharacterRelationship.character_a_id == character_id,
                    CharacterRelationship.character_b_id == character_id
                )
            )
            .order_by(CharacterRelationship.strength)
        )
        return list(result.scalars().all())

    async def get_network_data(self, world_id: str) -> dict:
        """
        Get all relationship data for network graph visualization.

        Args:
            world_id: World UUID

        Returns:
            Dictionary with nodes (characters) and edges (relationships)
        """
        from shinkei.models.character import Character

        # Get all relationships with characters loaded
        result = await self.session.execute(
            select(CharacterRelationship)
            .options(
                joinedload(CharacterRelationship.character_a),
                joinedload(CharacterRelationship.character_b)
            )
            .where(CharacterRelationship.world_id == world_id)
        )
        relationships = list(result.scalars().all())

        # Build nodes (unique characters)
        characters_map = {}
        for rel in relationships:
            if rel.character_a_id not in characters_map:
                characters_map[rel.character_a_id] = rel.character_a
            if rel.character_b_id not in characters_map:
                characters_map[rel.character_b_id] = rel.character_b

        nodes = [
            {
                "character_id": char.id,
                "character_name": char.name,
                "importance": char.importance.value
            }
            for char in characters_map.values()
        ]

        # Build edges
        edges = [
            {
                "relationship_id": rel.id,
                "from_character_id": rel.character_a_id,
                "to_character_id": rel.character_b_id,
                "relationship_type": rel.relationship_type,
                "strength": rel.strength.value
            }
            for rel in relationships
        ]

        return {
            "nodes": nodes,
            "edges": edges,
            "total_characters": len(nodes),
            "total_relationships": len(edges)
        }

    async def update(self, relationship_id: str, relationship_data: CharacterRelationshipUpdate) -> Optional[CharacterRelationship]:
        """
        Update a character relationship.

        Args:
            relationship_id: Character relationship UUID
            relationship_data: Character relationship update data

        Returns:
            Updated character relationship instance or None if not found
        """
        relationship = await self.get_by_id(relationship_id)
        if not relationship:
            return None

        update_data = relationship_data.model_dump(exclude_unset=True)

        # Convert strength to enum if present
        if "strength" in update_data:
            update_data["strength"] = RelationshipStrength(update_data["strength"])

        for field, value in update_data.items():
            setattr(relationship, field, value)

        await self.session.flush()
        await self.session.refresh(relationship)

        logger.info("character_relationship_updated", relationship_id=relationship.id)
        return relationship

    async def delete(self, relationship_id: str) -> bool:
        """
        Delete a character relationship.

        Args:
            relationship_id: Character relationship UUID

        Returns:
            True if deleted, False if not found
        """
        relationship = await self.get_by_id(relationship_id)
        if not relationship:
            return False

        await self.session.delete(relationship)
        await self.session.flush()

        logger.info("character_relationship_deleted", relationship_id=relationship_id)
        return True
