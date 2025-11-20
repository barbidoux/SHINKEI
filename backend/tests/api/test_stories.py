"""Tests for Story API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from datetime import datetime

from shinkei.main import app
from shinkei.models.user import User
from shinkei.models.world import World
from shinkei.models.story import Story
from shinkei.config import settings
from shinkei.auth.dependencies import get_current_user

@pytest.mark.asyncio(loop_scope="session")
async def test_create_story():
    """Test creating a new story."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")
    
    mock_story = Story(
        id="story-1",
        world_id="world-1",
        title="My Story",
        synopsis="A summary",
        theme="A theme",
        status="draft",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.stories.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.stories.StoryRepository") as MockStoryRepo:
        
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        mock_story_repo = MockStoryRepo.return_value
        mock_story_repo.create = AsyncMock(return_value=mock_story)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    f"{settings.api_v1_prefix}/worlds/world-1/stories",
                    json={
                        "title": "My Story",
                        "synopsis": "A summary",
                        "theme": "A theme",
                        "status": "draft"
                    }
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "story-1"
    assert data["title"] == "My Story"

@pytest.mark.asyncio(loop_scope="session")
async def test_list_stories():
    """Test listing stories."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")
    
    mock_stories = [
        Story(id="s1", world_id="world-1", title="S1", synopsis="Sum1", theme="T1", status="draft", created_at=datetime.now(), updated_at=datetime.now()),
        Story(id="s2", world_id="world-1", title="S2", synopsis="Sum2", theme="T2", status="draft", created_at=datetime.now(), updated_at=datetime.now())
    ]
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.stories.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.stories.StoryRepository") as MockStoryRepo:
        
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        mock_story_repo = MockStoryRepo.return_value
        mock_story_repo.list_by_world = AsyncMock(return_value=(mock_stories, len(mock_stories)))
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get(f"{settings.api_v1_prefix}/worlds/world-1/stories")
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == "s1"

@pytest.mark.asyncio(loop_scope="session")
async def test_get_story():
    """Test getting a specific story."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")
    mock_story = Story(id="s1", world_id="world-1", title="S1", synopsis="Sum1", theme="T1", status="draft", created_at=datetime.now(), updated_at=datetime.now())
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.stories.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.stories.StoryRepository") as MockStoryRepo:
        
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        mock_story_repo = MockStoryRepo.return_value
        mock_story_repo.get_by_id = AsyncMock(return_value=mock_story)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get(f"{settings.api_v1_prefix}/stories/s1")
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "s1"

@pytest.mark.asyncio(loop_scope="session")
async def test_create_story_forbidden():
    """Test creating story in another user's world."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="Other World", user_id="other-user-id", laws={}, chronology_mode="linear")
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.stories.WorldRepository") as MockWorldRepo:
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    f"{settings.api_v1_prefix}/worlds/world-1/stories",
                    json={"title": "T", "synopsis": "S", "theme": "Th", "status": "draft"}
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 403

@pytest.mark.asyncio(loop_scope="session")
async def test_update_story():
    """Test updating a story."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")
    
    existing_story = Story(
        id="s1",
        world_id="world-1",
        title="Old Title",
        synopsis="Old synopsis",
        theme="Old theme",
        status="draft",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    updated_story = Story(
        id="s1",
        world_id="world-1",
        title="New Title",
        synopsis="New synopsis",
        theme="New theme",
        status="active",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.stories.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.stories.StoryRepository") as MockStoryRepo:
        
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        mock_story_repo = MockStoryRepo.return_value
        mock_story_repo.get_by_id = AsyncMock(return_value=existing_story)
        mock_story_repo.update = AsyncMock(return_value=updated_story)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.put(
                    f"{settings.api_v1_prefix}/stories/s1",
                    json={"title": "New Title", "synopsis": "New synopsis", "theme": "New theme", "status": "active"}
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["status"] == "active"

@pytest.mark.asyncio(loop_scope="session")
async def test_update_story_not_found():
    """Test updating a non-existent story."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.stories.StoryRepository") as MockStoryRepo:
        mock_story_repo = MockStoryRepo.return_value
        mock_story_repo.get_by_id = AsyncMock(return_value=None)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.put(
                    f"{settings.api_v1_prefix}/stories/999",
                    json={"title": "Updated"}
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 404

@pytest.mark.asyncio(loop_scope="session")
async def test_update_story_forbidden():
    """Test updating a story belonging to another user."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="Other World", user_id="other-user-id", laws={}, chronology_mode="linear")
    mock_story = Story(id="s1", world_id="world-1", title="S1", status="draft", created_at=datetime.now(), updated_at=datetime.now())
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.stories.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.stories.StoryRepository") as MockStoryRepo:
        
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        mock_story_repo = MockStoryRepo.return_value
        mock_story_repo.get_by_id = AsyncMock(return_value=mock_story)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.put(
                    f"{settings.api_v1_prefix}/stories/s1",
                    json={"title": "Hacked"}
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 403

@pytest.mark.asyncio(loop_scope="session")
async def test_delete_story():
    """Test deleting a story."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")
    mock_story = Story(id="s1", world_id="world-1", title="To Delete", status="draft", created_at=datetime.now(), updated_at=datetime.now())
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.stories.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.stories.StoryRepository") as MockStoryRepo:
        
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        mock_story_repo = MockStoryRepo.return_value
        mock_story_repo.get_by_id = AsyncMock(return_value=mock_story)
        mock_story_repo.delete = AsyncMock(return_value=True)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.delete(f"{settings.api_v1_prefix}/stories/s1")
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 204

@pytest.mark.asyncio(loop_scope="session")
async def test_delete_story_not_found():
    """Test deleting a non-existent story."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.stories.StoryRepository") as MockStoryRepo:
        mock_story_repo = MockStoryRepo.return_value
        mock_story_repo.get_by_id = AsyncMock(return_value=None)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.delete(f"{settings.api_v1_prefix}/stories/999")
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 404

@pytest.mark.asyncio(loop_scope="session")
async def test_delete_story_forbidden():
    """Test deleting a story belonging to another user."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="Other World", user_id="other-user-id", laws={}, chronology_mode="linear")
    mock_story = Story(id="s1", world_id="world-1", title="S1", status="draft", created_at=datetime.now(), updated_at=datetime.now())
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.stories.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.stories.StoryRepository") as MockStoryRepo:
        
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        mock_story_repo = MockStoryRepo.return_value
        mock_story_repo.get_by_id = AsyncMock(return_value=mock_story)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.delete(f"{settings.api_v1_prefix}/stories/s1")
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 403

@pytest.mark.asyncio(loop_scope="session")
async def test_list_stories_with_pagination():
    """Test listing stories with pagination."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")
    
    mock_stories = [
        Story(id=f"s{i}", world_id="world-1", title=f"Story {i}", status="draft", created_at=datetime.now(), updated_at=datetime.now())
        for i in range(3)
    ]
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.stories.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.stories.StoryRepository") as MockStoryRepo:
        
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        mock_story_repo = MockStoryRepo.return_value
        mock_story_repo.list_by_world = AsyncMock(return_value=(mock_stories, 10))
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get(
                    f"{settings.api_v1_prefix}/worlds/world-1/stories",
                    params={"skip": 0, "limit": 3}
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    mock_story_repo.list_by_world.assert_called_once_with("world-1", skip=0, limit=3)
