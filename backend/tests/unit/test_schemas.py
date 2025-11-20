"""Unit tests for Pydantic schemas."""
import pytest
from datetime import datetime
from pydantic import ValidationError

from shinkei.schemas.user import (
    UserSettings, UserBase, UserCreate, UserUpdate, UserResponse, UserListResponse
)
from shinkei.schemas.world import (
    WorldLaws, WorldBase, WorldCreate, WorldUpdate, WorldResponse, WorldListResponse
)
from shinkei.schemas.story import (
    StoryBase, StoryCreate, StoryUpdate, StoryResponse, StoryListResponse
)
from shinkei.schemas.story_beat import (
    StoryBeatBase, StoryBeatCreate, StoryBeatUpdate, StoryBeatResponse, StoryBeatListResponse
)
from shinkei.schemas.world_event import (
    WorldEventBase, WorldEventCreate, WorldEventUpdate, WorldEventResponse, WorldEventListResponse
)


class TestUserSchemas:
    """Tests for User Pydantic schemas."""

    def test_user_settings_defaults(self):
        """Test UserSettings with default values."""
        settings = UserSettings()
        assert settings.language == "en"
        assert settings.default_model == "gpt-4"
        assert settings.ui_theme == "system"
        assert settings.llm_provider == "openai"
        assert settings.llm_model == "gpt-4"
        assert settings.llm_base_url is None

    def test_user_settings_custom_values(self):
        """Test UserSettings with custom values."""
        settings = UserSettings(
            language="fr",
            default_model="claude-3",
            ui_theme="dark",
            llm_provider="anthropic",
            llm_model="claude-3-opus",
            llm_base_url="https://custom.api.com"
        )
        assert settings.language == "fr"
        assert settings.default_model == "claude-3"
        assert settings.ui_theme == "dark"
        assert settings.llm_provider == "anthropic"
        assert settings.llm_model == "claude-3-opus"
        assert settings.llm_base_url == "https://custom.api.com"

    def test_user_base_valid_email(self):
        """Test UserBase with valid email."""
        user = UserBase(
            email="test@example.com",
            name="Test User"
        )
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert isinstance(user.settings, UserSettings)

    def test_user_base_invalid_email(self):
        """Test UserBase with invalid email."""
        with pytest.raises(ValidationError) as exc_info:
            UserBase(email="invalid-email", name="Test")

        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("email" in str(error) for error in errors)

    def test_user_base_name_min_length(self):
        """Test UserBase name minimum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            UserBase(email="test@example.com", name="")

        errors = exc_info.value.errors()
        assert any("name" in error.get("loc", []) for error in errors)

    def test_user_base_name_max_length(self):
        """Test UserBase name maximum length validation."""
        long_name = "a" * 256
        with pytest.raises(ValidationError) as exc_info:
            UserBase(email="test@example.com", name=long_name)

        errors = exc_info.value.errors()
        assert any("name" in error.get("loc", []) for error in errors)

    def test_user_create_valid(self):
        """Test UserCreate with valid data."""
        user = UserCreate(
            email="create@example.com",
            name="Create User",
            id="some-uuid"
        )
        assert user.email == "create@example.com"
        assert user.name == "Create User"
        assert user.id == "some-uuid"

    def test_user_create_without_id(self):
        """Test UserCreate without ID (will be provided by Supabase)."""
        user = UserCreate(
            email="create@example.com",
            name="Create User"
        )
        assert user.id is None

    def test_user_update_partial(self):
        """Test UserUpdate with partial data."""
        update = UserUpdate(name="New Name")
        assert update.name == "New Name"
        assert update.settings is None

    def test_user_update_settings_only(self):
        """Test UserUpdate with settings only."""
        update = UserUpdate(settings=UserSettings(language="es"))
        assert update.name is None
        assert update.settings.language == "es"

    def test_user_update_extra_fields_forbidden(self):
        """Test UserUpdate rejects extra fields."""
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(name="Test", extra_field="not allowed")

        errors = exc_info.value.errors()
        assert any("extra_field" in error.get("loc", []) for error in errors)

    def test_user_response_valid(self):
        """Test UserResponse with valid data."""
        now = datetime.utcnow()
        response = UserResponse(
            id="test-uuid",
            email="response@example.com",
            name="Response User",
            settings=UserSettings(),
            created_at=now,
            updated_at=now
        )
        assert response.id == "test-uuid"
        assert response.email == "response@example.com"
        assert response.created_at == now
        assert response.updated_at == now

    def test_user_list_response(self):
        """Test UserListResponse."""
        now = datetime.utcnow()
        users = [
            UserResponse(
                id="1",
                email="user1@example.com",
                name="User 1",
                settings=UserSettings(),
                created_at=now,
                updated_at=now
            ),
            UserResponse(
                id="2",
                email="user2@example.com",
                name="User 2",
                settings=UserSettings(),
                created_at=now,
                updated_at=now
            )
        ]
        response = UserListResponse(
            users=users,
            total=2,
            page=1,
            page_size=10
        )
        assert len(response.users) == 2
        assert response.total == 2
        assert response.page == 1
        assert response.page_size == 10


class TestWorldSchemas:
    """Tests for World Pydantic schemas."""

    def test_world_laws_defaults(self):
        """Test WorldLaws with default values."""
        laws = WorldLaws()
        assert laws.physics is None
        assert laws.metaphysics is None
        assert laws.social is None
        assert laws.forbidden is None

    def test_world_laws_custom_values(self):
        """Test WorldLaws with custom values."""
        laws = WorldLaws(
            physics="Newtonian",
            metaphysics="No magic",
            social="Democratic",
            forbidden="Time travel"
        )
        assert laws.physics == "Newtonian"
        assert laws.metaphysics == "No magic"
        assert laws.social == "Democratic"
        assert laws.forbidden == "Time travel"

    def test_world_base_valid(self):
        """Test WorldBase with valid data."""
        world = WorldBase(
            name="Test World",
            description="A test world",
            tone="dark, cold",
            backdrop="Space station",
            laws=WorldLaws(),
            chronology_mode="linear"
        )
        assert world.name == "Test World"
        assert world.description == "A test world"
        assert world.tone == "dark, cold"
        assert world.backdrop == "Space station"
        assert world.chronology_mode == "linear"

    def test_world_base_name_min_length(self):
        """Test WorldBase name minimum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            WorldBase(name="")

        errors = exc_info.value.errors()
        assert any("name" in error.get("loc", []) for error in errors)

    def test_world_base_name_max_length(self):
        """Test WorldBase name maximum length validation."""
        long_name = "a" * 256
        with pytest.raises(ValidationError) as exc_info:
            WorldBase(name=long_name)

        errors = exc_info.value.errors()
        assert any("name" in error.get("loc", []) for error in errors)

    def test_world_base_tone_max_length(self):
        """Test WorldBase tone maximum length validation."""
        long_tone = "a" * 501
        with pytest.raises(ValidationError) as exc_info:
            WorldBase(name="Test", tone=long_tone)

        errors = exc_info.value.errors()
        assert any("tone" in error.get("loc", []) for error in errors)

    def test_world_base_chronology_mode_valid_values(self):
        """Test WorldBase chronology_mode accepts valid values."""
        for mode in ["linear", "fragmented", "timeless"]:
            world = WorldBase(name="Test", chronology_mode=mode)
            assert world.chronology_mode == mode

    def test_world_base_chronology_mode_invalid(self):
        """Test WorldBase chronology_mode rejects invalid values."""
        with pytest.raises(ValidationError) as exc_info:
            WorldBase(name="Test", chronology_mode="invalid")

        errors = exc_info.value.errors()
        assert any("chronology_mode" in error.get("loc", []) for error in errors)

    def test_world_create_valid(self):
        """Test WorldCreate with valid data."""
        world = WorldCreate(
            name="Create World",
            description="Test description",
            laws=WorldLaws(physics="Standard")
        )
        assert world.name == "Create World"
        assert world.description == "Test description"
        assert world.laws.physics == "Standard"

    def test_world_update_partial(self):
        """Test WorldUpdate with partial data."""
        update = WorldUpdate(name="Updated World")
        assert update.name == "Updated World"
        assert update.description is None

    def test_world_update_extra_fields_forbidden(self):
        """Test WorldUpdate rejects extra fields."""
        with pytest.raises(ValidationError) as exc_info:
            WorldUpdate(name="Test", invalid_field="not allowed")

        errors = exc_info.value.errors()
        assert any("invalid_field" in error.get("loc", []) for error in errors)

    def test_world_response_valid(self):
        """Test WorldResponse with valid data."""
        now = datetime.utcnow()
        response = WorldResponse(
            id="world-uuid",
            user_id="user-uuid",
            name="Response World",
            description="Test",
            tone="neutral",
            backdrop="Test backdrop",
            laws=WorldLaws(),
            chronology_mode="linear",
            created_at=now,
            updated_at=now
        )
        assert response.id == "world-uuid"
        assert response.user_id == "user-uuid"
        assert response.name == "Response World"

    def test_world_list_response(self):
        """Test WorldListResponse."""
        now = datetime.utcnow()
        worlds = [
            WorldResponse(
                id="1",
                user_id="user-1",
                name="World 1",
                laws=WorldLaws(),
                chronology_mode="linear",
                created_at=now,
                updated_at=now
            )
        ]
        response = WorldListResponse(
            worlds=worlds,
            total=1,
            page=1,
            page_size=10
        )
        assert len(response.worlds) == 1
        assert response.total == 1


