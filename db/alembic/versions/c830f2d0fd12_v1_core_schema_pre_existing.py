"""V1 core schema (pre-existing)

Revision ID: c830f2d0fd12
Revises: 
Create Date: 2025-08-18 22:33:55.742403

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql

# revision identifiers, used by Alembic.
revision = "c830f2d0fd12"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Extensions & schema
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.execute("CREATE SCHEMA IF NOT EXISTS core;")

    # --- core.bookmakers
    op.create_table(
        "bookmakers",
        sa.Column("bookmaker_id", psql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
        sa.Column("country", sa.Text()),
        sa.Column("website", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="core",
    )

    # --- core.markets
    op.create_table(
        "markets",
        sa.Column("market_id", psql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("code", sa.Text(), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="core",
    )

    # --- core.selections
    op.create_table(
        "selections",
        sa.Column("selection_id", psql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("market_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("params", psql.JSONB()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["market_id"], ["core.markets.market_id"], ondelete="CASCADE"),
        schema="core",
    )
    # funktionellt unikt index: (market_id, code, COALESCE(params->>'line','null'))
    op.create_index(
        "uq_selections_market_code_line",
        "selections",
        [
            "market_id",
            "code",
            sa.text("COALESCE((params->>'line'), 'null')"),
        ],
        unique=True,
        schema="core",
    )

    # --- core.models
    op.create_table(
        "models",
        sa.Column("model_id", psql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("metadata", psql.JSONB()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("name", "version"),
        schema="core",
    )

    # --- core.odds (OBS: utan uniq på snapshot; det lägger vi i nästa revision)
    op.create_table(
        "odds",
        sa.Column("odds_id", psql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("match_id", sa.Text(), nullable=False),
        sa.Column("bookmaker_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("selection_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("price", sa.Numeric(10, 4), nullable=False),
        sa.Column("probability", sa.Numeric(7, 6)),
        sa.Column("captured_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("source", sa.Text()),
        sa.Column("checksum", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("price > 1.0", name="chk_odds_price_gt_1"),
        sa.CheckConstraint("probability IS NULL OR (probability >= 0 AND probability <= 1)", name="chk_odds_prob_0_1"),
        sa.ForeignKeyConstraint(["bookmaker_id"], ["core.bookmakers.bookmaker_id"]),
        sa.ForeignKeyConstraint(["selection_id"], ["core.selections.selection_id"]),
        schema="core",
    )
    op.create_index("idx_odds_match", "odds", ["match_id"], schema="core")
    op.create_index("idx_odds_selection", "odds", ["selection_id"], schema="core")
    op.create_index("idx_odds_bookmaker", "odds", ["bookmaker_id"], schema="core")
    op.create_index("idx_odds_captured_at", "odds", ["captured_at"], schema="core")

    # --- core.predictions
    op.create_table(
        "predictions",
        sa.Column("prediction_id", psql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("match_id", sa.Text(), nullable=False),
        sa.Column("model_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("selection_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("probability", sa.Numeric(7, 6), nullable=False),
        sa.Column("odds_fair", sa.Numeric(10, 4)),
        sa.Column("features", psql.JSONB()),
        sa.Column("predicted_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("probability >= 0 AND probability <= 1", name="chk_predictions_prob_0_1"),
        sa.ForeignKeyConstraint(["model_id"], ["core.models.model_id"]),
        sa.ForeignKeyConstraint(["selection_id"], ["core.selections.selection_id"]),
        sa.UniqueConstraint("match_id", "model_id", "version", "selection_id", name="uq_predictions_key"),
        schema="core",
    )
    op.create_index("idx_predictions_match", "predictions", ["match_id"], schema="core")
    op.create_index("idx_predictions_model", "predictions", ["model_id"], schema="core")

    # --- core.bets
    op.create_table(
        "bets",
        sa.Column("bet_id", psql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("external_id", sa.Text()),
        sa.Column("user_ref", sa.Text()),
        sa.Column("match_id", sa.Text(), nullable=False),
        sa.Column("bookmaker_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("selection_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("stake", sa.Numeric(12, 2), nullable=False),
        sa.Column("price", sa.Numeric(10, 4), nullable=False),
        sa.Column("placed_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'open'")),
        sa.Column("result", sa.Text()),
        sa.Column("payout", sa.Numeric(12, 2)),
        sa.Column("idempotency_key", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("stake > 0", name="chk_bets_stake_gt_0"),
        sa.CheckConstraint("price > 1.0", name="chk_bets_price_gt_1"),
        sa.CheckConstraint("payout IS NULL OR payout >= 0", name="chk_bets_payout_ge_0"),
        sa.ForeignKeyConstraint(["bookmaker_id"], ["core.bookmakers.bookmaker_id"]),
        sa.ForeignKeyConstraint(["selection_id"], ["core.selections.selection_id"]),
        sa.UniqueConstraint("idempotency_key", name="uq_bets_idempotency_key"),
        schema="core",
    )
    op.create_index("idx_bets_match", "bets", ["match_id"], schema="core")
    op.create_index("idx_bets_user", "bets", ["user_ref"], schema="core")
    op.create_index("idx_bets_status", "bets", ["status"], schema="core")

    # --- core.ingest_audit
    op.create_table(
        "ingest_audit",
        sa.Column("audit_id", psql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("entity", sa.Text(), nullable=False),
        sa.Column("source", sa.Text()),
        sa.Column("count", sa.Integer()),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("finished_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'ok'")),
        sa.Column("details", sa.Text()),
        schema="core",
    )

    # --- Vyer
    op.execute("""
        CREATE OR REPLACE VIEW core.readiness AS
        SELECT
            (SELECT COUNT(*) FROM core.markets)     AS markets,
            (SELECT COUNT(*) FROM core.selections)  AS selections,
            (SELECT COUNT(*) FROM core.bookmakers)  AS bookmakers
    """)


def downgrade():
    # Droppa vy
    op.execute("DROP VIEW IF EXISTS core.readiness")

    # Droppa tabeller i omvänd FK-ordning
    op.drop_table("ingest_audit", schema="core")
    op.drop_index("idx_bets_status", table_name="bets", schema="core")
    op.drop_index("idx_bets_user", table_name="bets", schema="core")
    op.drop_index("idx_bets_match", table_name="bets", schema="core")
    op.drop_table("bets", schema="core")

    op.drop_index("idx_predictions_model", table_name="predictions", schema="core")
    op.drop_index("idx_predictions_match", table_name="predictions", schema="core")
    op.drop_table("predictions", schema="core")

    op.drop_index("idx_odds_captured_at", table_name="odds", schema="core")
    op.drop_index("idx_odds_bookmaker", table_name="odds", schema="core")
    op.drop_index("idx_odds_selection", table_name="odds", schema="core")
    op.drop_index("idx_odds_match", table_name="odds", schema="core")
    op.drop_table("odds", schema="core")

    op.drop_index("uq_selections_market_code_line", table_name="selections", schema="core")
    op.drop_table("selections", schema="core")

    op.drop_table("models", schema="core")
    op.drop_table("markets", schema="core")
    op.drop_table("bookmakers", schema="core")

    # Schema kan lämnas kvar; vill du verkligen rulla tillbaka allt:
    # op.execute("DROP SCHEMA IF EXISTS core CASCADE")
