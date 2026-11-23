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
  notify,
}: {
  item: Recommendation;
  token: string;
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
        ? await approveRecommendation(item.id, token)
        : await rejectRecommendation(item.id, token, reason.trim());
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
  const { status } = useEventStream();
  const pollInterval = status === "live" ? false : 10000;
  const recommendationsQuery = useQuery({ queryKey: ["recommendations"], queryFn: fetchRecommendations, refetchInterval: pollInterval });
  const decisionsQuery = useQuery({ queryKey: ["decisions"], queryFn: fetchDecisions, refetchInterval: pollInterval });
  const recommendations = [...(recommendationsQuery.data ?? [])].sort((a, b) => hoursToStockout(a) - hoursToStockout(b));

  return <>
    <section className="overview-heading">
      <div><p className="eyebrow">HUMAN REVIEW</p><h2>Recommendations</h2><p className="muted">Every allocation requires an operator decision and fresh validation.</p></div>
      <label className="token-field">Operator token <input type="password" autoComplete="off" value={token} onChange={(event) => onTokenChange(event.target.value)} /></label>
    </section>
    {notice && <div className="notice notice-warning" role="status">{notice}<button className="close-button" onClick={() => setNotice("")} aria-label="Dismiss">×</button></div>}
    {recommendationsQuery.isError && <div className="notice notice-warning" role="alert">Could not load recommendations. Polling will retry.</div>}
    <section className="recommendation-list">
      {recommendations.map((item) => <RecommendationCard key={item.id} item={item} token={token} notify={setNotice} />)}
      {recommendations.length === 0 && <div className="panel section-panel"><p className="empty-note">No recommendations have been generated yet.</p></div>}
    </section>
    <section className="panel section-panel decision-history">
      <div className="section-heading"><div><p className="eyebrow">AUDIT TRAIL</p><h2>Decision history</h2></div><span className="count-badge">{decisionsQuery.data?.length ?? 0}</span></div>
      <div className="table-scroll"><table><thead><tr><th>Time</th><th>Action</th><th>Recommendation</th><th>Allocation</th><th>Reason</th><th>Status</th></tr></thead>
        <tbody>{(decisionsQuery.data ?? []).map((decision) => <tr key={decision.id}><td>{new Date(decision.at).toLocaleString()}</td><td>{decision.action}</td><td>{decision.fuel_type} · {decision.station_id}</td><td>{liters.format(decision.quantity)} L · {decision.route_id}</td><td>{decision.reason || "—"}</td><td><span className={`status-pill status-${decision.status.toLowerCase().replaceAll("_", "-")}`}>{decision.status}</span></td></tr>)}
        {decisionsQuery.data?.length === 0 && <tr><td colSpan={6}>No decisions recorded.</td></tr>}</tbody>
      </table></div>
    </section>
  </>;
}
