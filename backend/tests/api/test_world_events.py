"""Tests for WorldEvent API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from datetime import datetime

from shinkei.main import app
from shinkei.models.user import User
from shinkei.models.world import World
from shinkei.models.world_event import WorldEvent
from shinkei.config import settings
from shinkei.auth.dependencies import get_current_user

@pytest.mark.asyncio(loop_scope="session")
async def test_create_world_event():
    """Test creating a new world event."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")
    
    mock_event = WorldEvent(
        id="event-1",
        world_id="world-1",
        t=100.0,
        label_time="Day 100",
        type="incident",
        summary="Something happened",
        tags=["tag1", "tag2"],
        location_id=None,
        caused_by_ids=[],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.world_events.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.world_events.WorldEventRepository") as MockEventRepo:
        
        # Mock World Repo
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        # Mock Event Repo
        mock_event_repo = MockEventRepo.return_value
        mock_event_repo.create = AsyncMock(return_value=mock_event)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    f"{settings.api_v1_prefix}/worlds/world-1/events",
                    json={
                        "world_id": "world-1",
                        "t": 100.0,
                        "label_time": "Day 100",
                        "type": "incident",
                        "summary": "Something happened",
                        "tags": ["tag1", "tag2"]
                    }
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "event-1"
    assert data["summary"] == "Something happened"
    assert data["tags"] == ["tag1", "tag2"]

@pytest.mark.asyncio(loop_scope="session")
async def test_list_world_events():
    """Test listing world events."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")
    
    mock_events = [
        WorldEvent(id="e1", world_id="world-1", t=1.0, label_time="T1", type="type1", summary="S1", tags=[], location_id=None, caused_by_ids=[], created_at=datetime.now(), updated_at=datetime.now()),
        WorldEvent(id="e2", world_id="world-1", t=2.0, label_time="T2", type="type2", summary="S2", tags=[], location_id=None, caused_by_ids=[], created_at=datetime.now(), updated_at=datetime.now())
    ]
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.world_events.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.world_events.WorldEventRepository") as MockEventRepo:
        
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        mock_event_repo = MockEventRepo.return_value
        mock_event_repo.list_by_world = AsyncMock(return_value=(mock_events, len(mock_events)))
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get(f"{settings.api_v1_prefix}/worlds/world-1/events")
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == "e1"
    assert data[1]["id"] == "e2"

@pytest.mark.asyncio(loop_scope="session")
async def test_get_world_event():
    """Test getting a specific event."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")
    mock_event = WorldEvent(id="e1", world_id="world-1", t=1.0, label_time="T1", type="type1", summary="S1", tags=[], location_id=None, caused_by_ids=[], created_at=datetime.now(), updated_at=datetime.now())
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.world_events.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.world_events.WorldEventRepository") as MockEventRepo:
        
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        mock_event_repo = MockEventRepo.return_value
        mock_event_repo.get_by_id = AsyncMock(return_value=mock_event)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get(f"{settings.api_v1_prefix}/events/e1")
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "e1"

