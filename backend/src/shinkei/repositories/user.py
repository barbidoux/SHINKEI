"""User repository for database operations."""
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from shinkei.models.user import User
from shinkei.schemas.user import UserCreate, UserUpdate
from shinkei.logging_config import get_logger

logger = get_logger(__name__)


class UserRepository:
    """Repository for User model database operations."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
    
    async def create(self, user_data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user_data: User creation data

        Returns:
            Created user instance
        """
        user = User(
            id=user_data.id,
            email=user_data.email.lower().strip(),  # Normalize to lowercase
            password_hash=user_data.password_hash,
            name=user_data.name,
            settings=user_data.settings.model_dump(),
        )

        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)

        logger.info("user_created", user_id=user.id, email=user.email)
        return user
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User UUID
            
        Returns:
            User instance or None if not found
        """
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address (case-insensitive).

        Args:
            email: User email address

        Returns:
            User instance or None if not found
        """
        # Normalize email to lowercase for case-insensitive lookup
        normalized_email = email.lower().strip()

        result = await self.session.execute(
            select(User).where(User.email == normalized_email)
        )
        return result.scalar_one_or_none()
    
    async def update(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """
        Update user information.
        
        Args:
            user_id: User UUID
            user_data: Update data
            
        Returns:
            Updated user instance or None if not found
        """
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        update_data = user_data.model_dump(exclude_unset=True)
        
        if "name" in update_data:
            user.name = update_data["name"]
        
        if "settings" in update_data:
            user.settings = update_data["settings"]
        
        await self.session.flush()
        await self.session.refresh(user)
        
        logger.info("user_updated", user_id=user.id)
        return user
    
    async def delete(self, user_id: str) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            True if deleted, False if not found
        """
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        await self.session.delete(user)
        await self.session.flush()
        
        logger.info("user_deleted", user_id=user_id)
        return True
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[User], int]:
        """
        List users with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (users list, total count)
        """
        # Get total count
        count_result = await self.session.execute(
            select(func.count()).select_from(User)
        )
        total = count_result.scalar_one()
        
        # Get users
        result = await self.session.execute(
            select(User)
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        users = list(result.scalars().all())
        
        return users, total
    
    async def exists(self, user_id: str) -> bool:
        """
        Check if user exists.
        
        Args:
            user_id: User UUID
            
        Returns:
            True if user exists, False otherwise
        """
        result = await self.session.execute(
            select(func.count()).select_from(User).where(User.id == user_id)
        )
        return result.scalar_one() > 0
