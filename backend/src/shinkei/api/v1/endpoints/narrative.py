"""Narrative generation API endpoints."""
from typing import Optional, AsyncGenerator
import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shinkei.database.engine import get_db
from shinkei.auth.dependencies import get_current_user
from shinkei.models.user import User
from shinkei.models.story_beat import StoryBeat
from shinkei.models.beat_modification import BeatModification
from shinkei.repositories.story_beat import StoryBeatRepository
from shinkei.repositories.story import StoryRepository
from shinkei.repositories.world import WorldRepository
from shinkei.schemas.beat_modification import (
    BeatModificationRequest,
    BeatModificationResponse,
    BeatModificationApply,
    BeatModificationHistoryResponse
)
from shinkei.schemas.story_beat import StoryBeatResponse
from shinkei.schemas.authoring import (
    ProposalRequest,
    ProposalResponse,
    BeatProposalResponse,
    ManualAssistanceRequest,
    ManualAssistanceResponse
)
from shinkei.generation.narrative_service import NarrativeGenerationService
from shinkei.services.authoring_service import AuthoringService
from shinkei.generation.base import GenerationConfig
from shinkei.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/narrative", tags=["narrative"])


# Request/Response schemas

class GenerateBeatRequest(BaseModel):
    """Request for generating a new story beat."""
    provider: Optional[str] = Field(
        None,
        description="LLM provider (openai/anthropic/ollama). Defaults to user settings."
    )
    model: Optional[str] = Field(
        None,
        description="Model name override. Defaults to provider default."
    )
    user_instructions: Optional[str] = Field(
        None,
        description="User guidance for collaborative mode"
    )
    target_event_id: Optional[str] = Field(
        None,
        description="Optional WorldEvent ID to write toward"
    )
    # === BASIC TAB: Length Control ===
    target_length_preset: Optional[str] = Field(
        None,
        pattern="^(short|medium|long)$",
        description="Length preset: short (~500 words), medium (~1000), long (~2000)"
    )
    target_length_words: Optional[int] = Field(
        None,
        ge=100,
        le=10000,
        description="Custom word count target (overrides preset if set)"
    )

    # === ADVANCED TAB: LLM Parameters ===
    temperature: float = Field(
        0.7,
        ge=0.0,
        le=2.0,
        description="Creativity: 0=focused, 2=creative"
    )
    max_tokens: int = Field(
        2000,
        ge=100,
        le=32000,
        description="Maximum output length in tokens"
    )
    top_p: float = Field(
        0.9,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling: considers top P% tokens"
    )
    frequency_penalty: float = Field(
        0.0,
        ge=-2.0,
        le=2.0,
        description="Reduces word repetition (-2 to 2)"
    )
    presence_penalty: float = Field(
        0.0,
        ge=-2.0,
        le=2.0,
        description="Encourages new topics (-2 to 2)"
    )
    top_k: Optional[int] = Field(
        None,
        ge=1,
        le=100,
        description="Top-K sampling: considers top K tokens"
    )
    ollama_host: Optional[str] = Field(
        None,
        description="Ollama server host (for Ollama provider)"
    )

    # === EXPERT TAB: Narrative Style Controls ===
    pacing: Optional[str] = Field(
        None,
        pattern="^(slow|medium|fast)$",
        description="Story pacing: slow=detailed, medium=balanced, fast=action-focused"
    )
    tension_level: Optional[str] = Field(
        None,
        pattern="^(low|medium|high)$",
        description="Narrative tension: low=calm, medium=engaging, high=intense"
    )
    dialogue_density: Optional[str] = Field(
        None,
        pattern="^(minimal|moderate|heavy)$",
        description="Dialogue amount: minimal=narration-focused, heavy=conversation-rich"
    )
    description_richness: Optional[str] = Field(
        None,
        pattern="^(sparse|balanced|detailed)$",
        description="Descriptive detail: sparse=concise, detailed=immersive"
    )

    # Beat insertion parameters
    insertion_mode: str = Field(
        default="append",
        pattern="^(append|insert_after|insert_at)$",
        description="Where to insert the beat: append (end), insert_after (after specific beat), insert_at (at position)"
    )
    insert_after_beat_id: Optional[str] = Field(
        None,
        description="Beat ID to insert after (required if insertion_mode='insert_after')"
    )
    insert_at_position: Optional[int] = Field(
        None,
        ge=1,
        description="Position to insert at (1-based index, required if insertion_mode='insert_at')"
    )

    # Metadata control parameters
    beat_type_mode: str = Field(
        default="automatic",
        pattern="^(blank|manual|automatic)$",
        description="How to determine beat_type: blank (leave empty), manual (use provided value), automatic (AI determines)"
    )
    beat_type_manual: Optional[str] = Field(
        None,
        description="Manual beat_type value (used when beat_type_mode='manual')"
    )
    summary_mode: str = Field(
        default="automatic",
        pattern="^(blank|manual|automatic)$",
        description="How to determine summary: blank (leave empty), manual (use provided value), automatic (AI determines)"
    )
    summary_manual: Optional[str] = Field(
        None,
        description="Manual summary value (used when summary_mode='manual')"
    )
    local_time_label_mode: str = Field(
        default="automatic",
        pattern="^(blank|manual|automatic)$",
        description="How to determine local_time_label: blank (leave empty), manual (use provided value), automatic (AI determines)"
    )
    local_time_label_manual: Optional[str] = Field(
        None,
        description="Manual local_time_label value (used when local_time_label_mode='manual')"
    )
    world_event_id_mode: str = Field(
        default="automatic",
        pattern="^(blank|manual|automatic)$",
        description="How to determine world_event_id: blank (leave empty), manual (select from list), automatic (AI suggests)"
    )
    world_event_id_manual: Optional[str] = Field(
        None,
        description="Manual world_event_id value (used when world_event_id_mode='manual')"
    )