@pytest.mark.asyncio(loop_scope="session")
async def test_create_world_event_forbidden():
    """Test creating event in another user's world."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="Other World", user_id="other-user-id", laws={}, chronology_mode="linear")
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.world_events.WorldRepository") as MockWorldRepo:
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    f"{settings.api_v1_prefix}/worlds/world-1/events",
                    json={"world_id": "world-1", "t": 1.0, "label_time": "T", "type": "t", "summary": "s"}
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 403

@pytest.mark.asyncio(loop_scope="session")
async def test_update_world_event():
    """Test updating a world event."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")
    
    existing_event = WorldEvent(
        id="e1",
        world_id="world-1",
        t=1.0,
        label_time="Old Time",
        type="old_type",
        summary="Old summary",
        tags=[],
        caused_by_ids=[],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    updated_event = WorldEvent(
        id="e1",
        world_id="world-1",
        t=2.0,
        label_time="New Time",
        type="new_type",
        summary="New summary",
        tags=["new"],
        caused_by_ids=[],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.world_events.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.world_events.WorldEventRepository") as MockEventRepo:
        
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        mock_event_repo = MockEventRepo.return_value
        mock_event_repo.get_by_id = AsyncMock(return_value=existing_event)
        mock_event_repo.update = AsyncMock(return_value=updated_event)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.put(
                    f"{settings.api_v1_prefix}/events/e1",
                    json={"t": 2.0, "label_time": "New Time", "type": "new_type", "summary": "New summary", "tags": ["new"]}
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "New summary"
    assert data["t"] == 2.0

@pytest.mark.asyncio(loop_scope="session")
async def test_update_world_event_not_found():
    """Test updating a non-existent event."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.world_events.WorldEventRepository") as MockEventRepo:
        mock_event_repo = MockEventRepo.return_value
        mock_event_repo.get_by_id = AsyncMock(return_value=None)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.put(
                    f"{settings.api_v1_prefix}/events/999",
                    json={"summary": "Updated"}
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 404

@pytest.mark.asyncio(loop_scope="session")
async def test_update_world_event_forbidden():
    """Test updating an event belonging to another user."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="Other World", user_id="other-user-id", laws={}, chronology_mode="linear")
    mock_event = WorldEvent(id="e1", world_id="world-1", t=1.0, label_time="T", type="t", summary="s", tags=[], caused_by_ids=[], created_at=datetime.now(), updated_at=datetime.now())
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.world_events.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.world_events.WorldEventRepository") as MockEventRepo:
        
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        mock_event_repo = MockEventRepo.return_value
        mock_event_repo.get_by_id = AsyncMock(return_value=mock_event)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.put(
                    f"{settings.api_v1_prefix}/events/e1",
                    json={"summary": "Hacked"}
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 403

@pytest.mark.asyncio(loop_scope="session")
async def test_delete_world_event():
    """Test deleting a world event."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")
    mock_event = WorldEvent(id="e1", world_id="world-1", t=1.0, label_time="T", type="t", summary="To delete", tags=[], caused_by_ids=[], created_at=datetime.now(), updated_at=datetime.now())
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.world_events.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.world_events.WorldEventRepository") as MockEventRepo:
        
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        mock_event_repo = MockEventRepo.return_value
        mock_event_repo.get_by_id = AsyncMock(return_value=mock_event)
        mock_event_repo.delete = AsyncMock(return_value=True)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.delete(f"{settings.api_v1_prefix}/events/e1")
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 204

@pytest.mark.asyncio(loop_scope="session")
async def test_delete_world_event_not_found():
    """Test deleting a non-existent event."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.world_events.WorldEventRepository") as MockEventRepo:
        mock_event_repo = MockEventRepo.return_value
        mock_event_repo.get_by_id = AsyncMock(return_value=None)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.delete(f"{settings.api_v1_prefix}/events/999")
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 404

@pytest.mark.asyncio(loop_scope="session")
async def test_delete_world_event_forbidden():
    """Test deleting an event belonging to another user."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="Other World", user_id="other-user-id", laws={}, chronology_mode="linear")
    mock_event = WorldEvent(id="e1", world_id="world-1", t=1.0, label_time="T", type="t", summary="s", tags=[], caused_by_ids=[], created_at=datetime.now(), updated_at=datetime.now())
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.world_events.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.world_events.WorldEventRepository") as MockEventRepo:
        
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        mock_event_repo = MockEventRepo.return_value
        mock_event_repo.get_by_id = AsyncMock(return_value=mock_event)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.delete(f"{settings.api_v1_prefix}/events/e1")
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 403

@pytest.mark.asyncio(loop_scope="session")
async def test_list_world_events_with_pagination():
    """Test listing events with pagination."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")
    
    mock_events = [
        WorldEvent(id=f"e{i}", world_id="world-1", t=float(i), label_time=f"T{i}", type="t", summary=f"Event {i}", tags=[], caused_by_ids=[], created_at=datetime.now(), updated_at=datetime.now())
        for i in range(3)
    ]
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.world_events.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.world_events.WorldEventRepository") as MockEventRepo:
        
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        mock_event_repo = MockEventRepo.return_value
        mock_event_repo.list_by_world = AsyncMock(return_value=(mock_events, 10))
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get(
                    f"{settings.api_v1_prefix}/worlds/world-1/events",
                    params={"skip": 0, "limit": 3}
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    mock_event_repo.list_by_world.assert_called_once_with("world-1", skip=0, limit=3)


# ====== Phase 4: Event Dependency Tests ======

@pytest.mark.asyncio(loop_scope="session")
async def test_create_event_with_dependencies():
    """Test creating an event with caused_by_ids field."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")

    mock_event = WorldEvent(
        id="event-2",
        world_id="world-1",
        t=200.0,
        label_time="Day 200",
        type="incident",
        summary="Effect event",
        tags=[],
        location_id=None,
        caused_by_ids=["event-1"],  # Dependency
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()

    with patch("shinkei.api.v1.endpoints.world_events.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.world_events.WorldEventRepository") as MockEventRepo:

        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)

        mock_event_repo = MockEventRepo.return_value
        mock_event_repo.create = AsyncMock(return_value=mock_event)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    f"{settings.api_v1_prefix}/worlds/world-1/events",
                    json={
                        "t": 200.0,
                        "label_time": "Day 200",
                        "type": "incident",
                        "summary": "Effect event",
                        "caused_by_ids": ["event-1"]
                    }
                )
        finally:
            app.dependency_overrides = {}

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "event-2"
    assert data["caused_by_ids"] == ["event-1"]


@pytest.mark.asyncio(loop_scope="session")
async def test_add_event_dependency():
    """Test adding a dependency between two events."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")

    mock_cause_event = WorldEvent(
        id="cause-event",
        world_id="world-1",
        t=100.0,
        label_time="Day 100",
        type="incident",
        summary="Cause",
        tags=[],
        caused_by_ids=[],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    mock_effect_event = WorldEvent(
        id="effect-event",
        world_id="world-1",
        t=200.0,
        label_time="Day 200",
        type="incident",
        summary="Effect",
        tags=[],
        caused_by_ids=[],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user

    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    app.dependency_overrides["get_db_session"] = lambda: mock_session

    with patch("shinkei.api.v1.endpoints.world_events.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.world_events.WorldEventRepository") as MockEventRepo, \
         patch("shinkei.api.v1.endpoints.world_events._would_create_cycle") as mock_cycle_check:

        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)

        mock_event_repo = MockEventRepo.return_value
        mock_event_repo.get_by_id = AsyncMock(side_effect=lambda id:
            mock_effect_event if id == "effect-event" else mock_cause_event
        )

        mock_cycle_check.return_value = False

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    f"{settings.api_v1_prefix}/events/effect-event/dependencies/cause-event"
                )
        finally:
            app.dependency_overrides = {}

    assert response.status_code == 204
    mock_cycle_check.assert_called_once()


@pytest.mark.asyncio(loop_scope="session")
async def test_add_event_dependency_self_reference():
    """Test that adding a self-reference dependency is blocked."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")

    mock_event = WorldEvent(
        id="event-1",
        world_id="world-1",
        t=100.0,
        label_time="Day 100",
        type="incident",
        summary="Event",
        tags=[],
        caused_by_ids=[],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()

    with patch("shinkei.api.v1.endpoints.world_events.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.world_events.WorldEventRepository") as MockEventRepo, \
         patch("shinkei.api.v1.endpoints.world_events._would_create_cycle") as mock_cycle_check:

        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)

        mock_event_repo = MockEventRepo.return_value
        mock_event_repo.get_by_id = AsyncMock(return_value=mock_event)

        # Cycle detection should catch self-reference
        mock_cycle_check.return_value = True

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    f"{settings.api_v1_prefix}/events/event-1/dependencies/event-1"
                )
        finally:
            app.dependency_overrides = {}

    assert response.status_code == 400
    assert "circular dependency" in response.json()["detail"].lower()


@pytest.mark.asyncio(loop_scope="session")
async def test_add_event_dependency_circular():
    """Test that adding a circular dependency is blocked (A→B, B→A)."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")

    # Event A already has B as a cause
    mock_event_a = WorldEvent(
        id="event-a",
        world_id="world-1",
        t=100.0,
        label_time="Day 100",
        type="incident",
        summary="Event A",
        tags=[],
        caused_by_ids=["event-b"],  # A is caused by B
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    mock_event_b = WorldEvent(
        id="event-b",
        world_id="world-1",
        t=200.0,
        label_time="Day 200",
        type="incident",
        summary="Event B",
        tags=[],
        caused_by_ids=[],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()

    with patch("shinkei.api.v1.endpoints.world_events.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.world_events.WorldEventRepository") as MockEventRepo, \
         patch("shinkei.api.v1.endpoints.world_events._would_create_cycle") as mock_cycle_check:

        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)

        mock_event_repo = MockEventRepo.return_value
        mock_event_repo.get_by_id = AsyncMock(side_effect=lambda id:
            mock_event_b if id == "event-b" else mock_event_a
        )

        # Cycle detection should detect A→B→A cycle
        mock_cycle_check.return_value = True

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                # Trying to add A as cause of B, which would create B→A (cycle)
                response = await ac.post(
                    f"{settings.api_v1_prefix}/events/event-b/dependencies/event-a"
                )
        finally:
            app.dependency_overrides = {}

    assert response.status_code == 400
    assert "circular dependency" in response.json()["detail"].lower()


@pytest.mark.asyncio(loop_scope="session")
async def test_add_event_dependency_different_worlds():
    """Test that adding dependency across different worlds is blocked."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")

    mock_event_1 = WorldEvent(
        id="event-1",
        world_id="world-1",
        t=100.0,
        label_time="Day 100",
        type="incident",
        summary="Event 1",
        tags=[],
        caused_by_ids=[],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    mock_event_2 = WorldEvent(
        id="event-2",
        world_id="world-2",  # Different world!
        t=200.0,
        label_time="Day 200",
        type="incident",
        summary="Event 2",
        tags=[],
        caused_by_ids=[],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()

    with patch("shinkei.api.v1.endpoints.world_events.WorldEventRepository") as MockEventRepo:

        mock_event_repo = MockEventRepo.return_value
        mock_event_repo.get_by_id = AsyncMock(side_effect=lambda id:
            mock_event_1 if id == "event-1" else mock_event_2
        )

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    f"{settings.api_v1_prefix}/events/event-1/dependencies/event-2"
                )
        finally:
            app.dependency_overrides = {}

    assert response.status_code == 400
    assert "same world" in response.json()["detail"].lower()


@pytest.mark.asyncio(loop_scope="session")
async def test_remove_event_dependency():
    """Test removing a dependency between two events."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")

    mock_event = WorldEvent(
        id="event-1",
        world_id="world-1",
        t=100.0,
        label_time="Day 100",
        type="incident",
        summary="Event",
        tags=[],
        caused_by_ids=["cause-1", "cause-2"],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user

    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    app.dependency_overrides["get_db_session"] = lambda: mock_session

    with patch("shinkei.api.v1.endpoints.world_events.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.world_events.WorldEventRepository") as MockEventRepo:

        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)

        mock_event_repo = MockEventRepo.return_value
        mock_event_repo.get_by_id = AsyncMock(return_value=mock_event)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.delete(
                    f"{settings.api_v1_prefix}/events/event-1/dependencies/cause-1"
                )
        finally:
            app.dependency_overrides = {}

    assert response.status_code == 204


@pytest.mark.asyncio(loop_scope="session")
async def test_get_dependency_graph():
    """Test getting the event dependency graph for a world."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")

    mock_events = [
        WorldEvent(
            id="event-1",
            world_id="world-1",
            t=100.0,
            label_time="Day 100",
            type="incident",
            summary="Cause event",
            tags=[],
            caused_by_ids=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        WorldEvent(
            id="event-2",
            world_id="world-1",
            t=200.0,
            label_time="Day 200",
            type="incident",
            summary="Effect event",
            tags=[],
            caused_by_ids=["event-1"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()

    with patch("shinkei.api.v1.endpoints.world_events.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.world_events.WorldEventRepository") as MockEventRepo:

        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)

        mock_event_repo = MockEventRepo.return_value
        mock_event_repo.list_by_world = AsyncMock(return_value=(mock_events, len(mock_events)))

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get(
                    f"{settings.api_v1_prefix}/worlds/world-1/events/dependency-graph"
                )
        finally:
            app.dependency_overrides = {}

    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert "world_id" in data
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1
    assert data["edges"][0]["source"] == "event-1"
    assert data["edges"][0]["target"] == "event-2"
    assert data["edges"][0]["type"] == "causes"
