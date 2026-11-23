import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import WhatIfSimulator from "./WhatIfSimulator";
import {
  approveRecommendation,
  fetchDecisions,
  fetchRecommendations,
  rejectRecommendation,
} from "../../services/api";
import type { AllocationRequest, Recommendation } from "../../types/api";

const liters = new Intl.NumberFormat("en-BD", { maximumFractionDigits: 20 });

function hoursToStockout(item: Recommendation): number {
  const hours = item.explanation_json.risk_before.hours_to_stockout;
  return typeof hours === "number" ? hours : Number.POSITIVE_INFINITY;
}

function isAllocationRequest(value: unknown): value is AllocationRequest {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  return typeof body.source_depot_id === "string"
    && typeof body.destination_station_id === "string"
    && typeof body.route_id === "string"
    && ["DIESEL", "PETROL", "OCTANE"].includes(String(body.fuel_type))
    && typeof body.quantity === "number"
    && Number.isFinite(body.quantity)
    && body.quantity > 0
    && typeof body.idempotency_key === "string"
    && body.idempotency_key.length > 0;
}

function RecommendationCard({
  item,
  token,
  operatorName,
  notify,
}: {
  item: Recommendation;
  token: string;
  operatorName: string;
  notify: (message: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [confirmedReview, setConfirmedReview] = useState(false);
  const queryClient = useQueryClient();
  const request = isAllocationRequest(item.request_body) ? item.request_body : null;
  const requestMismatch = !request || item.quantity !== request.quantity
    || item.idempotency_key !== request.idempotency_key
    || item.depot_id !== request.source_depot_id
    || item.station_id !== request.destination_station_id
    || item.route_id !== request.route_id
    || item.fuel_type !== request.fuel_type;
  const canDecide = item.status === "PROPOSED" && !requestMismatch;
  const needsReview = item.explanation_json.confidence < 0.5;
  const canApprove = canDecide && (!needsReview || confirmedReview);

  async function decide(action: "approve" | "reject") {
    if (!token.trim()) {
      notify("Enter the operator token to record a decision.");
      return;
    }
    if (!operatorName.trim()) {
      notify("Enter an operator name to record a decision.");
      return;
    }
    if (action === "approve") {
      if (!request) {
        notify("This recommendation has no valid persisted allocation request.");
        return;
      }
      if (!window.confirm(`Approve recommendation ${item.id}: ${liters.format(request.quantity)} L of ${request.fuel_type} for ${request.destination_station_id}?`)) return;
    }
    if (action === "reject" && !reason.trim()) {
      notify("Enter a reason before rejecting this recommendation.");
      return;
    }
    setBusy(true);
    try {
      const result = action === "approve"
        ? await approveRecommendation(item.id, token, operatorName.trim())
        : await rejectRecommendation(item.id, token, reason.trim(), operatorName.trim());
      notify(`Recommendation ${result.status.toLowerCase()}.`);
      setReason("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["recommendations"] }),
        queryClient.invalidateQueries({ queryKey: ["decisions"] }),
      ]);
    } catch (error) {
      notify(error instanceof Error ? error.message : "Decision failed.");
    } finally {
      setBusy(false);
    }
  }

  const before = item.explanation_json.risk_before;
  const after = item.explanation_json.risk_after;
  const drivers = item.explanation_json.drivers;
  const constraints = item.explanation_json.constraints_applied;
  const alternatives = item.explanation_json.alternatives;

  return (
    <article className="recommendation-card panel">
      <div className="recommendation-main">
        <div>
          <div className="recommendation-title">
            <h3>{item.fuel_type} · {item.station_id}</h3>
            <span className={`status-pill status-${item.status.toLowerCase().replaceAll("_", "-")}`}>{item.status}</span>
            {canDecide && <span className="review-badge">Needs review</span>}
          </div>
          <p className="muted">{request ? `${liters.format(request.quantity)} L from ${request.source_depot_id} · Route ${request.route_id}` : "Allocation request unavailable"}</p>
          <p className="recommendation-id">Recommendation ID <code>{item.id}</code></p>
          <p className="recommendation-id">Idempotency key <code>{request?.idempotency_key ?? "Unavailable"}</code></p>
        </div>
        <div className="recommendation-meta">
          <span>{item.policy_used}{item.fallback_used ? " · fallback" : ""}</span>
          <span>{Math.round(item.explanation_json.confidence * 100)}% confidence</span>
          <span>ETA tick {String(drivers.arrival_tick ?? "unknown")}</span>
        </div>
      </div>

      <button className="text-button" onClick={() => setExpanded(!expanded)} aria-expanded={expanded}>
        {expanded ? "Hide explanation" : "Review explanation"}
      </button>

      {expanded && <div className="recommendation-details">
        <h4>Exact persisted allocation request</h4>
        <pre className="allocation-request-body">{JSON.stringify(item.request_body, null, 2)}</pre>
        <div className="risk-comparison">
          {[ ["Before", before], ["After", after] ].map(([label, risk]) => {
            const values = risk as Record<string, unknown>;
            const hours = values.hours_to_stockout;
            const probability = Number(values.stockout_probability_24h ?? 0);
            return <div className="risk-summary" key={label as string}>
              <div><span>{label as string}</span><strong>{typeof hours === "number" ? `${hours.toFixed(1)} h` : ">24 h"}</strong></div>
              <div className="meter meter-risk"><span style={{ width: `${Math.max(0, Math.min(100, probability * 100))}%` }} /></div>
              <small>{Math.round(probability * 100)}% 24-hour stockout probability · {String(values.risk_level ?? "unknown")}</small>
            </div>;
          })}
        </div>
        <dl className="driver-list">
          <div><dt>Demand multiplier</dt><dd>{String(drivers.demand_multiplier ?? "unknown")}×</dd></div>
          <div><dt>Recent demand trend</dt><dd>{String(drivers.recent_ratio ?? "unknown")}× baseline</dd></div>
          <div><dt>Projected inventory at arrival</dt><dd>{liters.format(Number(drivers.projected_inventory_at_arrival ?? 0))} L</dd></div>
          <div><dt>Target inventory</dt><dd>{liters.format(Number(drivers.target_inventory ?? 0))} L</dd></div>
          <div><dt>Data status</dt><dd>{item.explanation_json.data_status}</dd></div>
          {Array.isArray(drivers.delayed_supply) && drivers.delayed_supply.length > 0 && <div><dt>Delayed depot supply</dt><dd>{drivers.delayed_supply.length} arrival(s); ETA shown as context</dd></div>}
        </dl>
        <h4>Constraints applied</h4>
        <ul className="detail-list">{constraints.map((constraint, index) => <li key={index}>{Object.entries(constraint).map(([key, value]) => `${key.replaceAll("_", " ")}: ${String(value)}`).join(" · ")}</li>)}</ul>
        <h4>Rejected alternatives</h4>
        {alternatives.length ? <ul className="detail-list">{alternatives.map((alternative, index) => <li key={index}>{Object.entries(alternative).map(([key, value]) => `${key.replaceAll("_", " ")}: ${String(value)}`).join(" · ")}</li>)}</ul> : <p className="empty-note">No alternatives were rejected.</p>}
        <WhatIfSimulator item={item} />
      </div>}

      {requestMismatch && <p className="notice notice-warning" role="alert">Stored recommendation fields do not match its allocation request. Operator decisions are disabled until the record is corrected.</p>}

      {needsReview && canDecide && (
        <div className="notice notice-warning" style={{ margin: "0.5rem 0", fontSize: "0.85rem" }}>
          <strong>Low Confidence Advisory ({Math.round(item.explanation_json.confidence * 100)}%):</strong> Data status is {item.explanation_json.data_status}. Requires explicit confirmation before approval.
          <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "0.5rem", cursor: "pointer" }}>
            <input type="checkbox" checked={confirmedReview} onChange={(e) => setConfirmedReview(e.target.checked)} />
            <span>I have reviewed the low-confidence explanation and accept this allocation.</span>
          </label>
        </div>
      )}

      {canDecide && <div className="decision-controls">
        <label>Rejection reason<textarea value={reason} maxLength={500} onChange={(event) => setReason(event.target.value)} placeholder="Required to reject" /></label>
        <div className="button-row">
          <button className="action-button secondary" disabled={busy} onClick={() => void decide("reject")}>Reject</button>
          <button className="action-button" disabled={busy || !canApprove} onClick={() => void decide("approve")}>Approve allocation</button>
        </div>
        <p className="muted" style={{ fontSize: "0.75rem", margin: "0.25rem 0 0 0" }}>Approval submits the permanent proposal as stored ({request ? `${liters.format(request.quantity)} L` : "N/A"}).</p>
      </div>}
      {item.failure_reason && <p className="failure-reason">{item.failure_reason}</p>}
    </article>
  );
}

