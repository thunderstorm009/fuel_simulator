"""Shared metric definitions for the Python services."""

from prometheus_client import Counter, Gauge, Histogram

health_checks = Counter("service_health_checks_total", "Health checks served", ["service"])
sim_client_requests = Counter(
    "sim_client_requests_total",
    "Simulator requests by endpoint and outcome",
    ["endpoint", "outcome"],
)
sim_client_retries = Counter("sim_client_retries_total", "Simulator request retries", ["endpoint"])
sim_client_failures = Counter(
    "sim_client_failures_total", "Simulator request failures", ["endpoint"]
)
sim_breaker_state = Gauge("sim_breaker_state", "Simulator circuit breaker state", ["state"])
worker_ingest_success = Counter("worker_ingest_success_total", "Successful snapshot ingestions")
worker_ingest_failures = Counter("worker_ingest_failures_total", "Failed snapshot ingestions")
snapshot_rejected = Counter(
    "snapshot_rejected_total", "Snapshots rejected before persistence", ["reason"]
)
snapshot_age = Gauge("snapshot_age_seconds", "Age of the latest accepted snapshot")
forecasts_computed = Counter("forecasts_computed_total", "Forecasts calculated", ["risk_level"])
forecast_job_failures = Counter("forecast_job_failures_total", "Failed forecast jobs")
recommendations_created = Counter("recommendations_created_total", "Recommendations created")
recommendation_fallbacks = Counter(
    "recommendation_fallbacks_total", "Heuristic recommendation fallbacks"
)
recommendation_job_failures = Counter(
    "recommendation_job_failures_total", "Failed recommendation jobs"
)
allocation_executor_failures = Counter(
    "allocation_executor_failures_total", "Failed allocation executor poll cycles"
)
simulator_allocation_rejections = Counter(
    "simulator_allocation_rejections_total",
    "Allocation submissions rejected by the simulator",
    ["code"],
)
forecast_error_liters = Gauge(
    "forecast_error_liters",
    "Mean absolute demand forecast error in liters",
    ["station_id", "fuel_type"],
)
sse_events = Counter("worker_sse_events_total", "SSE hints received")
sse_reconnects = Counter("worker_sse_reconnects_total", "SSE reconnect attempts")
api_http_requests = Counter(
    "http_requests_total",
    "API requests by route and status class",
    ["method", "route", "status_class"],
)
api_http_request_duration = Histogram(
    "http_request_duration_seconds", "API request duration by route", ["method", "route"]
)
