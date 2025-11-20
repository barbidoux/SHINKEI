"""Integration tests for WorldEvent repository."""
import pytest
from shinkei.repositories.world_event import WorldEventRepository
from shinkei.repositories.world import WorldRepository
from shinkei.repositories.user import UserRepository
from shinkei.schemas.world_event import WorldEventCreate, WorldEventUpdate
from shinkei.schemas.world import WorldCreate, WorldLaws
from shinkei.schemas.user import UserCreate, UserSettings


@pytest.mark.asyncio
async def test_world_event_create(session):
    """Test creating a world event."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    event_repo = WorldEventRepository(session)

    user = await user_repo.create(UserCreate(
        email="event@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    # Create event
    event_data = WorldEventCreate(
        t=100.0,
        label_time="Day 100",
        location_id="test-location-uuid",
        type="meeting",
        summary="An important meeting at the station",
        tags=["important", "meeting"]
    )

    event = await event_repo.create(world.id, event_data)

    assert event.id is not None
    assert event.world_id == world.id
    assert event.t == 100.0
    assert event.label_time == "Day 100"
    assert event.location_id == "test-location-uuid"
    assert event.type == "meeting"
    assert event.summary == "An important meeting at the station"
    assert event.tags == ["important", "meeting"]
    assert event.created_at is not None
    assert event.updated_at is not None


@pytest.mark.asyncio
async def test_world_event_create_minimal(session):
    """Test creating a world event with minimal data."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    event_repo = WorldEventRepository(session)

    user = await user_repo.create(UserCreate(
        email="eventminimal@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    # Create event with minimal data
    event_data = WorldEventCreate(
        t=0.0,
        label_time="Genesis",
        type="genesis",
        summary="The beginning"
    )

    event = await event_repo.create(world.id, event_data)

    assert event.t == 0.0
    assert event.label_time == "Genesis"
    assert event.type == "genesis"
    assert event.summary == "The beginning"
    assert event.location_id is None
    assert event.tags == []


@pytest.mark.asyncio
async def test_world_event_get_by_id(session):
    """Test getting a world event by ID."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    event_repo = WorldEventRepository(session)

    user = await user_repo.create(UserCreate(
        email="getevent@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    event = await event_repo.create(world.id, WorldEventCreate(
        t=50.0,
        label_time="Log 050",
        type="discovery",
        summary="Found something"
    ))

    # Get by ID
    fetched_event = await event_repo.get_by_id(event.id)

    assert fetched_event is not None
    assert fetched_event.id == event.id
    assert fetched_event.t == 50.0
    assert fetched_event.label_time == "Log 050"


@pytest.mark.asyncio
async def test_world_event_get_by_id_not_found(session):
    """Test getting an event with non-existent ID."""
    event_repo = WorldEventRepository(session)

    fetched_event = await event_repo.get_by_id("non-existent-uuid")

    assert fetched_event is None


@pytest.mark.asyncio
async def test_world_event_list_by_world(session):
    """Test listing events for a world."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    event_repo = WorldEventRepository(session)

    user = await user_repo.create(UserCreate(
        email="listevents@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    # Create multiple events with different time values
    times = [0.0, 10.5, 25.0, 42.3, 100.0]
    for t in times:
        await event_repo.create(world.id, WorldEventCreate(
            t=t,
            label_time=f"Time {t}",
            type="test",
            summary=f"Event at {t}"
        ))

    # List events
    events, total = await event_repo.list_by_world(world.id)

    assert total == 5
    assert len(events) == 5
    # Events should be ordered by t asc
    assert events[0].t == 0.0
    assert events[1].t == 10.5
    assert events[2].t == 25.0
    assert events[3].t == 42.3
    assert events[4].t == 100.0
    assert all(event.world_id == world.id for event in events)


@pytest.mark.asyncio
async def test_world_event_list_by_world_with_pagination(session):
    """Test listing events with pagination."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    event_repo = WorldEventRepository(session)

    user = await user_repo.create(UserCreate(
        email="eventpagination@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    # Create 10 events
    for i in range(10):
        await event_repo.create(world.id, WorldEventCreate(
            t=float(i),
            label_time=f"Event {i}",
            type="test",
            summary=f"Test event {i}"
        ))

    # Test pagination - first page
    events_page1, total = await event_repo.list_by_world(world.id, skip=0, limit=3)
    assert total == 10
    assert len(events_page1) == 3
    assert events_page1[0].t == 0.0

    # Test pagination - second page
    events_page2, total = await event_repo.list_by_world(world.id, skip=3, limit=3)
    assert total == 10
    assert len(events_page2) == 3
    assert events_page2[0].t == 3.0


@pytest.mark.asyncio
async def test_world_event_list_by_world_empty(session):
    """Test listing events for a world with no events."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    event_repo = WorldEventRepository(session)

    user = await user_repo.create(UserCreate(
        email="emptyevents@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Empty World",
        laws=WorldLaws()
    ))

    # List events
    events, total = await event_repo.list_by_world(world.id)

    assert total == 0
    assert len(events) == 0


@pytest.mark.asyncio
async def test_world_event_update(session):
    """Test updating a world event."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    event_repo = WorldEventRepository(session)

    user = await user_repo.create(UserCreate(
        email="updateevent@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    event = await event_repo.create(world.id, WorldEventCreate(
        t=50.0,
        label_time="Original Time",
        type="original",
        summary="Original summary",
        tags=["original"]
    ))

    # Update event
    update_data = WorldEventUpdate(
        t=75.0,
        label_time="Updated Time",
        type="updated",
        summary="Updated summary",
        tags=["updated", "modified"]
    )

    updated_event = await event_repo.update(event.id, update_data)

    assert updated_event is not None
    assert updated_event.id == event.id
    assert updated_event.t == 75.0
    assert updated_event.label_time == "Updated Time"
    assert updated_event.type == "updated"
    assert updated_event.summary == "Updated summary"
    assert updated_event.tags == ["updated", "modified"]


@pytest.mark.asyncio
async def test_world_event_update_partial(session):
    """Test partial update of a world event."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    event_repo = WorldEventRepository(session)

    user = await user_repo.create(UserCreate(
        email="partialevent@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    event = await event_repo.create(world.id, WorldEventCreate(
        t=50.0,
        label_time="Original Time",
        type="original",
        summary="Original summary"
    ))

    # Update only summary
    update_data = WorldEventUpdate(summary="New summary only")

    updated_event = await event_repo.update(event.id, update_data)

    assert updated_event.summary == "New summary only"
    assert updated_event.t == 50.0  # Unchanged
    assert updated_event.label_time == "Original Time"  # Unchanged
    assert updated_event.type == "original"  # Unchanged


@pytest.mark.asyncio
async def test_world_event_update_not_found(session):
    """Test updating a non-existent event."""
    event_repo = WorldEventRepository(session)

    update_data = WorldEventUpdate(summary="Updated summary")
    updated_event = await event_repo.update("non-existent-uuid", update_data)

    assert updated_event is None


@pytest.mark.asyncio
async def test_world_event_delete(session):
    """Test deleting a world event."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    event_repo = WorldEventRepository(session)

    user = await user_repo.create(UserCreate(
        email="deleteevent@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    event = await event_repo.create(world.id, WorldEventCreate(
        t=100.0,
        label_time="To Delete",
        type="test",
        summary="Event to delete"
    ))

    event_id = event.id

    # Delete event
    result = await event_repo.delete(event_id)
    assert result is True

    # Verify deletion
    deleted_event = await event_repo.get_by_id(event_id)
    assert deleted_event is None


@pytest.mark.asyncio
async def test_world_event_delete_not_found(session):
    """Test deleting a non-existent event."""
    event_repo = WorldEventRepository(session)

    result = await event_repo.delete("non-existent-uuid")
    assert result is False


@pytest.mark.asyncio
async def test_world_event_temporal_ordering(session):
    """Test that events are properly ordered by time."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    event_repo = WorldEventRepository(session)

    user = await user_repo.create(UserCreate(
        email="temporal@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    # Create events in random order
    times = [100.0, 5.5, 42.0, 0.0, 75.3]
    for t in times:
        await event_repo.create(world.id, WorldEventCreate(
            t=t,
            label_time=f"Time {t}",
            type="test",
            summary=f"Event at {t}"
        ))

    # List events - should be ordered by t
    events, _ = await event_repo.list_by_world(world.id)

    sorted_times = sorted(times)
    for i, event in enumerate(events):
        assert event.t == sorted_times[i]


@pytest.mark.asyncio
async def test_world_event_tags_handling(session):
    """Test that tags array is properly handled."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    event_repo = WorldEventRepository(session)

    user = await user_repo.create(UserCreate(
        email="tags@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    # Create event with multiple tags
    tags = ["important", "combat", "character_death", "plot_twist"]
    event = await event_repo.create(world.id, WorldEventCreate(
        t=50.0,
        label_time="Critical Event",
        type="combat",
        summary="Major battle",
        tags=tags
    ))

    # Fetch and verify
    fetched_event = await event_repo.get_by_id(event.id)
    assert fetched_event.tags == tags
    assert len(fetched_event.tags) == 4


@pytest.mark.asyncio
async def test_world_event_cascade_deletion_with_world(session):
    """Test that events are deleted when world is deleted."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    event_repo = WorldEventRepository(session)

    user = await user_repo.create(UserCreate(
        email="cascadeevent@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    event = await event_repo.create(world.id, WorldEventCreate(
        t=1.0,
        label_time="Cascade Test",
        type="test",
        summary="Event to cascade delete"
    ))

    event_id = event.id

    # Delete world
    await world_repo.delete(world.id)

    # Event should be deleted
    deleted_event = await event_repo.get_by_id(event_id)
    assert deleted_event is None


@pytest.mark.asyncio
async def test_world_event_with_float_time(session):
    """Test that events support float time values."""
    # Setup
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    event_repo = WorldEventRepository(session)

    user = await user_repo.create(UserCreate(
        email="floattime@test.com",
        name="Test User",
        settings=UserSettings()
    ))

    world = await world_repo.create(user.id, WorldCreate(
        name="Test World",
        laws=WorldLaws()
    ))

    # Create event with precise float time
    event = await event_repo.create(world.id, WorldEventCreate(
        t=42.567891,
        label_time="Precise Time",
        type="test",
        summary="Precise timing test"
    ))

    assert event.t == 42.567891

    # Fetch and verify precision maintained
    fetched_event = await event_repo.get_by_id(event.id)
    assert fetched_event.t == 42.567891
