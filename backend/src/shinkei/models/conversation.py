"""Conversation model definitions for world chat feature and Story Pilot AI Chat Assistant."""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, DateTime, func, Index, JSON, Enum as SQLEnum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shinkei.database.engine import Base
import uuid
import enum

if TYPE_CHECKING:
    from shinkei.models.agent_persona import AgentPersona


class ConversationType(str, enum.Enum):
    """Conversation type enumeration."""
    WORLD_CHAT = "world_chat"
    BEAT_DISCUSSION = "beat_discussion"
    STORY_PLANNING = "story_planning"


class AgentMode(str, enum.Enum):
    """Agent operation mode enumeration."""
    PLAN = "plan"  # Agent creates a plan before any actions, user approves the plan
    ASK = "ask"    # Agent asks for approval before each write action
    AUTO = "auto"  # Agent executes actions automatically (with undo capability)


class Conversation(Base):
    """
    Conversation model representing a chat instance.

    Extended for Story Pilot AI Chat Assistant with agent mode,
    persona selection, and provider override support.

    Attributes:
        id: Unique identifier
        world_id: Foreign key to world (conversations are per-world)
        user_id: Foreign key to user
        type: Conversation type
        title: Optional conversation title
        context_summary: Rolling summary for context window management
        mode: Agent operation mode (plan, ask, auto)
        persona_id: Optional foreign key to agent persona
        provider_override: Optional LLM provider override
        model_override: Optional model override
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

    # Story Pilot fields
    mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ask",
        index=True,
        comment="Agent mode: plan, ask, auto"
    )

    persona_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("agent_personas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Selected agent persona"
    )

    provider_override: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Override user default provider for this chat"
    )

    model_override: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Override default model for this chat"
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
    persona: Mapped[Optional["AgentPersona"]] = relationship(
        "AgentPersona",
        back_populates="conversations",
        foreign_keys=[persona_id]
    )

    # Indexes
    __table_args__ = (
        Index('ix_conversations_world_user', 'world_id', 'user_id'),
        Index('ix_conversations_type', 'type'),
        Index('ix_conversations_mode', 'mode'),
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, world_id={self.world_id}, type={self.type}, mode={self.mode})>"


class ConversationMessage(Base):
    """
    ConversationMessage model representing a single message in a conversation.

    Extended for Story Pilot AI Chat Assistant with tool call tracking
    and approval workflow support.

    Attributes:
        id: Unique identifier
        conversation_id: Foreign key to conversation
        role: Message role (user, assistant, system, tool)
        content: Message text content
        reasoning: AI reasoning/thoughts (for assistant messages)
        message_metadata: JSON field for additional data (model used, tokens, etc.)
        tool_calls: JSON field for tool calls made by assistant
        tool_results: JSON field for results from tool execution
        pending_approval: Whether this action is awaiting user approval (Ask mode)
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
        comment="Message role: user, assistant, system, or tool"
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

    # Story Pilot fields for tool tracking
    tool_calls: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Tool calls made by assistant"
    )

    tool_results: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Results from tool execution"
    )

    pending_approval: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="True if action awaiting user approval (Ask mode)"
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
        Index('ix_conversation_messages_pending_approval', 'pending_approval'),
    )

    def __repr__(self) -> str:
        return f"<ConversationMessage(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"
