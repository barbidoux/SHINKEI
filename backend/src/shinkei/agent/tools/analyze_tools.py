"""Analyze tools for Story Pilot agent.

These tools allow the agent to analyze content for coherence,
timeline consistency, and other narrative quality checks.
"""
from typing import Dict, Any, Optional, List
from shinkei.agent.tools.registry import tool, ToolCategory
from shinkei.agent.tools.context import ToolContext
from shinkei.repositories.world import WorldRepository
from shinkei.repositories.story import StoryRepository
from shinkei.repositories.story_beat import StoryBeatRepository
from shinkei.repositories.character import CharacterRepository
from shinkei.repositories.world_event import WorldEventRepository
from shinkei.repositories.world_coherence import WorldCoherenceRepository
from shinkei.repositories.entity_mention import EntityMentionRepository


@tool(
    name="check_timeline_consistency",
    description="Check if events and beats follow a consistent timeline according to world rules.",
    parameters={
        "type": "object",
        "properties": {
            "story_id": {
                "type": "string",
                "description": "Story ID to check. Uses current story if not provided."
            }
        },
        "required": []
    },
    category=ToolCategory.ANALYZE
)
async def check_timeline_consistency(
    context: ToolContext,
    story_id: Optional[str] = None
) -> Dict[str, Any]:
    """Check timeline consistency for a story."""
    world_id = context.require_world()
    if not story_id:
        story_id = context.require_story()

    # Get coherence settings
    coherence_repo = WorldCoherenceRepository(context.session)
    settings = await coherence_repo.get_or_create(world_id)

    # If time is irrelevant, skip check
    if settings.time_consistency == "irrelevant":
        return {
            "status": "skipped",
            "message": "Time consistency is set to 'irrelevant' for this world"
        }

    # Get beats and events
    beat_repo = StoryBeatRepository(context.session)
    event_repo = WorldEventRepository(context.session)

    beats, _ = await beat_repo.list_by_story(story_id, limit=1000)
    events, _ = await event_repo.list_by_world(world_id, limit=1000)

    issues = []

    # Check beats linked to events
    event_map = {e.id: e for e in events}
    prev_event_t = None

    for beat in beats:
        if beat.world_event_id:
            event = event_map.get(beat.world_event_id)
            if event:
                if prev_event_t is not None:
                    if settings.time_consistency == "strict":
                        # In strict mode, time must always move forward
                        if event.t < prev_event_t:
                            issues.append({
                                "type": "timeline_violation",
                                "beat_id": beat.id,
                                "beat_order": beat.order_index,
                                "message": f"Beat at order {beat.order_index} links to event at t={event.t}, but previous event was at t={prev_event_t}. Time moved backward.",
                                "severity": "error"
                            })
                    elif settings.time_consistency == "flexible":
                        # In flexible mode, large jumps backward are warnings
                        if event.t < prev_event_t - 100:
                            issues.append({
                                "type": "timeline_jump",
                                "beat_id": beat.id,
                                "message": f"Large time jump backward from t={prev_event_t} to t={event.t}",
                                "severity": "warning"
                            })
                prev_event_t = event.t

    return {
        "status": "checked",
        "issues": issues,
        "issue_count": len(issues),
        "beats_checked": len(beats),
        "time_consistency_mode": settings.time_consistency
    }


