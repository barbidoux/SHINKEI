"""create_entity_mentions_table

Revision ID: 30978efe42d1
Revises: d09e1e5e2a3a
Create Date: 2025-11-22 13:31:37.510779

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '30978efe42d1'
down_revision: Union[str, None] = 'd09e1e5e2a3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Define enums (will be created automatically by op.create_table)
    entity_type = sa.Enum('character', 'location', name='entitytype')
    mention_type = sa.Enum('explicit', 'implicit', 'referenced', name='mentiontype')
    detection_source = sa.Enum('user', 'ai', name='detectionsource')

    # Create entity_mentions table
    op.create_table(
        'entity_mentions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('story_beat_id', sa.String(36), sa.ForeignKey('story_beats.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_type', entity_type, nullable=False),
        sa.Column('entity_id', sa.String(36), nullable=False),  # References characters.id or locations.id
        sa.Column('mention_type', mention_type, nullable=False, server_default='explicit'),
        sa.Column('confidence', sa.Float, nullable=True),  # 0.0 to 1.0 for AI detection confidence
        sa.Column('context_snippet', sa.Text, nullable=True),  # Text snippet where entity was mentioned
        sa.Column('detected_by', detection_source, nullable=False, server_default='user'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), onupdate=sa.text('now()')),
    )

    # Create indexes
    op.create_index('ix_entity_mentions_beat_id', 'entity_mentions', ['story_beat_id'])
    op.create_index('ix_entity_mentions_entity', 'entity_mentions', ['entity_type', 'entity_id'])
    op.create_index('ix_entity_mentions_detected_by', 'entity_mentions', ['detected_by'])

    # Create unique constraint to prevent duplicate mentions
    op.create_unique_constraint(
        'uq_entity_mentions_beat_entity',
        'entity_mentions',
        ['story_beat_id', 'entity_type', 'entity_id']
    )


def downgrade() -> None:
    # Drop table
    op.drop_table('entity_mentions')

    # Drop enum types
    sa.Enum(name='detectionsource').drop(op.get_bind())
    sa.Enum(name='mentiontype').drop(op.get_bind())
    sa.Enum(name='entitytype').drop(op.get_bind())
