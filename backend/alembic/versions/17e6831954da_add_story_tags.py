"""add_story_tags

Revision ID: 17e6831954da
Revises: 6c1c6123e69f
Create Date: 2025-11-21 15:47:39.655776

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY


# revision identifiers, used by Alembic.
revision: str = '17e6831954da'
down_revision: Union[str, None] = '6c1c6123e69f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add tags column to stories table
    op.add_column(
        'stories',
        sa.Column(
            'tags',
            ARRAY(sa.String()),
            nullable=False,
            server_default='{}',
            comment='Tags for categorizing and organizing stories'
        )
    )

    # Create GIN index for efficient tag search
    op.create_index(
        'ix_stories_tags_gin',
        'stories',
        ['tags'],
        unique=False,
        postgresql_using='gin'
    )


def downgrade() -> None:
    # Drop GIN index
    op.drop_index('ix_stories_tags_gin', table_name='stories')

    # Drop tags column
    op.drop_column('stories', 'tags')
