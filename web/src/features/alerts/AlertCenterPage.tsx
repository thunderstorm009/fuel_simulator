import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchIncidentsList, fetchIncidentSummary } from "../../services/api";
import { useEventStream } from "../stream/useEventStream";

export default function AlertCenterPage() {
  const [filter, setFilter] = useState<"all" | "open" | "resolved">("all");
  const { status } = useEventStream();
  const pollInterval = status === "live" ? false : 10000;
  const [summaries, setSummaries] = useState<
    Record<number, { text: string; source: string; label: string; loading?: boolean }>
  >({});

  const handleExplain = async (id: number) => {
    setSummaries((prev) => ({ ...prev, [id]: { text: "", source: "", label: "", loading: true } }));
    try {
      const res = await fetchIncidentSummary(id);
      setSummaries((prev) => ({
        ...prev,
        [id]: { text: res.summary, source: res.source, label: res.label, loading: false },
      }));
    } catch (err) {
      setSummaries((prev) => ({
        ...prev,
        [id]: {
          text: "Failed to generate plain-language summary.",
          source: "error",
          label: "AI-generated summary of simulated data",
          loading: false,
        },
      }));
    }
  };
  const { data, isLoading, isError } = useQuery({
    queryKey: ["incidents-full", filter],
    queryFn: () => fetchIncidentsList(filter),
    refetchInterval: pollInterval,
  });

  const incidents = data?.incidents || [];
  const openCount = incidents.filter((i) => !i.resolved_at).length;

  return (
    <div className="alert-center-page">
      <section className="overview-heading">
        <div>
          <p className="eyebrow">INCIDENT MANAGEMENT</p>
          <h2>Alert Center & Incident Log</h2>
          <p className="muted">
            Auditable log of detected anomalies, circuit breaker trips, calibration drift, and risk state transitions.
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <span className="status-pill status-simulated">SIMULATED</span>
          <span className={`status-pill ${openCount > 0 ? "status-offline" : "status-healthy"}`}>
            {openCount} Open Incident(s)
          </span>
        </div>
      </section>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem", flexWrap: "wrap", gap: "0.5rem" }}>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          {(["all", "open", "resolved"] as const).map((mode) => (
            <button
              key={mode}
              className={`action-button ${filter === mode ? "" : "secondary"}`}
              style={{ textTransform: "capitalize", padding: "0.35rem 0.9rem" }}
              onClick={() => setFilter(mode)}
            >
              {mode} Incidents
            </button>
          ))}
        </div>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button
            className="action-button secondary"
            style={{ padding: "0.25rem 0.6rem", fontSize: "0.75rem" }}
            onClick={async () => {
              await navigator.clipboard.writeText(JSON.stringify(incidents, null, 2));
              alert("Incidents JSON copied to clipboard.");
            }}
            title="Copy incidents to clipboard"
          >
            Copy JSON
          </button>
          <button
            className="action-button secondary"
            style={{ padding: "0.25rem 0.6rem", fontSize: "0.75rem" }}
            onClick={() => {
              if (!incidents.length) return;
              const headers = ["id", "type", "severity", "detected_at", "resolved_at", "detail"];
              const rows = incidents.map((i) => [
                i.id,
                i.type,
                i.severity,
                i.detected_at,
                i.resolved_at || "",
                `"${JSON.stringify(i.detail || {}).replace(/"/g, '""')}"`,
              ]);
              const csvContent = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
              const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = `incidents-${Date.now()}.csv`;
              a.click();
              URL.revokeObjectURL(url);
            }}
            title="Export incidents as RFC 4180 CSV"
          >
            Export CSV
          </button>
          <button
            className="action-button secondary"
            style={{ padding: "0.25rem 0.6rem", fontSize: "0.75rem" }}
            onClick={() => {
              if (!incidents.length) return;
              const blob = new Blob([JSON.stringify(incidents, null, 2)], { type: "application/json" });
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = `incidents-${Date.now()}.json`;
              a.click();
              URL.revokeObjectURL(url);
            }}
            title="Export incidents as structured JSON"
          >
            Export JSON
          </button>
        </div>
      </div>

      {isLoading && <p className="muted">Loading incidents...</p>}
      {isError && <p className="notice notice-warning">Failed to load incident history.</p>}

      <div className="incident-grid" style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        {incidents.map((inc) => {
          const isOpen = !inc.resolved_at;
          const severity = (inc.severity || "info").toLowerCase();
          const detail = inc.detail || {};
          return (
            <div
              key={inc.id}
              className="panel"
              style={{
                borderLeft: `4px solid ${
                  severity === "critical"
                    ? "#f85149"
                    : severity === "warning" || severity === "high"
                    ? "#d29922"
                    : "#58a6ff"
                }`,
                padding: "1rem",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.4rem" }}>
                <div>
                  <span
                    className={`status-pill ${
                      severity === "critical"
                        ? "status-offline"
                        : severity === "warning" || severity === "high"
                        ? "status-degraded"
                        : "status-healthy"
                    }`}
                    style={{ marginRight: "0.5rem" }}
                  >
                    {inc.severity.toUpperCase()}
                  </span>
                  <strong style={{ fontSize: "1rem" }}>{inc.type.replaceAll("_", " ").toUpperCase()}</strong>
                  {detail.entity_id && (
                    <span className="muted" style={{ marginLeft: "0.5rem", fontSize: "0.85rem" }}>
                      &bull; Entity: <code>{detail.entity_id}</code>
                    </span>
                  )}
                </div>
                <div style={{ textAlign: "right", fontSize: "0.8rem", color: "#8b949e" }}>
                  <div>Detected: {new Date(inc.detected_at).toLocaleTimeString()}</div>
                  {inc.resolved_at ? (
                    <div style={{ color: "#3fb950" }}>Resolved: {new Date(inc.resolved_at).toLocaleTimeString()}</div>
                  ) : (
                    <div style={{ color: "#f85149", fontWeight: 600 }}>Active / Open</div>
                  )}
                </div>
              </div>

              <p style={{ margin: "0.4rem 0", fontSize: "0.9rem" }}>
                {detail.explanation || "No narrative explanation recorded."}
              </p>

              {detail.recovery_condition && (
                <div style={{ fontSize: "0.8rem", color: "#8b949e", marginTop: "0.25rem" }}>
                  <strong>Recovery condition:</strong> {detail.recovery_condition}
                </div>
              )}

              {detail.evidence && Object.keys(detail.evidence).length > 0 && (
                <details style={{ marginTop: "0.5rem", fontSize: "0.8rem" }}>
                  <summary style={{ cursor: "pointer", color: "#58a6ff" }}>Structured Evidence</summary>
                  <pre
                    style={{
                      background: "rgba(0,0,0,0.3)",
                      padding: "0.5rem",
                      borderRadius: "4px",
                      overflowX: "auto",
                      margin: "0.25rem 0 0 0",
                    }}
                  >
                    {JSON.stringify(detail.evidence, null, 2)}
                  </pre>
                </details>
              )}

              <div style={{ marginTop: "0.75rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <button
                  type="button"
                  className="action-button secondary"
                  style={{ fontSize: "0.8rem", padding: "0.25rem 0.6rem" }}
                  onClick={() => handleExplain(inc.id)}
                  disabled={summaries[inc.id]?.loading}
                >
                  {summaries[inc.id]?.loading ? "Generating..." : "Explain Incident"}
                </button>
              </div>

              {summaries[inc.id] && !summaries[inc.id].loading && (
                <div
                  style={{
                    marginTop: "0.5rem",
                    padding: "0.6rem 0.8rem",
                    background: "rgba(56, 139, 253, 0.1)",
                    border: "1px solid rgba(56, 139, 253, 0.3)",
                    borderRadius: "4px",
                    fontSize: "0.85rem",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.25rem" }}>
                    <span className="muted" style={{ fontSize: "0.75rem", textTransform: "uppercase" }}>
                      Summary ({summaries[inc.id].source})
                    </span>
                    <span className="status-pill status-simulated" style={{ fontSize: "0.7rem", padding: "0.1rem 0.4rem" }}>
                      {summaries[inc.id].label}
                    </span>
                  </div>
                  <p style={{ margin: 0, lineHeight: 1.4 }}>{summaries[inc.id].text}</p>
                </div>
              )}
            </div>
          );
        })}

        {incidents.length === 0 && !isLoading && (
          <div className="panel section-panel">
            <p className="empty-note">No incidents match filter "{filter}". System operating within normal envelopes.</p>
          </div>
        )}
      </div>
    </div>
  );
}
