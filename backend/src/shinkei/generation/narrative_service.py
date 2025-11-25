"""Narrative generation service with database integration."""
from typing import Optional, AsyncGenerator, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from shinkei.generation.base import GenerationContext, GenerationConfig, GeneratedBeat, ModificationContext, ModifiedBeat
from shinkei.generation.factory import ModelFactory
from shinkei.models.story import Story
from shinkei.models.story_beat import StoryBeat, GeneratedBy
from shinkei.models.beat_modification import BeatModification
from shinkei.models.world import World
from shinkei.models.world_event import WorldEvent
from shinkei.utils.diff import generate_beat_modification_diff
from shinkei.config import settings
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
        insertion_mode: str = "append",
        insert_after_beat_id: Optional[str] = None,
        insert_at_position: Optional[int] = None,
        beat_type_mode: str = "automatic",
        beat_type_manual: Optional[str] = None,
        summary_mode: str = "automatic",
        summary_manual: Optional[str] = None,
        local_time_label_mode: str = "automatic",
        local_time_label_manual: Optional[str] = None,
        world_event_id_mode: str = "automatic",
        world_event_id_manual: Optional[str] = None,
        # Narrative style parameters
        target_length_preset: Optional[str] = None,
        target_length_words: Optional[int] = None,
        pacing: Optional[str] = None,
        tension_level: Optional[str] = None,
        dialogue_density: Optional[str] = None,
        description_richness: Optional[str] = None,
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
            insertion_mode: Where to insert: "append", "insert_after", or "insert_at"
            insert_after_beat_id: Beat ID to insert after (for insert_after mode)
            insert_at_position: Position to insert at (for insert_at mode)
            **provider_kwargs: Additional provider-specific args (e.g., host for Ollama)

        Returns:
            Created StoryBeat with generated content

        Raises:
            ValueError: If story not found, user doesn't own it, or insertion params invalid
            RuntimeError: If generation fails
        """
        # Load story with relationships
        story = await self._load_story(story_id, user_id)

        # Load user to get their settings
        user = await self._load_user(user_id)
        user_settings = user.settings or {}

        # Calculate target_length from preset or custom value
        target_length = target_length_words
        if not target_length and target_length_preset:
            length_presets = {"short": 500, "medium": 1000, "long": 2000}
            target_length = length_presets.get(target_length_preset)

        # Build generation context from database models
        context = await self._build_context(
            story,
            user_instructions=user_instructions,
            target_event_id=target_event_id,
            target_length=target_length,
            pacing=pacing,
            tension_level=tension_level,
            dialogue_density=dialogue_density,
            description_richness=description_richness
        )

        # Apply user settings as defaults
        effective_provider = provider or user_settings.get("llm_provider") or settings.default_llm_provider
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

            # Apply metadata overrides based on control modes
            final_beat_type = self._apply_metadata_override(
                mode=beat_type_mode,
                ai_value=generated.beat_type,
                manual_value=beat_type_manual
            )

            final_summary = self._apply_metadata_override(
                mode=summary_mode,
                ai_value=generated.summary,
                manual_value=summary_manual
            )

            final_local_time_label = self._apply_metadata_override(
                mode=local_time_label_mode,
                ai_value=generated.local_time_label,
                manual_value=local_time_label_manual
            )

            final_world_event_id = self._apply_metadata_override(
                mode=world_event_id_mode,
                ai_value=generated.world_event_id,
                manual_value=world_event_id_manual
            )

            # Determine insertion position based on mode
            from shinkei.repositories.story_beat import StoryBeatRepository
            from shinkei.schemas.story_beat import StoryBeatCreate

            repo = StoryBeatRepository(self.session)

            # Calculate insertion position
            if insertion_mode == "insert_after":
                if not insert_after_beat_id:
                    raise ValueError("insert_after_beat_id required when insertion_mode='insert_after'")

                after_beat_order = await repo.get_beat_order_index(insert_after_beat_id)
                if after_beat_order is None:
                    raise ValueError(f"Beat {insert_after_beat_id} not found")

                position = after_beat_order + 1

            elif insertion_mode == "insert_at":
                if insert_at_position is None or insert_at_position < 1:
                    raise ValueError("insert_at_position (>=1) required when insertion_mode='insert_at'")

                position = insert_at_position

            else:  # append mode (default)
                last_order = await repo.get_last_order_index(story_id)
                position = last_order + 1

            # Create beat data using final (potentially overridden) metadata values
            beat_data = StoryBeatCreate(
                order_index=position,
                content=generated.text,
                type=final_beat_type if final_beat_type else "scene",
                world_event_id=final_world_event_id,
                generated_by="ai",
                summary=final_summary,
                local_time_label=final_local_time_label,
                generation_reasoning=generated.reasoning
            )

            # Insert beat at calculated position
            if insertion_mode in ("insert_after", "insert_at"):
                beat = await repo.insert_at_position(story_id, position, beat_data)
            else:
                # Append mode - use standard create
                beat = await repo.create(story_id, beat_data)

            logger.info(
                "beat_generated_and_saved",
                story_id=story_id,
                beat_id=beat.id,
                order=position,
                insertion_mode=insertion_mode,
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

    async def generate_next_beat_stream(
        self,
        story_id: str,
        user_id: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        user_instructions: Optional[str] = None,
        target_event_id: Optional[str] = None,
        generation_config: Optional[GenerationConfig] = None,
        # Narrative style parameters
        target_length_preset: Optional[str] = None,
        target_length_words: Optional[int] = None,
        pacing: Optional[str] = None,
        tension_level: Optional[str] = None,
        dialogue_density: Optional[str] = None,
        description_richness: Optional[str] = None,
        **provider_kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream the generation of the next beat for a story.

        Yields SSE events:
        - {"type": "token", "content": "..."} - Progressive content tokens
        - {"type": "metadata", "summary": "...", "time_label": "..."} - Generated metadata
        - {"type": "complete", "beat": {...}} - Final beat with full data

        Args:
            story_id: Story UUID
            user_id: User ID for ownership verification
            provider: LLM provider (openai/anthropic/ollama)
            model: Model name override
            user_instructions: Optional user guidance
            target_event_id: Optional specific WorldEvent to write about
            generation_config: Optional generation parameters
            **provider_kwargs: Additional provider-specific args

        Yields:
            Dict events for SSE streaming

        Raises:
            ValueError: If story not found or user doesn't own it
            RuntimeError: If generation fails
        """
        # Load story with relationships
        story = await self._load_story(story_id, user_id)

        # Load user to get their settings
        user = await self._load_user(user_id)
        user_settings = user.settings or {}

        # Calculate target_length from preset or custom value
        target_length = target_length_words
        if not target_length and target_length_preset:
            length_presets = {"short": 500, "medium": 1000, "long": 2000}
            target_length = length_presets.get(target_length_preset)

        # Build generation context with narrative style parameters
        context = await self._build_context(
            story,
            user_instructions=user_instructions,
            target_event_id=target_event_id,
            target_length=target_length,
            pacing=pacing,
            tension_level=tension_level,
            dialogue_density=dialogue_density,
            description_richness=description_richness
        )

        # Apply user settings as defaults
        effective_provider = provider or user_settings.get("llm_provider") or settings.default_llm_provider
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
            "streaming_narrative_beat",
            story_id=story_id,
            story_title=story.title,
            mode=story.mode.value,
            provider=effective_provider
        )

        # Accumulate streamed content
        full_content = ""

        try:
            # Stream content generation
            async for chunk in model_instance.generate_next_beat_stream(context, generation_config):
                full_content += chunk
                yield {"type": "token", "content": chunk}

            # Generate summary and metadata from full content
            generated = await model_instance.generate_beat_metadata(
                content=full_content,
                context=context
            )

            # Yield metadata event
            yield {
                "type": "metadata",
                "summary": generated.summary,
                "time_label": generated.local_time_label,
                "reasoning": generated.reasoning
            }

            # Determine next sequence number
            last_beat = await self._get_last_beat(story_id)
            next_order = (last_beat.order_index + 1) if last_beat else 1

            # Create StoryBeat record
            beat = StoryBeat(
                story_id=story_id,
                order_index=next_order,
                content=full_content,
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
                "beat_generated_streaming_complete",
                story_id=story_id,
                beat_id=beat.id,
                order=next_order,
                word_count=len(full_content.split())
            )

            # Yield completion event with full beat data
            yield {
                "type": "complete",
                "beat": {
                    "id": beat.id,
                    "story_id": beat.story_id,
                    "order_index": beat.order_index,
                    "content": beat.content,
                    "summary": beat.summary,
                    "local_time_label": beat.local_time_label,
                    "type": beat.type.value,
                    "world_event_id": beat.world_event_id,
                    "generated_by": beat.generated_by.value,
                    "created_at": beat.created_at.isoformat(),
                    "updated_at": beat.updated_at.isoformat()
                }
            }

        except Exception as e:
            logger.error(
                "streaming_generation_failed",
                story_id=story_id,
                error=str(e),
                exc_info=True
            )
            raise RuntimeError(f"Failed to stream beat generation: {str(e)}")

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

    def _apply_metadata_override(
        self,
        mode: str,
        ai_value: Optional[Any],
        manual_value: Optional[Any]
    ) -> Optional[Any]:
        """
        Apply metadata override based on control mode.

        Args:
            mode: Control mode - "blank", "manual", or "automatic"
            ai_value: AI-generated value
            manual_value: User-provided manual value

        Returns:
            Final value based on mode:
            - "blank": None (leave empty)
            - "manual": manual_value (use user-provided value)
            - "automatic": ai_value (use AI-generated value)
        """
        if mode == "blank":
            return None
        elif mode == "manual":
            return manual_value
        else:  # "automatic" (default)
            return ai_value

    async def _build_context(
        self,
        story: Story,
        user_instructions: Optional[str] = None,
        target_event_id: Optional[str] = None,
        target_length: Optional[int] = None,
        pacing: Optional[str] = None,
        tension_level: Optional[str] = None,
        dialogue_density: Optional[str] = None,
        description_richness: Optional[str] = None
    ) -> GenerationContext:
        """
        Build generation context from database models.

        Args:
            story: Story instance with world loaded
            user_instructions: Optional user guidance
            target_event_id: Optional target event ID
            target_length: Target word count
            pacing: Narrative pacing (slow/medium/fast)
            tension_level: Narrative tension (low/medium/high)
            dialogue_density: Dialogue amount (minimal/moderate/heavy)
            description_richness: Description detail (sparse/balanced/detailed)

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

        # Build context with narrative style parameters
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
            user_instructions=user_instructions,
            target_length=target_length,
            pacing=pacing,
            tension_level=tension_level,
            dialogue_density=dialogue_density,
            description_richness=description_richness
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
        effective_provider = provider or user_settings.get("llm_provider") or settings.default_llm_provider
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

    async def check_beat_coherence(
        self,
        story_id: str,
        beat_id: str,
        user_id: str,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check a beat for narrative coherence against world rules, story context, and previous beats.

        Args:
            story_id: Story UUID
            beat_id: Beat UUID to check
            user_id: User ID for ownership verification
            provider: LLM provider override
            model: Model name override

        Returns:
            Dictionary with:
            - coherent: bool - overall coherence status
            - issues: List[dict] - detected issues with severity (low/medium/high)
            - suggestions: List[str] - improvement suggestions

        Raises:
            ValueError: If beat/story not found or user doesn't own it
            RuntimeError: If coherence check fails
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        # Load beat with story and world
        result = await self.session.execute(
            select(StoryBeat)
            .options(
                selectinload(StoryBeat.story).selectinload(Story.world)
            )
            .where(StoryBeat.id == beat_id, StoryBeat.story_id == story_id)
        )
        beat = result.scalar_one_or_none()

        if not beat:
            raise ValueError(f"Beat not found: {beat_id} in story {story_id}")

        # Verify ownership
        if beat.story.world.user_id != user_id:
            raise ValueError(f"User {user_id} does not own beat {beat_id}")

        # Load user settings
        user = await self._load_user(user_id)
        user_settings = user.settings or {}

        # Apply user settings as defaults
        effective_provider = provider or user_settings.get("llm_provider") or settings.default_llm_provider
        effective_model = model or user_settings.get("llm_model")

        logger.info(
            "coherence_check_provider_resolution",
            requested_provider=provider,
            user_default_provider=user_settings.get("llm_provider"),
            effective_provider=effective_provider,
            requested_model=model,
            user_default_model=user_settings.get("llm_model"),
            effective_model=effective_model
        )

        # Get recent beats for context (excluding the current beat)
        recent_beats = await self._get_recent_beats_before(story_id, beat.order_index, limit=5)

        # Build context for coherence check
        world = beat.story.world
        story = beat.story

        # Create prompt for coherence checking
        coherence_prompt = self._build_coherence_check_prompt(
            beat=beat,
            story=story,
            world=world,
            recent_beats=recent_beats
        )

        # Get model instance
        from shinkei.generation.factory import ModelFactory
        from shinkei.generation.base import GenerationRequest

        # Prepare provider kwargs (for Ollama host)
        provider_kwargs = {"model_name": effective_model}
        if effective_provider == "ollama" and user_settings.get("llm_base_url"):
            provider_kwargs["host"] = user_settings.get("llm_base_url")
            logger.info(
                "using_ollama_host_from_settings",
                host=user_settings.get("llm_base_url")
            )

        model_instance = ModelFactory.create(
            provider=effective_provider,
            **provider_kwargs
        )

        logger.info(
            "checking_beat_coherence",
            beat_id=beat_id,
            story_id=story_id,
            provider=effective_provider
        )

        try:
            # Generate coherence analysis
            request = GenerationRequest(
                prompt=coherence_prompt,
                system_prompt="You are a narrative coherence analyst. Analyze the beat for inconsistencies, contradictions, and coherence issues.",
                temperature=0.3,  # Lower temperature for consistent analysis
                max_tokens=1000
            )

            response = await model_instance.generate(request)
            analysis_text = response.content

            # Parse the AI response to extract issues and suggestions
            issues = self._parse_coherence_issues(analysis_text)
            suggestions = self._parse_coherence_suggestions(analysis_text)

            # Determine overall coherence (no medium or high severity issues)
            # Beat is coherent only if there are no issues, or all issues are low severity
            coherent = not any(issue.get("severity") in ["medium", "high"] for issue in issues)

            logger.info(
                "beat_coherence_checked",
                beat_id=beat_id,
                coherent=coherent,
                issue_count=len(issues),
                high_severity_count=sum(1 for i in issues if i.get("severity") == "high")
            )

            return {
                "coherent": coherent,
                "issues": issues,
                "suggestions": suggestions,
                "analysis": analysis_text
            }

        except Exception as e:
            logger.error(
                "coherence_check_failed",
                beat_id=beat_id,
                error=str(e),
                exc_info=True
            )
            raise RuntimeError(f"Failed to check beat coherence: {str(e)}")

    async def _get_recent_beats_before(
        self,
        story_id: str,
        before_order: int,
        limit: int = 5
    ) -> list[StoryBeat]:
        """
        Get recent beats before a specific order index.

        Args:
            story_id: Story UUID
            before_order: Order index to fetch before
            limit: Number of recent beats to fetch

        Returns:
            List of recent StoryBeat instances
        """
        from sqlalchemy import select

        result = await self.session.execute(
            select(StoryBeat)
            .where(
                StoryBeat.story_id == story_id,
                StoryBeat.order_index < before_order
            )
            .order_by(StoryBeat.order_index.desc())
            .limit(limit)
        )
        beats = result.scalars().all()
        return list(reversed(beats))  # Oldest to newest

    def _build_coherence_check_prompt(
        self,
        beat: StoryBeat,
        story: Story,
        world: "World",
        recent_beats: list[StoryBeat]
    ) -> str:
        """Build prompt for coherence checking."""
        prompt = f"""# Narrative Coherence Analysis

