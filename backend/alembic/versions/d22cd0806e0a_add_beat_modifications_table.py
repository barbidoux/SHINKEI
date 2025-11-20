"""add_beat_modifications_table

Revision ID: d22cd0806e0a
Revises: 1049c5ae82dd
Create Date: 2025-11-20 16:45:21.549701

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd22cd0806e0a'
down_revision: Union[str, None] = '1049c5ae82dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create beat_modifications table for tracking modification history
    op.create_table(
        'beat_modifications',
        sa.Column('id', sa.String(length=36), nullable=False, comment='Modification UUID'),
        sa.Column('beat_id', sa.String(length=36), nullable=False, comment='Beat being modified'),
        sa.Column('original_content', sa.Text(), nullable=False, comment='Original beat content'),
        sa.Column('modified_content', sa.Text(), nullable=False, comment='Modified beat content'),
        sa.Column('original_summary', sa.Text(), nullable=True, comment='Original beat summary'),
        sa.Column('modified_summary', sa.Text(), nullable=True, comment='Modified beat summary'),
        sa.Column('original_time_label', sa.String(length=100), nullable=True, comment='Original time label'),
        sa.Column('modified_time_label', sa.String(length=100), nullable=True, comment='Modified time label'),
        sa.Column('original_world_event_id', sa.String(length=36), nullable=True, comment='Original world event link'),
        sa.Column('modified_world_event_id', sa.String(length=36), nullable=True, comment='Modified world event link'),
        sa.Column('modification_instructions', sa.Text(), nullable=False, comment='User instructions for modification'),
        sa.Column('reasoning', sa.Text(), nullable=True, comment='AI reasoning for changes'),
        sa.Column('unified_diff', sa.Text(), nullable=True, comment='Unified diff of changes'),
        sa.Column('applied', sa.Boolean(), nullable=False, server_default=sa.text('false'), comment='Whether modification was applied'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp of modification'),
        sa.ForeignKeyConstraint(['beat_id'], ['story_beats.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for efficient queries
    op.create_index('ix_beat_modifications_beat_id', 'beat_modifications', ['beat_id'])
    op.create_index('ix_beat_modifications_created_at', 'beat_modifications', ['created_at'])
    op.create_index('ix_beat_modifications_applied', 'beat_modifications', ['applied'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_beat_modifications_applied', table_name='beat_modifications')
    op.drop_index('ix_beat_modifications_created_at', table_name='beat_modifications')
    op.drop_index('ix_beat_modifications_beat_id', table_name='beat_modifications')

    # Drop table
    op.drop_table('beat_modifications')
