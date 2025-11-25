"""API Router configuration."""
from fastapi import APIRouter
from shinkei.api.v1.endpoints import (
    users, worlds, world_events, stories, story_beats,
    generation, narrative, auth, health,
    characters, locations, entity_mentions, character_relationships,
    entity_generation
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(worlds.router, prefix="/worlds", tags=["worlds"])
api_router.include_router(world_events.router, tags=["world-events"])
api_router.include_router(stories.router, tags=["stories"])
api_router.include_router(story_beats.router, tags=["story-beats"])
api_router.include_router(generation.router, prefix="/generation", tags=["generation"])
api_router.include_router(narrative.router, tags=["narrative"])  # New narrative generation endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Phase 6: Entity Management
api_router.include_router(characters.router, prefix="/worlds", tags=["characters"])
api_router.include_router(locations.router, prefix="/worlds", tags=["locations"])
api_router.include_router(entity_mentions.router, tags=["entity-mentions"])
api_router.include_router(character_relationships.router, prefix="/worlds", tags=["character-relationships"])

# Phase 11: AI-Powered Entity Generation
api_router.include_router(entity_generation.router, tags=["entity-generation"])