@tool(
    name="check_character_consistency",
    description="Check if characters behave consistently with their established traits and knowledge.",
    parameters={
        "type": "object",
        "properties": {
            "character_id": {
                "type": "string",
                "description": "Character ID to check"
            },
            "story_id": {
                "type": "string",
                "description": "Story ID to check within. Uses current story if not provided."
            }
        },
        "required": ["character_id"]
    },
    category=ToolCategory.ANALYZE
)
async def check_character_consistency(
    context: ToolContext,
    character_id: str,
    story_id: Optional[str] = None
) -> Dict[str, Any]:
    """Check character consistency across story beats."""
    world_id = context.require_world()
    if not story_id:
        story_id = context.require_story()

    # Get character
    char_repo = CharacterRepository(context.session)
    character = await char_repo.get_by_id(character_id)
    if not character:
        return {"error": "Character not found"}

    # Get coherence settings
    coherence_repo = WorldCoherenceRepository(context.session)
    settings = await coherence_repo.get_or_create(world_id)

    # Get entity mentions for this character
    mention_repo = EntityMentionRepository(context.session)
    mentions = await mention_repo.list_by_entity("character", character_id)

    # Get associated beats
    beat_repo = StoryBeatRepository(context.session)
    mentioned_beats = []
    for mention in mentions:
        beat = await beat_repo.get_by_id(mention.story_beat_id)
        if beat and beat.story_id == story_id:
            mentioned_beats.append({
                "beat": beat,
                "mention": mention
            })

    # Sort by order
    mentioned_beats.sort(key=lambda x: x["beat"].order_index)

    analysis = {
        "character_id": character_id,
        "character_name": character.name,
        "appearances": len(mentioned_beats),
        "first_appearance": mentioned_beats[0]["beat"].order_index if mentioned_beats else None,
        "character_knowledge_mode": settings.character_knowledge,
        "issues": [],
        "notes": []
    }

    # Basic analysis - check for gaps in appearances for major characters
    if character.importance and character.importance.value == "major":
        if len(mentioned_beats) < 3:
            analysis["notes"].append({
                "type": "sparse_appearances",
                "message": f"Major character '{character.name}' only appears {len(mentioned_beats)} times in this story"
            })

    return analysis


@tool(
    name="analyze_story_structure",
    description="Analyze the structure of a story including beat distribution, pacing, and narrative flow.",
    parameters={
        "type": "object",
        "properties": {
            "story_id": {
                "type": "string",
                "description": "Story ID to analyze. Uses current story if not provided."
            }
        },
        "required": []
    },
    category=ToolCategory.ANALYZE
)
async def analyze_story_structure(
    context: ToolContext,
    story_id: Optional[str] = None
) -> Dict[str, Any]:
    """Analyze story structure and pacing."""
    if not story_id:
        story_id = context.require_story()

    # Get story
    story_repo = StoryRepository(context.session)
    story = await story_repo.get_by_id(story_id)
    if not story:
        return {"error": "Story not found"}

    # Get beats
    beat_repo = StoryBeatRepository(context.session)
    beats, total = await beat_repo.list_by_story(story_id, limit=1000)

    # Analyze beat types
    type_counts = {}
    for beat in beats:
        beat_type = beat.type.value if beat.type else "unknown"
        type_counts[beat_type] = type_counts.get(beat_type, 0) + 1

    # Calculate word counts
    total_words = sum(len(beat.content.split()) for beat in beats)
    avg_words_per_beat = total_words / len(beats) if beats else 0

    # Analyze authorship
    ai_count = sum(1 for b in beats if b.generated_by and b.generated_by.value == "ai")
    user_count = sum(1 for b in beats if b.generated_by and b.generated_by.value == "user")
    collab_count = sum(1 for b in beats if b.generated_by and b.generated_by.value == "collaborative")

    # Get unique events linked
    linked_events = set(b.world_event_id for b in beats if b.world_event_id)

    return {
        "story_id": story_id,
        "story_title": story.title,
        "total_beats": total,
        "total_words": total_words,
        "avg_words_per_beat": round(avg_words_per_beat, 1),
        "beat_type_distribution": type_counts,
        "authorship": {
            "ai": ai_count,
            "user": user_count,
            "collaborative": collab_count
        },
        "linked_events_count": len(linked_events),
        "has_summary": sum(1 for b in beats if b.summary),
        "has_time_labels": sum(1 for b in beats if b.local_time_label)
    }


