"""Integration tests for StoryBeat repository."""
import pytest
from shinkei.repositories.story_beat import StoryBeatRepository
from shinkei.repositories.story import StoryRepository
from shinkei.repositories.world import WorldRepository
from shinkei.repositories.world_event import WorldEventRepository
from shinkei.repositories.user import UserRepository
from shinkei.schemas.story_beat import StoryBeatCreate, StoryBeatUpdate
from shinkei.schemas.story import StoryCreate
from shinkei.schemas.world import WorldCreate, WorldLaws
from shinkei.schemas.world_event import WorldEventCreate
from shinkei.schemas.user import UserCreate, UserSettings


@pytest.mark.asyncio
async def test_story_beat_create(session):
    """Test creating a story beat."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)
    beat_repo = StoryBeatRepository(session)

    user = await user_repo.create(UserCreate(
        email="beat@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    story = await story_repo.create(world.id, StoryCreate(
        title="Test Story",
        status="draft"
    ))

    # Create beat
    beat_data = StoryBeatCreate(
        order_index=1,
        content="This is the first beat of the story.",
        type="scene"
    )

    beat = await beat_repo.create(story.id, beat_data)

    assert beat.id is not None
    assert beat.story_id == story.id
    assert beat.order_index == 1
    assert beat.content == "This is the first beat of the story."
    assert beat.type.value == "scene"
    assert beat.world_event_id is None
    assert beat.created_at is not None
    assert beat.updated_at is not None


@pytest.mark.asyncio
async def test_story_beat_create_with_world_event(session):
    """Test creating a story beat linked to a world event."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)
    event_repo = WorldEventRepository(session)
    beat_repo = StoryBeatRepository(session)

    user = await user_repo.create(UserCreate(
        email="beatlinked@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    story = await story_repo.create(world.id, StoryCreate(
        title="Test Story",
        status="draft"
    ))

    event = await event_repo.create(world.id, WorldEventCreate(
        t=100.0,
        label_time="Day 100",
        type="meeting",
        summary="An important meeting"
    ))

    # Create beat linked to event
    beat_data = StoryBeatCreate(
        order_index=1,
        content="The characters meet at the designated location.",
        type="scene",
        world_event_id=event.id
    )

    beat = await beat_repo.create(story.id, beat_data)

    assert beat.world_event_id == event.id


@pytest.mark.asyncio
async def test_story_beat_get_by_id(session):
    """Test getting a story beat by ID."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)
    beat_repo = StoryBeatRepository(session)

    user = await user_repo.create(UserCreate(
        email="getbeat@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    story = await story_repo.create(world.id, StoryCreate(
        title="Test Story",
        status="draft"
    ))

    beat = await beat_repo.create(story.id, StoryBeatCreate(
        order_index=1,
        content="Test beat",
        type="scene"
    ))

    # Get by ID
    fetched_beat = await beat_repo.get_by_id(beat.id)

    assert fetched_beat is not None
    assert fetched_beat.id == beat.id
    assert fetched_beat.content == "Test beat"


@pytest.mark.asyncio
async def test_story_beat_get_by_id_not_found(session):
    """Test getting a beat with non-existent ID."""
    beat_repo = StoryBeatRepository(session)

    fetched_beat = await beat_repo.get_by_id("non-existent-uuid")

    assert fetched_beat is None


@pytest.mark.asyncio
async def test_story_beat_list_by_story(session):
    """Test listing beats for a story."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)
    beat_repo = StoryBeatRepository(session)

    user = await user_repo.create(UserCreate(
        email="listbeats@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    story = await story_repo.create(world.id, StoryCreate(
        title="Test Story",
        status="draft"
    ))

    # Create multiple beats
    for i in range(1, 6):
        await beat_repo.create(story.id, StoryBeatCreate(
            order_index=i,
            content=f"Beat {i}",
            type="scene"
        ))

    # List beats
    beats, total = await beat_repo.list_by_story(story.id)

    assert total == 5
    assert len(beats) == 5
    # Beats should be ordered by order_index asc
    for i, beat in enumerate(beats, start=1):
        assert beat.order_index == i
        assert beat.story_id == story.id


@pytest.mark.asyncio
async def test_story_beat_list_by_story_with_pagination(session):
    """Test listing beats with pagination."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)
    beat_repo = StoryBeatRepository(session)

    user = await user_repo.create(UserCreate(
        email="beatpagination@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    story = await story_repo.create(world.id, StoryCreate(
        title="Test Story",
        status="draft"
    ))

    # Create 10 beats
    for i in range(1, 11):
        await beat_repo.create(story.id, StoryBeatCreate(
            order_index=i,
            content=f"Beat {i}",
            type="scene"
        ))

    # Test pagination - first page
    beats_page1, total = await beat_repo.list_by_story(story.id, skip=0, limit=3)
    assert total == 10
    assert len(beats_page1) == 3
    assert beats_page1[0].order_index == 1

    # Test pagination - second page
    beats_page2, total = await beat_repo.list_by_story(story.id, skip=3, limit=3)
    assert total == 10
    assert len(beats_page2) == 3
    assert beats_page2[0].order_index == 4


@pytest.mark.asyncio
async def test_story_beat_list_by_story_empty(session):
    """Test listing beats for a story with no beats."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)
    beat_repo = StoryBeatRepository(session)

    user = await user_repo.create(UserCreate(
        email="emptybeats@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    story = await story_repo.create(world.id, StoryCreate(
        title="Empty Story",
        status="draft"
    ))

    # List beats
    beats, total = await beat_repo.list_by_story(story.id)

    assert total == 0
    assert len(beats) == 0


