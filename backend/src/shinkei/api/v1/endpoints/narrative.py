"""Narrative generation API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
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
from shinkei.generation.narrative_service import NarrativeGenerationService
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
    temperature: float = Field(
        0.7,
        ge=0.0,
        le=2.0,
        description="Generation temperature"
    )
    max_tokens: int = Field(
        2000,
        ge=100,
        le=32000,
        description="Maximum tokens to generate"
    )
    ollama_host: Optional[str] = Field(
        None,
        description="Ollama server host (for Ollama provider)"
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

    # Build generation config
    generation_config = GenerationConfig(
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens
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
