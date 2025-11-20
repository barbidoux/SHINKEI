"""Tests for StoryBeat API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from datetime import datetime

from shinkei.main import app
from shinkei.models.user import User
from shinkei.models.world import World
from shinkei.models.story import Story
from shinkei.models.story_beat import StoryBeat
from shinkei.config import settings
from shinkei.auth.dependencies import get_current_user

@pytest.mark.asyncio(loop_scope="session")
async def test_create_story_beat():
    """Test creating a new story beat."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")
    mock_story = Story(id="story-1", world_id="world-1", title="My Story", synopsis="A summary", theme="A theme", status="draft", created_at=datetime.now(), updated_at=datetime.now())
    
    mock_beat = StoryBeat(
        id="beat-1",
        story_id="story-1",
        order_index=1,
        content="Beat content",
        type="scene",
        world_event_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.story_beats.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.story_beats.StoryRepository") as MockStoryRepo, \
         patch("shinkei.api.v1.endpoints.story_beats.StoryBeatRepository") as MockBeatRepo:
        
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        mock_story_repo = MockStoryRepo.return_value
        mock_story_repo.get_by_id = AsyncMock(return_value=mock_story)
        
        mock_beat_repo = MockBeatRepo.return_value
        mock_beat_repo.create = AsyncMock(return_value=mock_beat)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    f"{settings.api_v1_prefix}/stories/story-1/beats",
                    json={
                        "order_index": 1,
                        "content": "Beat content",
                        "type": "scene"
                    }
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "beat-1"
    assert data["content"] == "Beat content"

@pytest.mark.asyncio(loop_scope="session")
async def test_list_story_beats():
    """Test listing story beats."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")
    mock_story = Story(id="story-1", world_id="world-1", title="My Story", synopsis="A summary", theme="A theme", status="draft", created_at=datetime.now(), updated_at=datetime.now())
    
    mock_beats = [
        StoryBeat(id="b1", story_id="story-1", order_index=1, content="C1", type="scene", world_event_id=None, created_at=datetime.now(), updated_at=datetime.now()),
        StoryBeat(id="b2", story_id="story-1", order_index=2, content="C2", type="scene", world_event_id=None, created_at=datetime.now(), updated_at=datetime.now())
    ]
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.story_beats.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.story_beats.StoryRepository") as MockStoryRepo, \
         patch("shinkei.api.v1.endpoints.story_beats.StoryBeatRepository") as MockBeatRepo:
        
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        mock_story_repo = MockStoryRepo.return_value
        mock_story_repo.get_by_id = AsyncMock(return_value=mock_story)
        
        mock_beat_repo = MockBeatRepo.return_value
        mock_beat_repo.list_by_story = AsyncMock(return_value=(mock_beats, len(mock_beats)))
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get(f"{settings.api_v1_prefix}/stories/story-1/beats")
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == "b1"

@pytest.mark.asyncio(loop_scope="session")
async def test_update_story_beat():
    """Test updating a story beat."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")
    mock_story = Story(id="story-1", world_id="world-1", title="My Story", synopsis="A summary", theme="A theme", status="draft", created_at=datetime.now(), updated_at=datetime.now())
    mock_beat = StoryBeat(id="b1", story_id="story-1", order_index=1, content="C1", type="scene", world_event_id=None, created_at=datetime.now(), updated_at=datetime.now())
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.story_beats.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.story_beats.StoryRepository") as MockStoryRepo, \
         patch("shinkei.api.v1.endpoints.story_beats.StoryBeatRepository") as MockBeatRepo:
        
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        mock_story_repo = MockStoryRepo.return_value
        mock_story_repo.get_by_id = AsyncMock(return_value=mock_story)
        
        mock_beat_repo = MockBeatRepo.return_value
        mock_beat_repo.get_by_id = AsyncMock(return_value=mock_beat)
        mock_beat_repo.update = AsyncMock(return_value=mock_beat)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.put(
                    f"{settings.api_v1_prefix}/beats/b1",
                    json={"content": "Updated content"}
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 200

@pytest.mark.asyncio(loop_scope="session")
async def test_delete_story_beat():
    """Test deleting a story beat."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")
    mock_story = Story(id="story-1", world_id="world-1", title="My Story", synopsis="A summary", theme="A theme", status="draft", created_at=datetime.now(), updated_at=datetime.now())
    mock_beat = StoryBeat(id="b1", story_id="story-1", order_index=1, content="C1", type="scene", world_event_id=None, created_at=datetime.now(), updated_at=datetime.now())
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.story_beats.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.story_beats.StoryRepository") as MockStoryRepo, \
         patch("shinkei.api.v1.endpoints.story_beats.StoryBeatRepository") as MockBeatRepo:
        
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        mock_story_repo = MockStoryRepo.return_value
        mock_story_repo.get_by_id = AsyncMock(return_value=mock_story)
        
        mock_beat_repo = MockBeatRepo.return_value
        mock_beat_repo.get_by_id = AsyncMock(return_value=mock_beat)
        mock_beat_repo.delete = AsyncMock(return_value=True)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.delete(f"{settings.api_v1_prefix}/beats/b1")
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 204

@pytest.mark.asyncio(loop_scope="session")
async def test_update_story_beat_not_found():
    """Test updating a non-existent beat."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.story_beats.StoryBeatRepository") as MockBeatRepo:
        mock_beat_repo = MockBeatRepo.return_value
        mock_beat_repo.get_by_id = AsyncMock(return_value=None)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.put(
                    f"{settings.api_v1_prefix}/beats/999",
                    json={"content": "Updated"}
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 404

@pytest.mark.asyncio(loop_scope="session")
async def test_update_story_beat_forbidden():
    """Test updating a beat belonging to another user."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="Other World", user_id="other-user-id", laws={}, chronology_mode="linear")
    mock_story = Story(id="story-1", world_id="world-1", title="S", status="draft", created_at=datetime.now(), updated_at=datetime.now())
    mock_beat = StoryBeat(id="b1", story_id="story-1", order_index=1, content="C", type="scene", created_at=datetime.now(), updated_at=datetime.now())
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.story_beats.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.story_beats.StoryRepository") as MockStoryRepo, \
         patch("shinkei.api.v1.endpoints.story_beats.StoryBeatRepository") as MockBeatRepo:
        
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        mock_story_repo = MockStoryRepo.return_value
        mock_story_repo.get_by_id = AsyncMock(return_value=mock_story)
        
        mock_beat_repo = MockBeatRepo.return_value
        mock_beat_repo.get_by_id = AsyncMock(return_value=mock_beat)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.put(
                    f"{settings.api_v1_prefix}/beats/b1",
                    json={"content": "Hacked"}
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 403

@pytest.mark.asyncio(loop_scope="session")
async def test_delete_story_beat_not_found():
    """Test deleting a non-existent beat."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.story_beats.StoryBeatRepository") as MockBeatRepo:
        mock_beat_repo = MockBeatRepo.return_value
        mock_beat_repo.get_by_id = AsyncMock(return_value=None)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.delete(f"{settings.api_v1_prefix}/beats/999")
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 404

