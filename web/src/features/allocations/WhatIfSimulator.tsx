import { useEffect, useState } from "react";
import { fetchWhatIf } from "../../services/api";
import type { Recommendation, WhatIfCandidate, WhatIfResponse } from "../../types/api";

const liters = new Intl.NumberFormat("en-BD", { maximumFractionDigits: 0 });

export default function WhatIfSimulator({ item }: { item: Recommendation }) {
  const [quantity, setQuantity] = useState(item.quantity);
  const [depotId, setDepotId] = useState(item.depot_id);
  const [routeId, setRouteId] = useState(item.route_id);
  const [result, setResult] = useState<WhatIfResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Collect available routes/depots from item and alternatives
  const alternatives = item.explanation_json.alternatives || [];
  const routeOptions = [
    { depot: item.depot_id, route: item.route_id, label: `${item.depot_id} via ${item.route_id} (Proposed)` },
    ...alternatives
      .filter((alt) => alt.depot_id && alt.route_id)
      .map((alt) => ({
        depot: String(alt.depot_id),
        route: String(alt.route_id),
        label: `${alt.depot_id} via ${alt.route_id} (Alternative: ${alt.reason || "feasible"})`,
      })),
  ];

  async function runSimulation(candidateQty: number, candidateDepot: string, candidateRoute: string) {
    setLoading(true);
    setError(null);
    try {
      const candidate: WhatIfCandidate = {
        source_depot_id: candidateDepot,
        destination_station_id: item.station_id,
        route_id: candidateRoute,
        fuel_type: item.fuel_type,
        quantity: candidateQty,
      };
      const res = await fetchWhatIf(candidate);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Simulation failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void runSimulation(quantity, depotId, routeId);
  }, []);

  const handleRouteSelect = (selectedRoute: string) => {
    const found = routeOptions.find((r) => r.route === selectedRoute);
    if (found) {
      setRouteId(found.route);
      setDepotId(found.depot);
      void runSimulation(quantity, found.depot, found.route);
    }
  };

  const handleQuantityChange = (val: number) => {
    const q = Math.max(500, Math.min(25000, val));
    setQuantity(q);
  };

  return (
    <div className="what-if-panel" style={{ marginTop: "1rem", padding: "1rem", background: "var(--panel-bg, #1a1e24)", borderRadius: "8px", border: "1px solid var(--border-color, #2d333b)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
        <h4 style={{ margin: 0 }}>Simulate Allocation Impact (What-If)</h4>
        <span className="status-pill status-simulated" style={{ fontSize: "0.75rem", background: "#30363d", color: "#8b949e" }}>SIMULATED</span>
      </div>
      <p className="muted" style={{ fontSize: "0.85rem", marginTop: 0 }}>
        Test alternative shipment quantities and routes. Approving acts only on the permanent proposal body.
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
        <div>
          <label style={{ display: "block", fontSize: "0.85rem", marginBottom: "0.25rem" }}>
            Shipment Quantity: <strong>{liters.format(quantity)} L</strong>
          </label>
          <input
            type="range"
            min={500}
            max={15000}
            step={500}
            value={quantity}
            onChange={(e) => handleQuantityChange(Number(e.target.value))}
            style={{ width: "100%" }}
          />
        </div>
        <div>
          <label style={{ display: "block", fontSize: "0.85rem", marginBottom: "0.25rem" }}>Dispatch Corridor / Route</label>
          <select
            value={routeId}
            onChange={(e) => handleRouteSelect(e.target.value)}
            style={{ width: "100%", padding: "0.4rem", borderRadius: "4px", background: "var(--input-bg, #0d1117)", color: "inherit", border: "1px solid var(--border-color, #30363d)" }}
          >
            {routeOptions.map((opt) => (
              <option key={opt.route} value={opt.route}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div style={{ marginBottom: "0.75rem" }}>
        <button
          className="action-button secondary"
          style={{ fontSize: "0.85rem", padding: "0.3rem 0.8rem" }}
          onClick={() => void runSimulation(quantity, depotId, routeId)}
          disabled={loading}
        >
          {loading ? "Simulating..." : "Recalculate Impact"}
        </button>
      </div>

      {error && <p className="notice notice-warning" style={{ fontSize: "0.85rem" }}>{error}</p>}

      {result && (
        <div style={{ marginTop: "0.75rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
            <span style={{ fontSize: "0.85rem" }}>Verdict:</span>
            <span
              className={`status-pill ${
                result.verdict === "FEASIBLE_BENEFICIAL"
                  ? "status-healthy"
                  : result.verdict === "FEASIBLE_NEUTRAL"
                  ? "status-degraded"
                  : "status-offline"
              }`}
              style={{ fontWeight: 600 }}
            >
              {result.verdict.replaceAll("_", " ")}
            </span>
          </div>

          {!result.feasible && result.violations.length > 0 && (
            <div className="notice notice-warning" style={{ marginBottom: "0.75rem", fontSize: "0.85rem" }}>
              <strong>Constraint Violations:</strong>
              <ul style={{ margin: "0.25rem 0 0 1rem", padding: 0 }}>
                {result.violations.map((v, i) => (
                  <li key={i}>{v.message} ({v.code})</li>
                ))}
              </ul>
            </div>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <div style={{ padding: "0.5rem", background: "rgba(255,255,255,0.03)", borderRadius: "4px" }}>
              <div style={{ fontSize: "0.8rem", color: "#8b949e", marginBottom: "0.25rem" }}>STATION OUTLOOK</div>
              <div style={{ fontSize: "0.85rem" }}>
                Hours to stockout:{" "}
                <strong>
                  {result.before.hours_to_stockout !== null ? `${result.before.hours_to_stockout.toFixed(1)}h` : ">24h"}
                </strong>{" "}
                &rarr;{" "}
                <strong style={{ color: "#3fb950" }}>
                  {result.after.hours_to_stockout !== null ? `${result.after.hours_to_stockout.toFixed(1)}h` : ">24h"}
                </strong>{" "}
                {result.delta.hours_to_stockout_change !== null && result.delta.hours_to_stockout_change > 0 && (
                  <span style={{ color: "#3fb950", fontSize: "0.75rem" }}>(+{result.delta.hours_to_stockout_change.toFixed(1)}h)</span>
                )}
              </div>
              <div style={{ fontSize: "0.85rem", marginTop: "0.25rem" }}>
                P(stockout 24h):{" "}
                <strong>{Math.round(result.before.stockout_probability_24h * 100)}%</strong> &rarr;{" "}
                <strong style={{ color: "#3fb950" }}>{Math.round(result.after.stockout_probability_24h * 100)}%</strong>
              </div>
            </div>

            <div style={{ padding: "0.5rem", background: "rgba(255,255,255,0.03)", borderRadius: "4px" }}>
              <div style={{ fontSize: "0.8rem", color: "#8b949e", marginBottom: "0.25rem" }}>DEPOT IMPACT ({depotId})</div>
              <div style={{ fontSize: "0.85rem" }}>
                Net forward cover:{" "}
                <strong>{liters.format(result.before.depot_net_cover_liters)} L</strong> &rarr;{" "}
                <strong>{liters.format(result.after.depot_net_cover_liters)} L</strong>{" "}
                <span style={{ color: "#d29922", fontSize: "0.75rem" }}>({liters.format(result.delta.depot_net_cover_change)} L)</span>
              </div>
              <div style={{ fontSize: "0.85rem", marginTop: "0.25rem" }}>
                Depot cover hours:{" "}
                <strong>{result.before.depot_cover_hours.toFixed(1)}h</strong> &rarr;{" "}
                <strong>{result.after.depot_cover_hours.toFixed(1)}h</strong>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