## World Context
- **World Name**: {world.name}
- **Tone**: {world.tone or 'neutral'}
- **Backdrop**: {world.backdrop or 'Not specified'}
- **Laws**: {world.laws or {}}

## Story Context
- **Title**: {story.title}
- **Synopsis**: {story.synopsis or 'Not specified'}
- **POV**: {story.pov_type.value}
- **Mode**: {story.mode.value}

## Recent Beats (for context)
"""
        for i, prev_beat in enumerate(recent_beats, 1):
            prompt += f"\n### Beat {i} (Order {prev_beat.order_index})\n"
            if prev_beat.summary:
                prompt += f"Summary: {prev_beat.summary}\n"
            prompt += f"Content: {prev_beat.content[:300]}{'...' if len(prev_beat.content) > 300 else ''}\n"

        prompt += f"""

## Beat to Analyze (Order {beat.order_index})
**Summary**: {beat.summary or 'No summary'}
**Content**:
{beat.content}

---

## Your Task

Analyze the beat above for narrative coherence. Check for:

1. **World Law Violations**: Does the beat contradict established world laws or physics?
2. **Tone Inconsistency**: Does the beat match the world's tone?
3. **Continuity Errors**: Does it contradict previous beats?
4. **POV Violations**: Does it maintain the correct point of view?
5. **Character Consistency**: Do characters act consistently with their prior behavior?

