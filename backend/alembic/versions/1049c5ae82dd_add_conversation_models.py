"""add_conversation_models

Revision ID: 1049c5ae82dd
Revises: 42b06b85f639
Create Date: 2025-11-20 16:12:18.528499

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1049c5ae82dd'
down_revision: Union[str, None] = '42b06b85f639'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(length=36), nullable=False, comment='Conversation UUID'),
        sa.Column('world_id', sa.String(length=36), nullable=False, comment='World ID this conversation belongs to'),
        sa.Column('user_id', sa.String(length=36), nullable=False, comment='User ID who owns this conversation'),
        sa.Column('type', sa.Enum('WORLD_CHAT', 'BEAT_DISCUSSION', 'STORY_PLANNING', name='conversationtype'),
                  nullable=False, comment='Type of conversation'),
        sa.Column('title', sa.String(length=255), nullable=True, comment='Optional conversation title'),
        sa.Column('context_summary', sa.Text(), nullable=True, comment='Rolling summary for context window management'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False, comment='Timestamp of creation'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False, comment='Timestamp of last update'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_conversations_type', 'conversations', ['type'])
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('ix_conversations_world_id', 'conversations', ['world_id'])
    op.create_index('ix_conversations_world_user', 'conversations', ['world_id', 'user_id'])

    # Create conversation_messages table
    op.create_table(
        'conversation_messages',
        sa.Column('id', sa.String(length=36), nullable=False, comment='Message UUID'),
        sa.Column('conversation_id', sa.String(length=36), nullable=False, comment='Conversation ID this message belongs to'),
        sa.Column('role', sa.String(length=20), nullable=False, comment='Message role: user, assistant, or system'),
        sa.Column('content', sa.Text(), nullable=False, comment='Message text content'),
        sa.Column('reasoning', sa.Text(), nullable=True, comment='AI reasoning/thoughts (for assistant messages)'),
        sa.Column('metadata', sa.JSON(), nullable=True, comment='Additional metadata (model used, tokens, etc.)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False, comment='Timestamp of creation'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_conversation_messages_conversation_id', 'conversation_messages', ['conversation_id'])
    op.create_index('ix_conversation_messages_created_at', 'conversation_messages', ['created_at'])


def downgrade() -> None:
    # Drop conversation_messages table
    op.drop_index('ix_conversation_messages_created_at', table_name='conversation_messages')
    op.drop_index('ix_conversation_messages_conversation_id', table_name='conversation_messages')
    op.drop_table('conversation_messages')

    # Drop conversations table
    op.drop_index('ix_conversations_world_user', table_name='conversations')
    op.drop_index('ix_conversations_world_id', table_name='conversations')
    op.drop_index('ix_conversations_user_id', table_name='conversations')
    op.drop_index('ix_conversations_type', table_name='conversations')
    op.drop_table('conversations')

    # Drop enum type
    op.execute('DROP TYPE IF EXISTS conversationtype')
