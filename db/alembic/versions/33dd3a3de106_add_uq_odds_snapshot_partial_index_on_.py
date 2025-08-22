"""Add uq_odds_snapshot + partial index on open bets

Revision ID: 33dd3a3de106
Revises: c830f2d0fd12
Create Date: 2025-08-18 22:34:38.277414

"""
from alembic import op
import sqlalchemy as sa

revision = "33dd3a3de106"
down_revision = "c830f2d0fd12"
branch_labels = None
depends_on = None


def upgrade():
    # Unik snapshot-nyckel för odds
    op.create_unique_constraint(
        "uq_odds_snapshot",
        "odds",
        ["match_id", "bookmaker_id", "selection_id", "captured_at"],
        schema="core",
    )

    # Partial index på öppna bets
    op.create_index(
        "idx_bets_open_only",
        "bets",
        ["status"],
        unique=False,
        schema="core",
        postgresql_where=sa.text("status = 'open'"),
    )


def downgrade():
    op.drop_index("idx_bets_open_only", table_name="bets", schema="core")
    op.drop_constraint("uq_odds_snapshot", "odds", schema="core", type_="unique")