For each issue found, provide:
- **Type**: (world_law_violation | tone_mismatch | continuity_error | pov_violation | character_inconsistency)
- **Severity**: (low | medium | high)
- **Description**: Brief explanation of the issue

Format your response as:

### ISSUES
[List issues in the format: "- [SEVERITY] TYPE: description"]

### SUGGESTIONS
[List 2-3 concrete suggestions for improvement]

### OVERALL ASSESSMENT
[Brief overall coherence assessment]

If no issues are found, respond with "COHERENT: No issues detected."
"""
        return prompt

    def _parse_coherence_issues(self, analysis_text: str) -> list[Dict[str, str]]:
        """
        Parse coherence issues from AI analysis text.

        Args:
            analysis_text: AI-generated coherence analysis

        Returns:
            List of issue dictionaries with type, severity, description
        """
        issues = []

        # Look for the ISSUES section
        if "### ISSUES" in analysis_text:
            issues_section = analysis_text.split("### ISSUES")[1].split("###")[0].strip()

            # Parse each issue line
            for line in issues_section.split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("*"):
                    # Parse format: "- [SEVERITY] TYPE: description"
                    line = line.lstrip("-*").strip()

                    # Extract severity
                    severity = "medium"  # default
                    if "[HIGH]" in line or "[high]" in line:
                        severity = "high"
                        line = line.replace("[HIGH]", "").replace("[high]", "").strip()
                    elif "[MEDIUM]" in line or "[medium]" in line:
                        severity = "medium"
                        line = line.replace("[MEDIUM]", "").replace("[medium]", "").strip()
                    elif "[LOW]" in line or "[low]" in line:
                        severity = "low"
                        line = line.replace("[LOW]", "").replace("[low]", "").strip()

                    # Extract type and description
                    if ":" in line:
                        issue_type, description = line.split(":", 1)
                        issues.append({
                            "type": issue_type.strip().lower().replace(" ", "_"),
                            "severity": severity,
                            "description": description.strip()
                        })

        return issues

    def _parse_coherence_suggestions(self, analysis_text: str) -> list[str]:
        """
        Parse coherence suggestions from AI analysis text.

        Args:
            analysis_text: AI-generated coherence analysis

        Returns:
            List of suggestion strings
        """
        suggestions = []

        # Look for the SUGGESTIONS section
        if "### SUGGESTIONS" in analysis_text:
            suggestions_section = analysis_text.split("### SUGGESTIONS")[1].split("###")[0].strip()

            # Parse each suggestion line
            for line in suggestions_section.split("\n"):
                line = line.strip()
                if line and (line.startswith("-") or line.startswith("*") or line.startswith("1.")):
                    # Remove list markers
                    line = line.lstrip("-*123456789.").strip()
                    if line:
                        suggestions.append(line)

        return suggestions

    async def suggest_world_events(
        self,
        beat_content: str,
        story_id: str,
        user_id: str,
        max_suggestions: int = 5,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **provider_kwargs
    ) -> list[Dict[str, Any]]:
        """
        Suggest relevant world events for a beat based on its content.

        Uses AI to analyze the beat content and recommend which existing world events
        are most relevant to link to this beat.

        Args:
            beat_content: The narrative content to analyze
            story_id: Story UUID (to get world context)
            user_id: User ID for ownership verification
            max_suggestions: Maximum number of event suggestions to return (default: 5)
            provider: LLM provider override
            model: Model name override
            **provider_kwargs: Additional provider-specific args

        Returns:
            List of suggested events with:
            - event_id: WorldEvent UUID
            - label_time: Human-readable time label
            - summary: Event summary
            - type: Event type
            - relevance_score: 0.0-1.0 relevance score
            - reasoning: Why this event is relevant

        Raises:
            ValueError: If story not found or user doesn't own it
            RuntimeError: If suggestion generation fails
        """
        # Load story to get world_id and verify ownership
        story = await self._load_story(story_id, user_id)
        world_id = story.world_id

        # Load all world events for this world
        from shinkei.repositories.world_event import WorldEventRepository
        event_repo = WorldEventRepository(self.session)

        events, _ = await event_repo.list_by_world(world_id, limit=1000)

        if not events:
            logger.info(
                "no_world_events_for_suggestions",
                story_id=story_id,
                world_id=world_id
            )
            return []

        # Load user settings
        user = await self._load_user(user_id)
        user_settings = user.settings or {}

        # Apply user settings as defaults
        effective_provider = provider or user_settings.get("llm_provider") or settings.default_llm_provider
        effective_model = model or user_settings.get("llm_model")
        base_url = user_settings.get("llm_base_url")

        # Merge base_url if not already in provider_kwargs
        if base_url and "host" not in provider_kwargs:
            provider_kwargs["host"] = base_url

        # Build prompt for event suggestion
        suggestion_prompt = self._build_event_suggestion_prompt(
            beat_content=beat_content,
            events=events,
            max_suggestions=max_suggestions
        )

        # Get model instance
        from shinkei.generation.factory import ModelFactory
        from shinkei.generation.base import GenerationRequest

        model_instance = ModelFactory.create(
            provider=effective_provider,
            model_name=effective_model,
            **provider_kwargs
        )

        logger.info(
            "suggesting_world_events",
            story_id=story_id,
            world_id=world_id,
            event_count=len(events),
            provider=effective_provider
        )

        try:
            # Generate event suggestions
            request = GenerationRequest(
                prompt=suggestion_prompt,
                system_prompt="You are a narrative event matching assistant. Analyze beat content and suggest the most relevant world events to link to.",
                temperature=0.3,  # Lower temperature for consistent analysis
                max_tokens=1500
            )

            response = await model_instance.generate(request)
            analysis_text = response.content

            # Parse the AI response to extract suggestions
            suggestions = self._parse_event_suggestions(analysis_text, events)

            logger.info(
                "world_events_suggested",
                story_id=story_id,
                suggestion_count=len(suggestions)
            )

            return suggestions[:max_suggestions]

        except Exception as e:
            logger.error(
                "event_suggestion_failed",
                story_id=story_id,
                error=str(e),
                exc_info=True
            )
            raise RuntimeError(f"Failed to suggest world events: {str(e)}")

    def _build_event_suggestion_prompt(
        self,
        beat_content: str,
        events: list[WorldEvent],
        max_suggestions: int
    ) -> str:
        """
        Build prompt for world event suggestion.

        Args:
            beat_content: Beat narrative content
            events: List of available world events
            max_suggestions: Maximum suggestions to request

        Returns:
            Formatted prompt string
        """
        prompt = f"""# World Event Suggestion Task

