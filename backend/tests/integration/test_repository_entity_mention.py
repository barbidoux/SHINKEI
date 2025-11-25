"""Integration tests for EntityMention repository."""
import pytest
from shinkei.repositories.user import UserRepository
from shinkei.repositories.world import WorldRepository
from shinkei.repositories.story import StoryRepository
from shinkei.repositories.story_beat import StoryBeatRepository
from shinkei.repositories.character import CharacterRepository
from shinkei.repositories.location import LocationRepository
from shinkei.repositories.entity_mention import EntityMentionRepository
from shinkei.schemas.user import UserCreate
from shinkei.schemas.world import WorldCreate
from shinkei.schemas.story import StoryCreate
from shinkei.schemas.story_beat import StoryBeatCreate
from shinkei.schemas.character import CharacterCreate
from shinkei.schemas.location import LocationCreate
from shinkei.schemas.entity_mention import EntityMentionCreate, EntityMentionUpdate


@pytest.mark.asyncio
async def test_entity_mention_crud(session):
    """Test EntityMention CRUD operations."""
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)
    beat_repo = StoryBeatRepository(session)
    char_repo = CharacterRepository(session)
    mention_repo = EntityMentionRepository(session)

    # Setup
    user = await user_repo.create(UserCreate(email="mention_test@example.com", name="MentionTester", password_hash="hashed_pw"))
    world = await world_repo.create(user.id, WorldCreate(name="Test World", chronology_mode="linear"))
    character = await char_repo.create(world.id, CharacterCreate(name="Hero", importance="major"))
    story = await story_repo.create(world.id, StoryCreate(title="Test Story"))
    beat = await beat_repo.create(story.id, StoryBeatCreate(type="scene", content="Hero arrives"))

    # Create Mention
    mention_data = EntityMentionCreate(
        entity_type="character",
        entity_id=character.id,
        mention_type="explicit",
        confidence=0.95,
        context_snippet="The hero walked into the room",
        detected_by="ai"
    )
    mention = await mention_repo.create(beat.id, mention_data)

    assert mention.id is not None
    assert mention.story_beat_id == beat.id
    assert mention.entity_type.value == "character"
    assert mention.entity_id == character.id
    assert mention.confidence == 0.95

    # Get by ID
    fetched_mention = await mention_repo.get_by_id(mention.id)
    assert fetched_mention is not None
    assert fetched_mention.id == mention.id

    # List by Beat
    mentions, total = await mention_repo.list_by_beat(beat.id)
    assert total == 1
    assert len(mentions) == 1
    assert mentions[0].id == mention.id

    # List by Entity
    entity_mentions = await mention_repo.list_by_entity(character.id, "character")
    assert len(entity_mentions) == 1
    assert entity_mentions[0].entity_id == character.id

    # Update
    update_data = EntityMentionUpdate(
        mention_type="implicit",
        confidence=0.85,
        context_snippet="The brave one entered"
    )
    updated_mention = await mention_repo.update(mention.id, update_data)
    assert updated_mention.mention_type.value == "implicit"
    assert updated_mention.confidence == 0.85

    # Delete
    deleted = await mention_repo.delete(mention.id)
    assert deleted is True

    # Verify Deletion
    deleted_mention = await mention_repo.get_by_id(mention.id)
    assert deleted_mention is None


@pytest.mark.asyncio
async def test_entity_mention_bulk_create(session):
    """Test bulk creation of entity mentions."""
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)
    beat_repo = StoryBeatRepository(session)
    char_repo = CharacterRepository(session)
    loc_repo = LocationRepository(session)
    mention_repo = EntityMentionRepository(session)

    # Setup
    user = await user_repo.create(UserCreate(email="bulk_mention@example.com", name="BulkTester", password_hash="hashed_pw"))
    world = await world_repo.create(user.id, WorldCreate(name="Test World", chronology_mode="linear"))
    hero = await char_repo.create(world.id, CharacterCreate(name="Hero", importance="major"))
    villain = await char_repo.create(world.id, CharacterCreate(name="Villain", importance="major"))
    castle = await loc_repo.create(world.id, LocationCreate(name="Castle", location_type="building"))
    story = await story_repo.create(world.id, StoryCreate(title="Test Story"))
    beat = await beat_repo.create(story.id, StoryBeatCreate(type="scene", content="Battle at castle"))

    # Bulk create mentions
    mentions_data = [
        EntityMentionCreate(entity_type="character", entity_id=hero.id, mention_type="explicit", detected_by="ai"),
        EntityMentionCreate(entity_type="character", entity_id=villain.id, mention_type="explicit", detected_by="ai"),
        EntityMentionCreate(entity_type="location", entity_id=castle.id, mention_type="explicit", detected_by="ai")
    ]
    mentions = await mention_repo.bulk_create(beat.id, mentions_data)

    assert len(mentions) == 3
    assert all(m.story_beat_id == beat.id for m in mentions)

    # Verify all were created
    beat_mentions, total = await mention_repo.list_by_beat(beat.id)
    assert total == 3


