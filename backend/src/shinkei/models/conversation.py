"""Conversation model definitions for world chat feature."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, DateTime, func, Index, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shinkei.database.engine import Base
import uuid
import enum


class ConversationType(str, enum.Enum):
    """Conversation type enumeration."""
    WORLD_CHAT = "world_chat"
    BEAT_DISCUSSION = "beat_discussion"
    STORY_PLANNING = "story_planning"


class Conversation(Base):
    """
    Conversation model representing a chat instance.

    Attributes:
        id: Unique identifier
        world_id: Foreign key to world (conversations are per-world)
        user_id: Foreign key to user
        type: Conversation type
        title: Optional conversation title
        context_summary: Rolling summary for context window management
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Conversation UUID"
    )

    world_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="World ID this conversation belongs to"
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User ID who owns this conversation"
    )

    type: Mapped[ConversationType] = mapped_column(
        SQLEnum(ConversationType),
        nullable=False,
        default=ConversationType.WORLD_CHAT,
        comment="Type of conversation"
    )

    title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Optional conversation title"
    )

    context_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Rolling summary for context window management"
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
    world: Mapped["World"] = relationship("World", back_populates="conversations")
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[list["ConversationMessage"]] = relationship(
        "ConversationMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.created_at"
    )

    # Indexes
    __table_args__ = (
        Index('ix_conversations_world_user', 'world_id', 'user_id'),
        Index('ix_conversations_type', 'type'),
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, world_id={self.world_id}, type={self.type})>"


class ConversationMessage(Base):
    """
    ConversationMessage model representing a single message in a conversation.

    Attributes:
        id: Unique identifier
        conversation_id: Foreign key to conversation
        role: Message role (user, assistant, system)
        content: Message text content
        reasoning: AI reasoning/thoughts (for assistant messages)
        message_metadata: JSON field for additional data (model used, tokens, etc.)
        created_at: Timestamp of creation
    """
    __tablename__ = "conversation_messages"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Message UUID"
    )

    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        comment="Conversation ID this message belongs to"
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Message role: user, assistant, or system"
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Message text content"
    )

    reasoning: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="AI reasoning/thoughts (for assistant messages)"
    )

    message_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata",  # Column name in database
        JSON,
        nullable=True,
        comment="Additional metadata (model used, tokens, etc.)"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp of creation"
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")

    # Indexes
    __table_args__ = (
        Index('ix_conversation_messages_conversation_id', 'conversation_id'),
        Index('ix_conversation_messages_created_at', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<ConversationMessage(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"
