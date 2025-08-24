"""Bets idempotency indexes

Revision ID: ab8852cf8896
Revises: 33dd3a3de106
Create Date: 2025-08-19 22:30:58.021822

"""

from alembic import op


revision = "ab8852cf8896"
down_revision = "33dd3a3de106"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
    CREATE UNIQUE INDEX IF NOT EXISTS uq_bets_user_external_id
    ON core.bets(user_ref, external_id)
    WHERE external_id IS NOT NULL;
    """
    )
    op.execute(
        """
    CREATE INDEX IF NOT EXISTS idx_bets_placed_at
    ON core.bets(placed_at DESC);
    """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS core.idx_bets_placed_at;")
    op.execute("DROP INDEX IF EXISTS core.uq_bets_user_external_id;")