class TestStorySchemas:
    """Tests for Story Pydantic schemas."""

    def test_story_base_valid(self):
        """Test StoryBase with valid data."""
        story = StoryBase(
            title="Test Story",
            synopsis="A test synopsis",
            theme="Adventure",
            status="draft"
        )
        assert story.title == "Test Story"
        assert story.synopsis == "A test synopsis"
        assert story.theme == "Adventure"
        assert story.status == "draft"

    def test_story_base_title_min_length(self):
        """Test StoryBase title minimum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            StoryBase(title="")

        errors = exc_info.value.errors()
        assert any("title" in error.get("loc", []) for error in errors)

    def test_story_base_title_max_length(self):
        """Test StoryBase title maximum length validation."""
        long_title = "a" * 256
        with pytest.raises(ValidationError) as exc_info:
            StoryBase(title=long_title)

        errors = exc_info.value.errors()
        assert any("title" in error.get("loc", []) for error in errors)

    def test_story_base_status_valid_values(self):
        """Test StoryBase status accepts valid values."""
        for status in ["draft", "active", "completed", "archived"]:
            story = StoryBase(title="Test", status=status)
            assert story.status == status

    def test_story_base_status_invalid(self):
        """Test StoryBase status rejects invalid values."""
        with pytest.raises(ValidationError) as exc_info:
            StoryBase(title="Test", status="invalid")

        errors = exc_info.value.errors()
        assert any("status" in error.get("loc", []) for error in errors)

    def test_story_base_theme_max_length(self):
        """Test StoryBase theme maximum length validation."""
        long_theme = "a" * 256
        with pytest.raises(ValidationError) as exc_info:
            StoryBase(title="Test", theme=long_theme)

        errors = exc_info.value.errors()
        assert any("theme" in error.get("loc", []) for error in errors)

    def test_story_create_valid(self):
        """Test StoryCreate with valid data."""
        story = StoryCreate(
            title="Create Story",
            synopsis="Test synopsis"
        )
        assert story.title == "Create Story"
        assert story.synopsis == "Test synopsis"

    def test_story_update_partial(self):
        """Test StoryUpdate with partial data."""
        update = StoryUpdate(title="Updated Title")
        assert update.title == "Updated Title"
        assert update.synopsis is None

    def test_story_update_extra_fields_forbidden(self):
        """Test StoryUpdate rejects extra fields."""
        with pytest.raises(ValidationError) as exc_info:
            StoryUpdate(title="Test", extra="not allowed")

        errors = exc_info.value.errors()
        assert any("extra" in error.get("loc", []) for error in errors)

    def test_story_response_valid(self):
        """Test StoryResponse with valid data."""
        now = datetime.utcnow()
        response = StoryResponse(
            id="story-uuid",
            world_id="world-uuid",
            title="Response Story",
            synopsis="Test synopsis",
            theme="Drama",
            status="active",
            created_at=now,
            updated_at=now
        )
        assert response.id == "story-uuid"
        assert response.world_id == "world-uuid"
        assert response.title == "Response Story"

    def test_story_list_response(self):
        """Test StoryListResponse."""
        now = datetime.utcnow()
        stories = [
            StoryResponse(
                id="1",
                world_id="world-1",
                title="Story 1",
                status="draft",
                created_at=now,
                updated_at=now
            )
        ]
        response = StoryListResponse(
            stories=stories,
            total=1,
            page=1,
            page_size=10
        )
        assert len(response.stories) == 1
        assert response.total == 1


class TestStoryBeatSchemas:
    """Tests for StoryBeat Pydantic schemas."""

    def test_story_beat_base_valid(self):
        """Test StoryBeatBase with valid data."""
        beat = StoryBeatBase(
            order_index=1,
            content="This is a test beat",
            type="scene",
            world_event_id="event-uuid"
        )
        assert beat.order_index == 1
        assert beat.content == "This is a test beat"
        assert beat.type == "scene"
        assert beat.world_event_id == "event-uuid"

    def test_story_beat_base_content_min_length(self):
        """Test StoryBeatBase content minimum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            StoryBeatBase(order_index=1, content="")

        errors = exc_info.value.errors()
        assert any("content" in error.get("loc", []) for error in errors)

    def test_story_beat_base_type_valid_values(self):
        """Test StoryBeatBase type accepts valid values."""
        for beat_type in ["scene", "summary", "note"]:
            beat = StoryBeatBase(order_index=1, content="Test", type=beat_type)
            assert beat.type == beat_type

    def test_story_beat_base_type_invalid(self):
        """Test StoryBeatBase type rejects invalid values."""
        with pytest.raises(ValidationError) as exc_info:
            StoryBeatBase(order_index=1, content="Test", type="invalid")

        errors = exc_info.value.errors()
        assert any("type" in error.get("loc", []) for error in errors)

    def test_story_beat_base_optional_world_event(self):
        """Test StoryBeatBase with optional world_event_id."""
        beat = StoryBeatBase(order_index=1, content="Test")
        assert beat.world_event_id is None

    def test_story_beat_create_valid(self):
        """Test StoryBeatCreate with valid data."""
        beat = StoryBeatCreate(
            order_index=5,
            content="Create beat content",
            type="summary"
        )
        assert beat.order_index == 5
        assert beat.content == "Create beat content"
        assert beat.type == "summary"

    def test_story_beat_update_partial(self):
        """Test StoryBeatUpdate with partial data."""
        update = StoryBeatUpdate(content="Updated content")
        assert update.content == "Updated content"
        assert update.order_index is None
        assert update.type is None

    def test_story_beat_update_extra_fields_forbidden(self):
        """Test StoryBeatUpdate rejects extra fields."""
        with pytest.raises(ValidationError) as exc_info:
            StoryBeatUpdate(content="Test", invalid="not allowed")

        errors = exc_info.value.errors()
        assert any("invalid" in error.get("loc", []) for error in errors)

    def test_story_beat_response_valid(self):
        """Test StoryBeatResponse with valid data."""
        now = datetime.utcnow()
        response = StoryBeatResponse(
            id="beat-uuid",
            story_id="story-uuid",
            order_index=3,
            content="Response beat content",
            type="scene",
            world_event_id=None,
            created_at=now,
            updated_at=now
        )
        assert response.id == "beat-uuid"
        assert response.story_id == "story-uuid"
        assert response.order_index == 3

    def test_story_beat_list_response(self):
        """Test StoryBeatListResponse."""
        now = datetime.utcnow()
        beats = [
            StoryBeatResponse(
                id="1",
                story_id="story-1",
                order_index=1,
                content="Beat 1",
                type="scene",
                created_at=now,
                updated_at=now
            )
        ]
        response = StoryBeatListResponse(
            beats=beats,
            total=1,
            page=1,
            page_size=10
        )
        assert len(response.beats) == 1
        assert response.total == 1


