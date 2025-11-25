"""Agent Persona repository for database operations."""
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from shinkei.models.agent_persona import AgentPersona
from shinkei.logging_config import get_logger

logger = get_logger(__name__)


class AgentPersonaRepository:
    """Repository for AgentPersona model database operations."""

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
        name: str,
        system_prompt: str,
        description: Optional[str] = None,
        traits: Optional[dict] = None,
        generation_defaults: Optional[dict] = None,
        is_builtin: bool = False
    ) -> AgentPersona:
        """
        Create a new agent persona.

        Args:
            world_id: World ID the persona belongs to
            name: Display name for the persona
            system_prompt: System prompt defining behavior
            description: Brief description
            traits: Personality traits dict
            generation_defaults: Default generation params dict
            is_builtin: Whether this is a built-in persona

        Returns:
            Created persona instance
        """
        persona = AgentPersona(
            world_id=world_id,
            name=name,
            system_prompt=system_prompt,
            description=description,
            traits=traits or {},
            generation_defaults=generation_defaults or {},
            is_builtin=is_builtin,
            is_active=True,
        )

        self.session.add(persona)
        await self.session.flush()
        await self.session.refresh(persona)

        logger.info("agent_persona_created", persona_id=persona.id, world_id=world_id, name=name)
        return persona

    async def get_by_id(self, persona_id: str) -> Optional[AgentPersona]:
        """
        Get persona by ID.

        Args:
            persona_id: Persona UUID

        Returns:
            Persona instance or None if not found
        """
        result = await self.session.execute(
            select(AgentPersona).where(AgentPersona.id == persona_id)
        )
        return result.scalar_one_or_none()

    async def get_by_world_and_id(self, world_id: str, persona_id: str) -> Optional[AgentPersona]:
        """
        Get persona by world ID and persona ID.

        Args:
            world_id: World UUID
            persona_id: Persona UUID

        Returns:
            Persona instance or None if not found or not in world
        """
        result = await self.session.execute(
            select(AgentPersona).where(
                AgentPersona.id == persona_id,
                AgentPersona.world_id == world_id
            )
        )
        return result.scalar_one_or_none()

    async def list_by_world(
        self,
        world_id: str,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[AgentPersona], int]:
        """
        List personas in a world with pagination.

        Args:
            world_id: World UUID
            include_inactive: Include inactive personas
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of personas, total count)
        """
        query = select(AgentPersona).where(AgentPersona.world_id == world_id)

        if not include_inactive:
            query = query.where(AgentPersona.is_active == True)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Get paginated results - builtins first, then by name
        query = query.order_by(AgentPersona.is_builtin.desc(), AgentPersona.name).offset(skip).limit(limit)
        result = await self.session.execute(query)
        personas = list(result.scalars().all())

        return personas, total

    async def list_active_by_world(self, world_id: str) -> list[AgentPersona]:
        """
        List all active personas in a world.

        Args:
            world_id: World UUID

        Returns:
            List of active personas
        """
        result = await self.session.execute(
            select(AgentPersona).where(
                AgentPersona.world_id == world_id,
                AgentPersona.is_active == True
            ).order_by(AgentPersona.is_builtin.desc(), AgentPersona.name)
        )
        return list(result.scalars().all())

    async def update(
        self,
        persona_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        traits: Optional[dict] = None,
        generation_defaults: Optional[dict] = None,
        is_active: Optional[bool] = None
    ) -> Optional[AgentPersona]:
        """
        Update a persona.

        Args:
            persona_id: Persona UUID
            name: New name (optional)
            description: New description (optional)
            system_prompt: New system prompt (optional)
            traits: New traits dict (optional)
            generation_defaults: New generation defaults (optional)
            is_active: New active status (optional)

        Returns:
            Updated persona instance or None if not found
        """
        persona = await self.get_by_id(persona_id)
        if not persona:
            return None

        # Don't allow editing builtin personas except is_active
        if persona.is_builtin:
            if is_active is not None:
                persona.is_active = is_active
                await self.session.flush()
                await self.session.refresh(persona)
            return persona

        if name is not None:
            persona.name = name
        if description is not None:
            persona.description = description
        if system_prompt is not None:
            persona.system_prompt = system_prompt
        if traits is not None:
            persona.traits = traits
        if generation_defaults is not None:
            persona.generation_defaults = generation_defaults
        if is_active is not None:
            persona.is_active = is_active

        await self.session.flush()
        await self.session.refresh(persona)

        logger.info("agent_persona_updated", persona_id=persona_id, world_id=persona.world_id)
        return persona

    async def delete(self, persona_id: str) -> bool:
        """
        Delete a persona.

        Args:
            persona_id: Persona UUID

        Returns:
            True if deleted, False if not found or is builtin
        """
        persona = await self.get_by_id(persona_id)
        if not persona:
            return False

        # Don't allow deleting builtin personas
        if persona.is_builtin:
            logger.warning("cannot_delete_builtin_persona", persona_id=persona_id)
            return False

        world_id = persona.world_id
        await self.session.delete(persona)
        await self.session.flush()

        logger.info("agent_persona_deleted", persona_id=persona_id, world_id=world_id)
        return True

    async def get_by_name(self, world_id: str, name: str) -> Optional[AgentPersona]:
        """
        Get persona by name in a world.

        Args:
            world_id: World UUID
            name: Persona name

        Returns:
            Persona instance or None if not found
        """
        result = await self.session.execute(
            select(AgentPersona).where(
                AgentPersona.world_id == world_id,
                AgentPersona.name == name
            )
        )
        return result.scalar_one_or_none()

    async def ensure_builtin_personas(self, world_id: str) -> list[AgentPersona]:
        """
        Ensure builtin personas exist for a world.
        Creates them if they don't exist.

        Args:
            world_id: World UUID

        Returns:
            List of builtin personas
        """
        from shinkei.agent.builtin_personas import BUILTIN_PERSONAS

        existing = await self.session.execute(
            select(AgentPersona).where(
                AgentPersona.world_id == world_id,
                AgentPersona.is_builtin == True
            )
        )
        existing_names = {p.name for p in existing.scalars().all()}

        created = []
        for persona_data in BUILTIN_PERSONAS:
            if persona_data["name"] not in existing_names:
                persona = await self.create(
                    world_id=world_id,
                    name=persona_data["name"],
                    description=persona_data["description"],
                    system_prompt=persona_data["system_prompt"],
                    traits=persona_data["traits"],
                    generation_defaults=persona_data["generation_defaults"],
                    is_builtin=True
                )
                created.append(persona)

        return created
