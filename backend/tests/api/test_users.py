"""Tests for User API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from shinkei.main import app
from shinkei.models.user import User
from shinkei.config import settings
from shinkei.auth.dependencies import get_current_user
from datetime import datetime

@pytest.mark.asyncio(loop_scope="session")
async def test_create_user():
    """Test creating a new user."""
    mock_user = User(
        id="new-user-id", 
        email="newuser@example.com", 
        name="New User", 
        settings={"theme": "dark"},
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    with patch("shinkei.api.v1.endpoints.users.UserRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        mock_repo_instance.get_by_email = AsyncMock(return_value=None)
        mock_repo_instance.create = AsyncMock(return_value=mock_user)
        
        # We need to override get_db_session to return a dummy because the endpoint uses it
        app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    f"{settings.api_v1_prefix}/users/",
                    json={"email": "newuser@example.com", "name": "New User", "settings": {"theme": "dark"}}
                )
        finally:
            app.dependency_overrides = {}
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["name"] == "New User"
    assert "id" in data

@pytest.mark.asyncio(loop_scope="session")
async def test_read_user_me():
    """Test getting current user profile."""
    # Mock authentication
    mock_user = User(
        id="test-user-id", 
        email="me@example.com", 
        name="Me",
        settings={},
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get(f"{settings.api_v1_prefix}/users/me")
    finally:
        app.dependency_overrides = {}
            
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["id"] == "test-user-id"

@pytest.mark.asyncio(loop_scope="session")
async def test_update_user_me():
    """Test updating current user profile."""
    # We need a real user in DB for update to work because repository fetches it
    from shinkei.repositories.user import UserRepository
    from shinkei.schemas.user import UserCreate
    
    # repo = UserRepository(session)
    # user = await repo.create(UserCreate(email="update@example.com", name="Original Name"))
    
    user = User(
        id="update-user-id", 
        email="update@example.com", 
        name="Updated Name", 
        settings={},
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Mock authentication to return this user
    app.dependency_overrides[get_current_user] = lambda: user
    # Override DB session to use the same session as the test
    # app.dependency_overrides[get_db_session] = lambda: session
    pass
    
    
    with patch("shinkei.api.v1.endpoints.users.UserRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        mock_repo_instance.update = AsyncMock(return_value=user)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.put(
                    f"{settings.api_v1_prefix}/users/me",
                    json={"name": "Updated Name"}
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
