"""Beat modification Pydantic schemas for API validation."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class BeatModificationRequest(BaseModel):
    """Schema for requesting a beat modification."""
    model_config = ConfigDict(extra='forbid')

    modification_instructions: str = Field(
        ...,
        min_length=1,
        description="User instructions for how to modify the beat"
    )
    provider: str = Field(
        ...,
        pattern="^(openai|anthropic|ollama)$",
        description="LLM provider to use"
    )
    model: Optional[str] = Field(
        None,
        description="Specific model to use (provider-dependent)"
    )
    ollama_host: Optional[str] = Field(
        None,
        description="Ollama server URL (required for ollama provider)"
    )
    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Generation temperature"
    )
    max_tokens: Optional[int] = Field(
        default=8000,
        ge=100,
        le=32000,
        description="Maximum tokens to generate"
    )
    scope: List[str] = Field(
        default=["content", "summary", "time_label", "world_event"],
        description="Fields to modify: content, summary, time_label, world_event"
    )


class BeatModificationResponse(BaseModel):
    """Schema for beat modification responses."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    beat_id: str

    # Original and modified versions
    original_content: str
    modified_content: str
    original_summary: Optional[str] = None
    modified_summary: Optional[str] = None
    original_time_label: Optional[str] = None
    modified_time_label: Optional[str] = None
    original_world_event_id: Optional[str] = None
    modified_world_event_id: Optional[str] = None

    # Metadata
    modification_instructions: str
    reasoning: Optional[str] = None
    unified_diff: Optional[str] = None
    applied: bool
    created_at: datetime


class BeatModificationApply(BaseModel):
    """Schema for applying a beat modification."""
    model_config = ConfigDict(extra='forbid')

    modification_id: str = Field(..., description="ID of the modification to apply")
    apply_content: bool = Field(default=True, description="Apply content changes")
    apply_summary: bool = Field(default=True, description="Apply summary changes")
    apply_time_label: bool = Field(default=True, description="Apply time label changes")
    apply_world_event: bool = Field(default=True, description="Apply world event changes")


class BeatModificationHistoryResponse(BaseModel):
    """Schema for beat modification history."""
    model_config = ConfigDict(from_attributes=True)

    modifications: List[BeatModificationResponse]
    total: int
    beat_id: str
