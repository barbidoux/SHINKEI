"""Authoring mode orchestration service."""
import asyncio
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shinkei.generation.narrative_service import NarrativeGenerationService
from shinkei.generation.base import GenerationConfig
from shinkei.models.story import Story, AuthoringMode
from shinkei.models.story_beat import StoryBeat, GeneratedBy
from shinkei.models.user import User
from shinkei.logging_config import get_logger

logger = get_logger(__name__)


class BeatProposal:
    """
    Transient beat proposal for collaborative mode.

    Not persisted to database - used for user selection workflow.
    """

    def __init__(
        self,
        id: str,
        content: str,
        summary: str,
        local_time_label: str,
        beat_type: str,
        reasoning: Optional[str] = None
    ):
        self.id = id
        self.content = content
        self.summary = summary
        self.local_time_label = local_time_label
        self.beat_type = beat_type
        self.reasoning = reasoning

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "summary": self.summary,
            "local_time_label": self.local_time_label,
            "beat_type": self.beat_type,
            "reasoning": self.reasoning
        }


class ManualAssistance:
    """Assistance data for manual authoring mode."""

    def __init__(
        self,
        coherence_result: Dict[str, Any],
        suggested_summary: str,
        world_event_suggestions: List[str]
    ):
        self.coherence_result = coherence_result
        self.suggested_summary = suggested_summary
        self.world_event_suggestions = world_event_suggestions

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "coherence": self.coherence_result,
            "suggested_summary": self.suggested_summary,
            "world_event_suggestions": self.world_event_suggestions
        }


