"""Authentication and dependency injection."""
from typing import AsyncGenerator, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from shinkei.config import settings
from shinkei.database.engine import AsyncSessionLocal
from shinkei.models.user import User
from shinkei.repositories.user import UserRepository
from shinkei.logging_config import get_logger

logger = get_logger(__name__)

security = HTTPBearer()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get a database session.
    Yields an AsyncSession and ensures it's closed after use.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    """
    Dependency to get the current authenticated user.
    Verifies the JWT token and retrieves the user from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # In a real Supabase scenario, we would verify the signature using the project secret
        # For development/testing without a real Supabase instance, we might need to mock this
        # or use a local secret.
        # Assuming settings.supabase_jwt_secret is available.
        
        # Use secret_key for local dev auth
        secret = settings.supabase_jwt_secret if settings.supabase_jwt_secret else settings.secret_key
        
        payload = jwt.decode(
            token.credentials,
            secret,
            algorithms=[settings.algorithm],
            options={"verify_aud": False}
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except JWTError as e:
        logger.warning("jwt_validation_failed", error=str(e))
        raise credentials_exception

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    
    if user is None:
        # If user exists in Auth but not in our DB, we might want to create them (JIT provisioning)
        # or raise an error. For now, let's raise an error to be strict.
        # Alternatively, we could auto-create the user here if we trust the token.
        logger.warning("user_not_found_in_db", user_id=user_id)
        raise credentials_exception
        
    return user


async def get_repository(
    repo_type: type,
) -> callable:
    """
    Factory to create a dependency for a specific repository.
    Usage: Depends(get_repository(UserRepository))
    """
    def _get_repo(session: Annotated[AsyncSession, Depends(get_db_session)]):
        return repo_type(session)
    return _get_repo
