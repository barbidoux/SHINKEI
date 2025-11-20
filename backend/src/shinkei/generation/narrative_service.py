"""Narrative generation service with database integration."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from shinkei.generation.base import GenerationContext, GenerationConfig, GeneratedBeat, ModificationContext, ModifiedBeat
from shinkei.generation.factory import ModelFactory
from shinkei.models.story import Story
from shinkei.models.story_beat import StoryBeat, GeneratedBy
from shinkei.models.beat_modification import BeatModification
from shinkei.models.world import World
from shinkei.models.world_event import WorldEvent
from shinkei.utils.diff import generate_beat_modification_diff
from shinkei.logging_config import get_logger

logger = get_logger(__name__)


class NarrativeGenerationService:
    """
    Service for orchestrating narrative generation with database integration.

    This service:
    - Builds GenerationContext from World/Story/StoryBeat models
    - Generates narrative beats using AI providers
    - Automatically creates StoryBeat records with metadata
    - Handles sequence numbering and world event linking
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize narrative generation service.

        Args:
            session: Database session for loading context and saving beats
        """
        self.session = session

    async def generate_next_beat(
        self,
        story_id: str,
        user_id: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        user_instructions: Optional[str] = None,
        target_event_id: Optional[str] = None,
        generation_config: Optional[GenerationConfig] = None,
        **provider_kwargs
    ) -> StoryBeat:
        """
        Generate the next beat for a story.

        Args:
            story_id: Story UUID
            user_id: User ID for ownership verification
            provider: LLM provider (openai/anthropic/ollama), defaults to user settings
            model: Model name override
            user_instructions: Optional user guidance (collaborative mode)
            target_event_id: Optional specific WorldEvent to write about
            generation_config: Optional generation parameters
            **provider_kwargs: Additional provider-specific args (e.g., host for Ollama)

        Returns:
            Created StoryBeat with generated content

        Raises:
            ValueError: If story not found or user doesn't own it
            RuntimeError: If generation fails
        """
        # Load story with relationships
        story = await self._load_story(story_id, user_id)

        # Load user to get their settings
        user = await self._load_user(user_id)
        user_settings = user.settings or {}

        # Build generation context from database models
        context = await self._build_context(
            story,
            user_instructions=user_instructions,
            target_event_id=target_event_id
        )

        # Apply user settings as defaults
        effective_provider = provider or user_settings.get("llm_provider", "openai")
        effective_model = model or user_settings.get("llm_model")
        base_url = user_settings.get("llm_base_url")

        # Merge base_url if not already in provider_kwargs
        if base_url and "host" not in provider_kwargs:
            provider_kwargs["host"] = base_url

        # Get model instance (respects user settings)
        model_instance = ModelFactory.create(
            provider=effective_provider,
            model_name=effective_model,
            **provider_kwargs
        )

        # Set default config if not provided
        if not generation_config:
            generation_config = GenerationConfig()

        logger.info(
            "generating_narrative_beat",
            story_id=story_id,
            story_title=story.title,
            mode=story.mode.value,
            provider=provider or "default"
        )

        try:
            # Generate beat using provider
            generated = await model_instance.generate_next_beat(context, generation_config)

            # Determine next sequence number
            last_beat = await self._get_last_beat(story_id)
            next_order = (last_beat.order_index + 1) if last_beat else 1

            # Create StoryBeat record
            beat = StoryBeat(
                story_id=story_id,
                order_index=next_order,
                content=generated.text,
                summary=generated.summary,
                local_time_label=generated.local_time_label,
                generation_reasoning=generated.reasoning,
                type=generated.beat_type,
                world_event_id=generated.world_event_id,
                generated_by=GeneratedBy.AI
            )

            self.session.add(beat)
            await self.session.flush()
            await self.session.refresh(beat)

            logger.info(
                "beat_generated_and_saved",
                story_id=story_id,
                beat_id=beat.id,
                order=next_order,
                word_count=len(generated.text.split()),
                metadata=generated.metadata
            )

            return beat

        except Exception as e:
            logger.error(
                "narrative_generation_failed",
                story_id=story_id,
                error=str(e),
                exc_info=True
            )
            raise RuntimeError(f"Failed to generate beat: {str(e)}")

    async def _load_user(self, user_id: str):
        """
        Load user by ID.

        Args:
            user_id: User UUID

        Returns:
            User instance

        Raises:
            ValueError: If user not found
        """
        from sqlalchemy import select
        from shinkei.models.user import User

        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"User not found: {user_id}")

        return user

    async def _load_story(self, story_id: str, user_id: str) -> Story:
        """
        Load story with ownership verification.

        Args:
            story_id: Story UUID
            user_id: User ID for ownership check

        Returns:
            Story instance with world relationship loaded

        Raises:
            ValueError: If story not found or user doesn't own it
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        # Load story with world
        result = await self.session.execute(
            select(Story)
            .options(selectinload(Story.world))
            .where(Story.id == story_id)
        )
        story = result.scalar_one_or_none()

        if not story:
            raise ValueError(f"Story not found: {story_id}")

        # Verify ownership via world
        if story.world.user_id != user_id:
            raise ValueError(f"User {user_id} does not own story {story_id}")

        return story

    async def _build_context(
        self,
        story: Story,
        user_instructions: Optional[str] = None,
        target_event_id: Optional[str] = None
    ) -> GenerationContext:
        """
        Build generation context from database models.

        Args:
            story: Story instance with world loaded
            user_instructions: Optional user guidance
            target_event_id: Optional target event ID

        Returns:
            GenerationContext instance
        """
        world = story.world

        # Load recent beats for continuity
        recent_beats = await self._get_recent_beats(story.id, limit=5)
        recent_beats_data = [
            {
                "content": beat.content[:500],  # Truncate for context window
                "summary": beat.summary or "",
                "local_time_label": beat.local_time_label or ""
            }
            for beat in recent_beats
        ]

        # Load target event if specified
        target_event = None
        if target_event_id:
            event = await self._get_world_event(target_event_id)
            if event:
                target_event = {
                    "id": event.id,
                    "t": event.t,
                    "label_time": event.label_time,
                    "summary": event.summary,
                    "type": event.type,
                    "location": event.location or "Unknown"
                }

        # Build context
        return GenerationContext(
            world_name=world.name,
            world_tone=world.tone or "neutral",
            world_backdrop=world.backdrop or "",
            world_laws=world.laws or {},
            story_title=story.title,
            story_synopsis=story.synopsis or "",
            story_pov_type=story.pov_type.value,
            story_mode=story.mode.value,
            recent_beats=recent_beats_data,
            target_world_event=target_event,
            user_instructions=user_instructions
        )

    async def _get_recent_beats(self, story_id: str, limit: int = 5) -> list[StoryBeat]:
        """
        Get recent beats for context.

        Args:
            story_id: Story UUID
            limit: Number of recent beats to fetch

        Returns:
            List of recent StoryBeat instances
        """
        from sqlalchemy import select

        result = await self.session.execute(
            select(StoryBeat)
            .where(StoryBeat.story_id == story_id)
            .order_by(StoryBeat.order_index.desc())
            .limit(limit)
        )
        beats = result.scalars().all()
        return list(reversed(beats))  # Oldest to newest

    async def _get_last_beat(self, story_id: str) -> Optional[StoryBeat]:
        """
        Get the last beat in the story.

        Args:
            story_id: Story UUID

        Returns:
            Last StoryBeat or None if story has no beats
        """
        from sqlalchemy import select

        result = await self.session.execute(
            select(StoryBeat)
            .where(StoryBeat.story_id == story_id)
            .order_by(StoryBeat.order_index.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _get_world_event(self, event_id: str) -> Optional[WorldEvent]:
        """
        Get world event by ID.

        Args:
            event_id: WorldEvent UUID

        Returns:
            WorldEvent instance or None
        """
        from sqlalchemy import select

        result = await self.session.execute(
            select(WorldEvent).where(WorldEvent.id == event_id)
        )
        return result.scalar_one_or_none()

    async def summarize_beat(self, beat_id: str, user_id: str, provider: Optional[str] = None) -> str:
        """
        Generate or regenerate a summary for an existing beat.

        Args:
            beat_id: StoryBeat UUID
            user_id: User ID for ownership verification
            provider: LLM provider override

        Returns:
            Generated summary text

        Raises:
            ValueError: If beat not found or user doesn't own it
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        # Load beat with story and world for ownership check
        result = await self.session.execute(
            select(StoryBeat)
            .options(
                selectinload(StoryBeat.story).selectinload(Story.world)
            )
            .where(StoryBeat.id == beat_id)
        )
        beat = result.scalar_one_or_none()

        if not beat:
            raise ValueError(f"Beat not found: {beat_id}")

        # Verify ownership
        if beat.story.world.user_id != user_id:
            raise ValueError(f"User {user_id} does not own beat {beat_id}")

        # Get model instance
        model_instance = ModelFactory.create(provider=provider)

        # Generate summary
        summary = await model_instance.summarize(beat.content)

        # Update beat
        beat.summary = summary
        await self.session.flush()

        logger.info("beat_summary_generated", beat_id=beat_id, summary_length=len(summary))

        return summary

    async def modify_beat(
        self,
        beat_id: str,
        user_id: str,
        modification_instructions: str,
        scope: Optional[list[str]] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        generation_config: Optional[GenerationConfig] = None,
        **provider_kwargs
    ) -> BeatModification:
        """
        Modify an existing beat based on user instructions.

        Args:
            beat_id: StoryBeat UUID
            user_id: User ID for ownership verification
            modification_instructions: User's instructions for modification
            scope: Fields to modify (default: all)
            provider: LLM provider override
            model: Model name override
            generation_config: Optional generation parameters
            **provider_kwargs: Additional provider-specific args

        Returns:
            BeatModification record with proposed changes

        Raises:
            ValueError: If beat not found or user doesn't own it
            RuntimeError: If modification fails
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        # Load beat with story and world
        result = await self.session.execute(
            select(StoryBeat)
            .options(
                selectinload(StoryBeat.story).selectinload(Story.world)
            )
            .where(StoryBeat.id == beat_id)
        )
        beat = result.scalar_one_or_none()

        if not beat:
            raise ValueError(f"Beat not found: {beat_id}")

        # Verify ownership
        if beat.story.world.user_id != user_id:
            raise ValueError(f"User {user_id} does not own beat {beat_id}")

        # Load user to get their settings
        user = await self._load_user(user_id)
        user_settings = user.settings or {}

        # Apply default scope if not provided
        if not scope:
            scope = ["content", "summary", "time_label", "world_event"]

        # Build modification context
        context = ModificationContext(
            original_content=beat.content,
            original_summary=beat.summary,
            original_time_label=beat.local_time_label,
            original_world_event_id=beat.world_event_id,
            modification_instructions=modification_instructions,
            world_name=beat.story.world.name,
            world_tone=beat.story.world.tone or "neutral",
            world_backdrop=beat.story.world.backdrop or "",
            world_laws=beat.story.world.laws or {},
            story_title=beat.story.title,
            story_synopsis=beat.story.synopsis or "",
            story_pov_type=beat.story.pov_type.value,
            scope=scope
        )

        # Apply user settings as defaults
        effective_provider = provider or user_settings.get("llm_provider", "openai")
        effective_model = model or user_settings.get("llm_model")
        base_url = user_settings.get("llm_base_url")

        # Merge base_url if not already in provider_kwargs
        if base_url and "host" not in provider_kwargs:
            provider_kwargs["host"] = base_url

        # Get model instance
        model_instance = ModelFactory.create(
            provider=effective_provider,
            model_name=effective_model,
            **provider_kwargs
        )

        # Set default config if not provided
        if not generation_config:
            generation_config = GenerationConfig()

        logger.info(
            "modifying_beat",
            beat_id=beat_id,
            story_title=beat.story.title,
            provider=effective_provider,
            scope=scope
        )

        try:
            # Generate modification using provider
            modified = await model_instance.modify_beat(context, generation_config)

            # Generate unified diff
            unified_diff = generate_beat_modification_diff(
                original_content=beat.content,
                modified_content=modified.modified_content,
                original_summary=beat.summary,
                modified_summary=modified.modified_summary,
                original_time_label=beat.local_time_label,
                modified_time_label=modified.modified_time_label
            )

            # Create BeatModification record
            modification = BeatModification(
                beat_id=beat_id,
                original_content=beat.content,
                modified_content=modified.modified_content,
                original_summary=beat.summary,
                modified_summary=modified.modified_summary,
                original_time_label=beat.local_time_label,
                modified_time_label=modified.modified_time_label,
                original_world_event_id=beat.world_event_id,
                modified_world_event_id=modified.modified_world_event_id,
                modification_instructions=modification_instructions,
                reasoning=modified.reasoning,
                unified_diff=unified_diff,
                applied=False  # Not applied yet
            )

            self.session.add(modification)
            await self.session.flush()
            await self.session.refresh(modification)

            logger.info(
                "beat_modification_created",
                beat_id=beat_id,
                modification_id=modification.id,
                content_changed=beat.content != modified.modified_content,
                summary_changed=beat.summary != modified.modified_summary
            )

            return modification

        except Exception as e:
            logger.error(
                "beat_modification_failed",
                beat_id=beat_id,
                error=str(e),
                exc_info=True
            )
            raise RuntimeError(f"Failed to modify beat: {str(e)}")
