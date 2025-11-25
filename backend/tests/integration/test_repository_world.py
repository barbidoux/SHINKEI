"""Integration tests for World repository."""
import pytest
from shinkei.repositories.user import UserRepository
from shinkei.repositories.world import WorldRepository
from shinkei.schemas.user import UserCreate
from shinkei.schemas.world import WorldCreate, WorldUpdate

@pytest.mark.asyncio
async def test_world_crud(session):
    """Test World CRUD operations."""
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    
    # Create User
    user = await user_repo.create(UserCreate(email="world_owner@example.com", name="Owner", password_hash="hashed_pw"))
    
    # Create World
    world_data = WorldCreate(
        name="Test World",
        description="A test world",
        tone="Dark",
        chronology_mode="linear"
    )
    world = await world_repo.create(user.id, world_data)
    
    assert world.id is not None
    assert world.user_id == user.id
    assert world.name == "Test World"
    
    # Get by ID
    fetched_world = await world_repo.get_by_id(world.id)
    assert fetched_world is not None
    assert fetched_world.id == world.id
    
    # Get by User and ID
    fetched_world_user = await world_repo.get_by_user_and_id(user.id, world.id)
    assert fetched_world_user is not None
    
    # List by User
    worlds, total = await world_repo.list_by_user(user.id)
    assert total == 1
    assert len(worlds) == 1
    assert worlds[0].id == world.id
    
    # Update
    update_data = WorldUpdate(name="Updated World")
    updated_world = await world_repo.update(world.id, update_data)
    assert updated_world.name == "Updated World"
    
    # Delete
    deleted = await world_repo.delete(world.id)
    assert deleted is True
    
    # Verify Deletion
    deleted_world = await world_repo.get_by_id(world.id)
    assert deleted_world is None
