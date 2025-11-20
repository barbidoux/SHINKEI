"""User API endpoints."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shinkei.auth.dependencies import get_current_user, get_db_session
from shinkei.models.user import User
from shinkei.schemas.user import UserCreate, UserResponse, UserUpdate
from shinkei.repositories.user import UserRepository
from shinkei.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    """
    Register a new user.
    
    This endpoint is used to sync a user from Supabase Auth to our database.
    In a real production flow, this might be handled by a Supabase webhook,
    but for now, the frontend can call this after successful signup.
    """
    repo = UserRepository(session)
    
    # Check if user already exists (by email)
    existing_user = await repo.get_by_email(user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
        
    # We might also want to check if ID exists if provided, but repo.create handles that constraints
    
    user = await repo.create(user_in)
    logger.info("user_registered", user_id=user.id)
    return user


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Get current user.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_user_me(
    user_in: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    """
    Update current user settings.
    """
    repo = UserRepository(session)
    updated_user = await repo.update(current_user.id, user_in)
    
    if not updated_user:
        # Should not happen since we have current_user
        raise HTTPException(status_code=404, detail="User not found")
        
    logger.info("user_updated", user_id=updated_user.id)
    return updated_user
