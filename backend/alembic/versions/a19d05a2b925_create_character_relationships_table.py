"""create_character_relationships_table

Revision ID: a19d05a2b925
Revises: 30978efe42d1
Create Date: 2025-11-22 13:32:14.806485

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a19d05a2b925'
down_revision: Union[str, None] = '30978efe42d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Define enum (will be created automatically by op.create_table)
    relationship_strength = sa.Enum('strong', 'moderate', 'weak', name='relationshipstrength')

    # Create character_relationships table
    op.create_table(
        'character_relationships',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('world_id', sa.String(36), sa.ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False),
        sa.Column('character_a_id', sa.String(36), sa.ForeignKey('characters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('character_b_id', sa.String(36), sa.ForeignKey('characters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relationship_type', sa.String(100), nullable=False),  # e.g., friend, enemy, family, ally
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('strength', relationship_strength, nullable=False, server_default='moderate'),
        sa.Column('first_established_beat_id', sa.String(36), sa.ForeignKey('story_beats.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), onupdate=sa.text('now()')),
        # Check constraint: prevent self-relationships
        sa.CheckConstraint('character_a_id != character_b_id', name='ck_no_self_relationship')
    )

    # Create indexes
    op.create_index('ix_character_relationships_world_id', 'character_relationships', ['world_id'])
    op.create_index('ix_character_relationships_char_a', 'character_relationships', ['character_a_id'])
    op.create_index('ix_character_relationships_char_b', 'character_relationships', ['character_b_id'])
    op.create_index('ix_character_relationships_strength', 'character_relationships', ['strength'])

    # Create unique constraint to prevent duplicate relationships (bidirectional uniqueness)
    # Note: This allows both (A->B) and (B->A) as separate entries if needed for directed relationships
    op.create_unique_constraint(
        'uq_character_relationships_pair',
        'character_relationships',
        ['character_a_id', 'character_b_id', 'relationship_type']
    )


def downgrade() -> None:
    # Drop table
    op.drop_table('character_relationships')

    # Drop enum type
    sa.Enum(name='relationshipstrength').drop(op.get_bind())
