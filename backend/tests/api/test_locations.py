"""Tests for Location API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from datetime import datetime

from shinkei.main import app
from shinkei.models.user import User
from shinkei.models.world import World
from shinkei.models.location import Location
from shinkei.config import settings
from shinkei.auth.dependencies import get_current_user


@pytest.mark.asyncio(loop_scope="session")
async def test_create_location():
    """Test creating a new location."""
    mock_user = User(id="test-user-id", email="test@example.com", name="Tester")
    mock_world = World(
        id="world-1",
        name="Fantasy World",
        user_id="test-user-id",
        laws={},
        chronology_mode="linear",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    mock_location = Location(
        id="loc-1",
        world_id="world-1",
        name="Rivendell",
        description="Elven city",
        location_type="city",
        coordinates={"lat": 45.0, "lng": -120.0},
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()

    with patch("shinkei.api.v1.endpoints.locations.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.locations.LocationRepository") as MockLocRepo:

        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_user_and_id = AsyncMock(return_value=mock_world)

        mock_loc_repo = MockLocRepo.return_value
        mock_loc_repo.create = AsyncMock(return_value=mock_location)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    f"{settings.api_v1_prefix}/worlds/world-1/locations",
                    json={
                        "name": "Rivendell",
                        "description": "Elven city",
                        "location_type": "city",
                        "coordinates": {"lat": 45.0, "lng": -120.0}
                    }
                )
        finally:
            app.dependency_overrides = {}

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Rivendell"
    assert data["location_type"] == "city"


@pytest.mark.asyncio(loop_scope="session")
async def test_list_locations():
    """Test listing locations."""
    mock_user = User(id="test-user-id", email="test@example.com", name="Tester")
    mock_world = World(
        id="world-1",
        name="Fantasy World",
        user_id="test-user-id",
        laws={},
        chronology_mode="linear",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    mock_locations = [
        Location(id="1", world_id="world-1", name="Rivendell", location_type="city", created_at=datetime.now(), updated_at=datetime.now()),
        Location(id="2", world_id="world-1", name="Moria", location_type="mine", created_at=datetime.now(), updated_at=datetime.now())
    ]

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()

    with patch("shinkei.api.v1.endpoints.locations.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.locations.LocationRepository") as MockLocRepo:

        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_user_and_id = AsyncMock(return_value=mock_world)

        mock_loc_repo = MockLocRepo.return_value
        mock_loc_repo.list_by_world = AsyncMock(return_value=(mock_locations, 2))

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get(f"{settings.api_v1_prefix}/worlds/world-1/locations")
        finally:
            app.dependency_overrides = {}

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["locations"]) == 2


@pytest.mark.asyncio(loop_scope="session")
async def test_get_location():
    """Test getting a specific location."""
    mock_user = User(id="test-user-id", email="test@example.com", name="Tester")
    mock_world = World(
        id="world-1",
        name="Fantasy World",
        user_id="test-user-id",
        laws={},
        chronology_mode="linear",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    mock_location = Location(
        id="loc-1",
        world_id="world-1",
        name="Rivendell",
        location_type="city",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()

    with patch("shinkei.api.v1.endpoints.locations.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.locations.LocationRepository") as MockLocRepo:

        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_user_and_id = AsyncMock(return_value=mock_world)

        mock_loc_repo = MockLocRepo.return_value
        mock_loc_repo.get_with_mention_count = AsyncMock(return_value=(mock_location, 3))

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get(f"{settings.api_v1_prefix}/worlds/world-1/locations/loc-1")
        finally:
            app.dependency_overrides = {}

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Rivendell"
    assert data["mention_count"] == 3


@pytest.mark.asyncio(loop_scope="session")
async def test_get_root_locations():
    """Test getting root locations."""
    mock_user = User(id="test-user-id", email="test@example.com", name="Tester")
    mock_world = World(
        id="world-1",
        name="Fantasy World",
        user_id="test-user-id",
        laws={},
        chronology_mode="linear",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    mock_roots = [
        Location(id="1", world_id="world-1", name="Middle-earth", location_type="continent", created_at=datetime.now(), updated_at=datetime.now())
    ]

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()

    with patch("shinkei.api.v1.endpoints.locations.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.locations.LocationRepository") as MockLocRepo:

        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_user_and_id = AsyncMock(return_value=mock_world)

        mock_loc_repo = MockLocRepo.return_value
        mock_loc_repo.get_root_locations = AsyncMock(return_value=mock_roots)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get(f"{settings.api_v1_prefix}/worlds/world-1/locations/roots")
        finally:
            app.dependency_overrides = {}

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Middle-earth"


@pytest.mark.asyncio(loop_scope="session")
async def test_get_location_children():
    """Test getting location children."""
    mock_user = User(id="test-user-id", email="test@example.com", name="Tester")
    mock_world = World(
        id="world-1",
        name="Fantasy World",
        user_id="test-user-id",
        laws={},
        chronology_mode="linear",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    mock_parent = Location(
        id="parent-1",
        world_id="world-1",
        name="The Shire",
        location_type="region",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    mock_children = [
        Location(id="child-1", world_id="world-1", name="Hobbiton", location_type="village", parent_location_id="parent-1", created_at=datetime.now(), updated_at=datetime.now())
    ]

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()

    with patch("shinkei.api.v1.endpoints.locations.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.locations.LocationRepository") as MockLocRepo:

        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_user_and_id = AsyncMock(return_value=mock_world)

        mock_loc_repo = MockLocRepo.return_value
        mock_loc_repo.get_by_world_and_id = AsyncMock(return_value=mock_parent)
        mock_loc_repo.get_children = AsyncMock(return_value=mock_children)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get(f"{settings.api_v1_prefix}/worlds/world-1/locations/parent-1/children")
        finally:
            app.dependency_overrides = {}

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Hobbiton"


@pytest.mark.asyncio(loop_scope="session")
async def test_update_location():
    """Test updating a location."""
    mock_user = User(id="test-user-id", email="test@example.com", name="Tester")
    mock_world = World(
        id="world-1",
        name="Fantasy World",
        user_id="test-user-id",
        laws={},
        chronology_mode="linear",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    mock_location = Location(
        id="loc-1",
        world_id="world-1",
        name="Rivendell",
        location_type="city",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    mock_updated_location = Location(
        id="loc-1",
        world_id="world-1",
        name="Rivendell",
        description="Updated description",
        location_type="city",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()

    with patch("shinkei.api.v1.endpoints.locations.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.locations.LocationRepository") as MockLocRepo:

        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_user_and_id = AsyncMock(return_value=mock_world)

        mock_loc_repo = MockLocRepo.return_value
        mock_loc_repo.get_by_world_and_id = AsyncMock(return_value=mock_location)
        mock_loc_repo.update = AsyncMock(return_value=mock_updated_location)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.put(
                    f"{settings.api_v1_prefix}/worlds/world-1/locations/loc-1",
                    json={"description": "Updated description"}
                )
        finally:
            app.dependency_overrides = {}

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated description"


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_location():
    """Test deleting a location."""
    mock_user = User(id="test-user-id", email="test@example.com", name="Tester")
    mock_world = World(
        id="world-1",
        name="Fantasy World",
        user_id="test-user-id",
        laws={},
        chronology_mode="linear",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    mock_location = Location(
        id="loc-1",
        world_id="world-1",
        name="Isengard",
        location_type="fortress",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()

    with patch("shinkei.api.v1.endpoints.locations.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.locations.LocationRepository") as MockLocRepo:

        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_user_and_id = AsyncMock(return_value=mock_world)

        mock_loc_repo = MockLocRepo.return_value
        mock_loc_repo.get_by_world_and_id = AsyncMock(return_value=mock_location)
        mock_loc_repo.delete = AsyncMock(return_value=True)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.delete(f"{settings.api_v1_prefix}/worlds/world-1/locations/loc-1")
        finally:
            app.dependency_overrides = {}

    assert response.status_code == 204
