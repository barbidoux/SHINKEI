"""Integration tests for Character repository."""
import pytest
from shinkei.repositories.user import UserRepository
from shinkei.repositories.world import WorldRepository
from shinkei.repositories.character import CharacterRepository
from shinkei.repositories.story import StoryRepository
from shinkei.repositories.story_beat import StoryBeatRepository
from shinkei.schemas.user import UserCreate
from shinkei.schemas.world import WorldCreate
from shinkei.schemas.character import CharacterCreate, CharacterUpdate
from shinkei.schemas.story import StoryCreate
from shinkei.schemas.story_beat import StoryBeatCreate


@pytest.mark.asyncio
async def test_character_crud(session):
    """Test Character CRUD operations."""
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    char_repo = CharacterRepository(session)

    # Create User and World
    user = await user_repo.create(UserCreate(email="char_test@example.com", name="CharTester", password_hash="hashed_pw"))
    world = await world_repo.create(user.id, WorldCreate(name="Fantasy World", chronology_mode="linear"))

    # Create Character
    char_data = CharacterCreate(
        name="Aragorn",
        description="<p>Ranger of the North</p>",
        aliases=["Strider", "Elessar"],
        role="Protagonist",
        importance="major",
        custom_metadata={"species": "Human", "age": 87}
    )
    character = await char_repo.create(world.id, char_data)

    assert character.id is not None
    assert character.world_id == world.id
    assert character.name == "Aragorn"
    assert character.importance.value == "major"
    assert "Strider" in character.aliases
    assert character.custom_metadata["age"] == 87

    # Get by ID
    fetched_char = await char_repo.get_by_id(character.id)
    assert fetched_char is not None
    assert fetched_char.id == character.id

    # Get by World and ID
    fetched_char_world = await char_repo.get_by_world_and_id(world.id, character.id)
    assert fetched_char_world is not None

    # List by World
    characters, total = await char_repo.list_by_world(world.id)
    assert total == 1
    assert len(characters) == 1
    assert characters[0].id == character.id

    # Update
    update_data = CharacterUpdate(
        description="<p>King of Gondor</p>",
        importance="major",
        aliases=["Strider", "Elessar", "King Elessar"]
    )
    updated_char = await char_repo.update(character.id, update_data)
    assert "King of Gondor" in updated_char.description
    assert len(updated_char.aliases) == 3

    # Delete
    deleted = await char_repo.delete(character.id)
    assert deleted is True

    # Verify Deletion
    deleted_char = await char_repo.get_by_id(character.id)
    assert deleted_char is None


@pytest.mark.asyncio
async def test_character_search_and_filters(session):
    """Test Character search and filtering."""
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    char_repo = CharacterRepository(session)

    user = await user_repo.create(UserCreate(email="char_search@example.com", name="SearchTester", password_hash="hashed_pw"))
    world = await world_repo.create(user.id, WorldCreate(name="Middle Earth", chronology_mode="linear"))

    # Create multiple characters
    await char_repo.create(world.id, CharacterCreate(name="Frodo", importance="major", role="Ring-bearer"))
    await char_repo.create(world.id, CharacterCreate(name="Sam", importance="major", role="Gardener"))
    await char_repo.create(world.id, CharacterCreate(name="Pippin", importance="minor", role="Fool of a Took"))
    await char_repo.create(world.id, CharacterCreate(name="Merry", importance="minor", role="Knight"))

    # Filter by importance
    major_chars, major_total = await char_repo.list_by_world(world.id, importance="major")
    assert major_total == 2

    minor_chars, minor_total = await char_repo.list_by_world(world.id, importance="minor")
    assert minor_total == 2

    # Search by name
    search_results, search_total = await char_repo.list_by_world(world.id, search="fro")
    assert search_total == 1
    assert search_results[0].name == "Frodo"

    # Search by name (case-insensitive)
    search_chars = await char_repo.search_by_name(world.id, "pip")
    assert len(search_chars) == 1
    assert search_chars[0].name == "Pippin"


@pytest.mark.asyncio
async def test_character_with_mention_count(session):
    """Test getting character with mention count."""
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    char_repo = CharacterRepository(session)
    story_repo = StoryRepository(session)
    beat_repo = StoryBeatRepository(session)

    user = await user_repo.create(UserCreate(email="char_mentions@example.com", name="MentionTester", password_hash="hashed_pw"))
    world = await world_repo.create(user.id, WorldCreate(name="Test World", chronology_mode="linear"))
    character = await char_repo.create(world.id, CharacterCreate(name="Hero", importance="major"))

    # Character with no mentions
    result = await char_repo.get_with_mention_count(character.id)
    assert result is not None
    char_obj, mention_count = result
    assert char_obj.id == character.id
    assert mention_count == 0


@pytest.mark.asyncio
async def test_character_first_appearance(session):
    """Test character first appearance beat tracking."""
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    char_repo = CharacterRepository(session)
    story_repo = StoryRepository(session)
    beat_repo = StoryBeatRepository(session)

    user = await user_repo.create(UserCreate(email="char_appearance@example.com", name="AppearanceTester", password_hash="hashed_pw"))
    world = await world_repo.create(user.id, WorldCreate(name="Story World", chronology_mode="linear"))
    story = await story_repo.create(world.id, StoryCreate(title="The Beginning"))
    beat = await beat_repo.create(story.id, StoryBeatCreate(type="scene", content="Hero appears"))

    # Create character with first appearance
    char_data = CharacterCreate(
        name="Hero",
        importance="major",
        first_appearance_beat_id=beat.id
    )
    character = await char_repo.create(world.id, char_data)

    assert character.first_appearance_beat_id == beat.id

    # Fetch and verify relationship is loaded
    fetched_char = await char_repo.get_by_id(character.id)
    assert fetched_char.first_appearance_beat_id == beat.id
