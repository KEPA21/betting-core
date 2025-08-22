CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE SCHEMA IF NOT EXISTS core;

-- Referens: bookmakers
CREATE TABLE IF NOT EXISTS core.bookmakers (
    bookmaker_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    country TEXT,
    website TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Referens: markets (t.ex. 1X2, OU_2_5)
CREATE TABLE IF NOT EXISTS core.markets (
    market_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code TEXT NOT NULL UNIQUE,
    description TEXT, 
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Referens selections (HOME/DRAW/AWAY, OVER/UNDER, etc)
CREATE TABLE IF NOT EXISTS core.selections (
    selection_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    market_id UUID NOT NULL REFERENCES core.markets(market_id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    params JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_selections_market_code_line
ON core.selections (
  market_id,
  code,
  (COALESCE(params->>'line', 'null'))
);

-- Modellregister för predictions
CREATE TABLE IF NOT EXISTS core.models (
    model_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    metadata JSONB,
    UNIQUE (name, version),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Odds (historik över tid)
CREATE TABLE IF NOT EXISTS core.odds (
    odds_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id TEXT NOT NULL,
    bookmaker_id UUID NOT NULL REFERENCES core.bookmakers(bookmaker_id),
    selection_id UUID NOT NULL REFERENCES core.selections(selection_id),
    price NUMERIC(10,4) NOT NULL CHECK (price > 1.0),
    probability NUMERIC(7,6) CHECK (probability >= 0 AND probability <= 1),
    captured_at TIMESTAMPTZ NOT NULL,
    source TEXT, 
    checksum TEXT, 
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_odds_match ON core.odds(match_id);
CREATE INDEX IF NOT EXISTS idx_odds_selection ON core.odds(selection_id);
CREATE INDEX IF NOT EXISTS idx_odds_bookmaker ON core.odds(bookmaker_id);
CREATE INDEX IF NOT EXISTS idx_odds_captured_at ON core.odds(captured_at);

-- Predictions
CREATE TABLE IF NOT EXISTS core.predictions (
    prediction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id TEXT NOT NULL,
    model_id UUID NOT NULL REFERENCES core.models(model_id),
    version TEXT NOT NULL,
    selection_id UUID NOT NULL REFERENCES core.selections(selection_id),
    probability NUMERIC(7,6) NOT NULL CHECK (probability >= 0 AND probability <= 1),
    odds_fair NUMERIC(10,4),
    features JSONB,
    predicted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (match_id, model_id, version, selection_id)
);

CREATE INDEX IF NOT EXISTS idx_predictions_match ON core.predictions(match_id);
CREATE INDEX IF NOT EXISTS idx_predictions_model ON core.predictions(model_id);

-- Bets
CREATE TABLE IF NOT EXISTS core.bets (
    bet_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id TEXT,
    user_ref TEXT, 
    match_id TEXT NOT NULL,
    bookmaker_id UUID NOT NULL REFERENCES core.bookmakers(bookmaker_id),
    selection_id UUID NOT NULL REFERENCES core.selections(selection_id),
    stake NUMERIC(12,2) NOT NULL CHECK (stake > 0),
    price NUMERIC(10,4) NOT NULL CHECK (price > 1.0),
    placed_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    result TEXT,
    payout NUMERIC(12,2) CHECK (payout IS NULL OR payout >= 0),
    idempotency_key TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_bets_match ON core.bets(match_id);
CREATE INDEX IF NOT EXISTS idx_bets_user ON core.bets(user_ref);
CREATE INDEX IF NOT EXISTS idx_bets_status ON core.bets(status);

-- Ingest audit
CREATE TABLE IF NOT EXISTS core.ingest_audit (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity TEXT NOT NULL,
    source TEXT,
    count INTEGER,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'ok',
    details TEXT
);

-- Readiness-vy
CREATE OR REPLACE VIEW core.readiness AS SELECT (SELECT COUNT(*) FROM core.markets) AS markets, (SELECT COUNT(*) FROM core.selections) AS selections, (SELECT COUNT(*) FROM core.bookmakers) AS bookmakers;
