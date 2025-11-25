"""Schemas for authoring mode operations."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class BeatProposalResponse(BaseModel):
    """Single beat proposal returned to frontend."""

    id: str = Field(..., description="Temporary proposal ID for tracking")
    content: str = Field(..., description="Generated beat content")
    summary: str = Field(..., description="Beat summary")
    local_time_label: str = Field(..., description="Local time label")
    beat_type: str = Field(..., description="Beat type (scene, log, etc.)")
    reasoning: Optional[str] = Field(None, description="AI reasoning for this beat")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "proposal-1",
                "content": "The protagonist discovers a hidden message...",
                "summary": "Discovery of crucial information",
                "local_time_label": "Log 0042",
                "beat_type": "scene",
                "reasoning": "Advancing the mystery plot thread while maintaining tension"
            }
        }


class ProposalRequest(BaseModel):
    """Request to generate beat proposals (collaborative mode)."""

    user_guidance: Optional[str] = Field(
        None,
        description="Optional user instructions to guide the AI generation",
        max_length=2000
    )
    num_proposals: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Number of proposals to generate (1-5)"
    )
    provider: Optional[str] = Field(
        None,
        description="LLM provider override (openai, anthropic, ollama)"
    )
    model: Optional[str] = Field(
        None,
        description="Model name override"
    )
    target_event_id: Optional[str] = Field(
        None,
        description="Optional specific WorldEvent to write about"
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

    # === COLLABORATIVE-SPECIFIC: Proposal Variation ===
    proposal_diversity: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="How different proposals are from each other: 0=similar, 1=very different"
    )
    variation_focus: Optional[str] = Field(
        None,
        pattern="^(style|plot|tone|all)$",
        description="What aspect to vary between proposals: style, plot direction, tone, or all aspects"
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

    class Config:
        json_schema_extra = {
            "example": {
                "user_guidance": "Make the scene more suspenseful and mysterious",
                "num_proposals": 3,
                "provider": "openai",
                "target_event_id": "event-uuid-here"
            }
        }


class ProposalResponse(BaseModel):
    """Response containing multiple beat proposals."""

    proposals: List[BeatProposalResponse] = Field(
        ...,
        description="List of generated beat proposals",
        min_length=1,
        max_length=5
    )

    class Config:
        json_schema_extra = {
            "example": {
                "proposals": [
                    {
                        "id": "proposal-0",
                        "content": "Variant 1: The protagonist discovers...",
                        "summary": "Discovery scene - mysterious tone",
                        "local_time_label": "Scene 042",
                        "beat_type": "scene",
                        "reasoning": "Emphasizes mystery"
                    },
                    {
                        "id": "proposal-1",
                        "content": "Variant 2: In a tense moment, the protagonist...",
                        "summary": "Discovery scene - suspenseful tone",
                        "local_time_label": "Scene 042",
                        "beat_type": "scene",
                        "reasoning": "Emphasizes tension"
                    },
                    {
                        "id": "proposal-2",
                        "content": "Variant 3: Carefully examining the evidence...",
                        "summary": "Discovery scene - analytical tone",
                        "local_time_label": "Scene 042",
                        "beat_type": "scene",
                        "reasoning": "Emphasizes investigation"
                    }
                ]
            }
        }


class ManualAssistanceRequest(BaseModel):
    """Request for manual authoring assistance."""

    content: str = Field(
        ...,
        description="User-written beat content to validate and assist with",
        min_length=1,
        max_length=50000
    )
    provider: Optional[str] = Field(
        None,
        description="LLM provider override"
    )
    model: Optional[str] = Field(
        None,
        description="Model name override"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content": "The captain stared at the viewscreen...",
                "provider": "openai"
            }
        }


class ManualAssistanceResponse(BaseModel):
    """Response with assistance for manually authored content."""

    coherence: Dict[str, Any] = Field(
        ...,
        description="Coherence check results"
    )
    suggested_summary: str = Field(
        ...,
        description="AI-generated summary suggestion"
    )
    world_event_suggestions: List[str] = Field(
        default_factory=list,
        description="Suggested relevant world events"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "coherence": {
                    "is_coherent": True,
                    "issues": [],
                    "suggestions": ["Consider adding more sensory details"],
                    "score": 0.85
                },
                "suggested_summary": "Captain confronts difficult decision aboard ship",
                "world_event_suggestions": []
            }
        }