## Beat Content to Analyze
{beat_content}

## Available World Events
"""
        for i, event in enumerate(events, 1):
            prompt += f"""
{i}. **Event ID**: {event.id}
   - **Time**: {event.label_time} (t={event.t})
   - **Type**: {event.type}
   - **Summary**: {event.summary}
   - **Tags**: {', '.join(event.tags) if event.tags else 'None'}
"""

        prompt += f"""

---

## Your Task

Analyze the beat content above and identify which world events (if any) are most relevant to this narrative beat.

For each relevant event, provide:
- **Event ID**: The exact event ID from the list above
- **Relevance Score**: A score from 0.0 (not relevant) to 1.0 (highly relevant)
- **Reasoning**: 1-2 sentences explaining why this event is relevant

Return up to {max_suggestions} suggestions, ordered by relevance (highest first).

Format your response as:

### SUGGESTIONS
1. EVENT_ID: [exact event ID]
   SCORE: [0.0-1.0]
   REASONING: [explanation]

2. EVENT_ID: [exact event ID]
   SCORE: [0.0-1.0]
   REASONING: [explanation]

If no events are relevant, respond with "NO_RELEVANT_EVENTS"
"""
        return prompt

    def _parse_event_suggestions(
        self,
        analysis_text: str,
        events: list[WorldEvent]
    ) -> list[Dict[str, Any]]:
        """
        Parse event suggestions from AI analysis text.

        Args:
            analysis_text: AI-generated event suggestion analysis
            events: List of available world events (for lookup)

        Returns:
            List of suggestion dictionaries
        """
        suggestions = []

        # Return empty if no relevant events
        if "NO_RELEVANT_EVENTS" in analysis_text:
            return suggestions

        # Create event lookup by ID
        event_map = {event.id: event for event in events}

        # Look for the SUGGESTIONS section
        if "### SUGGESTIONS" in analysis_text:
            suggestions_section = analysis_text.split("### SUGGESTIONS")[1].strip()

            # Parse each numbered suggestion
            current_suggestion = {}

            for line in suggestions_section.split("\n"):
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                # Check for EVENT_ID line
                if "EVENT_ID:" in line:
                    # Save previous suggestion if complete
                    if current_suggestion.get("event_id") and current_suggestion.get("relevance_score"):
                        event = event_map.get(current_suggestion["event_id"])
                        if event:
                            suggestions.append({
                                "event_id": event.id,
                                "label_time": event.label_time,
                                "summary": event.summary,
                                "type": event.type,
                                "relevance_score": current_suggestion["relevance_score"],
                                "reasoning": current_suggestion.get("reasoning", "")
                            })

                    # Start new suggestion
                    event_id = line.split("EVENT_ID:")[1].strip()
                    current_suggestion = {"event_id": event_id}

                # Check for SCORE line
                elif "SCORE:" in line:
                    try:
                        score_str = line.split("SCORE:")[1].strip()
                        score = float(score_str)
                        current_suggestion["relevance_score"] = max(0.0, min(1.0, score))
                    except ValueError:
                        current_suggestion["relevance_score"] = 0.5  # Default

                # Check for REASONING line
                elif "REASONING:" in line:
                    reasoning = line.split("REASONING:")[1].strip()
                    current_suggestion["reasoning"] = reasoning

            # Add final suggestion if complete
            if current_suggestion.get("event_id") and current_suggestion.get("relevance_score"):
                event = event_map.get(current_suggestion["event_id"])
                if event:
                    suggestions.append({
                        "event_id": event.id,
                        "label_time": event.label_time,
                        "summary": event.summary,
                        "type": event.type,
                        "relevance_score": current_suggestion["relevance_score"],
                        "reasoning": current_suggestion.get("reasoning", "")
                    })

        # Sort by relevance score (highest first)
        suggestions.sort(key=lambda x: x["relevance_score"], reverse=True)

        return suggestions

    async def check_story_coherence(
        self,
        story_id: str,
        user_id: str,
        start_beat_index: Optional[int] = None,
        end_beat_index: Optional[int] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **provider_kwargs
    ) -> Dict[str, Any]:
        """
        Check story-level narrative coherence across multiple beats.

        Analyzes timeline consistency, character arcs, plot threads, and world event
        integration across the entire story or a specified range of beats.

        Args:
            story_id: Story UUID
            user_id: User ID for ownership verification
            start_beat_index: Optional starting beat order_index (inclusive)
            end_beat_index: Optional ending beat order_index (inclusive)
            provider: LLM provider override
            model: Model name override
            **provider_kwargs: Additional provider-specific args

        Returns:
            Dictionary with:
            - coherent: bool - overall story coherence
            - issues: List[dict] - detected issues (type, severity, description, beat_range)
            - suggestions: List[str] - improvement suggestions
            - character_arcs: List[dict] - character consistency analysis
            - plot_threads: List[dict] - plot thread tracking
            - timeline_issues: List[dict] - temporal inconsistencies
            - analysis: str - full AI analysis text

        Raises:
            ValueError: If story not found or user doesn't own it
            RuntimeError: If coherence check fails
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

        # Verify ownership
        if story.world.user_id != user_id:
            raise ValueError(f"User {user_id} does not own story {story_id}")

        # Load beats in the specified range
        from shinkei.repositories.story_beat import StoryBeatRepository
        beat_repo = StoryBeatRepository(self.session)

        # Build query for beats
        query = select(StoryBeat).where(StoryBeat.story_id == story_id)

        if start_beat_index is not None:
            query = query.where(StoryBeat.order_index >= start_beat_index)
        if end_beat_index is not None:
            query = query.where(StoryBeat.order_index <= end_beat_index)

        query = query.order_by(StoryBeat.order_index.asc())

        result = await self.session.execute(query)
        beats = list(result.scalars().all())

        if not beats:
            logger.warning(
                "no_beats_for_coherence_check",
                story_id=story_id,
                start_index=start_beat_index,
                end_index=end_beat_index
            )
            return {
                "coherent": True,
                "issues": [],
                "suggestions": [],
                "character_arcs": [],
                "plot_threads": [],
                "timeline_issues": [],
                "analysis": "No beats found in the specified range."
            }

        # Load user settings
        user = await self._load_user(user_id)
        user_settings = user.settings or {}

        # Apply user settings as defaults
        effective_provider = provider or user_settings.get("llm_provider") or settings.default_llm_provider
        effective_model = model or user_settings.get("llm_model")
        base_url = user_settings.get("llm_base_url")

        # Merge base_url if not already in provider_kwargs
        if base_url and "host" not in provider_kwargs:
            provider_kwargs["host"] = base_url

        # Build coherence check prompt
        coherence_prompt = self._build_story_coherence_prompt(
            story=story,
            world=story.world,
            beats=beats
        )

        # Get model instance
        from shinkei.generation.factory import ModelFactory
        from shinkei.generation.base import GenerationRequest

        model_instance = ModelFactory.create(
            provider=effective_provider,
            model_name=effective_model,
            **provider_kwargs
        )

        logger.info(
            "checking_story_coherence",
            story_id=story_id,
            beat_count=len(beats),
            start_index=start_beat_index or beats[0].order_index,
            end_index=end_beat_index or beats[-1].order_index,
            provider=effective_provider
        )

        try:
            # Generate coherence analysis
            request = GenerationRequest(
                prompt=coherence_prompt,
                system_prompt="You are a narrative coherence analyst specializing in story-level analysis. Identify inconsistencies, track character arcs, and analyze plot structure.",
                temperature=0.3,  # Lower temperature for consistent analysis
                max_tokens=3000  # Larger for comprehensive story analysis
            )

            response = await model_instance.generate(request)
            analysis_text = response.content

            # Parse the AI response
            issues = self._parse_story_coherence_issues(analysis_text)
            suggestions = self._parse_story_coherence_suggestions(analysis_text)
            character_arcs = self._parse_character_arcs(analysis_text)
            plot_threads = self._parse_plot_threads(analysis_text)
            timeline_issues = self._parse_timeline_issues(analysis_text)

            # Determine overall coherence (no medium or high severity issues)
            # Story is coherent only if there are no issues, or all issues are low severity
            coherent = not any(issue.get("severity") in ["medium", "high"] for issue in issues)

            logger.info(
                "story_coherence_checked",
                story_id=story_id,
                coherent=coherent,
                issue_count=len(issues),
                character_count=len(character_arcs),
                plot_thread_count=len(plot_threads)
            )

            return {
                "coherent": coherent,
                "issues": issues,
                "suggestions": suggestions,
                "character_arcs": character_arcs,
                "plot_threads": plot_threads,
                "timeline_issues": timeline_issues,
                "analysis": analysis_text
            }

        except Exception as e:
            logger.error(
                "story_coherence_check_failed",
                story_id=story_id,
                error=str(e),
                exc_info=True
            )
            raise RuntimeError(f"Failed to check story coherence: {str(e)}")

    def _build_story_coherence_prompt(
        self,
        story: Story,
        world: "World",
        beats: list[StoryBeat]
    ) -> str:
        """
        Build prompt for story-level coherence checking.

        Args:
            story: Story instance
            world: World instance
            beats: List of story beats to analyze

        Returns:
            Formatted prompt string
        """
        prompt = f"""# Story-Level Coherence Analysis

## World Context
- **World Name**: {world.name}
- **Tone**: {world.tone or 'neutral'}
- **Backdrop**: {world.backdrop or 'Not specified'}
- **Laws**: {world.laws or {}}

## Story Context
- **Title**: {story.title}
- **Synopsis**: {story.synopsis or 'Not specified'}
- **POV**: {story.pov_type.value}
- **Mode**: {story.mode.value}

## Story Beats to Analyze ({len(beats)} beats)

"""
        for beat in beats:
            prompt += f"""
### Beat {beat.order_index}
**Type**: {beat.type.value if beat.type else 'unknown'}
**Time Label**: {beat.local_time_label or 'Not specified'}
**Summary**: {beat.summary or 'No summary'}

**Content**:
{beat.content[:1000]}{'...' if len(beat.content) > 1000 else ''}

---
"""

        prompt += f"""

## Your Task

Perform a comprehensive story-level coherence analysis. Examine:

### 1. Timeline Consistency
- Are events sequenced logically?
- Do time references (local_time_label) make sense?
- Are there temporal contradictions?

### 2. Character Arcs
- Identify main characters mentioned
- Track their development and consistency
- Note any character behavior inconsistencies

### 3. Plot Threads
- Identify active plot threads
- Track which threads are resolved vs. unresolved
- Note any dropped or contradictory plot elements

### 4. World Law Adherence
- Does the narrative respect established world laws?
- Are there violations of physics, metaphysics, or social rules?

### 5. POV Consistency
- Is the {story.pov_type.value} POV maintained throughout?
- Are there any POV violations?

### 6. Overall Narrative Flow
- Does the story progress coherently?
- Are transitions between beats smooth?
- Is pacing consistent?

Format your response as follows:

### ISSUES
[List issues in this EXACT format: "- [SEVERITY] TYPE (Beat X-Y): description"]
- SEVERITY must be: LOW, MEDIUM, or HIGH
- TYPE must be one of: timeline, character, plot, world_law, pov, pacing
- Beat range MUST be in parentheses immediately after TYPE, e.g., "(Beat 2)", "(Beat 2-3)", "(Beat 1-4)"
- If issue affects a single beat, use "(Beat X)"
- If issue spans multiple beats, use "(Beat X-Y)"

Example: "- [MEDIUM] timeline (Beat 2-3): Time labels are inconsistent between these beats"
Example: "- [HIGH] character (Beat 4): Character motivation contradicts earlier behavior"

### CHARACTER_ARCS
[List characters with format: "- CHARACTER_NAME: current arc status and consistency notes"]

### PLOT_THREADS
[List plot threads with format: "- THREAD_NAME (status): description"]
Use status: active, resolved, dropped, contradictory

### TIMELINE_ISSUES
[List specific timeline problems with format: "- Beat X to Y: description of temporal issue"]

### SUGGESTIONS
[List 3-5 specific suggestions for improving story coherence]

### OVERALL_ASSESSMENT
[Brief 2-3 sentence overall assessment]

If the story is fully coherent with no issues, respond with "FULLY_COHERENT: No issues detected."
"""
        return prompt

    def _parse_story_coherence_issues(self, analysis_text: str) -> list[Dict[str, Any]]:
        """Parse story coherence issues from AI analysis."""
        import re

        issues = []

        if "FULLY_COHERENT" in analysis_text:
            return issues

        if "### ISSUES" in analysis_text:
            issues_section = analysis_text.split("### ISSUES")[1].split("###")[0].strip()

            for line in issues_section.split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("*"):
                    # Remove markdown bold markers if present
                    line = line.replace("**", "")
                    line = line.lstrip("-*").strip()

                    # Skip empty lines or section headers
                    if not line or line.startswith("#"):
                        continue

                    # Extract severity
                    severity = "medium"
                    if "[HIGH]" in line or "[high]" in line:
                        severity = "high"
                        line = line.replace("[HIGH]", "").replace("[high]", "").strip()
                    elif "[MEDIUM]" in line or "[medium]" in line:
                        severity = "medium"
                        line = line.replace("[MEDIUM]", "").replace("[medium]", "").strip()
                    elif "[LOW]" in line or "[low]" in line:
                        severity = "low"
                        line = line.replace("[LOW]", "").replace("[low]", "").strip()

                    # Extract beat range using regex for more robust parsing
                    # Looks for patterns like (Beat 2), (Beat 2-3), (Beat 1-4)
                    beat_range = None
                    beat_match = re.search(r'\(Beat\s+(\d+(?:-\d+)?)\)', line, re.IGNORECASE)
                    if beat_match:
                        beat_range = beat_match.group(1)
                        # Clean up the line by removing the beat range in parentheses
                        line = re.sub(r'\(Beat\s+\d+(?:-\d+)?\)', '', line, flags=re.IGNORECASE).strip()
                    else:
                        # Fallback: try to find beat numbers anywhere in the line before the colon
                        # This catches cases like "Beat 2 time label" or "Beats 2-3"
                        if ":" in line:
                            prefix = line.split(":")[0]
                            beat_fallback = re.search(r'Beat[s]?\s+(\d+(?:-\d+)?)', prefix, re.IGNORECASE)
                            if beat_fallback:
                                beat_range = beat_fallback.group(1)

                    # Extract type and description
                    if ":" in line:
                        type_part, description = line.split(":", 1)
                        issue_type = type_part.strip().lower().replace(" ", "_")

                        # Clean up any remaining beat references from type
                        issue_type = re.sub(r'beat[s]?\s+\d+(?:-\d+)?', '', issue_type, flags=re.IGNORECASE).strip()
                        issue_type = re.sub(r'\s+', '_', issue_type)  # Replace spaces with underscores

                        issues.append({
                            "type": issue_type,
                            "severity": severity,
                            "description": description.strip(),
                            "beat_range": beat_range
                        })

        return issues

    def _parse_story_coherence_suggestions(self, analysis_text: str) -> list[str]:
        """Parse story coherence suggestions from AI analysis."""
        suggestions = []

        if "### SUGGESTIONS" in analysis_text:
            suggestions_section = analysis_text.split("### SUGGESTIONS")[1].split("###")[0].strip()

            for line in suggestions_section.split("\n"):
                line = line.strip()
                if line and (line.startswith("-") or line.startswith("*") or line.startswith("1.")):
                    line = line.lstrip("-*123456789.").strip()
                    if line:
                        suggestions.append(line)

        return suggestions

    def _parse_character_arcs(self, analysis_text: str) -> list[Dict[str, str]]:
        """Parse character arc analysis from AI response."""
        characters = []

        if "### CHARACTER_ARCS" in analysis_text:
            arcs_section = analysis_text.split("### CHARACTER_ARCS")[1].split("###")[0].strip()

            for line in arcs_section.split("\n"):
                line = line.strip()
                if line and (line.startswith("-") or line.startswith("*")):
                    line = line.lstrip("-*").strip()
                    if ":" in line:
                        name, arc_status = line.split(":", 1)
                        characters.append({
                            "name": name.strip(),
                            "arc_status": arc_status.strip()
                        })

        return characters

    def _parse_plot_threads(self, analysis_text: str) -> list[Dict[str, str]]:
        """Parse plot thread analysis from AI response."""
        threads = []

        if "### PLOT_THREADS" in analysis_text:
            threads_section = analysis_text.split("### PLOT_THREADS")[1].split("###")[0].strip()

            for line in threads_section.split("\n"):
                line = line.strip()
                if line and (line.startswith("-") or line.startswith("*")):
                    line = line.lstrip("-*").strip()

                    # Extract status if present
                    status = "active"
                    if "(" in line and ")" in line:
                        status_part = line.split("(")[1].split(")")[0]
                        status = status_part.strip().lower()

                    # Extract thread name and description
                    if ":" in line:
                        name_part, description = line.split(":", 1)
                        # Remove status from name if it's there
                        thread_name = name_part.split("(")[0].strip() if "(" in name_part else name_part.strip()

                        threads.append({
                            "name": thread_name,
                            "status": status,
                            "description": description.strip()
                        })

        return threads

    def _parse_timeline_issues(self, analysis_text: str) -> list[Dict[str, str]]:
        """Parse timeline issues from AI response."""
        timeline_issues = []

        if "### TIMELINE_ISSUES" in analysis_text:
            timeline_section = analysis_text.split("### TIMELINE_ISSUES")[1].split("###")[0].strip()

            for line in timeline_section.split("\n"):
                line = line.strip()
                if line and (line.startswith("-") or line.startswith("*")):
                    line = line.lstrip("-*").strip()

                    # Extract beat range
                    beat_range = None
                    if "Beat " in line:
                        beat_part = line.split("Beat ")[1].split(":")[0]
                        beat_range = beat_part.strip()

                    # Extract description
                    if ":" in line:
                        _, description = line.split(":", 1)
                        timeline_issues.append({
                            "beat_range": beat_range or "unknown",
                            "description": description.strip()
                        })

        return timeline_issues