class TestWorldEventSchemas:
    """Tests for WorldEvent Pydantic schemas."""

    def test_world_event_base_valid(self):
        """Test WorldEventBase with valid data."""
        event = WorldEventBase(
            t=42.5,
            label_time="Day 42",
            location_id="location-uuid",
            type="combat",
            summary="A major battle",
            tags=["important", "combat"]
        )
        assert event.t == 42.5
        assert event.label_time == "Day 42"
        assert event.location_id == "location-uuid"
        assert event.type == "combat"
        assert event.summary == "A major battle"
        assert event.tags == ["important", "combat"]

    def test_world_event_base_label_time_min_length(self):
        """Test WorldEventBase label_time minimum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            WorldEventBase(
                t=1.0,
                label_time="",
                type="test",
                summary="Test"
            )

        errors = exc_info.value.errors()
        assert any("label_time" in error.get("loc", []) for error in errors)

    def test_world_event_base_label_time_max_length(self):
        """Test WorldEventBase label_time maximum length validation."""
        long_label = "a" * 256
        with pytest.raises(ValidationError) as exc_info:
            WorldEventBase(
                t=1.0,
                label_time=long_label,
                type="test",
                summary="Test"
            )

        errors = exc_info.value.errors()
        assert any("label_time" in error.get("loc", []) for error in errors)

    def test_world_event_base_type_min_length(self):
        """Test WorldEventBase type minimum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            WorldEventBase(
                t=1.0,
                label_time="Test",
                type="",
                summary="Test"
            )

        errors = exc_info.value.errors()
        assert any("type" in error.get("loc", []) for error in errors)

    def test_world_event_base_type_max_length(self):
        """Test WorldEventBase type maximum length validation."""
        long_type = "a" * 101
        with pytest.raises(ValidationError) as exc_info:
            WorldEventBase(
                t=1.0,
                label_time="Test",
                type=long_type,
                summary="Test"
            )

        errors = exc_info.value.errors()
        assert any("type" in error.get("loc", []) for error in errors)

    def test_world_event_base_summary_min_length(self):
        """Test WorldEventBase summary minimum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            WorldEventBase(
                t=1.0,
                label_time="Test",
                type="test",
                summary=""
            )

        errors = exc_info.value.errors()
        assert any("summary" in error.get("loc", []) for error in errors)

    def test_world_event_base_empty_tags(self):
        """Test WorldEventBase with empty tags list."""
        event = WorldEventBase(
            t=1.0,
            label_time="Test",
            type="test",
            summary="Test summary",
            tags=[]
        )
        assert event.tags == []

    def test_world_event_base_default_tags(self):
        """Test WorldEventBase tags default factory."""
        event = WorldEventBase(
            t=1.0,
            label_time="Test",
            type="test",
            summary="Test summary"
        )
        assert event.tags == []

    def test_world_event_create_valid(self):
        """Test WorldEventCreate with valid data."""
        event = WorldEventCreate(
            t=100.0,
            label_time="Log 100",
            type="discovery",
            summary="Found something interesting",
            tags=["discovery", "important"]
        )
        assert event.t == 100.0
        assert event.label_time == "Log 100"
        assert event.type == "discovery"

    def test_world_event_update_partial(self):
        """Test WorldEventUpdate with partial data."""
        update = WorldEventUpdate(summary="Updated summary")
        assert update.summary == "Updated summary"
        assert update.t is None
        assert update.label_time is None

    def test_world_event_update_extra_fields_forbidden(self):
        """Test WorldEventUpdate rejects extra fields."""
        with pytest.raises(ValidationError) as exc_info:
            WorldEventUpdate(summary="Test", invalid="not allowed")

        errors = exc_info.value.errors()
        assert any("invalid" in error.get("loc", []) for error in errors)

    def test_world_event_response_valid(self):
        """Test WorldEventResponse with valid data."""
        now = datetime.utcnow()
        response = WorldEventResponse(
            id="event-uuid",
            world_id="world-uuid",
            t=50.0,
            label_time="Event 50",
            location_id=None,
            type="meeting",
            summary="An important meeting",
            tags=["meeting"],
            created_at=now,
            updated_at=now
        )
        assert response.id == "event-uuid"
        assert response.world_id == "world-uuid"
        assert response.t == 50.0

    def test_world_event_list_response(self):
        """Test WorldEventListResponse."""
        now = datetime.utcnow()
        events = [
            WorldEventResponse(
                id="1",
                world_id="world-1",
                t=1.0,
                label_time="Event 1",
                type="test",
                summary="Test event",
                tags=[],
                created_at=now,
                updated_at=now
            )
        ]
        response = WorldEventListResponse(
            events=events,
            total=1,
            page=1,
            page_size=10
        )
        assert len(response.events) == 1
        assert response.total == 1
