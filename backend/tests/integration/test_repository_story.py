"""Integration tests for Story repository."""
import pytest
from shinkei.repositories.story import StoryRepository
from shinkei.repositories.world import WorldRepository
from shinkei.repositories.user import UserRepository
from shinkei.schemas.story import StoryCreate, StoryUpdate
from shinkei.schemas.world import WorldCreate, WorldLaws
from shinkei.schemas.user import UserCreate, UserSettings


@pytest.mark.asyncio
async def test_story_create(session):
    """Test creating a story."""
    # Setup: Create user and world
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)

    user = await user_repo.create(UserCreate(
        email="story@test.com",
        name="Story Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    # Create story
    story_data = StoryCreate(
        title="Test Story",
        synopsis="A test story synopsis",
        theme="Adventure",
        status="draft"
    )

    story = await story_repo.create(world.id, story_data)

    assert story.id is not None
    assert story.world_id == world.id
    assert story.title == "Test Story"
    assert story.synopsis == "A test story synopsis"
    assert story.theme == "Adventure"
    assert story.status.value == "draft"
    assert story.created_at is not None
    assert story.updated_at is not None


@pytest.mark.asyncio
async def test_story_get_by_id(session):
    """Test getting a story by ID."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)

    user = await user_repo.create(UserCreate(
        email="getbyid@test.com",
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

    # Get by ID
    fetched_story = await story_repo.get_by_id(story.id)

    assert fetched_story is not None
    assert fetched_story.id == story.id
    assert fetched_story.title == "Test Story"


@pytest.mark.asyncio
async def test_story_get_by_id_not_found(session):
    """Test getting a story with non-existent ID."""
    story_repo = StoryRepository(session)

    fetched_story = await story_repo.get_by_id("non-existent-uuid")

    assert fetched_story is None


@pytest.mark.asyncio
async def test_story_list_by_world(session):
    """Test listing stories for a world."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)

    user = await user_repo.create(UserCreate(
        email="listbyworld@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    # Create multiple stories
    for i in range(5):
        await story_repo.create(world.id, StoryCreate(
            title=f"Story {i}",
            status="draft"
        ))

    # List stories
    stories, total = await story_repo.list_by_world(world.id)

    assert total == 5
    assert len(stories) == 5
    # Stories should be ordered by updated_at desc
    assert all(story.world_id == world.id for story in stories)


@pytest.mark.asyncio
async def test_story_list_by_world_with_pagination(session):
    """Test listing stories with pagination."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)

    user = await user_repo.create(UserCreate(
        email="pagination@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    # Create 10 stories
    for i in range(10):
        await story_repo.create(world.id, StoryCreate(
            title=f"Story {i}",
            status="draft"
        ))

    # Test pagination - first page
    stories_page1, total = await story_repo.list_by_world(world.id, skip=0, limit=3)
    assert total == 10
    assert len(stories_page1) == 3

    # Test pagination - second page
    stories_page2, total = await story_repo.list_by_world(world.id, skip=3, limit=3)
    assert total == 10
    assert len(stories_page2) == 3

    # Ensure different stories
    page1_ids = {s.id for s in stories_page1}
    page2_ids = {s.id for s in stories_page2}
    assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.asyncio
async def test_story_list_by_world_empty(session):
    """Test listing stories for a world with no stories."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)

    user = await user_repo.create(UserCreate(
        email="emptylist@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Empty World",
        laws=WorldLaws()
    ))

    # List stories
    stories, total = await story_repo.list_by_world(world.id)

    assert total == 0
    assert len(stories) == 0


@pytest.mark.asyncio
async def test_story_update(session):
    """Test updating a story."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)

    user = await user_repo.create(UserCreate(
        email="update@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    story = await story_repo.create(world.id, StoryCreate(
        title="Original Title",
        synopsis="Original synopsis",
        theme="Original theme",
        status="draft"
    ))

    # Update story
    update_data = StoryUpdate(
        title="Updated Title",
        synopsis="Updated synopsis",
        theme="Updated theme",
        status="active"
    )

    updated_story = await story_repo.update(story.id, update_data)

    assert updated_story is not None
    assert updated_story.id == story.id
    assert updated_story.title == "Updated Title"
    assert updated_story.synopsis == "Updated synopsis"
    assert updated_story.theme == "Updated theme"
    assert updated_story.status.value == "active"


@pytest.mark.asyncio
async def test_story_update_partial(session):
    """Test partial update of a story."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)

    user = await user_repo.create(UserCreate(
        email="partialupdate@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    story = await story_repo.create(world.id, StoryCreate(
        title="Original Title",
        synopsis="Original synopsis",
        status="draft"
    ))

    # Update only title
    update_data = StoryUpdate(title="New Title Only")

    updated_story = await story_repo.update(story.id, update_data)

    assert updated_story.title == "New Title Only"
    assert updated_story.synopsis == "Original synopsis"  # Unchanged
    assert updated_story.status.value == "draft"  # Unchanged


@pytest.mark.asyncio
async def test_story_update_not_found(session):
    """Test updating a non-existent story."""
    story_repo = StoryRepository(session)

    update_data = StoryUpdate(title="Updated Title")
    updated_story = await story_repo.update("non-existent-uuid", update_data)

    assert updated_story is None


@pytest.mark.asyncio
async def test_story_delete(session):
    """Test deleting a story."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)

    user = await user_repo.create(UserCreate(
        email="delete@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    story = await story_repo.create(world.id, StoryCreate(
        title="To Delete",
        status="draft"
    ))

    story_id = story.id

    # Delete story
    result = await story_repo.delete(story_id)
    assert result is True

    # Verify deletion
    deleted_story = await story_repo.get_by_id(story_id)
    assert deleted_story is None


@pytest.mark.asyncio
async def test_story_delete_not_found(session):
    """Test deleting a non-existent story."""
    story_repo = StoryRepository(session)

    result = await story_repo.delete("non-existent-uuid")
    assert result is False


@pytest.mark.asyncio
async def test_story_all_status_values(session):
    """Test creating stories with all status enum values."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)

    user = await user_repo.create(UserCreate(
        email="statustest@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    # Test all status values
    statuses = ["draft", "active", "completed", "archived"]

    for status in statuses:
        story = await story_repo.create(world.id, StoryCreate(
            title=f"Story {status}",
            status=status
        ))
        assert story.status.value == status


@pytest.mark.asyncio
async def test_story_cascade_deletion_with_world(session):
    """Test that stories are deleted when world is deleted."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    story_repo = StoryRepository(session)

    user = await user_repo.create(UserCreate(
        email="cascade@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    story = await story_repo.create(world.id, StoryCreate(
        title="Cascade Test",
        status="draft"
    ))

    story_id = story.id

    # Delete world
    await world_repo.delete(world.id)

    # Story should be deleted
    deleted_story = await story_repo.get_by_id(story_id)
    assert deleted_story is None
