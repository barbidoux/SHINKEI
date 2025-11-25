"""World Coherence Settings repository for database operations."""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shinkei.models.world_coherence import WorldCoherenceSettings
from shinkei.logging_config import get_logger

logger = get_logger(__name__)


class WorldCoherenceRepository:
    """Repository for WorldCoherenceSettings model database operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(
        self,
        world_id: str,
        time_consistency: str = "strict",
        spatial_consistency: str = "euclidean",
        causality: str = "strict",
        character_knowledge: str = "strict",
        death_permanence: str = "permanent",
        custom_rules: Optional[List[str]] = None
    ) -> WorldCoherenceSettings:
        """
        Create coherence settings for a world.

        Args:
            world_id: World ID
            time_consistency: Time coherence level
            spatial_consistency: Spatial rules
            causality: Cause-effect rules
            character_knowledge: Character info access rules
            death_permanence: Death permanence rules
            custom_rules: List of custom coherence rules

        Returns:
            Created settings instance
        """
        settings = WorldCoherenceSettings(
            world_id=world_id,
            time_consistency=time_consistency,
            spatial_consistency=spatial_consistency,
            causality=causality,
            character_knowledge=character_knowledge,
            death_permanence=death_permanence,
            custom_rules=custom_rules,
        )

        self.session.add(settings)
        await self.session.flush()
        await self.session.refresh(settings)

        logger.info("world_coherence_settings_created", world_id=world_id)
        return settings

    async def get_by_world_id(self, world_id: str) -> Optional[WorldCoherenceSettings]:
        """
        Get coherence settings for a world.

        Args:
            world_id: World UUID

        Returns:
            Settings instance or None if not found
        """
        result = await self.session.execute(
            select(WorldCoherenceSettings).where(
                WorldCoherenceSettings.world_id == world_id
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, world_id: str) -> WorldCoherenceSettings:
        """
        Get coherence settings for a world, creating defaults if they don't exist.

        Args:
            world_id: World UUID

        Returns:
            Settings instance (existing or newly created)
        """
        settings = await self.get_by_world_id(world_id)
        if settings:
            return settings
        return await self.create(world_id)

    async def update(
        self,
        world_id: str,
        time_consistency: Optional[str] = None,
        spatial_consistency: Optional[str] = None,
        causality: Optional[str] = None,
        character_knowledge: Optional[str] = None,
        death_permanence: Optional[str] = None,
        custom_rules: Optional[List[str]] = None
    ) -> Optional[WorldCoherenceSettings]:
        """
        Update coherence settings for a world.

        Args:
            world_id: World UUID
            time_consistency: Time coherence level (optional)
            spatial_consistency: Spatial rules (optional)
            causality: Cause-effect rules (optional)
            character_knowledge: Character info access rules (optional)
            death_permanence: Death permanence rules (optional)
            custom_rules: List of custom coherence rules (optional)

        Returns:
            Updated settings instance or None if not found
        """
        settings = await self.get_by_world_id(world_id)
        if not settings:
            return None

        # Validate and update fields
        if time_consistency is not None:
            if time_consistency not in WorldCoherenceSettings.TIME_CONSISTENCY_OPTIONS:
                raise ValueError(f"Invalid time_consistency: {time_consistency}")
            settings.time_consistency = time_consistency

        if spatial_consistency is not None:
            if spatial_consistency not in WorldCoherenceSettings.SPATIAL_CONSISTENCY_OPTIONS:
                raise ValueError(f"Invalid spatial_consistency: {spatial_consistency}")
            settings.spatial_consistency = spatial_consistency

        if causality is not None:
            if causality not in WorldCoherenceSettings.CAUSALITY_OPTIONS:
                raise ValueError(f"Invalid causality: {causality}")
            settings.causality = causality

        if character_knowledge is not None:
            if character_knowledge not in WorldCoherenceSettings.CHARACTER_KNOWLEDGE_OPTIONS:
                raise ValueError(f"Invalid character_knowledge: {character_knowledge}")
            settings.character_knowledge = character_knowledge

        if death_permanence is not None:
            if death_permanence not in WorldCoherenceSettings.DEATH_PERMANENCE_OPTIONS:
                raise ValueError(f"Invalid death_permanence: {death_permanence}")
            settings.death_permanence = death_permanence

        if custom_rules is not None:
            settings.custom_rules = custom_rules

        await self.session.flush()
        await self.session.refresh(settings)

        logger.info("world_coherence_settings_updated", world_id=world_id)
        return settings

    async def delete(self, world_id: str) -> bool:
        """
        Delete coherence settings for a world.

        Args:
            world_id: World UUID

        Returns:
            True if deleted, False if not found
        """
        settings = await self.get_by_world_id(world_id)
        if not settings:
            return False

        await self.session.delete(settings)
        await self.session.flush()

        logger.info("world_coherence_settings_deleted", world_id=world_id)
        return True

    async def add_custom_rule(self, world_id: str, rule: str) -> Optional[WorldCoherenceSettings]:
        """
        Add a custom rule to coherence settings.

        Args:
            world_id: World UUID
            rule: Custom rule text

        Returns:
            Updated settings instance or None if not found
        """
        settings = await self.get_by_world_id(world_id)
        if not settings:
            return None

        current_rules = settings.custom_rules or []
        if rule not in current_rules:
            current_rules.append(rule)
            settings.custom_rules = current_rules

            await self.session.flush()
            await self.session.refresh(settings)

        return settings

    async def remove_custom_rule(self, world_id: str, rule: str) -> Optional[WorldCoherenceSettings]:
        """
        Remove a custom rule from coherence settings.

        Args:
            world_id: World UUID
            rule: Custom rule text to remove

        Returns:
            Updated settings instance or None if not found
        """
        settings = await self.get_by_world_id(world_id)
        if not settings:
            return None

        current_rules = settings.custom_rules or []
        if rule in current_rules:
            current_rules.remove(rule)
            settings.custom_rules = current_rules

            await self.session.flush()
            await self.session.refresh(settings)

        return settings
