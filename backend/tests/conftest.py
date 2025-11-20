"""Pytest configuration and fixtures."""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from shinkei.config import settings
from shinkei.database.engine import Base
# Import all models to ensure they are registered with Base.metadata
from shinkei.models.user import User
from shinkei.models.world import World
from shinkei.models.world_event import WorldEvent
from shinkei.models.story import Story
from shinkei.models.story_beat import StoryBeat

# Use the database URL from settings
# In a real scenario, we might want to use a separate test database
TEST_DATABASE_URL = str(settings.database_url).replace("postgresql://", "postgresql+asyncpg://")


@pytest_asyncio.fixture(scope="function")
async def engine() -> AsyncGenerator:
    """Create a SQLAlchemy engine for testing."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for a test."""
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        yield session
        # Rollback transaction after test
        await session.rollback()


# Synchronous session for model unit tests
@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a synchronous database session for model unit tests."""
    # Use synchronous version of database URL
    sync_db_url = str(settings.database_url)
    engine = create_engine(sync_db_url, echo=False)

    # Create all tables
    Base.metadata.create_all(engine)

    # Create session
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    # Rollback and close
    session.rollback()
    session.close()

    # Drop all tables after test
    Base.metadata.drop_all(engine)
    engine.dispose()


# Test data fixtures
@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user."""
    user = User(
        email="testuser@example.com",
        name="Test User",
        settings={"language": "en", "theme": "dark"}
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_world(db_session: Session, test_user: User) -> World:
    """Create a test world."""
    world = World(
        user_id=test_user.id,
        name="Test World",
        description="A test world for unit tests",
        laws={"physics": "standard"},
        tone="neutral"
    )
    db_session.add(world)
    db_session.commit()
    db_session.refresh(world)
    return world


@pytest.fixture
def test_story(db_session: Session, test_world: World) -> Story:
    """Create a test story."""
    story = Story(
        world_id=test_world.id,
        title="Test Story",
        synopsis="A test story for unit tests"
    )
    db_session.add(story)
    db_session.commit()
    db_session.refresh(story)
    return story


@pytest.fixture
def test_world_event(db_session: Session, test_world: World) -> WorldEvent:
    """Create a test world event."""
    event = WorldEvent(
        world_id=test_world.id,
        t=1.0,
        label_time="Test Time",
        type="test",
        summary="A test event"
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