class BeatResponse(BaseModel):
    """Response containing generated beat."""
    id: str
    story_id: str
    order_index: int
    content: str
    summary: Optional[str]
    local_time_label: Optional[str]
    type: str
    world_event_id: Optional[str]
    generated_by: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class SummarizeBeatRequest(BaseModel):
    """Request for summarizing an existing beat."""
    provider: Optional[str] = Field(
        None,
        description="LLM provider override"
    )


class SummarizeBeatResponse(BaseModel):
    """Response containing generated summary."""
    beat_id: str
    summary: str


# Endpoints

@router.post("/stories/{story_id}/beats/generate", response_model=BeatResponse)
async def generate_next_beat(
    story_id: str,
    request: GenerateBeatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate the next narrative beat for a story.

    This endpoint:
    - Loads World/Story context from database
    - Builds narrative-aware prompts
    - Generates text respecting world laws, tone, and POV
    - Auto-generates summary and time label
    - Saves beat to database with metadata

    Supports three authoring modes:
    - **Autonomous**: AI generates freely
    - **Collaborative**: User provides guidance via `user_instructions`
    - **Manual**: AI assists but user will edit

    ## Example (Ollama on Windows):
    ```json
    {
      "provider": "ollama",
      "ollama_host": "http://192.168.1.100:11434",
      "model": "llama3",
      "temperature": 0.8
    }
    ```

    ## Example (Collaborative mode):
    ```json
    {
      "provider": "openai",
      "user_instructions": "The protagonist discovers a hidden passage",
      "temperature": 0.7
    }
    ```
    """
    service = NarrativeGenerationService(db)

    # Build generation config with all LLM parameters
    generation_config = GenerationConfig(
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        top_p=request.top_p,
        frequency_penalty=request.frequency_penalty,
        presence_penalty=request.presence_penalty,
        top_k=request.top_k
    )

    # Prepare provider kwargs
    provider_kwargs = {}
    if request.ollama_host:
        provider_kwargs["host"] = request.ollama_host

    try:
        beat = await service.generate_next_beat(
            story_id=story_id,
            user_id=current_user.id,
            provider=request.provider,
            model=request.model,
            user_instructions=request.user_instructions,
            target_event_id=request.target_event_id,
            generation_config=generation_config,
            insertion_mode=request.insertion_mode,
            insert_after_beat_id=request.insert_after_beat_id,
            insert_at_position=request.insert_at_position,
            beat_type_mode=request.beat_type_mode,
            beat_type_manual=request.beat_type_manual,
            summary_mode=request.summary_mode,
            summary_manual=request.summary_manual,
            local_time_label_mode=request.local_time_label_mode,
            local_time_label_manual=request.local_time_label_manual,
            world_event_id_mode=request.world_event_id_mode,
            world_event_id_manual=request.world_event_id_manual,
            # Narrative style parameters
            target_length_preset=request.target_length_preset,
            target_length_words=request.target_length_words,
            pacing=request.pacing,
            tension_level=request.tension_level,
            dialogue_density=request.dialogue_density,
            description_richness=request.description_richness,
            **provider_kwargs
        )

        # Commit transaction
        await db.commit()

        logger.info(
            "beat_generated_via_api",
            story_id=story_id,
            beat_id=beat.id,
            user_id=current_user.id
        )

        return BeatResponse(
            id=beat.id,
            story_id=beat.story_id,
            order_index=beat.order_index,
            content=beat.content,
            summary=beat.summary,
            local_time_label=beat.local_time_label,
            type=beat.type.value,
            world_event_id=beat.world_event_id,
            generated_by=beat.generated_by.value,
            created_at=beat.created_at.isoformat(),
            updated_at=beat.updated_at.isoformat()
        )

    except ValueError as e:
        # User doesn't own story or story not found
        logger.warning("generate_beat_forbidden", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RuntimeError as e:
        # Generation failed
        logger.error("generate_beat_failed", error=str(e), story_id=story_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate beat: {str(e)}"
        )
    except Exception as e:
        # Unexpected error
        logger.error("generate_beat_unexpected_error", error=str(e), exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("/stories/{story_id}/beats/generate/stream")
async def generate_next_beat_stream(
    story_id: str,
    request: GenerateBeatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stream the generation of the next narrative beat for a story.

    Returns Server-Sent Events (SSE) with:
    - Progressive content tokens as they're generated
    - Final beat metadata when generation completes
    - Error messages if generation fails

    SSE format:
    - `data: {"type": "token", "content": "..."}` - Progressive content
    - `data: {"type": "complete", "beat": {...}}` - Final beat with full metadata
    - `data: {"type": "error", "message": "..."}` - Error occurred
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        service = NarrativeGenerationService(db)

        # Build generation config with all LLM parameters
        generation_config = GenerationConfig(
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
            top_k=request.top_k
        )

        # Prepare provider kwargs
        provider_kwargs = {}
        if request.ollama_host:
            provider_kwargs["host"] = request.ollama_host

        try:
            # Stream beat generation
            async for event in service.generate_next_beat_stream(
                story_id=story_id,
                user_id=current_user.id,
                provider=request.provider,
                model=request.model,
                user_instructions=request.user_instructions,
                target_event_id=request.target_event_id,
                generation_config=generation_config,
                # Narrative style parameters
                target_length_preset=request.target_length_preset,
                target_length_words=request.target_length_words,
                pacing=request.pacing,
                tension_level=request.tension_level,
                dialogue_density=request.dialogue_density,
                description_richness=request.description_richness,
                **provider_kwargs
            ):
                # Send SSE event
                yield f"data: {json.dumps(event)}\n\n"

            # Commit transaction after successful generation
            await db.commit()

            logger.info(
                "beat_generated_streaming",
                story_id=story_id,
                user_id=current_user.id
            )

        except ValueError as e:
            error_event = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_event)}\n\n"
            logger.warning("generate_beat_stream_forbidden", error=str(e), user_id=current_user.id)

        except Exception as e:
            error_event = {"type": "error", "message": f"Generation failed: {str(e)}"}
            yield f"data: {json.dumps(error_event)}\n\n"
            logger.error("generate_beat_stream_failed", error=str(e), exc_info=True)
            await db.rollback()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.post("/stories/{story_id}/beats/propose", response_model=ProposalResponse)
async def generate_beat_proposals(
    story_id: str,
    request: ProposalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate multiple beat proposals for collaborative mode.

    Creates 1-5 AI-generated beat variations based on user guidance.
    Proposals are transient (not persisted to database) - user must
    select and create an actual beat from a proposal.

    **Collaborative Mode Only**: This endpoint is intended for stories
    in collaborative authoring mode. It will work for other modes but
    logs a warning.

    Args:
        story_id: Story UUID
        request: Proposal generation parameters
        db: Database session
        current_user: Authenticated user

    Returns:
        ProposalResponse with 1-5 beat proposals

    Raises:
        404: Story not found
        403: User doesn't own the story
        400: Invalid num_proposals value
        500: Generation failed
    """
    service = AuthoringService(db)

    # Prepare provider kwargs
    provider_kwargs = {}
    # Note: Ollama host would come from user settings via AuthoringService

    try:
        # Generate proposals
        proposals = await service.collaborative_propose(
            story_id=story_id,
            user_id=current_user.id,
            user_guidance=request.user_guidance,
            num_proposals=request.num_proposals,
            provider=request.provider,
            model=request.model,
            target_event_id=request.target_event_id,
            insertion_mode=request.insertion_mode,
            insert_after_beat_id=request.insert_after_beat_id,
            insert_at_position=request.insert_at_position,
            **provider_kwargs
        )

        # Convert to response schema
        proposal_responses = [
            BeatProposalResponse(
                id=p.id,
                content=p.content,
                summary=p.summary,
                local_time_label=p.local_time_label,
                beat_type=p.beat_type,
                reasoning=p.reasoning
            )
            for p in proposals
        ]

        logger.info(
            "proposals_generated",
            story_id=story_id,
            user_id=current_user.id,
            num_proposals=len(proposals)
        )

        return ProposalResponse(proposals=proposal_responses)

    except ValueError as e:
        logger.warning(
            "generate_proposals_forbidden",
            error=str(e),
            user_id=current_user.id,
            story_id=story_id
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except RuntimeError as e:
        logger.error(
            "generate_proposals_failed",
            error=str(e),
            exc_info=True
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate proposals: {str(e)}"
        )

    except Exception as e:
        logger.error(
            "generate_proposals_unexpected_error",
            error=str(e),
            exc_info=True
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("/stories/{story_id}/beats/propose/stream")
async def generate_beat_proposals_stream(
    story_id: str,
    request: ProposalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stream beat proposal generation for collaborative mode.

    Generates 1-5 proposals in parallel and streams each one as it completes,
    providing live feedback to the user.

    Returns Server-Sent Events (SSE) with:
    - Progressive proposal completion events
    - Error messages if individual proposals fail

    SSE format:
    - `data: {"type": "proposal", "index": N, "completed": N, "total": N, "proposal": {...}}`
    - `data: {"type": "error", "message": "..."}`
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        service = AuthoringService(db)
        provider_kwargs = {}

        try:
            # Stream proposals as they complete
            async for event in service.collaborative_propose_stream(
                story_id=story_id,
                user_id=current_user.id,
                user_guidance=request.user_guidance,
                num_proposals=request.num_proposals,
                provider=request.provider,
                model=request.model,
                target_event_id=request.target_event_id,
                insertion_mode=request.insertion_mode,
                insert_after_beat_id=request.insert_after_beat_id,
                insert_at_position=request.insert_at_position,
                # Metadata control parameters
                beat_type_mode=request.beat_type_mode,
                beat_type_manual=request.beat_type_manual,
                summary_mode=request.summary_mode,
                summary_manual=request.summary_manual,
                local_time_label_mode=request.local_time_label_mode,
                local_time_label_manual=request.local_time_label_manual,
                world_event_id_mode=request.world_event_id_mode,
                world_event_id_manual=request.world_event_id_manual,
                **provider_kwargs
            ):
                yield f"data: {json.dumps(event)}\n\n"

            logger.info(
                "proposals_stream_completed",
                story_id=story_id,
                user_id=current_user.id
            )

        except ValueError as e:
            error_event = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_event)}\n\n"
            logger.warning(
                "proposals_stream_forbidden",
                error=str(e),
                user_id=current_user.id
            )

        except Exception as e:
            error_event = {"type": "error", "message": f"Generation failed: {str(e)}"}
            yield f"data: {json.dumps(error_event)}\n\n"
            logger.error(
                "proposals_stream_failed",
                error=str(e),
                exc_info=True
            )
            await db.rollback()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/stories/{story_id}/beats/assist", response_model=ManualAssistanceResponse)
async def manual_authoring_assist(
    story_id: str,
    request: ManualAssistanceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Provide AI assistance for manually authored content.

    Validates coherence, generates summary suggestions, and provides
    guidance for user-written beat content. Particularly useful for
    manual authoring mode.

    Args:
        story_id: Story UUID
        request: User-written content to assist with
        db: Database session
        current_user: Authenticated user

    Returns:
        ManualAssistanceResponse with coherence check, summary, and suggestions

    Raises:
        404: Story not found
        403: User doesn't own the story
        500: Assistance generation failed
    """
    service = AuthoringService(db)

    try:
        assistance = await service.manual_assist(
            story_id=story_id,
            user_id=current_user.id,
            user_content=request.content,
            provider=request.provider,
            model=request.model
        )

        logger.info(
            "manual_assist_completed",
            story_id=story_id,
            user_id=current_user.id,
            content_length=len(request.content)
        )

        return ManualAssistanceResponse(
            coherence=assistance.coherence_result,
            suggested_summary=assistance.suggested_summary,
            world_event_suggestions=assistance.world_event_suggestions
        )

    except ValueError as e:
        logger.warning(
            "manual_assist_forbidden",
            error=str(e),
            user_id=current_user.id,
            story_id=story_id
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.error(
            "manual_assist_failed",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to provide assistance: {str(e)}"
        )


class CheckCoherenceRequest(BaseModel):
    """Request body for coherence check."""
    provider: Optional[str] = Field(None, description="LLM provider override (openai/anthropic/ollama)")
    model: Optional[str] = Field(None, description="Model name override")


class StoryCoherenceRequest(BaseModel):
    """Request body for story-level coherence check."""
    provider: Optional[str] = Field(None, description="LLM provider override (openai/anthropic/ollama)")
    model: Optional[str] = Field(None, description="Model name override")
    start_beat_index: Optional[int] = Field(
        None,
        ge=1,
        description="Starting beat index (1-based) for range analysis. If not provided, analyzes from beginning."
    )
    end_beat_index: Optional[int] = Field(
        None,
        ge=1,
        description="Ending beat index (1-based) for range analysis. If not provided, analyzes to end."
    )


@router.post("/stories/{story_id}/beats/{beat_id}/check-coherence")
async def check_beat_coherence(
    story_id: str,
    beat_id: str,
    request: CheckCoherenceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check a beat for narrative coherence.

    Validates that the beat:
    - Doesn't contradict world laws or tone
    - Is consistent with previous beats
    - Maintains narrative continuity
    - Follows story POV and mode

    Returns:
    - coherent: bool - whether beat passes coherence checks
    - issues: List[dict] - list of detected issues with severity levels
    - suggestions: List[str] - suggested fixes
    """
    service = NarrativeGenerationService(db)

    # Debug logging to see what provider was requested
    logger.info(
        "coherence_check_request",
        story_id=story_id,
        beat_id=beat_id,
        requested_provider=request.provider,
        requested_model=request.model
    )

    try:
        result = await service.check_beat_coherence(
            story_id=story_id,
            beat_id=beat_id,
            user_id=current_user.id,
            provider=request.provider,
            model=request.model
        )

        await db.commit()

        logger.info(
            "beat_coherence_checked",
            story_id=story_id,
            beat_id=beat_id,
            coherent=result.get("coherent", True),
            issue_count=len(result.get("issues", []))
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("coherence_check_failed", error=str(e), exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Coherence check failed: {str(e)}"
        )


@router.post("/stories/{story_id}/check-coherence")
async def check_story_coherence(
    story_id: str,
    request: StoryCoherenceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check story-level narrative coherence.

    Performs comprehensive coherence analysis across multiple beats or the entire story.
    Analyzes:
    - Timeline consistency across beats
    - Character arc development
    - Plot thread progression
    - World law adherence
    - POV consistency
    - Overall narrative flow

    Args:
        story_id: Story UUID
        request: Coherence check parameters (optional beat range)
        db: Database session
        current_user: Authenticated user

    Returns:
        Dict with:
        - coherent: bool - whether story is coherent (no medium/high severity issues)
        - issues: List[dict] - detected issues with:
            - type: str (timeline, character, plot, world_law, pov, pacing)
            - severity: str (low, medium, high)
            - description: str (detailed explanation)
            - beat_range: str | None (e.g., "2", "2-3", "1-4" - specific beats affected)
        - suggestions: List[str] - suggested improvements
        - character_arcs: List[dict] - character development tracking
        - plot_threads: List[dict] - plot thread status
        - timeline_issues: List[dict] - timeline inconsistencies
        - analysis: str - full AI analysis

    Raises:
        404: Story not found
        403: User doesn't own the story
        500: Coherence check failed
    """
    service = NarrativeGenerationService(db)

    logger.info(
        "story_coherence_check_request",
        story_id=story_id,
        start_beat_index=request.start_beat_index,
        end_beat_index=request.end_beat_index,
        requested_provider=request.provider,
        requested_model=request.model
    )

    try:
        result = await service.check_story_coherence(
            story_id=story_id,
            user_id=current_user.id,
            start_beat_index=request.start_beat_index,
            end_beat_index=request.end_beat_index,
            provider=request.provider,
            model=request.model
        )

        await db.commit()

        logger.info(
            "story_coherence_checked",
            story_id=story_id,
            coherent=result.get("coherent", True),
            issue_count=len(result.get("issues", [])),
            character_arcs_count=len(result.get("character_arcs", [])),
            plot_threads_count=len(result.get("plot_threads", []))
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("story_coherence_check_failed", error=str(e), exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Story coherence check failed: {str(e)}"
        )


@router.post("/beats/{beat_id}/summarize", response_model=SummarizeBeatResponse)
async def summarize_beat(
    beat_id: str,
    request: SummarizeBeatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate or regenerate a summary for an existing beat.

    Useful for:
    - Summarizing manually-written beats
    - Regenerating summaries with different providers
    - Creating summaries for imported content

    ## Example:
    ```json
    {
      "provider": "anthropic"
    }
    ```
    """
    service = NarrativeGenerationService(db)

    try:
        summary = await service.summarize_beat(
            beat_id=beat_id,
            user_id=current_user.id,
            provider=request.provider
        )

        # Commit transaction
        await db.commit()

        logger.info(
            "beat_summarized_via_api",
            beat_id=beat_id,
            user_id=current_user.id
        )

        return SummarizeBeatResponse(
            beat_id=beat_id,
            summary=summary
        )

    except ValueError as e:
        logger.warning("summarize_beat_forbidden", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("summarize_beat_failed", error=str(e), exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to summarize beat: {str(e)}"
        )


# Beat Modification Endpoints

@router.post(
    "/stories/{story_id}/beats/{beat_id}/modifications",
    response_model=BeatModificationResponse,
    status_code=status.HTTP_201_CREATED
)
async def request_beat_modification(
    story_id: str,
    beat_id: str,
    modification_request: BeatModificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BeatModification:
    """
    Request a modification for an existing beat using AI.

    This endpoint:
    1. Takes user modification instructions
    2. Uses AI to generate modified content
    3. Creates a modification record with unified diff
    4. Returns the proposed modification (not yet applied)
    """
    # Verify ownership through repository chain
    repo = StoryBeatRepository(db)
    beat = await repo.get_by_id(beat_id)
    if not beat:
        raise HTTPException(status_code=404, detail="Beat not found")

    if beat.story_id != story_id:
        raise HTTPException(status_code=404, detail="Beat not found in this story")

    story_repo = StoryRepository(db)
    story = await story_repo.get_by_id(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    world_repo = WorldRepository(db)
    world = await world_repo.get_by_id(story.world_id)
    if not world or world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this beat")

    # Use narrative service to generate modification
    narrative_service = NarrativeGenerationService(db)

    # Build generation config
    config = GenerationConfig(
        temperature=modification_request.temperature or 0.7,
        max_tokens=modification_request.max_tokens or 8000
    )

    try:
        # Generate modification
        modification = await narrative_service.modify_beat(
            beat_id=beat_id,
            user_id=current_user.id,
            modification_instructions=modification_request.modification_instructions,
            scope=modification_request.scope,
            provider=modification_request.provider,
            model=modification_request.model,
            generation_config=config,
            host=modification_request.ollama_host
        )

        await db.commit()

        logger.info(
            "beat_modification_requested",
            beat_id=beat_id,
            modification_id=modification.id,
            provider=modification_request.provider
        )

        return modification

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Modification failed: {str(e)}")


@router.get(
    "/stories/{story_id}/beats/{beat_id}/modifications",
    response_model=BeatModificationHistoryResponse
)
async def get_beat_modification_history(
    story_id: str,
    beat_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 10,
) -> BeatModificationHistoryResponse:
    """
    Get modification history for a beat.

    Returns up to `limit` most recent modifications (applied and unapplied).
    """
    # Verify ownership
    repo = StoryBeatRepository(db)
    beat = await repo.get_by_id(beat_id)
    if not beat:
        raise HTTPException(status_code=404, detail="Beat not found")

    if beat.story_id != story_id:
        raise HTTPException(status_code=404, detail="Beat not found in this story")

    story_repo = StoryRepository(db)
    story = await story_repo.get_by_id(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    world_repo = WorldRepository(db)
    world = await world_repo.get_by_id(story.world_id)
    if not world or world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this beat")

    # Get modifications
    result = await db.execute(
        select(BeatModification)
        .where(BeatModification.beat_id == beat_id)
        .order_by(BeatModification.created_at.desc())
        .limit(limit)
    )
    modifications = result.scalars().all()

    logger.info(
        "beat_modification_history_retrieved",
        beat_id=beat_id,
        count=len(modifications)
    )

    return BeatModificationHistoryResponse(
        modifications=modifications,
        total=len(modifications),
        beat_id=beat_id
    )


@router.post(
    "/stories/{story_id}/beats/{beat_id}/modifications/{modification_id}/apply",
    response_model=StoryBeatResponse
)
async def apply_beat_modification(
    story_id: str,
    beat_id: str,
    modification_id: str,
    apply_request: BeatModificationApply,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StoryBeat:
    """
    Apply a proposed modification to a beat.

    User can selectively apply changes to content, summary, time_label, and world_event.
    """
    # Verify ownership
    repo = StoryBeatRepository(db)
    beat = await repo.get_by_id(beat_id)
    if not beat:
        raise HTTPException(status_code=404, detail="Beat not found")

    if beat.story_id != story_id:
        raise HTTPException(status_code=404, detail="Beat not found in this story")

    story_repo = StoryRepository(db)
    story = await story_repo.get_by_id(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    world_repo = WorldRepository(db)
    world = await world_repo.get_by_id(story.world_id)
    if not world or world.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this beat")

    # Get modification
    result = await db.execute(
        select(BeatModification).where(BeatModification.id == modification_id)
    )
    modification = result.scalar_one_or_none()

    if not modification:
        raise HTTPException(status_code=404, detail="Modification not found")

    if modification.beat_id != beat_id:
        raise HTTPException(status_code=404, detail="Modification not found for this beat")

    # Apply selected changes
    if apply_request.apply_content:
        beat.content = modification.modified_content

    if apply_request.apply_summary and modification.modified_summary is not None:
        beat.summary = modification.modified_summary

    if apply_request.apply_time_label and modification.modified_time_label is not None:
        beat.local_time_label = modification.modified_time_label

    if apply_request.apply_world_event and modification.modified_world_event_id is not None:
        beat.world_event_id = modification.modified_world_event_id

    # Mark modification as applied
    modification.applied = True

    await db.flush()
    await db.commit()
    await db.refresh(beat)

    logger.info(
        "beat_modification_applied",
        beat_id=beat_id,
        modification_id=modification_id,
        applied_content=apply_request.apply_content,
        applied_summary=apply_request.apply_summary,
        applied_time_label=apply_request.apply_time_label,
        applied_world_event=apply_request.apply_world_event
    )

    return beat