class AuthoringService:
    """
    High-level orchestration service for mode-specific authoring workflows.

    This service provides mode-aware interfaces for the three authoring modes:
    - Autonomous: Direct AI generation without user intervention
    - Collaborative: Generate multiple proposals for user selection
    - Manual: Validation and assistance for user-written content

    Uses NarrativeGenerationService for underlying AI operations.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize authoring service.

        Args:
            session: Database session for operations
        """
        self.session = session
        self.narrative_service = NarrativeGenerationService(session)

    async def autonomous_generate(
        self,
        story_id: str,
        user_id: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        target_event_id: Optional[str] = None,
        insertion_mode: str = "append",
        insert_after_beat_id: Optional[str] = None,
        insert_at_position: Optional[int] = None,
        **provider_kwargs
    ) -> StoryBeat:
        """
        Generate a beat autonomously without user intervention.

        This is a direct wrapper around NarrativeGenerationService.generate_next_beat()
        for clarity and consistency with other mode-specific methods.

        Args:
            story_id: Story UUID
            user_id: User ID for ownership verification
            provider: Optional LLM provider override
            model: Optional model name override
            target_event_id: Optional specific WorldEvent to write about
            insertion_mode: Where to insert: "append", "insert_after", or "insert_at"
            insert_after_beat_id: Beat ID to insert after (for insert_after mode)
            insert_at_position: Position to insert at (for insert_at mode)
            **provider_kwargs: Additional provider-specific arguments

        Returns:
            Created StoryBeat with generated_by=AI

        Raises:
            ValueError: If story not found, wrong mode, or user doesn't own it
            RuntimeError: If generation fails
        """
        # Verify story is in autonomous mode
        story = await self._get_story(story_id)
        if story.mode != AuthoringMode.AUTONOMOUS:
            raise ValueError(
                f"Story {story_id} is in {story.mode} mode, not autonomous. "
                "Use appropriate method for the current mode."
            )

        logger.info(
            "autonomous_generation_started",
            story_id=story_id,
            user_id=user_id,
            target_event_id=target_event_id,
            insertion_mode=insertion_mode
        )

        # Generate beat directly
        beat = await self.narrative_service.generate_next_beat(
            story_id=story_id,
            user_id=user_id,
            provider=provider,
            model=model,
            user_instructions=None,  # No user guidance in autonomous mode
            target_event_id=target_event_id,
            insertion_mode=insertion_mode,
            insert_after_beat_id=insert_after_beat_id,
            insert_at_position=insert_at_position,
            **provider_kwargs
        )

        logger.info(
            "autonomous_generation_completed",
            story_id=story_id,
            beat_id=beat.id,
            sequence=beat.order_index
        )

        return beat

    async def collaborative_propose(
        self,
        story_id: str,
        user_id: str,
        user_guidance: Optional[str] = None,
        num_proposals: int = 3,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        target_event_id: Optional[str] = None,
        insertion_mode: str = "append",
        insert_after_beat_id: Optional[str] = None,
        insert_at_position: Optional[int] = None,
        # LLM parameters
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 0.9,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        top_k: Optional[int] = None,
        # Narrative style parameters
        target_length_preset: Optional[str] = None,
        target_length_words: Optional[int] = None,
        pacing: Optional[str] = None,
        tension_level: Optional[str] = None,
        dialogue_density: Optional[str] = None,
        description_richness: Optional[str] = None,
        # Collaborative-specific parameters
        proposal_diversity: float = 0.5,
        variation_focus: Optional[str] = None,
        **provider_kwargs
    ) -> List[BeatProposal]:
        """
        Generate multiple beat proposals for user selection.

        Proposals are generated in parallel with varying temperature to produce
        diverse options. They are NOT persisted - user must select and create
        an actual beat from a proposal.

        Args:
            story_id: Story UUID
            user_id: User ID for ownership verification
            user_guidance: Optional user instructions to guide generation
            num_proposals: Number of proposals to generate (1-5, default 3)
            provider: Optional LLM provider override
            model: Optional model name override
            target_event_id: Optional specific WorldEvent to write about
            insertion_mode: Where to insert: "append", "insert_after", or "insert_at"
            insert_after_beat_id: Beat ID to insert after (for insert_after mode)
            insert_at_position: Position to insert at (for insert_at mode)
            temperature: Base temperature for generation
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling threshold
            frequency_penalty: Frequency penalty for repetition
            presence_penalty: Presence penalty for new topics
            top_k: Top-k sampling (if supported)
            target_length_preset: Length preset (short/medium/long)
            target_length_words: Custom word count target
            pacing: Narrative pacing (slow/medium/fast)
            tension_level: Narrative tension (low/medium/high)
            dialogue_density: Dialogue amount (minimal/moderate/heavy)
            description_richness: Description detail (sparse/balanced/detailed)
            proposal_diversity: How different proposals are (0=similar, 1=very different)
            variation_focus: What aspect to vary (style/plot/tone/all)
            **provider_kwargs: Additional provider-specific arguments

        Returns:
            List of BeatProposal objects (transient, not persisted)

        Raises:
            ValueError: If story not found, wrong mode, invalid num_proposals, or user doesn't own it
            RuntimeError: If generation fails
        """
        # Validate num_proposals
        if not 1 <= num_proposals <= 5:
            raise ValueError(f"num_proposals must be between 1 and 5, got {num_proposals}")

        # Verify story is in collaborative mode
        story = await self._get_story(story_id)
        if story.mode != AuthoringMode.COLLABORATIVE:
            raise ValueError(
                f"Story {story_id} is in {story.mode} mode, not collaborative. "
                "Use appropriate method for the current mode."
            )

        logger.info(
            "collaborative_proposals_started",
            story_id=story_id,
            user_id=user_id,
            num_proposals=num_proposals,
            has_guidance=bool(user_guidance),
            proposal_diversity=proposal_diversity,
            variation_focus=variation_focus
        )

        # Generate variation instructions based on variation_focus
        variation_hints = self._build_variation_hints(variation_focus, num_proposals)

        # Generate proposals in parallel with varying temperature
        # Temperature variance is controlled by proposal_diversity
        tasks = []
        for i in range(num_proposals):
            # Calculate temperature variance: diversity=0 → same temp, diversity=1 → +/-0.3
            temp_offset = (i - (num_proposals - 1) / 2) * (proposal_diversity * 0.2)
            proposal_temp = max(0.0, min(2.0, temperature + temp_offset))

            config = GenerationConfig(
                temperature=proposal_temp,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                top_k=top_k
            )

            # Build guidance with variation hint if applicable
            effective_guidance = self._build_variation_guidance(user_guidance, variation_hints, i)

            # Create coroutine for parallel execution
            task = self.narrative_service.generate_next_beat(
                story_id=story_id,
                user_id=user_id,
                provider=provider,
                model=model,
                user_instructions=effective_guidance,
                target_event_id=target_event_id,
                generation_config=config,
                insertion_mode=insertion_mode,
                insert_after_beat_id=insert_after_beat_id,
                insert_at_position=insert_at_position,
                target_length_preset=target_length_preset,
                target_length_words=target_length_words,
                pacing=pacing,
                tension_level=tension_level,
                dialogue_density=dialogue_density,
                description_richness=description_richness,
                **provider_kwargs
            )
            tasks.append(task)

        # Execute in parallel
        try:
            beats = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(
                "collaborative_proposals_failed",
                story_id=story_id,
                error=str(e)
            )
            raise RuntimeError(f"Failed to generate proposals: {str(e)}") from e

        # Convert successful beats to proposals (filter out exceptions)
        proposals = []
        for i, beat_or_exception in enumerate(beats):
            if isinstance(beat_or_exception, Exception):
                logger.warning(
                    "proposal_generation_failed",
                    proposal_index=i,
                    error=str(beat_or_exception)
                )
                continue

            beat = beat_or_exception
            # Delete the temporarily created beat from database
            # (proposals are transient, not persisted)
            await self.session.delete(beat)

            # Convert to proposal
            proposal = BeatProposal(
                id=f"proposal-{i}",
                content=beat.content,
                summary=beat.summary or "",
                local_time_label=beat.local_time_label or "",
                beat_type=beat.type.value if beat.type else "scene",
                reasoning=getattr(beat, "generation_reasoning", None)
            )
            proposals.append(proposal)

        # Commit the deletions
        await self.session.commit()

        if not proposals:
            raise RuntimeError("All proposal generations failed")

        logger.info(
            "collaborative_proposals_completed",
            story_id=story_id,
            num_proposals=len(proposals),
            num_failed=num_proposals - len(proposals)
        )

        return proposals

    async def collaborative_propose_stream(
        self,
        story_id: str,
        user_id: str,
        user_guidance: Optional[str] = None,
        num_proposals: int = 3,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        target_event_id: Optional[str] = None,
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
        # LLM parameters
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 0.9,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        top_k: Optional[int] = None,
        # Narrative style parameters
        target_length_preset: Optional[str] = None,
        target_length_words: Optional[int] = None,
        pacing: Optional[str] = None,
        tension_level: Optional[str] = None,
        dialogue_density: Optional[str] = None,
        description_richness: Optional[str] = None,
        # Collaborative-specific parameters
        proposal_diversity: float = 0.5,
        variation_focus: Optional[str] = None,
        **provider_kwargs
    ):
        """
        Stream beat proposals as they complete (for live UI updates).

        Generates proposals in parallel and yields each one as soon as it's ready.

        Args:
            story_id: Story UUID
            user_id: User ID for ownership verification
            user_guidance: Optional user instructions to guide generation
            num_proposals: Number of proposals to generate (1-5, default 3)
            provider: Optional LLM provider override
            model: Optional model name override
            target_event_id: Optional specific WorldEvent to write about
            insertion_mode: Where to insert: "append", "insert_after", or "insert_at"
            insert_after_beat_id: Beat ID to insert after (for insert_after mode)
            insert_at_position: Position to insert at (for insert_at mode)
            beat_type_mode: How to determine beat_type (blank/manual/automatic)
            beat_type_manual: Manual beat_type value (used when mode='manual')
            summary_mode: How to determine summary (blank/manual/automatic)
            summary_manual: Manual summary value (used when mode='manual')
            local_time_label_mode: How to determine time label (blank/manual/automatic)
            local_time_label_manual: Manual time label value (used when mode='manual')
            world_event_id_mode: How to determine world event (blank/manual/automatic)
            world_event_id_manual: Manual world event ID (used when mode='manual')
            **provider_kwargs: Additional provider-specific arguments

        Yields:
            Dict with proposal data as each completes

        Raises:
            ValueError: If story not found, wrong mode, or invalid num_proposals
        """
        # Validate num_proposals
        if not 1 <= num_proposals <= 5:
            raise ValueError(f"num_proposals must be between 1 and 5, got {num_proposals}")

        # Verify story is in collaborative mode
        story = await self._get_story(story_id)
        if story.mode != AuthoringMode.COLLABORATIVE:
            raise ValueError(
                f"Story {story_id} is in {story.mode} mode, not collaborative. "
                "Use appropriate method for the current mode."
            )

        logger.info(
            "collaborative_proposals_stream_started",
            story_id=story_id,
            user_id=user_id,
            num_proposals=num_proposals,
            proposal_diversity=proposal_diversity,
            variation_focus=variation_focus
        )

        # Generate variation instructions based on variation_focus
        variation_hints = self._build_variation_hints(variation_focus, num_proposals)

        # Create tasks with different temperatures, wrapped with their index
        async def generate_with_index(index: int):
            """Wrapper to track which task is which."""
            # Calculate temperature variance: diversity=0 → same temp, diversity=1 → +/-0.3
            temp_offset = (index - (num_proposals - 1) / 2) * (proposal_diversity * 0.2)
            proposal_temp = max(0.0, min(2.0, temperature + temp_offset))

            config = GenerationConfig(
                temperature=proposal_temp,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                top_k=top_k
            )

            # Build guidance with variation hint if applicable
            effective_guidance = self._build_variation_guidance(user_guidance, variation_hints, index)

            beat = await self.narrative_service.generate_next_beat(
                story_id=story_id,
                user_id=user_id,
                provider=provider,
                model=model,
                user_instructions=effective_guidance,
                target_event_id=target_event_id,
                generation_config=config,
                insertion_mode=insertion_mode,
                insert_after_beat_id=insert_after_beat_id,
                insert_at_position=insert_at_position,
                # Metadata control parameters
                beat_type_mode=beat_type_mode,
                beat_type_manual=beat_type_manual,
                summary_mode=summary_mode,
                summary_manual=summary_manual,
                local_time_label_mode=local_time_label_mode,
                local_time_label_manual=local_time_label_manual,
                world_event_id_mode=world_event_id_mode,
                world_event_id_manual=world_event_id_manual,
                # Narrative style parameters
                target_length_preset=target_length_preset,
                target_length_words=target_length_words,
                pacing=pacing,
                tension_level=tension_level,
                dialogue_density=dialogue_density,
                description_richness=description_richness,
                **provider_kwargs
            )
            return index, beat

        # Create all tasks
        tasks = [
            asyncio.create_task(generate_with_index(i))
            for i in range(num_proposals)
        ]

        # Yield proposals as they complete
        completed_count = 0
        for coro in asyncio.as_completed(tasks):
            try:
                proposal_index, beat = await coro

                # Delete temporary beat from database
                await self.session.delete(beat)
                await self.session.flush()

                # Convert to proposal
                proposal = BeatProposal(
                    id=f"proposal-{proposal_index}",
                    content=beat.content,
                    summary=beat.summary or "",
                    local_time_label=beat.local_time_label or "",
                    beat_type=beat.type.value if beat.type else "scene",
                    reasoning=getattr(beat, "generation_reasoning", None)
                )

                completed_count += 1

                yield {
                    "type": "proposal",
                    "index": proposal_index,
                    "total": num_proposals,
                    "completed": completed_count,
                    "proposal": proposal.to_dict()
                }

            except Exception as e:
                logger.warning(
                    "proposal_stream_generation_failed",
                    error=str(e)
                )
                yield {
                    "type": "error",
                    "message": f"Failed to generate one proposal: {str(e)}"
                }

        # Commit deletions
        await self.session.commit()

        logger.info(
            "collaborative_proposals_stream_completed",
            story_id=story_id,
            num_completed=completed_count
        )

    async def manual_assist(
        self,
        story_id: str,
        user_id: str,
        user_content: str,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> ManualAssistance:
        """
        Provide assistance for manually authored content.

        Validates coherence with existing story and world context,
        generates a suggested summary, and suggests relevant world events.

        Args:
            story_id: Story UUID
            user_id: User ID for ownership verification
            user_content: User-written beat content to validate/assist
            provider: Optional LLM provider override
            model: Optional model name override

        Returns:
            ManualAssistance with coherence check, summary, and suggestions

        Raises:
            ValueError: If story not found or user doesn't own it
            RuntimeError: If assistance generation fails
        """
        # Verify story exists (mode check with warning only)
        story = await self._get_story(story_id)
        if story.mode != AuthoringMode.MANUAL:
            logger.warning(
                "manual_assist_wrong_mode",
                story_id=story_id,
                current_mode=story.mode.value,
                message="Manual assistance requested for non-manual story. Proceeding anyway."
            )

        logger.info(
            "manual_assist_started",
            story_id=story_id,
            user_id=user_id,
            content_length=len(user_content)
        )

        # Create temporary beat for coherence check and summarization
        temp_beat = StoryBeat(
            story_id=story_id,
            order_index=999999,  # Temporary sequence
            content=user_content,
            generated_by=GeneratedBy.USER
        )

        # Add to session and flush to get ID (but don't commit)
        self.session.add(temp_beat)
        await self.session.flush()

        coherence_result = {}
        suggested_summary = ""

        try:
            # Coherence check using temporary beat
            try:
                coherence_result = await self.narrative_service.check_beat_coherence(
                    story_id=story_id,
                    beat_id=temp_beat.id,
                    user_id=user_id,
                    provider=provider,
                    model=model
                )
            except Exception as e:
                logger.error("coherence_check_failed", error=str(e))
                coherence_result = {
                    "is_coherent": None,
                    "issues": [],
                    "suggestions": [],
                    "error": str(e)
                }

            # Generate suggested summary
            try:
                suggested_summary = await self.narrative_service.summarize_beat(
                    beat_id=temp_beat.id,
                    user_id=user_id,
                    provider=provider
                )
            except Exception as e:
                logger.error("summary_generation_failed", error=str(e))
                suggested_summary = ""

        finally:
            # Clean up temporary beat - rollback to remove from session
            await self.session.rollback()

        # World event suggestions (placeholder - could be enhanced with AI)
        # For now, return empty list - future enhancement could use AI to suggest
        # which existing world events this beat might relate to
        world_event_suggestions = []

        assistance = ManualAssistance(
            coherence_result=coherence_result,
            suggested_summary=suggested_summary,
            world_event_suggestions=world_event_suggestions
        )

        logger.info(
            "manual_assist_completed",
            story_id=story_id,
            is_coherent=coherence_result.get("is_coherent"),
            has_summary=bool(suggested_summary)
        )

        return assistance

    async def _get_story(self, story_id: str) -> Story:
        """
        Load story by ID.

        Args:
            story_id: Story UUID

        Returns:
            Story instance

        Raises:
            ValueError: If story not found
        """
        result = await self.session.execute(
            select(Story).where(Story.id == story_id)
        )
        story = result.scalar_one_or_none()

        if not story:
            raise ValueError(f"Story {story_id} not found")

        return story

    def _build_variation_hints(
        self,
        variation_focus: Optional[str],
        num_proposals: int
    ) -> List[str]:
        """
        Build variation hints for each proposal based on variation_focus.

        Args:
            variation_focus: What aspect to vary (style/plot/tone/all)
            num_proposals: Number of proposals to generate

        Returns:
            List of variation hint strings, one per proposal
        """
        if not variation_focus:
            return [""] * num_proposals

        # Define variation hints for each focus type
        hints = {
            "style": [
                "Use a formal, literary writing style.",
                "Use a casual, conversational writing style.",
                "Use a dramatic, cinematic writing style.",
                "Use a poetic, evocative writing style.",
                "Use a direct, minimalist writing style."
            ],
            "plot": [
                "Focus on character development and internal conflict.",
                "Advance the main plot with a significant event.",
                "Explore a subplot or secondary character.",
                "Create a turning point or revelation.",
                "Build towards a climactic moment."
            ],
            "tone": [
                "Use a lighter, more hopeful emotional tone.",
                "Maintain a neutral, balanced emotional tone.",
                "Use a darker, more tense emotional tone.",
                "Use a reflective, contemplative tone.",
                "Use an urgent, energetic tone."
            ],
            "all": [
                "Vary the style, plot direction, and tone in this proposal.",
                "Take a different approach to style, plot, and tone.",
                "Explore an alternative narrative direction.",
                "Create a distinct variation from other proposals.",
                "Offer a unique perspective on this beat."
            ]
        }

        focus_hints = hints.get(variation_focus, [""] * 5)

        # Return hints for the number of proposals needed
        return focus_hints[:num_proposals] + [""] * max(0, num_proposals - len(focus_hints))

    def _build_variation_guidance(
        self,
        user_guidance: Optional[str],
        variation_hints: List[str],
        index: int
    ) -> Optional[str]:
        """
        Build the effective guidance for a proposal, combining user guidance with variation hint.

        Args:
            user_guidance: User's original guidance
            variation_hints: List of variation hints
            index: Index of the current proposal

        Returns:
            Combined guidance string or None
        """
        hint = variation_hints[index] if index < len(variation_hints) else ""

        if user_guidance and hint:
            return f"{user_guidance}\n\n[Variation: {hint}]"
        elif hint:
            return f"[Variation: {hint}]"
        else:
            return user_guidance