import { useEventStream } from "../stream/useEventStream";

export default function RecommendationsPage({ token, onTokenChange }: { token: string; onTokenChange: (value: string) => void }) {
  const [notice, setNotice] = useState("");
  const [operatorName, setOperatorName] = useState(() => localStorage.getItem("operator_name") || "Chief Dispatcher Rahat");
  const [historyActionFilter, setHistoryActionFilter] = useState<string>("ALL");
  const [historyStatusFilter, setHistoryStatusFilter] = useState<string>("ALL");
  const [historySort, setHistorySort] = useState<"NEWEST" | "OLDEST" | "QUANTITY">("NEWEST");
  const [recFuelFilter, setRecFuelFilter] = useState<string>("ALL");

  const handleOperatorNameChange = (val: string) => {
    setOperatorName(val);
    localStorage.setItem("operator_name", val);
  };

  const { status } = useEventStream();
  const pollInterval = status === "live" ? false : 10000;
  const recommendationsQuery = useQuery({ queryKey: ["recommendations"], queryFn: fetchRecommendations, refetchInterval: pollInterval });
  const decisionsQuery = useQuery({ queryKey: ["decisions"], queryFn: fetchDecisions, refetchInterval: pollInterval });

  let recommendations = [...(recommendationsQuery.data ?? [])].sort((a, b) => hoursToStockout(a) - hoursToStockout(b));
  if (recFuelFilter !== "ALL") {
    recommendations = recommendations.filter((r) => r.fuel_type === recFuelFilter);
  }

  let decisions = [...(decisionsQuery.data ?? [])];
  if (historyActionFilter !== "ALL") {
    decisions = decisions.filter((d) => d.action.toUpperCase() === historyActionFilter);
  }
  if (historyStatusFilter !== "ALL") {
    decisions = decisions.filter((d) => d.status.toUpperCase() === historyStatusFilter);
  }
  if (historySort === "NEWEST") {
    decisions.sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime());
  } else if (historySort === "OLDEST") {
    decisions.sort((a, b) => new Date(a.at).getTime() - new Date(b.at).getTime());
  } else if (historySort === "QUANTITY") {
    decisions.sort((a, b) => b.quantity - a.quantity);
  }

  const exportDecisionsCSV = () => {
    const list = decisionsQuery.data ?? [];
    if (!list.length) return;
    const headers = ["id", "at", "operator", "action", "station_id", "fuel_type", "quantity", "route_id", "status", "reason"];
    const rows = list.map((d) => [
      d.id,
      d.at,
      `"${(d.actor || "operator").replace(/"/g, '""')}"`,
      d.action,
      d.station_id,
      d.fuel_type,
      d.quantity,
      d.route_id,
      d.status,
      `"${(d.reason || "").replace(/"/g, '""')}"`,
    ]);
    const csvContent = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `decision-history-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportDecisionsJSON = () => {
    const list = decisionsQuery.data ?? [];
    if (!list.length) return;
    const blob = new Blob([JSON.stringify(list, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `decision-history-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const copyDecisionsJSON = async () => {
    const list = decisionsQuery.data ?? [];
    await navigator.clipboard.writeText(JSON.stringify(list, null, 2));
    setNotice("Decision history JSON copied to clipboard.");
  };

  return <>
    <section className="overview-heading">
      <div>
        <p className="eyebrow">HUMAN REVIEW</p>
        <h2>Recommendations</h2>
        <p className="muted">Every allocation requires an operator decision, verified identity, and fresh validation.</p>
      </div>
      <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", alignItems: "center" }}>
        <label className="token-field">
          Operator name{" "}
          <input
            type="text"
            value={operatorName}
            onChange={(e) => handleOperatorNameChange(e.target.value)}
            placeholder="e.g. Chief Dispatcher"
            style={{ width: "160px" }}
          />
        </label>
        <label className="token-field">
          Operator token{" "}
          <input
            type="password"
            autoComplete="off"
            value={token}
            onChange={(event) => onTokenChange(event.target.value)}
            style={{ width: "140px" }}
          />
        </label>
      </div>
    </section>

    {notice && <div className="notice notice-warning" role="status">{notice}<button className="close-button" onClick={() => setNotice("")} aria-label="Dismiss">×</button></div>}
    {recommendationsQuery.isError && <div className="notice notice-warning" role="alert">Could not load recommendations. Polling will retry.</div>}

    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", margin: "0.5rem 0" }}>
      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", fontSize: "0.85rem" }}>
        <span className="muted">Filter fuel:</span>
        {(["ALL", "DIESEL", "PETROL", "OCTANE"] as const).map((fuel) => (
          <button
            key={fuel}
            className={`action-button ${recFuelFilter === fuel ? "" : "secondary"}`}
            style={{ padding: "0.2rem 0.6rem", fontSize: "0.75rem" }}
            onClick={() => setRecFuelFilter(fuel)}
          >
            {fuel}
          </button>
        ))}
      </div>
      <span className="muted" style={{ fontSize: "0.8rem" }}>{recommendations.length} candidate proposal(s)</span>
    </div>

    <section className="recommendation-list">
      {recommendations.map((item) => <RecommendationCard key={item.id} item={item} token={token} operatorName={operatorName} notify={setNotice} />)}
      {recommendations.length === 0 && <div className="panel section-panel"><p className="empty-note">No recommendations have been generated yet.</p></div>}
    </section>

    <section className="panel section-panel decision-history">
      <div className="section-heading" style={{ flexWrap: "wrap", gap: "0.5rem" }}>
        <div><p className="eyebrow">AUDIT TRAIL</p><h2>Decision history</h2></div>
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
          <select
            value={historyActionFilter}
            onChange={(e) => setHistoryActionFilter(e.target.value)}
            style={{ background: "#21262d", color: "#c9d1d9", border: "1px solid #30363d", borderRadius: "4px", padding: "0.25rem 0.5rem", fontSize: "0.75rem" }}
            aria-label="Filter decisions by action"
          >
            <option value="ALL">All Actions</option>
            <option value="APPROVE">Approved</option>
            <option value="REJECT">Rejected</option>
          </select>
          <select
            value={historyStatusFilter}
            onChange={(e) => setHistoryStatusFilter(e.target.value)}
            style={{ background: "#21262d", color: "#c9d1d9", border: "1px solid #30363d", borderRadius: "4px", padding: "0.25rem 0.5rem", fontSize: "0.75rem" }}
            aria-label="Filter decisions by status"
          >
            <option value="ALL">All Statuses</option>
            <option value="APPROVED">APPROVED</option>
            <option value="SUBMITTED">SUBMITTED</option>
            <option value="IN_TRANSIT">IN_TRANSIT</option>
            <option value="ARRIVED">ARRIVED</option>
            <option value="REJECTED">REJECTED</option>
          </select>
          <select
            value={historySort}
            onChange={(e) => setHistorySort(e.target.value as any)}
            style={{ background: "#21262d", color: "#c9d1d9", border: "1px solid #30363d", borderRadius: "4px", padding: "0.25rem 0.5rem", fontSize: "0.75rem" }}
            aria-label="Sort decisions"
          >
            <option value="NEWEST">Newest First</option>
            <option value="OLDEST">Oldest First</option>
            <option value="QUANTITY">Highest Quantity</option>
          </select>
          <button className="action-button secondary" style={{ padding: "0.2rem 0.5rem", fontSize: "0.75rem" }} onClick={copyDecisionsJSON} title="Copy full decision log to clipboard">Copy JSON</button>
          <button className="action-button secondary" style={{ padding: "0.2rem 0.5rem", fontSize: "0.75rem" }} onClick={exportDecisionsCSV} title="Export decisions as RFC 4180 CSV">Export CSV</button>
          <button className="action-button secondary" style={{ padding: "0.2rem 0.5rem", fontSize: "0.75rem" }} onClick={exportDecisionsJSON} title="Export decisions as structured JSON">Export JSON</button>
          <span className="count-badge">{decisions.length}</span>
        </div>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th title="Timestamp when the decision was committed to the audit trail">Time</th>
              <th title="Identity of the operator who recorded the decision">Operator</th>
              <th title="Decision action: approve or reject">Action</th>
              <th title="Destination station and requested fuel product">Recommendation</th>
              <th title="Allocated shipment volume in liters and designated route">Allocation</th>
              <th title="Documented reason (mandatory for rejection)">Reason</th>
              <th title="Lifecycle execution status of the allocation">Status</th>
            </tr>
          </thead>
          <tbody>
            {decisions.map((decision) => (
              <tr key={decision.id}>
                <td title={new Date(decision.at).toISOString()}>{new Date(decision.at).toLocaleString()}</td>
                <td><code>{decision.actor || "operator"}</code></td>
                <td><span className={`status-pill ${decision.action === "approve" ? "status-healthy" : "status-offline"}`}>{decision.action}</span></td>
                <td>{decision.fuel_type} · {decision.station_id}</td>
                <td>{liters.format(decision.quantity)} L · {decision.route_id}</td>
                <td>{decision.reason || "—"}</td>
                <td><span className={`status-pill status-${decision.status.toLowerCase().replaceAll("_", "-")}`}>{decision.status}</span></td>
              </tr>
            ))}
            {decisions.length === 0 && <tr><td colSpan={7}>No decisions recorded.</td></tr>}
          </tbody>
        </table>
      </div>
    </section>
  </>;
}
