"""Tests for authentication dependencies."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt
from shinkei.auth.dependencies import get_current_user
from shinkei.models.user import User
from shinkei.config import settings

# Mock settings for test
settings.supabase_jwt_secret = "test-secret"
settings.algorithm = "HS256"

@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    """Test get_current_user with a valid token."""
    # Create a valid token
    user_id = "test-user-id"
    token_data = {"sub": user_id}
    token = jwt.encode(token_data, settings.supabase_jwt_secret, algorithm=settings.algorithm)
    
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    
    # Mock session and repository
    mock_session = MagicMock()
    
    # Mock UserRepository.get_by_id
    # Since we instantiate UserRepository inside the function, we need to patch it
    with patch("shinkei.auth.dependencies.UserRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        
        # Mock async get_by_id
        expected_user = User(id=user_id, email="test@example.com")
        mock_repo_instance.get_by_id = AsyncMock(return_value=expected_user)
        
        user = await get_current_user(credentials, mock_session)
        
        assert user.id == user_id
        assert user.email == "test@example.com"
        MockRepo.assert_called_once_with(mock_session)
        mock_repo_instance.get_by_id.assert_called_once_with(user_id)

@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    """Test get_current_user with an invalid token."""
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")
    mock_session = MagicMock()
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials, mock_session)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Could not validate credentials"

@pytest.mark.asyncio
async def test_get_current_user_user_not_found():
    """Test get_current_user when user exists in token but not in DB."""
    user_id = "non-existent-user"
    token_data = {"sub": user_id}
    token = jwt.encode(token_data, settings.supabase_jwt_secret, algorithm=settings.algorithm)
    
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    mock_session = MagicMock()
    
    with patch("shinkei.auth.dependencies.UserRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        mock_repo_instance.get_by_id = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, mock_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
