"""add_generation_reasoning_to_story_beats

Revision ID: 42b06b85f639
Revises: a7b3e4d9f2c1
Create Date: 2025-11-20 16:10:06.892404

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42b06b85f639'
down_revision: Union[str, None] = 'a7b3e4d9f2c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add generation_reasoning column to story_beats table
    op.add_column(
        'story_beats',
        sa.Column('generation_reasoning', sa.Text(), nullable=True,
                 comment='AI reasoning/thoughts behind beat generation')
    )


def downgrade() -> None:
    # Remove generation_reasoning column
    op.drop_column('story_beats', 'generation_reasoning')
