from typing import Annotated
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext

from shinkei.config import settings
from shinkei.auth.dependencies import get_db_session
from shinkei.models.user import User
from shinkei.repositories.user import UserRepository
from shinkei.schemas.user import UserCreate
from shinkei.logging_config import get_logger
from shinkei.middleware.rate_limiter import limiter, AUTH_RATE_LIMIT
from shinkei.security.password import validate_password_strength
from shinkei.security.jwt import create_access_token

logger = get_logger(__name__)

router = APIRouter()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from pydantic import BaseModel, EmailStr, field_validator

class LoginRequest(BaseModel):
    email: EmailStr  # Validates email format
    password: str

    @field_validator('email')
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        """Normalize email to lowercase for case-insensitive matching."""
        return v.lower().strip()

class RegisterRequest(BaseModel):
    email: EmailStr  # Validates email format
    password: str
    name: str | None = None

    @field_validator('email')
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        """Normalize email to lowercase for case-insensitive matching."""
        return v.lower().strip()

@router.post("/register")
# @limiter.limit(AUTH_RATE_LIMIT)  # ← TEMPORARILY DISABLED - needs Response type fix
async def register(
    # request: Request,  # ← Required for rate limiting
    register_data: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Register a new user account.

    ⚠️ IMPORTANT: Always use this endpoint to create new users.
    The /login endpoint will NOT auto-create accounts.
    """
    repo = UserRepository(session)

    # Check if user already exists (first level check)
    existing_user = await repo.get_by_email(register_data.email)
    if existing_user:
        logger.warning(
            "registration_duplicate_email_attempt",
            email=register_data.email,
            existing_user_id=existing_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email {register_data.email} already exists. Please login instead."
        )

    # SECURITY FIX: Validate password strength before hashing
    is_valid, error_message = validate_password_strength(register_data.password)
    if not is_valid:
        logger.warning(
            "registration_weak_password_rejected",
            email=register_data.email,
            reason=error_message
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password does not meet security requirements: {error_message}"
        )

    # Hash the password
    password_hash = pwd_context.hash(register_data.password)

    # Create new user (with database-level duplicate protection)
    try:
        user = await repo.create(UserCreate(
            email=register_data.email,
            password_hash=password_hash,
            name=register_data.name or register_data.email.split("@")[0],
            settings={}
        ))

        logger.info(
            "user_registered_successfully",
            user_id=user.id,
            email=user.email
        )

    except IntegrityError as e:
        # Database-level unique constraint violation (race condition caught)
        logger.error(
            "registration_database_constraint_violation",
            email=register_data.email,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email {register_data.email} already exists. This email is already registered."
        )

    # Create access token for immediate login (with JTI and enhanced security)
    access_token = create_access_token(subject=str(user.id))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name
        }
    }

@router.post("/login")
# @limiter.limit(AUTH_RATE_LIMIT)  # ← TEMPORARILY DISABLED - needs Response type fix
async def login(
    # request: Request,  # ← Required for rate limiting
    login_data: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Login endpoint with password verification.

    ⚠️ SECURITY: This endpoint NO LONGER auto-registers users.
    User must be registered via /auth/register endpoint first.
    """
    repo = UserRepository(session)
    user = await repo.get_by_email(login_data.email)

    if not user:
        # ❌ REMOVED AUTO-REGISTRATION - This was causing data loss!
        # Users must explicitly register via /auth/register endpoint
        logger.warning(
            "login_attempt_unknown_email",
            email=login_data.email
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not pwd_context.verify(login_data.password, user.password_hash):
        logger.warning(
            "login_attempt_invalid_password",
            email=login_data.email,
            user_id=user.id
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    logger.info(
        "user_logged_in_successfully",
        user_id=user.id,
        email=user.email
    )

    # Create access token (with JTI and enhanced security)
    access_token = create_access_token(subject=str(user.id))

    return {"access_token": access_token, "token_type": "bearer"}
