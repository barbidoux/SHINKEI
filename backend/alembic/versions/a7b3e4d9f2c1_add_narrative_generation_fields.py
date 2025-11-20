"""add_narrative_generation_fields

Revision ID: a7b3e4d9f2c1
Revises: 9678c121e009
Create Date: 2025-11-20 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7b3e4d9f2c1'
down_revision: Union[str, None] = '9678c121e009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create new enum types
    op.execute("CREATE TYPE authoringmode AS ENUM ('AUTONOMOUS', 'COLLABORATIVE', 'MANUAL')")
    op.execute("CREATE TYPE povtype AS ENUM ('FIRST', 'THIRD', 'OMNISCIENT')")
    op.execute("CREATE TYPE generatedby AS ENUM ('AI', 'USER', 'COLLABORATIVE')")

    # Add new columns to stories table
    op.add_column('stories', sa.Column('mode', sa.Enum('AUTONOMOUS', 'COLLABORATIVE', 'MANUAL', name='authoringmode'), nullable=False, server_default='MANUAL', comment='Authoring mode (autonomous/collaborative/manual)'))
    op.add_column('stories', sa.Column('pov_type', sa.Enum('FIRST', 'THIRD', 'OMNISCIENT', name='povtype'), nullable=False, server_default='THIRD', comment='Point of view type for narrative'))

    # Add new columns to story_beats table
    op.add_column('story_beats', sa.Column('generated_by', sa.Enum('AI', 'USER', 'COLLABORATIVE', name='generatedby'), nullable=False, server_default='USER', comment='Source of beat generation (ai/user/collaborative)'))
    op.add_column('story_beats', sa.Column('summary', sa.Text(), nullable=True, comment='Short summary for UI display (auto-generated for AI beats)'))
    op.add_column('story_beats', sa.Column('local_time_label', sa.String(length=255), nullable=True, comment="In-world narrative timestamp (e.g., 'Day 3', 'Log 0017')"))


def downgrade() -> None:
    # Remove columns from story_beats table
    op.drop_column('story_beats', 'local_time_label')
    op.drop_column('story_beats', 'summary')
    op.drop_column('story_beats', 'generated_by')

    # Remove columns from stories table
    op.drop_column('stories', 'pov_type')
    op.drop_column('stories', 'mode')

    # Drop enum types
    op.execute("DROP TYPE generatedby")
    op.execute("DROP TYPE povtype")
    op.execute("DROP TYPE authoringmode")
