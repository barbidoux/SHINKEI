"""create_locations_table

Revision ID: d09e1e5e2a3a
Revises: f015af755a3d
Create Date: 2025-11-22 13:31:04.619651

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd09e1e5e2a3a'
down_revision: Union[str, None] = 'f015af755a3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create locations table with hierarchical structure
    op.create_table(
        'locations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('world_id', sa.String(36), sa.ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('location_type', sa.String(50), nullable=True),  # e.g., city, building, planet, region
        sa.Column('parent_location_id', sa.String(36), sa.ForeignKey('locations.id', ondelete='SET NULL'), nullable=True),  # Self-referential for hierarchy
        sa.Column('significance', sa.Text, nullable=True),
        sa.Column('first_appearance_beat_id', sa.String(36), sa.ForeignKey('story_beats.id', ondelete='SET NULL'), nullable=True),
        sa.Column('coordinates', sa.JSON, nullable=True),  # Flexible coordinate storage (lat/long, x/y/z, etc.)
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), onupdate=sa.text('now()')),
    )

    # Create indexes
    op.create_index('ix_locations_world_id', 'locations', ['world_id'])
    op.create_index('ix_locations_parent_id', 'locations', ['parent_location_id'])
    op.create_index('ix_locations_type', 'locations', ['location_type'])

    # Create unique constraint on world_id + name
    op.create_unique_constraint('uq_locations_world_name', 'locations', ['world_id', 'name'])


def downgrade() -> None:
    # Drop table (cascade will handle FK dependencies)
    op.drop_table('locations')
