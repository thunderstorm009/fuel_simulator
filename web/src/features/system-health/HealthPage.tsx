import type { HealthResponse } from "../../types/api";

const displayName: Record<string, string> = {
  backend: "API backend",
  database: "Database",
  worker: "Worker",
  simulator: "Simulator / worker feed",
  predictor: "Predictor",
  decision_engine: "Decision engine",
};

export default function HealthPage({
  report,
  loading,
  error,
}: {
  report?: HealthResponse;
  loading: boolean;
  error: boolean;
}) {
  return (
    <section className="health-page">
      <div className="overview-heading">
        <div><p className="eyebrow">SIMULATED PLATFORM HEALTH</p><h2>System health</h2></div>
        {report && <span className={`health-overall health-${report.status.toLowerCase()}`}>{report.status}</span>}
      </div>
      {loading && <p className="empty-note" role="status">Checking services…</p>}
      {error && <p className="notice notice-warning" role="status">Health details are temporarily unavailable.</p>}
      {report && (
        <>
          <div className="health-grid">
            {Object.entries(report.components).map(([name, component]) => (
              <article className="health-card panel" key={name}>
                <div><h3>{displayName[name] ?? name}</h3><span className={`health-overall health-${component.status.toLowerCase()}`}>{component.status}</span></div>
                <p>{component.age_seconds === null ? "Live probe" : `Last update ${Math.floor(component.age_seconds)}s ago`}</p>
              </article>
            ))}
          </div>
          <section className="health-summary panel" aria-label="API performance">
            <h3>API performance</h3>
            <p>In-process p95 latency: {(report.latency.p95_seconds * 1000).toFixed(0)} ms</p>
            <p>5xx error rate: {(report.latency.error_rate * 100).toFixed(2)}%</p>
            <small>Last checked {new Date(report.last_check_at).toLocaleTimeString()}</small>
          </section>
        </>
      )}
    </section>
  );
}