@pytest.mark.asyncio
async def test_story_beat_update(session):
    """Test updating a story beat."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)
    beat_repo = StoryBeatRepository(session)

    user = await user_repo.create(UserCreate(
        email="updatebeat@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    story = await story_repo.create(world.id, StoryCreate(
        title="Test Story",
        status="draft"
    ))

    beat = await beat_repo.create(story.id, StoryBeatCreate(
        order_index=1,
        content="Original content",
        type="scene"
    ))

    # Update beat
    update_data = StoryBeatUpdate(
        content="Updated content",
        type="summary",
        order_index=2
    )

    updated_beat = await beat_repo.update(beat.id, update_data)

    assert updated_beat is not None
    assert updated_beat.id == beat.id
    assert updated_beat.content == "Updated content"
    assert updated_beat.type.value == "summary"
    assert updated_beat.order_index == 2


@pytest.mark.asyncio
async def test_story_beat_update_partial(session):
    """Test partial update of a story beat."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)
    beat_repo = StoryBeatRepository(session)

    user = await user_repo.create(UserCreate(
        email="partialbeat@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    story = await story_repo.create(world.id, StoryCreate(
        title="Test Story",
        status="draft"
    ))

    beat = await beat_repo.create(story.id, StoryBeatCreate(
        order_index=5,
        content="Original content",
        type="scene"
    ))

    # Update only content
    update_data = StoryBeatUpdate(content="New content only")

    updated_beat = await beat_repo.update(beat.id, update_data)

    assert updated_beat.content == "New content only"
    assert updated_beat.order_index == 5  # Unchanged
    assert updated_beat.type.value == "scene"  # Unchanged


@pytest.mark.asyncio
async def test_story_beat_update_not_found(session):
    """Test updating a non-existent beat."""
    beat_repo = StoryBeatRepository(session)

    update_data = StoryBeatUpdate(content="Updated content")
    updated_beat = await beat_repo.update("non-existent-uuid", update_data)

    assert updated_beat is None


@pytest.mark.asyncio
async def test_story_beat_delete(session):
    """Test deleting a story beat."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)
    beat_repo = StoryBeatRepository(session)

    user = await user_repo.create(UserCreate(
        email="deletebeat@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    story = await story_repo.create(world.id, StoryCreate(
        title="Test Story",
        status="draft"
    ))

    beat = await beat_repo.create(story.id, StoryBeatCreate(
        order_index=1,
        content="To delete",
        type="scene"
    ))

    beat_id = beat.id

    # Delete beat
    result = await beat_repo.delete(beat_id)
    assert result is True

    # Verify deletion
    deleted_beat = await beat_repo.get_by_id(beat_id)
    assert deleted_beat is None


@pytest.mark.asyncio
async def test_story_beat_delete_not_found(session):
    """Test deleting a non-existent beat."""
    beat_repo = StoryBeatRepository(session)

    result = await beat_repo.delete("non-existent-uuid")
    assert result is False


@pytest.mark.asyncio
async def test_story_beat_all_type_values(session):
    """Test creating beats with all type enum values."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)
    beat_repo = StoryBeatRepository(session)

    user = await user_repo.create(UserCreate(
        email="beattype@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    story = await story_repo.create(world.id, StoryCreate(
        title="Test Story",
        status="draft"
    ))

    # Test all beat type values
    beat_types = ["scene", "summary", "note"]

    for i, beat_type in enumerate(beat_types, start=1):
        beat = await beat_repo.create(story.id, StoryBeatCreate(
            order_index=i,
            content=f"Beat of type {beat_type}",
            type=beat_type
        ))
        assert beat.type.value == beat_type


@pytest.mark.asyncio
async def test_story_beat_reorder(session):
    """Test reordering beats in a story."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)
    beat_repo = StoryBeatRepository(session)

    user = await user_repo.create(UserCreate(
        email="reorder@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    story = await story_repo.create(world.id, StoryCreate(
        title="Test Story",
        status="draft"
    ))

    # Create beats in order
    beat1 = await beat_repo.create(story.id, StoryBeatCreate(
        order_index=1, content="Beat 1", type="scene"
    ))
    beat2 = await beat_repo.create(story.id, StoryBeatCreate(
        order_index=2, content="Beat 2", type="scene"
    ))
    beat3 = await beat_repo.create(story.id, StoryBeatCreate(
        order_index=3, content="Beat 3", type="scene"
    ))

    # Reorder: 3, 1, 2
    new_order = [beat3.id, beat1.id, beat2.id]
    result = await beat_repo.reorder(story.id, new_order)

    assert result is True

    # Verify new order
    beats, _ = await beat_repo.list_by_story(story.id)
    assert beats[0].id == beat3.id
    assert beats[0].order_index == 1
    assert beats[1].id == beat1.id
    assert beats[1].order_index == 2
    assert beats[2].id == beat2.id
    assert beats[2].order_index == 3


@pytest.mark.asyncio
async def test_story_beat_cascade_deletion_with_story(session):
    """Test that beats are deleted when story is deleted."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)
    beat_repo = StoryBeatRepository(session)

    user = await user_repo.create(UserCreate(
        email="cascadebeat@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    story = await story_repo.create(world.id, StoryCreate(
        title="Test Story",
        status="draft"
    ))

    beat = await beat_repo.create(story.id, StoryBeatCreate(
        order_index=1,
        content="Cascade test",
        type="scene"
    ))

    beat_id = beat.id

    # Delete story
    await story_repo.delete(story.id)

    # Beat should be deleted
    deleted_beat = await beat_repo.get_by_id(beat_id)
    assert deleted_beat is None
