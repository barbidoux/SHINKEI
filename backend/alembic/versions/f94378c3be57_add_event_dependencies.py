"""add_event_dependencies

Revision ID: f94378c3be57
Revises: d22cd0806e0a
Create Date: 2025-11-21 07:24:10.925672

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY


# revision identifiers, used by Alembic.
revision: str = 'f94378c3be57'
down_revision: Union[str, None] = 'd22cd0806e0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add caused_by_ids field to world_events for dependency tracking."""
    op.add_column(
        'world_events',
        sa.Column(
            'caused_by_ids',
            ARRAY(sa.String()),
            nullable=False,
            server_default='{}',
            comment='IDs of events that caused this event (dependency graph)'
        )
    )


def downgrade() -> None:
    """Remove caused_by_ids field from world_events."""
    op.drop_column('world_events', 'caused_by_ids')
