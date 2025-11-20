"""User model definition."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shinkei.database.engine import Base
import uuid


class User(Base):
    """
    User model representing a Shinkei author.
    
    Attributes:
        id: Unique identifier (UUID from Supabase Auth)
        email: User email address
        name: Display name
        settings: JSON object containing user preferences
        created_at: Timestamp of user creation
        updated_at: Timestamp of last update
    """
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="UUID from Supabase Auth"
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address"
    )
    
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Display name"
    )
    
    settings: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="User preferences (language, theme, default_model, etc.)"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp of creation"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Timestamp of last update"
    )
    
    # Relationships
    worlds: Mapped[list["World"]] = relationship("World", back_populates="user", cascade="all, delete-orphan")
    conversations: Mapped[list["Conversation"]] = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"
