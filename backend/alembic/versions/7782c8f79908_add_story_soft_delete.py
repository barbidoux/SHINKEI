"""add_story_soft_delete

Revision ID: 7782c8f79908
Revises: 17e6831954da
Create Date: 2025-11-21 15:48:03.973327

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7782c8f79908'
down_revision: Union[str, None] = '17e6831954da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add archived_at column to stories table
    op.add_column(
        'stories',
        sa.Column(
            'archived_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Timestamp when story was archived (soft delete)'
        )
    )

    # Create index for efficient filtering of non-archived stories
    op.create_index(
        'ix_stories_archived_at',
        'stories',
        ['archived_at'],
        unique=False
    )


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_stories_archived_at', table_name='stories')

    # Drop archived_at column
    op.drop_column('stories', 'archived_at')
