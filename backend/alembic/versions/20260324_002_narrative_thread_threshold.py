"""add transition_threshold to narrative_threads

Revision ID: wedge_core_v2_002
Revises: wedge_core_v1_001
Create Date: 2026-03-24

Additive only: adds transition_threshold Float column with server default 0.2.
"""

from alembic import op
import sqlalchemy as sa

revision = "wedge_core_v2_002"
down_revision = "wedge_core_v1_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "narrative_threads",
        sa.Column(
            "transition_threshold",
            sa.Float(),
            nullable=False,
            server_default="0.2",
        ),
    )


def downgrade() -> None:
    op.drop_column("narrative_threads", "transition_threshold")
