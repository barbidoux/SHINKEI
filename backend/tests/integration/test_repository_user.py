"""Integration tests for User repository."""
import pytest
from shinkei.repositories.user import UserRepository
from shinkei.schemas.user import UserCreate, UserUpdate, UserSettings

@pytest.mark.asyncio
async def test_user_crud(session):
    """Test User CRUD operations."""
    repo = UserRepository(session)
    
    # Create
    user_data = UserCreate(
        email="test@example.com",
        name="Test User",
        settings=UserSettings(language="en")
    )
    user = await repo.create(user_data)
    
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.settings["language"] == "en"
    
    # Get by ID
    fetched_user = await repo.get_by_id(user.id)
    assert fetched_user is not None
    assert fetched_user.id == user.id
    
    # Get by Email
    fetched_user_email = await repo.get_by_email("test@example.com")
    assert fetched_user_email is not None
    assert fetched_user_email.id == user.id
    
    # Update
    update_data = UserUpdate(name="Updated Name")
    updated_user = await repo.update(user.id, update_data)
    assert updated_user.name == "Updated Name"
    
    # List
    users, total = await repo.list_users()
    assert total >= 1
    assert len(users) >= 1
    
    # Delete
    deleted = await repo.delete(user.id)
    assert deleted is True
    
    # Verify Deletion
    deleted_user = await repo.get_by_id(user.id)
    assert deleted_user is None