@tool(
    name="find_narrative_gaps",
    description="Identify potential gaps or missing elements in the narrative.",
    parameters={
        "type": "object",
        "properties": {
            "story_id": {
                "type": "string",
                "description": "Story ID to analyze. Uses current story if not provided."
            }
        },
        "required": []
    },
    category=ToolCategory.ANALYZE
)
async def find_narrative_gaps(
    context: ToolContext,
    story_id: Optional[str] = None
) -> Dict[str, Any]:
    """Find potential gaps in the narrative."""
    world_id = context.require_world()
    if not story_id:
        story_id = context.require_story()

    # Get beats
    beat_repo = StoryBeatRepository(context.session)
    beats, _ = await beat_repo.list_by_story(story_id, limit=1000)

    # Get entity mentions
    mention_repo = EntityMentionRepository(context.session)

    gaps = []

    # Check for beats without summaries
    beats_without_summary = [b for b in beats if not b.summary]
    if len(beats_without_summary) > len(beats) * 0.5:
        gaps.append({
            "type": "missing_summaries",
            "count": len(beats_without_summary),
            "message": f"{len(beats_without_summary)} of {len(beats)} beats lack summaries"
        })

    # Check for isolated characters (mentioned once then never again)
    char_mentions = {}
    for beat in beats:
        mentions = await mention_repo.list_by_beat(beat.id)
        for m in mentions:
            if m.entity_type == "character":
                if m.entity_id not in char_mentions:
                    char_mentions[m.entity_id] = []
                char_mentions[m.entity_id].append(beat.order_index)

    for char_id, appearances in char_mentions.items():
        if len(appearances) == 1:
            gaps.append({
                "type": "abandoned_character",
                "character_id": char_id,
                "last_seen_at_beat": appearances[0],
                "message": "Character introduced but never mentioned again"
            })

    # Check for large time gaps (if events are linked)
    prev_event_t = None
    event_repo = WorldEventRepository(context.session)

    for beat in beats:
        if beat.world_event_id:
            event = await event_repo.get_by_id(beat.world_event_id)
            if event and prev_event_t is not None:
                time_gap = event.t - prev_event_t
                if time_gap > 1000:  # Arbitrary threshold
                    gaps.append({
                        "type": "large_time_gap",
                        "from_t": prev_event_t,
                        "to_t": event.t,
                        "gap": time_gap,
                        "beat_order": beat.order_index,
                        "message": f"Large time gap of {time_gap} units between beats"
                    })
            if event:
                prev_event_t = event.t

    return {
        "story_id": story_id,
        "gaps": gaps,
        "gap_count": len(gaps),
        "beats_analyzed": len(beats)
    }


@tool(
    name="get_coherence_rules",
    description="Get the current coherence rules for this world.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    },
    category=ToolCategory.ANALYZE
)
async def get_coherence_rules(context: ToolContext) -> Dict[str, Any]:
    """Get world coherence rules."""
    world_id = context.require_world()

    repo = WorldCoherenceRepository(context.session)
    settings = await repo.get_or_create(world_id)

    return {
        "world_id": world_id,
        "time_consistency": settings.time_consistency,
        "spatial_consistency": settings.spatial_consistency,
        "causality": settings.causality,
        "character_knowledge": settings.character_knowledge,
        "death_permanence": settings.death_permanence,
        "custom_rules": settings.custom_rules or []
    }


@tool(
    name="compare_beats",
    description="Compare two beats for similarity, conflicts, or continuity.",
    parameters={
        "type": "object",
        "properties": {
            "beat_id_1": {
                "type": "string",
                "description": "First beat ID"
            },
            "beat_id_2": {
                "type": "string",
                "description": "Second beat ID"
            }
        },
        "required": ["beat_id_1", "beat_id_2"]
    },
    category=ToolCategory.ANALYZE
)
async def compare_beats(
    context: ToolContext,
    beat_id_1: str,
    beat_id_2: str
) -> Dict[str, Any]:
    """Compare two beats."""
    beat_repo = StoryBeatRepository(context.session)

    beat1 = await beat_repo.get_by_id(beat_id_1)
    beat2 = await beat_repo.get_by_id(beat_id_2)

    if not beat1:
        return {"error": f"Beat {beat_id_1} not found"}
    if not beat2:
        return {"error": f"Beat {beat_id_2} not found"}

    # Get entity mentions for both
    mention_repo = EntityMentionRepository(context.session)
    mentions1 = await mention_repo.list_by_beat(beat_id_1)
    mentions2 = await mention_repo.list_by_beat(beat_id_2)

    # Find common entities
    entities1 = {(m.entity_type, m.entity_id) for m in mentions1}
    entities2 = {(m.entity_type, m.entity_id) for m in mentions2}
    common = entities1.intersection(entities2)

    # Word count comparison
    words1 = len(beat1.content.split())
    words2 = len(beat2.content.split())

    return {
        "beat_1": {
            "id": beat1.id,
            "order_index": beat1.order_index,
            "type": beat1.type.value if beat1.type else None,
            "word_count": words1,
            "entities": len(entities1)
        },
        "beat_2": {
            "id": beat2.id,
            "order_index": beat2.order_index,
            "type": beat2.type.value if beat2.type else None,
            "word_count": words2,
            "entities": len(entities2)
        },
        "common_entities": list(common),
        "order_difference": abs(beat2.order_index - beat1.order_index),
        "same_story": beat1.story_id == beat2.story_id
    }
