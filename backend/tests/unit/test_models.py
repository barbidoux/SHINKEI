"""Unit tests for SQLAlchemy models."""
import pytest
from datetime import datetime
import uuid
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from shinkei.models.user import User
from shinkei.models.world import World, ChronologyMode
from shinkei.models.story import Story, StoryStatus
from shinkei.models.story_beat import StoryBeat, BeatType
from shinkei.models.world_event import WorldEvent


class TestUserModel:
    """Tests for User model."""

    def test_user_creation_with_defaults(self, db_session: Session):
        """Test creating a user with default values."""
        user = User(
            email="test@example.com",
            name="Test User"
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert len(user.id) == 36  # UUID string length
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.settings == {}
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_user_creation_with_settings(self, db_session: Session):
        """Test creating a user with custom settings."""
        settings = {
            "language": "en",
            "theme": "dark",
            "default_model": "gpt-4"
        }
        user = User(
            email="user@example.com",
            name="User",
            settings=settings
        )
        db_session.add(user)
        db_session.commit()

        assert user.settings == settings
        assert user.settings["language"] == "en"

    def test_user_uuid_generation(self, db_session: Session):
        """Test that user IDs are valid UUIDs."""
        user = User(email="uuid@test.com", name="UUID Test")
        db_session.add(user)
        db_session.commit()

        # Should be parseable as UUID
        parsed_uuid = uuid.UUID(user.id)
        assert str(parsed_uuid) == user.id

    def test_user_email_uniqueness(self, db_session: Session):
        """Test that email must be unique."""
        user1 = User(email="duplicate@test.com", name="User 1")
        db_session.add(user1)
        db_session.commit()

        user2 = User(email="duplicate@test.com", name="User 2")
        db_session.add(user2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_required_fields(self, db_session: Session):
        """Test that required fields cannot be null."""
        # Missing email
        with pytest.raises(Exception):
            user = User(name="No Email")
            db_session.add(user)
            db_session.commit()

        db_session.rollback()

        # Missing name
        with pytest.raises(Exception):
            user = User(email="noemail@test.com")
            db_session.add(user)
            db_session.commit()

    def test_user_repr(self, db_session: Session):
        """Test user string representation."""
        user = User(email="repr@test.com", name="Repr Test")
        db_session.add(user)
        db_session.commit()

        repr_str = repr(user)
        assert "User" in repr_str
        assert user.id in repr_str
        assert "repr@test.com" in repr_str
        assert "Repr Test" in repr_str

    def test_user_worlds_relationship(self, db_session: Session):
        """Test user-worlds relationship and cascade deletion."""
        user = User(email="cascade@test.com", name="Cascade Test")
        db_session.add(user)
        db_session.commit()

        world = World(
            user_id=user.id,
            name="Test World",
            laws={}
        )
        db_session.add(world)
        db_session.commit()

        # Check relationship
        assert len(user.worlds) == 1
        assert user.worlds[0].name == "Test World"

        # Test cascade deletion
        user_id = user.id
        world_id = world.id
        db_session.delete(user)
        db_session.commit()

        # World should be deleted due to cascade
        deleted_world = db_session.get(World, world_id)
        assert deleted_world is None


class TestWorldModel:
    """Tests for World model."""

    def test_world_creation_with_defaults(self, db_session: Session, test_user: User):
        """Test creating a world with default values."""
        world = World(
            user_id=test_user.id,
            name="Test World",
            laws={}
        )
        db_session.add(world)
        db_session.commit()

        assert world.id is not None
        assert len(world.id) == 36
        assert world.user_id == test_user.id
        assert world.name == "Test World"
        assert world.description is None
        assert world.tone is None
        assert world.backdrop is None
        assert world.laws == {}
        assert world.chronology_mode == ChronologyMode.LINEAR
        assert isinstance(world.created_at, datetime)
        assert isinstance(world.updated_at, datetime)

    def test_world_creation_with_full_data(self, db_session: Session, test_user: User):
        """Test creating a world with all fields populated."""
        laws = {
            "physics": "Standard Newtonian physics",
            "metaphysics": "No magic",
            "social": "Isolated colonies",
            "forbidden": ["time travel", "FTL travel"]
        }

        world = World(
            user_id=test_user.id,
            name="Complex World",
            description="A detailed world with complex rules",
            tone="dark, introspective, cold",
            backdrop="A dying space station orbiting a black hole",
            laws=laws,
            chronology_mode=ChronologyMode.FRAGMENTED
        )
        db_session.add(world)
        db_session.commit()

        assert world.description == "A detailed world with complex rules"
        assert world.tone == "dark, introspective, cold"
        assert world.backdrop == "A dying space station orbiting a black hole"
        assert world.laws == laws
        assert world.chronology_mode == ChronologyMode.FRAGMENTED

    def test_world_chronology_modes(self, db_session: Session, test_user: User):
        """Test all chronology mode enum values."""
        modes = [ChronologyMode.LINEAR, ChronologyMode.FRAGMENTED, ChronologyMode.TIMELESS]

        for mode in modes:
            world = World(
                user_id=test_user.id,
                name=f"World {mode.value}",
                laws={},
                chronology_mode=mode
            )
            db_session.add(world)
            db_session.commit()

            assert world.chronology_mode == mode

            # Fetch from DB to ensure enum is properly stored/retrieved
            fetched_world = db_session.get(World, world.id)
            assert fetched_world.chronology_mode == mode

    def test_world_laws_json_handling(self, db_session: Session, test_user: User):
        """Test that laws JSON field handles complex data."""
        complex_laws = {
            "physics": ["gravity", "thermodynamics"],
            "metaphysics": {
                "magic": False,
                "psychic_powers": True,
                "tech_level": 5
            },
            "social": "Democratic federation",
            "forbidden": []
        }

        world = World(
            user_id=test_user.id,
            name="JSON World",
            laws=complex_laws
        )
        db_session.add(world)
        db_session.commit()

        # Fetch from DB
        fetched_world = db_session.get(World, world.id)
        assert fetched_world.laws == complex_laws
        assert fetched_world.laws["metaphysics"]["tech_level"] == 5

    def test_world_required_fields(self, db_session: Session, test_user: User):
        """Test that required fields cannot be null."""
        # Missing user_id
        with pytest.raises(Exception):
            world = World(name="No User", laws={})
            db_session.add(world)
            db_session.commit()

        db_session.rollback()

        # Missing name
        with pytest.raises(Exception):
            world = World(user_id=test_user.id, laws={})
            db_session.add(world)
            db_session.commit()

    def test_world_user_relationship(self, db_session: Session, test_user: User):
        """Test world-user relationship."""
        world = World(
            user_id=test_user.id,
            name="Relationship World",
            laws={}
        )
        db_session.add(world)
        db_session.commit()

        assert world.user.id == test_user.id
        assert world.user.email == test_user.email

    def test_world_cascade_deletion_with_stories(self, db_session: Session, test_user: User):
        """Test that deleting a world cascades to stories."""
        world = World(user_id=test_user.id, name="Cascade World", laws={})
        db_session.add(world)
        db_session.commit()

        story = Story(world_id=world.id, title="Test Story")
        db_session.add(story)
        db_session.commit()

        world_id = world.id
        story_id = story.id

        db_session.delete(world)
        db_session.commit()

        # Story should be deleted
        deleted_story = db_session.get(Story, story_id)
        assert deleted_story is None

    def test_world_repr(self, db_session: Session, test_user: User):
        """Test world string representation."""
        world = World(user_id=test_user.id, name="Repr World", laws={})
        db_session.add(world)
        db_session.commit()

        repr_str = repr(world)
        assert "World" in repr_str
        assert world.id in repr_str
        assert "Repr World" in repr_str
        assert test_user.id in repr_str


class TestStoryModel:
    """Tests for Story model."""

    def test_story_creation_with_defaults(self, db_session: Session, test_world: World):
        """Test creating a story with default values."""
        story = Story(
            world_id=test_world.id,
            title="Test Story"
        )
        db_session.add(story)
        db_session.commit()

        assert story.id is not None
        assert len(story.id) == 36
        assert story.world_id == test_world.id
        assert story.title == "Test Story"
        assert story.synopsis is None
        assert story.theme is None
        assert story.status == StoryStatus.DRAFT
        assert isinstance(story.created_at, datetime)
        assert isinstance(story.updated_at, datetime)

    def test_story_creation_with_full_data(self, db_session: Session, test_world: World):
        """Test creating a story with all fields."""
        story = Story(
            world_id=test_world.id,
            title="Complete Story",
            synopsis="A story about everything",
            theme="Redemption",
            status=StoryStatus.ACTIVE
        )
        db_session.add(story)
        db_session.commit()

        assert story.synopsis == "A story about everything"
        assert story.theme == "Redemption"
        assert story.status == StoryStatus.ACTIVE

    def test_story_status_enum_values(self, db_session: Session, test_world: World):
        """Test all story status enum values."""
        statuses = [
            StoryStatus.DRAFT,
            StoryStatus.ACTIVE,
            StoryStatus.COMPLETED,
            StoryStatus.ARCHIVED
        ]

        for status in statuses:
            story = Story(
                world_id=test_world.id,
                title=f"Story {status.value}",
                status=status
            )
            db_session.add(story)
            db_session.commit()

            assert story.status == status

            # Fetch from DB
            fetched_story = db_session.get(Story, story.id)
            assert fetched_story.status == status

    def test_story_required_fields(self, db_session: Session, test_world: World):
        """Test that required fields cannot be null."""
        # Missing title
        with pytest.raises(Exception):
            story = Story(world_id=test_world.id)
            db_session.add(story)
            db_session.commit()

        db_session.rollback()

        # Missing world_id
        with pytest.raises(Exception):
            story = Story(title="No World")
            db_session.add(story)
            db_session.commit()

    def test_story_world_relationship(self, db_session: Session, test_world: World):
        """Test story-world relationship."""
        story = Story(world_id=test_world.id, title="Relationship Story")
        db_session.add(story)
        db_session.commit()

        assert story.world.id == test_world.id
        assert story.world.name == test_world.name

    def test_story_cascade_deletion_with_beats(self, db_session: Session, test_world: World):
        """Test that deleting a story cascades to beats."""
        story = Story(world_id=test_world.id, title="Cascade Story")
        db_session.add(story)
        db_session.commit()

        beat = StoryBeat(
            story_id=story.id,
            order_index=1,
            content="Test content"
        )
        db_session.add(beat)
        db_session.commit()

        story_id = story.id
        beat_id = beat.id

        db_session.delete(story)
        db_session.commit()

        # Beat should be deleted
        deleted_beat = db_session.get(StoryBeat, beat_id)
        assert deleted_beat is None

    def test_story_repr(self, db_session: Session, test_world: World):
        """Test story string representation."""
        story = Story(world_id=test_world.id, title="Repr Story")
        db_session.add(story)
        db_session.commit()

        repr_str = repr(story)
        assert "Story" in repr_str
        assert story.id in repr_str
        assert test_world.id in repr_str
        assert "Repr Story" in repr_str


class TestStoryBeatModel:
    """Tests for StoryBeat model."""

    def test_story_beat_creation_with_defaults(self, db_session: Session, test_story: Story):
        """Test creating a story beat with default values."""
        beat = StoryBeat(
            story_id=test_story.id,
            order_index=1,
            content="This is a test beat."
        )
        db_session.add(beat)
        db_session.commit()

        assert beat.id is not None
        assert len(beat.id) == 36
        assert beat.story_id == test_story.id
        assert beat.order_index == 1
        assert beat.content == "This is a test beat."
        assert beat.type == BeatType.SCENE
        assert beat.world_event_id is None
        assert isinstance(beat.created_at, datetime)
        assert isinstance(beat.updated_at, datetime)

    def test_story_beat_creation_with_world_event(
        self, db_session: Session, test_story: Story, test_world_event: WorldEvent
    ):
        """Test creating a story beat linked to a world event."""
        beat = StoryBeat(
            story_id=test_story.id,
            order_index=1,
            content="Beat linked to event",
            world_event_id=test_world_event.id
        )
        db_session.add(beat)
        db_session.commit()

        assert beat.world_event_id == test_world_event.id
        assert beat.world_event.label_time == test_world_event.label_time

    def test_story_beat_type_enum_values(self, db_session: Session, test_story: Story):
        """Test all beat type enum values."""
        types = [BeatType.SCENE, BeatType.SUMMARY, BeatType.NOTE]

        for i, beat_type in enumerate(types, start=1):
            beat = StoryBeat(
                story_id=test_story.id,
                order_index=i,
                content=f"Beat of type {beat_type.value}",
                type=beat_type
            )
            db_session.add(beat)
            db_session.commit()

            assert beat.type == beat_type

            # Fetch from DB
            fetched_beat = db_session.get(StoryBeat, beat.id)
            assert fetched_beat.type == beat_type

    def test_story_beat_ordering(self, db_session: Session, test_story: Story):
        """Test that beats can be ordered correctly."""
        beats = []
        for i in range(1, 6):
            beat = StoryBeat(
                story_id=test_story.id,
                order_index=i,
                content=f"Beat {i}"
            )
            db_session.add(beat)
            beats.append(beat)

        db_session.commit()

        # Verify ordering
        for i, beat in enumerate(beats, start=1):
            assert beat.order_index == i

    def test_story_beat_required_fields(self, db_session: Session, test_story: Story):
        """Test that required fields cannot be null."""
        # Missing content
        with pytest.raises(Exception):
            beat = StoryBeat(story_id=test_story.id, order_index=1)
            db_session.add(beat)
            db_session.commit()

        db_session.rollback()

        # Missing order_index
        with pytest.raises(Exception):
            beat = StoryBeat(story_id=test_story.id, content="No order")
            db_session.add(beat)
            db_session.commit()

    def test_story_beat_story_relationship(self, db_session: Session, test_story: Story):
        """Test beat-story relationship."""
        beat = StoryBeat(
            story_id=test_story.id,
            order_index=1,
            content="Relationship beat"
        )
        db_session.add(beat)
        db_session.commit()

        assert beat.story.id == test_story.id
        assert beat.story.title == test_story.title

    def test_story_beat_world_event_null_on_delete(
        self, db_session: Session, test_story: Story
    ):
        """Test that deleting a world event sets beat's world_event_id to NULL."""
        # Create world event
        world_event = WorldEvent(
            world_id=test_story.world_id,
            t=100.0,
            label_time="Test Time",
            type="test",
            summary="Test event"
        )
        db_session.add(world_event)
        db_session.commit()

        # Create beat linked to event
        beat = StoryBeat(
            story_id=test_story.id,
            order_index=1,
            content="Linked beat",
            world_event_id=world_event.id
        )
        db_session.add(beat)
        db_session.commit()

        beat_id = beat.id

        # Delete world event
        db_session.delete(world_event)
        db_session.commit()

        # Beat should still exist but with null world_event_id
        fetched_beat = db_session.get(StoryBeat, beat_id)
        assert fetched_beat is not None
        assert fetched_beat.world_event_id is None

    def test_story_beat_repr(self, db_session: Session, test_story: Story):
        """Test beat string representation."""
        beat = StoryBeat(
            story_id=test_story.id,
            order_index=42,
            content="Repr beat"
        )
        db_session.add(beat)
        db_session.commit()

        repr_str = repr(beat)
        assert "StoryBeat" in repr_str
        assert beat.id in repr_str
        assert test_story.id in repr_str
        assert "42" in repr_str


class TestWorldEventModel:
    """Tests for WorldEvent model."""

    def test_world_event_creation_with_defaults(self, db_session: Session, test_world: World):
        """Test creating a world event with minimal data."""
        event = WorldEvent(
            world_id=test_world.id,
            t=0.0,
            label_time="Initial Event",
            type="genesis",
            summary="The beginning of everything"
        )
        db_session.add(event)
        db_session.commit()

        assert event.id is not None
        assert len(event.id) == 36
        assert event.world_id == test_world.id
        assert event.t == 0.0
        assert event.label_time == "Initial Event"
        assert event.type == "genesis"
        assert event.summary == "The beginning of everything"
        assert event.location_id is None
        assert event.tags == []
        assert isinstance(event.created_at, datetime)
        assert isinstance(event.updated_at, datetime)

    def test_world_event_creation_with_full_data(self, db_session: Session, test_world: World):
        """Test creating a world event with all fields."""
        tags = ["important", "combat", "character_death"]
        event = WorldEvent(
            world_id=test_world.id,
            t=42.5,
            label_time="Day 42, Hour 12",
            location_id="some-location-uuid",
            type="combat",
            summary="Major battle occurs at the station",
            tags=tags
        )
        db_session.add(event)
        db_session.commit()

        assert event.t == 42.5
        assert event.label_time == "Day 42, Hour 12"
        assert event.location_id == "some-location-uuid"
        assert event.tags == tags

    def test_world_event_temporal_ordering(self, db_session: Session, test_world: World):
        """Test that events can be ordered by time."""
        times = [0.0, 10.5, 20.0, 35.7, 100.0]
        events = []

        for t in times:
            event = WorldEvent(
                world_id=test_world.id,
                t=t,
                label_time=f"Time {t}",
                type="test",
                summary=f"Event at {t}"
            )
            db_session.add(event)
            events.append(event)

        db_session.commit()

        # Verify temporal values
        for event, expected_t in zip(events, times):
            assert event.t == expected_t

    def test_world_event_tags_array(self, db_session: Session, test_world: World):
        """Test that tags array handles multiple values."""
        tags = ["tag1", "tag2", "tag3", "tag-with-dash", "tag_with_underscore"]
        event = WorldEvent(
            world_id=test_world.id,
            t=1.0,
            label_time="Tagged Event",
            type="test",
            summary="Event with many tags",
            tags=tags
        )
        db_session.add(event)
        db_session.commit()

        # Fetch from DB
        fetched_event = db_session.get(WorldEvent, event.id)
        assert fetched_event.tags == tags
        assert len(fetched_event.tags) == 5

    def test_world_event_empty_tags(self, db_session: Session, test_world: World):
        """Test that empty tags array works."""
        event = WorldEvent(
            world_id=test_world.id,
            t=1.0,
            label_time="No Tags",
            type="test",
            summary="Event without tags",
            tags=[]
        )
        db_session.add(event)
        db_session.commit()

        assert event.tags == []

    def test_world_event_required_fields(self, db_session: Session, test_world: World):
        """Test that required fields cannot be null."""
        # Missing t
        with pytest.raises(Exception):
            event = WorldEvent(
                world_id=test_world.id,
                label_time="No Time",
                type="test",
                summary="Missing t"
            )
            db_session.add(event)
            db_session.commit()

        db_session.rollback()

        # Missing type
        with pytest.raises(Exception):
            event = WorldEvent(
                world_id=test_world.id,
                t=1.0,
                label_time="No Type",
                summary="Missing type"
            )
            db_session.add(event)
            db_session.commit()

    def test_world_event_world_relationship(self, db_session: Session, test_world: World):
        """Test event-world relationship."""
        event = WorldEvent(
            world_id=test_world.id,
            t=1.0,
            label_time="Test",
            type="test",
            summary="Relationship test"
        )
        db_session.add(event)
        db_session.commit()

        assert event.world.id == test_world.id
        assert event.world.name == test_world.name

    def test_world_event_story_beats_relationship(
        self, db_session: Session, test_world: World, test_story: Story
    ):
        """Test event-beats relationship (multiple beats can reference same event)."""
        event = WorldEvent(
            world_id=test_world.id,
            t=50.0,
            label_time="Shared Event",
            type="meeting",
            summary="Event referenced by multiple stories"
        )
        db_session.add(event)
        db_session.commit()

        # Create multiple beats referencing this event
        for i in range(1, 4):
            beat = StoryBeat(
                story_id=test_story.id,
                order_index=i,
                content=f"Beat {i} referencing event",
                world_event_id=event.id
            )
            db_session.add(beat)

        db_session.commit()

        # Verify relationship
        assert len(event.story_beats) == 3

    def test_world_event_repr(self, db_session: Session, test_world: World):
        """Test event string representation."""
        event = WorldEvent(
            world_id=test_world.id,
            t=99.9,
            label_time="Repr Event",
            type="test",
            summary="Test repr"
        )
        db_session.add(event)
        db_session.commit()

        repr_str = repr(event)
        assert "WorldEvent" in repr_str
        assert event.id in repr_str
        assert test_world.id in repr_str
        assert "99.9" in repr_str
        assert "Repr Event" in repr_str
