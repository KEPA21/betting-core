"""Add uq_odds_snapshot + partial index on open bets

Revision ID: 33dd3a3de106
Revises: c830f2d0fd12
Create Date: 2025-08-18 22:34:38.277414

"""
from alembic import op

revision = "33dd3a3de106"
down_revision = "c830f2d0fd12"
branch_labels = None
depends_on = None

def upgrade():
    op.create_unique_constraint(
        "uq_odds_snapshot",
        "odds",
        ["match_id", "bookmaker_id", "selection_id", "captured_at"],
        schema="core",
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_bets_open ON core.bets(match_id) WHERE status='open';")

def downgrade():
    op.execute("DROP INDEX IF EXISTS core.idx_bets_open;")
    op.drop_constraint("uq_odds_snapshot", "odds", type_="unique", schema="core")