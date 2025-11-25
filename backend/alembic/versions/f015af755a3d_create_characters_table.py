"""create_characters_table

Revision ID: f015af755a3d
Revises: 7782c8f79908
Create Date: 2025-11-22 13:30:28.968623

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f015af755a3d'
down_revision: Union[str, None] = '7782c8f79908'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Define enum (will be created automatically by op.create_table)
    entity_importance = sa.Enum('major', 'minor', 'background', name='entityimportance')

    # Create characters table
    op.create_table(
        'characters',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('world_id', sa.String(36), sa.ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('aliases', sa.ARRAY(sa.String(100)), nullable=True),
        sa.Column('role', sa.String(200), nullable=True),
        sa.Column('importance', entity_importance, nullable=False, server_default='background'),
        sa.Column('first_appearance_beat_id', sa.String(36), sa.ForeignKey('story_beats.id', ondelete='SET NULL'), nullable=True),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), onupdate=sa.text('now()')),
    )

    # Create indexes
    op.create_index('ix_characters_world_id', 'characters', ['world_id'])
    op.create_index('ix_characters_world_importance', 'characters', ['world_id', 'importance'])

    # Create unique constraint on world_id + name
    op.create_unique_constraint('uq_characters_world_name', 'characters', ['world_id', 'name'])


def downgrade() -> None:
    # Drop table (cascade will handle FK dependencies)
    op.drop_table('characters')

    # Drop enum type
    sa.Enum(name='entityimportance').drop(op.get_bind())