@pytest.mark.asyncio(loop_scope="session")
async def test_delete_story_beat_forbidden():
    """Test deleting a beat belonging to another user."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="Other World", user_id="other-user-id", laws={}, chronology_mode="linear")
    mock_story = Story(id="story-1", world_id="world-1", title="S", status="draft", created_at=datetime.now(), updated_at=datetime.now())
    mock_beat = StoryBeat(id="b1", story_id="story-1", order_index=1, content="C", type="scene", created_at=datetime.now(), updated_at=datetime.now())
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.story_beats.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.story_beats.StoryRepository") as MockStoryRepo, \
         patch("shinkei.api.v1.endpoints.story_beats.StoryBeatRepository") as MockBeatRepo:
        
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        mock_story_repo = MockStoryRepo.return_value
        mock_story_repo.get_by_id = AsyncMock(return_value=mock_story)
        
        mock_beat_repo = MockBeatRepo.return_value
        mock_beat_repo.get_by_id = AsyncMock(return_value=mock_beat)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.delete(f"{settings.api_v1_prefix}/beats/b1")
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 403

@pytest.mark.asyncio(loop_scope="session")
async def test_list_story_beats_with_pagination():
    """Test listing beats with pagination."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    mock_world = World(id="world-1", name="My World", user_id="test-user-id", laws={}, chronology_mode="linear")
    mock_story = Story(id="story-1", world_id="world-1", title="My Story", status="draft", created_at=datetime.now(), updated_at=datetime.now())
    
    mock_beats = [
        StoryBeat(id=f"b{i}", story_id="story-1", order_index=i, content=f"Beat {i}", type="scene", created_at=datetime.now(), updated_at=datetime.now())
        for i in range(1, 4)
    ]
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()
    
    with patch("shinkei.api.v1.endpoints.story_beats.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.story_beats.StoryRepository") as MockStoryRepo, \
         patch("shinkei.api.v1.endpoints.story_beats.StoryBeatRepository") as MockBeatRepo:
        
        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_id = AsyncMock(return_value=mock_world)
        
        mock_story_repo = MockStoryRepo.return_value
        mock_story_repo.get_by_id = AsyncMock(return_value=mock_story)
        
        mock_beat_repo = MockBeatRepo.return_value
        mock_beat_repo.list_by_story = AsyncMock(return_value=(mock_beats, 10))
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get(
                    f"{settings.api_v1_prefix}/stories/story-1/beats",
                    params={"skip": 0, "limit": 3}
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    mock_beat_repo.list_by_story.assert_called_once_with("story-1", skip=0, limit=3)
