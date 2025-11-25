"""Tests for Character API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from datetime import datetime

from shinkei.main import app
from shinkei.models.user import User
from shinkei.models.world import World
from shinkei.models.character import Character, EntityImportance
from shinkei.config import settings
from shinkei.auth.dependencies import get_current_user


@pytest.mark.asyncio(loop_scope="session")
async def test_create_character():
    """Test creating a new character."""
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
    mock_character = Character(
        id="char-1",
        world_id="world-1",
        name="Aragorn",
        description="Ranger",
        aliases=["Strider"],
        role="Protagonist",
        importance=EntityImportance.MAJOR,
        custom_metadata={"age": 87},
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()

    with patch("shinkei.api.v1.endpoints.characters.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.characters.CharacterRepository") as MockCharRepo:

        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_user_and_id = AsyncMock(return_value=mock_world)

        mock_char_repo = MockCharRepo.return_value
        mock_char_repo.create = AsyncMock(return_value=mock_character)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    f"{settings.api_v1_prefix}/worlds/world-1/characters",
                    json={
                        "name": "Aragorn",
                        "description": "Ranger",
                        "aliases": ["Strider"],
                        "role": "Protagonist",
                        "importance": "major",
                        "custom_metadata": {"age": 87}
                    }
                )
        finally:
            app.dependency_overrides = {}

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Aragorn"
    assert data["id"] == "char-1"
    assert data["importance"] == "major"
    assert "Strider" in data["aliases"]


@pytest.mark.asyncio(loop_scope="session")
async def test_list_characters():
    """Test listing characters."""
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
    mock_characters = [
        Character(id="1", world_id="world-1", name="Frodo", importance=EntityImportance.MAJOR, created_at=datetime.now(), updated_at=datetime.now()),
        Character(id="2", world_id="world-1", name="Sam", importance=EntityImportance.MAJOR, created_at=datetime.now(), updated_at=datetime.now())
    ]

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()

    with patch("shinkei.api.v1.endpoints.characters.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.characters.CharacterRepository") as MockCharRepo:

        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_user_and_id = AsyncMock(return_value=mock_world)

        mock_char_repo = MockCharRepo.return_value
        mock_char_repo.list_by_world = AsyncMock(return_value=(mock_characters, 2))

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get(f"{settings.api_v1_prefix}/worlds/world-1/characters")
        finally:
            app.dependency_overrides = {}

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["characters"]) == 2
    assert data["characters"][0]["name"] == "Frodo"


@pytest.mark.asyncio(loop_scope="session")
async def test_get_character():
    """Test getting a specific character."""
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
    mock_character = Character(
        id="char-1",
        world_id="world-1",
        name="Gandalf",
        importance=EntityImportance.MAJOR,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()

    with patch("shinkei.api.v1.endpoints.characters.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.characters.CharacterRepository") as MockCharRepo:

        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_user_and_id = AsyncMock(return_value=mock_world)

        mock_char_repo = MockCharRepo.return_value
        mock_char_repo.get_with_mention_count = AsyncMock(return_value=(mock_character, 5))

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get(f"{settings.api_v1_prefix}/worlds/world-1/characters/char-1")
        finally:
            app.dependency_overrides = {}

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Gandalf"
    assert data["mention_count"] == 5


@pytest.mark.asyncio(loop_scope="session")
async def test_update_character():
    """Test updating a character."""
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
    mock_character = Character(
        id="char-1",
        world_id="world-1",
        name="Aragorn",
        importance=EntityImportance.MAJOR,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    mock_updated_character = Character(
        id="char-1",
        world_id="world-1",
        name="Aragorn",
        description="King of Gondor",
        importance=EntityImportance.MAJOR,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()

    with patch("shinkei.api.v1.endpoints.characters.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.characters.CharacterRepository") as MockCharRepo:

        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_user_and_id = AsyncMock(return_value=mock_world)

        mock_char_repo = MockCharRepo.return_value
        mock_char_repo.get_by_world_and_id = AsyncMock(return_value=mock_character)
        mock_char_repo.update = AsyncMock(return_value=mock_updated_character)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.put(
                    f"{settings.api_v1_prefix}/worlds/world-1/characters/char-1",
                    json={"description": "King of Gondor"}
                )
        finally:
            app.dependency_overrides = {}

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "King of Gondor"


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_character():
    """Test deleting a character."""
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
    mock_character = Character(
        id="char-1",
        world_id="world-1",
        name="Boromir",
        importance=EntityImportance.MAJOR,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()

    with patch("shinkei.api.v1.endpoints.characters.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.characters.CharacterRepository") as MockCharRepo:

        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_user_and_id = AsyncMock(return_value=mock_world)

        mock_char_repo = MockCharRepo.return_value
        mock_char_repo.get_by_world_and_id = AsyncMock(return_value=mock_character)
        mock_char_repo.delete = AsyncMock(return_value=True)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.delete(f"{settings.api_v1_prefix}/worlds/world-1/characters/char-1")
        finally:
            app.dependency_overrides = {}

    assert response.status_code == 204


@pytest.mark.asyncio(loop_scope="session")
async def test_search_characters():
    """Test searching characters by name."""
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
    mock_character = Character(
        id="char-1",
        world_id="world-1",
        name="Frodo",
        importance=EntityImportance.MAJOR,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides["get_db_session"] = lambda: AsyncMock()

    with patch("shinkei.api.v1.endpoints.characters.WorldRepository") as MockWorldRepo, \
         patch("shinkei.api.v1.endpoints.characters.CharacterRepository") as MockCharRepo:

        mock_world_repo = MockWorldRepo.return_value
        mock_world_repo.get_by_user_and_id = AsyncMock(return_value=mock_world)

        mock_char_repo = MockCharRepo.return_value
        mock_char_repo.search_by_name = AsyncMock(return_value=[mock_character])
        mock_char_repo.get_with_mention_count = AsyncMock(return_value=(mock_character, 10))

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.get(f"{settings.api_v1_prefix}/worlds/world-1/characters/search?name=Frodo")
        finally:
            app.dependency_overrides = {}

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["characters"][0]["name"] == "Frodo"
    assert data["characters"][0]["mention_count"] == 10
