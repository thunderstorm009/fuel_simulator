CREATE TABLE IF NOT EXISTS snapshots (
    id BIGSERIAL PRIMARY KEY,
    tick INTEGER NOT NULL,
    sim_time TIMESTAMPTZ NOT NULL,
    raw_json JSONB NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL,
    stale BOOLEAN NOT NULL DEFAULT FALSE,
    data_status TEXT NOT NULL CHECK (data_status IN ('HEALTHY', 'DEGRADED', 'OFFLINE'))
);
CREATE INDEX IF NOT EXISTS snapshots_fetched_at_idx ON snapshots (fetched_at DESC);
CREATE INDEX IF NOT EXISTS snapshots_tick_fetched_idx ON snapshots (tick, fetched_at DESC);

CREATE TABLE IF NOT EXISTS forecasts (
    id BIGSERIAL PRIMARY KEY,
    snapshot_id BIGINT NOT NULL REFERENCES snapshots(id) ON DELETE CASCADE,
    tick INTEGER NOT NULL,
    station_id TEXT NOT NULL,
    fuel_type TEXT NOT NULL CHECK (fuel_type IN ('DIESEL', 'PETROL', 'OCTANE')),
    hours_to_stockout DOUBLE PRECISION,
    p10 DOUBLE PRECISION,
    p50 DOUBLE PRECISION,
    p90 DOUBLE PRECISION,
    stockout_prob_24h DOUBLE PRECISION NOT NULL CHECK (stockout_prob_24h BETWEEN 0 AND 1),
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    risk_level TEXT NOT NULL,
    needs_review BOOLEAN NOT NULL,
    source TEXT NOT NULL,
    trajectory JSONB NOT NULL DEFAULT '[]'::jsonb,
    drivers JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS forecasts_pair_tick_idx ON forecasts (station_id, fuel_type, tick DESC);
CREATE UNIQUE INDEX IF NOT EXISTS forecasts_snapshot_pair_idx
    ON forecasts (snapshot_id, station_id, fuel_type);

CREATE TABLE IF NOT EXISTS recommendations (
    id UUID PRIMARY KEY,
    status TEXT NOT NULL,
    policy_used TEXT NOT NULL,
    fallback_used BOOLEAN NOT NULL DEFAULT FALSE,
    depot_id TEXT NOT NULL,
    station_id TEXT NOT NULL,
    route_id TEXT NOT NULL,
    fuel_type TEXT NOT NULL CHECK (fuel_type IN ('DIESEL', 'PETROL', 'OCTANE')),
    quantity DOUBLE PRECISION NOT NULL CHECK (quantity > 0),
    idempotency_key TEXT NOT NULL UNIQUE,
    request_body JSONB NOT NULL,
    explanation_json JSONB NOT NULL,
    created_tick INTEGER NOT NULL,
    expires_tick INTEGER NOT NULL,
    correlation_id TEXT,
    sim_allocation_id BIGINT,
    failure_reason TEXT
);
CREATE INDEX IF NOT EXISTS recommendations_status_idx ON recommendations (status, created_tick);

CREATE TABLE IF NOT EXISTS decisions (
    id BIGSERIAL PRIMARY KEY,
    recommendation_id UUID NOT NULL REFERENCES recommendations(id),
    actor TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('approve', 'reject')),
    reason TEXT,
    at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS decisions_recommendation_idx ON decisions (recommendation_id, at);

CREATE TABLE IF NOT EXISTS incidents (
    id BIGSERIAL PRIMARY KEY,
    type TEXT NOT NULL,
    severity TEXT NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ,
    detail JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS incidents_open_idx ON incidents (severity, detected_at DESC) WHERE resolved_at IS NULL;
CREATE INDEX IF NOT EXISTS incidents_dedup_idx ON incidents (type, (detail->>'dedup_key')) WHERE resolved_at IS NULL;

CREATE TABLE IF NOT EXISTS depot_risks (
    id BIGSERIAL PRIMARY KEY,
    snapshot_id BIGINT NOT NULL REFERENCES snapshots(id) ON DELETE CASCADE,
    tick INTEGER NOT NULL,
    depot_id TEXT NOT NULL,
    fuel_type TEXT NOT NULL CHECK (fuel_type IN ('DIESEL', 'PETROL', 'OCTANE')),
    current_inventory DOUBLE PRECISION NOT NULL,
    scheduled_arrivals DOUBLE PRECISION NOT NULL,
    committed_allocations DOUBLE PRECISION NOT NULL,
    projected_demand DOUBLE PRECISION NOT NULL,
    net_cover_liters DOUBLE PRECISION NOT NULL,
    cover_hours DOUBLE PRECISION NOT NULL,
    is_bottleneck BOOLEAN NOT NULL DEFAULT FALSE,
    dispatch_utilization DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    evidence JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS depot_risks_depot_tick_idx ON depot_risks (depot_id, fuel_type, tick DESC);
CREATE UNIQUE INDEX IF NOT EXISTS depot_risks_snapshot_pair_idx
    ON depot_risks (snapshot_id, depot_id, fuel_type);


CREATE TABLE IF NOT EXISTS integration_events (
    id BIGSERIAL PRIMARY KEY,
    kind TEXT NOT NULL,
    detail JSONB NOT NULL DEFAULT '{}'::jsonb,
    at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS integration_events_kind_at_idx ON integration_events (kind, at DESC);

CREATE TABLE IF NOT EXISTS heartbeats (
    component TEXT PRIMARY KEY,
    last_seen TIMESTAMPTZ NOT NULL,
    detail JSONB NOT NULL DEFAULT '{}'::jsonb
);
