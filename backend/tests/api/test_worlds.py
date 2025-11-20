"""Tests for World API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from datetime import datetime

from shinkei.main import app
from shinkei.models.user import User
from shinkei.models.world import World
from shinkei.config import settings
from shinkei.auth.dependencies import get_current_user

@pytest.mark.asyncio(loop_scope="session")
async def test_create_world():
    """Test creating a new world."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    
    mock_world = World(
        id="1",
        name="New World",
        description="A new world description",
        user_id="test-user-id",
        laws={},
        chronology_mode="linear",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Mock authentication
    app.dependency_overrides[get_current_user] = lambda: mock_user
    # Mock DB session
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.worlds.WorldRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        mock_repo_instance.create = AsyncMock(return_value=mock_world)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    f"{settings.api_v1_prefix}/worlds/",
                    json={"name": "New World", "description": "A new world description"}
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New World"
    assert data["id"] == "1"
    assert data["user_id"] == "test-user-id"

@pytest.mark.asyncio(loop_scope="session")
async def test_list_worlds():
    """Test listing worlds."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    
    mock_worlds = [
        World(id="1", name="World 1", user_id="test-user-id", laws={}, chronology_mode="linear", created_at=datetime.now(), updated_at=datetime.now()),
        World(id="2", name="World 2", user_id="test-user-id", laws={}, chronology_mode="linear", created_at=datetime.now(), updated_at=datetime.now())
    ]
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.worlds.WorldRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        mock_repo_instance.list_by_user = AsyncMock(return_value=(mock_worlds, len(mock_worlds)))

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get(f"{settings.api_v1_prefix}/worlds/")
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "World 1"
    assert data[1]["name"] == "World 2"

@pytest.mark.asyncio(loop_scope="session")
async def test_get_world():
    """Test getting a specific world."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear", created_at=datetime.now(), updated_at=datetime.now())
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.worlds.WorldRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        mock_repo_instance.get_by_id = AsyncMock(return_value=mock_world)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get(f"{settings.api_v1_prefix}/worlds/1")
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "My World"

@pytest.mark.asyncio(loop_scope="session")
async def test_get_world_not_found():
    """Test getting a non-existent world."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.worlds.WorldRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        mock_repo_instance.get_by_id = AsyncMock(return_value=None)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get(f"{settings.api_v1_prefix}/worlds/999")
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 404

@pytest.mark.asyncio(loop_scope="session")
async def test_get_world_forbidden():
    """Test getting a world belonging to another user."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="1", name="Other World", user_id="other-user-id", laws={}, chronology_mode="linear", created_at=datetime.now(), updated_at=datetime.now())
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.worlds.WorldRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        mock_repo_instance.get_by_id = AsyncMock(return_value=mock_world)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get(f"{settings.api_v1_prefix}/worlds/1")
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 403

@pytest.mark.asyncio(loop_scope="session")
async def test_update_world():
    """Test updating a world."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    
    existing_world = World(
        id="1",
        name="Old Name",
        description="Old description",
        user_id="test-user-id",
        laws={},
        chronology_mode="linear",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    updated_world = World(
        id="1",
        name="New Name",
        description="New description",
        user_id="test-user-id",
        laws={},
        chronology_mode="linear",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.worlds.WorldRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        mock_repo_instance.get_by_id = AsyncMock(return_value=existing_world)
        mock_repo_instance.update = AsyncMock(return_value=updated_world)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.put(
                    f"{settings.api_v1_prefix}/worlds/1",
                    json={"name": "New Name", "description": "New description"}
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "New description"

@pytest.mark.asyncio(loop_scope="session")
async def test_update_world_not_found():
    """Test updating a non-existent world."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.worlds.WorldRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        mock_repo_instance.get_by_id = AsyncMock(return_value=None)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.put(
                    f"{settings.api_v1_prefix}/worlds/999",
                    json={"name": "Updated"}
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 404

@pytest.mark.asyncio(loop_scope="session")
async def test_update_world_forbidden():
    """Test updating a world belonging to another user."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="1", name="Other World", user_id="other-user-id", laws={}, chronology_mode="linear", created_at=datetime.now(), updated_at=datetime.now())
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.worlds.WorldRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        mock_repo_instance.get_by_id = AsyncMock(return_value=mock_world)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.put(
                    f"{settings.api_v1_prefix}/worlds/1",
                    json={"name": "Hacked"}
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 403

@pytest.mark.asyncio(loop_scope="session")
async def test_delete_world():
    """Test deleting a world."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="1", name="To Delete", user_id="test-user-id", laws={}, chronology_mode="linear", created_at=datetime.now(), updated_at=datetime.now())
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.worlds.WorldRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        mock_repo_instance.get_by_id = AsyncMock(return_value=mock_world)
        mock_repo_instance.delete = AsyncMock(return_value=True)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.delete(f"{settings.api_v1_prefix}/worlds/1")
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 204

@pytest.mark.asyncio(loop_scope="session")
async def test_delete_world_not_found():
    """Test deleting a non-existent world."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.worlds.WorldRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        mock_repo_instance.get_by_id = AsyncMock(return_value=None)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.delete(f"{settings.api_v1_prefix}/worlds/999")
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 404

@pytest.mark.asyncio(loop_scope="session")
async def test_delete_world_forbidden():
    """Test deleting a world belonging to another user."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="1", name="Other World", user_id="other-user-id", laws={}, chronology_mode="linear", created_at=datetime.now(), updated_at=datetime.now())
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.worlds.WorldRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        mock_repo_instance.get_by_id = AsyncMock(return_value=mock_world)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.delete(f"{settings.api_v1_prefix}/worlds/1")
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 403

@pytest.mark.asyncio(loop_scope="session")
async def test_list_worlds_with_pagination():
    """Test listing worlds with pagination."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    
    mock_worlds = [
        World(id=str(i), name=f"World {i}", user_id="test-user-id", laws={}, chronology_mode="linear", created_at=datetime.now(), updated_at=datetime.now())
        for i in range(3)
    ]
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.worlds.WorldRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        mock_repo_instance.list_by_user = AsyncMock(return_value=(mock_worlds, 10))
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get(
                    f"{settings.api_v1_prefix}/worlds/",
                    params={"skip": 0, "limit": 3}
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    mock_repo_instance.list_by_user.assert_called_once_with("test-user-id", skip=0, limit=3)

@pytest.mark.asyncio(loop_scope="session")
async def test_create_world_validation_error():
    """Test creating a world with invalid data."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                f"{settings.api_v1_prefix}/worlds/",
                json={}  # Missing required 'name' field
            )
    finally:
        app.dependency_overrides = {}
        
    assert response.status_code == 422  # Validation error