@pytest.mark.asyncio
async def test_entity_timeline(session):
    """Test entity timeline across multiple beats."""
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)
    beat_repo = StoryBeatRepository(session)
    char_repo = CharacterRepository(session)
    mention_repo = EntityMentionRepository(session)

    # Setup
    user = await user_repo.create(UserCreate(email="timeline@example.com", name="TimelineTester", password_hash="hashed_pw"))
    world = await world_repo.create(user.id, WorldCreate(name="Test World", chronology_mode="linear"))
    character = await char_repo.create(world.id, CharacterCreate(name="Protagonist", importance="major"))
    story = await story_repo.create(world.id, StoryCreate(title="Test Story"))

    # Create multiple beats with mentions
    beat1 = await beat_repo.create(story.id, StoryBeatCreate(seq_in_story=1, type="scene", content="Introduction"))
    beat2 = await beat_repo.create(story.id, StoryBeatCreate(seq_in_story=2, type="scene", content="Rising Action"))
    beat3 = await beat_repo.create(story.id, StoryBeatCreate(seq_in_story=3, type="scene", content="Climax"))

    # Create mentions
    await mention_repo.create(beat1.id, EntityMentionCreate(
        entity_type="character",
        entity_id=character.id,
        mention_type="explicit",
        detected_by="user"
    ))
    await mention_repo.create(beat2.id, EntityMentionCreate(
        entity_type="character",
        entity_id=character.id,
        mention_type="explicit",
        detected_by="user"
    ))
    await mention_repo.create(beat3.id, EntityMentionCreate(
        entity_type="character",
        entity_id=character.id,
        mention_type="explicit",
        detected_by="user"
    ))

    # Get timeline
    timeline = await mention_repo.get_timeline_for_entity(character.id, "character")

    assert len(timeline) == 3
    # Timeline should be ordered by seq_in_story
    assert timeline[0].seq_in_story == 1
    assert timeline[1].seq_in_story == 2
    assert timeline[2].seq_in_story == 3


@pytest.mark.asyncio
async def test_location_mentions(session):
    """Test mentions for locations."""
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)
    beat_repo = StoryBeatRepository(session)
    loc_repo = LocationRepository(session)
    mention_repo = EntityMentionRepository(session)

    # Setup
    user = await user_repo.create(UserCreate(email="loc_mention@example.com", name="LocMentionTester", password_hash="hashed_pw"))
    world = await world_repo.create(user.id, WorldCreate(name="Test World", chronology_mode="linear"))
    location = await loc_repo.create(world.id, LocationCreate(name="Forest", location_type="forest"))
    story = await story_repo.create(world.id, StoryCreate(title="Test Story"))
    beat = await beat_repo.create(story.id, StoryBeatCreate(type="scene", content="Journey through forest"))

    # Create location mention
    mention_data = EntityMentionCreate(
        entity_type="location",
        entity_id=location.id,
        mention_type="explicit",
        context_snippet="They entered the dark forest",
        detected_by="ai"
    )
    mention = await mention_repo.create(beat.id, mention_data)

    assert mention.entity_type.value == "location"
    assert mention.entity_id == location.id

    # Get mentions for location
    location_mentions = await mention_repo.list_by_entity(location.id, "location")
    assert len(location_mentions) == 1


@pytest.mark.asyncio
async def test_delete_by_beat(session):
    """Test deleting all mentions for a beat."""
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)
    beat_repo = StoryBeatRepository(session)
    char_repo = CharacterRepository(session)
    mention_repo = EntityMentionRepository(session)

    # Setup
    user = await user_repo.create(UserCreate(email="delete_beat@example.com", name="DeleteTester", password_hash="hashed_pw"))
    world = await world_repo.create(user.id, WorldCreate(name="Test World", chronology_mode="linear"))
    char1 = await char_repo.create(world.id, CharacterCreate(name="Char1", importance="major"))
    char2 = await char_repo.create(world.id, CharacterCreate(name="Char2", importance="major"))
    story = await story_repo.create(world.id, StoryCreate(title="Test Story"))
    beat = await beat_repo.create(story.id, StoryBeatCreate(type="scene", content="Scene"))

    # Create mentions
    await mention_repo.create(beat.id, EntityMentionCreate(entity_type="character", entity_id=char1.id, mention_type="explicit", detected_by="user"))
    await mention_repo.create(beat.id, EntityMentionCreate(entity_type="character", entity_id=char2.id, mention_type="explicit", detected_by="user"))

    # Verify mentions exist
    mentions_before, total_before = await mention_repo.list_by_beat(beat.id)
    assert total_before == 2

    # Delete all mentions for beat
    deleted = await mention_repo.delete_by_beat(beat.id)
    assert deleted is True

    # Verify all deleted
    mentions_after, total_after = await mention_repo.list_by_beat(beat.id)
    assert total_after == 0
