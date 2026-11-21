import { useQuery } from "@tanstack/react-query";
import { fetchRegionalDemand } from "../../services/api";
import type { Fuel } from "../../types/api";

const liters = new Intl.NumberFormat("en-BD", { maximumFractionDigits: 0 });
const fuels: Fuel[] = ["DIESEL", "PETROL", "OCTANE"];

export default function RegionalDemandPanel() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["regional-demand"],
    queryFn: fetchRegionalDemand,
    refetchInterval: 3000,
  });

  if (isLoading) {
    return (
      <div className="panel section-panel">
        <p className="muted">Loading regional demand data...</p>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="panel section-panel">
        <p className="notice notice-warning">Regional demand metrics temporarily unavailable.</p>
      </div>
    );
  }

  return (
    <div className="panel section-panel regional-demand-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">REGIONAL PROFILE</p>
          <h2>Regional Demand vs Served (Last {data.window_ticks} Ticks)</h2>
        </div>
        <span className="status-pill status-simulated">SIMULATED</span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "1rem" }}>
        {data.regional_demand.map((reg) => (
          <div
            key={reg.region_id}
            style={{
              background: "rgba(255, 255, 255, 0.02)",
              border: "1px solid var(--border-color, #30363d)",
              borderRadius: "6px",
              padding: "1rem",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
              <h3 style={{ margin: 0, fontSize: "1.05rem" }}>{reg.region_name}</h3>
              <span className="status-pill status-healthy" style={{ fontSize: "0.75rem" }}>
                Multiplier: {reg.demand_factor.toFixed(2)}×
              </span>
            </div>
            <p className="muted" style={{ fontSize: "0.8rem", margin: "0 0 0.75rem 0" }}>
              {reg.station_count} station(s) connected
            </p>

            <table style={{ width: "100%", fontSize: "0.85rem", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ color: "#8b949e", textAlign: "left", borderBottom: "1px solid #30363d" }}>
                  <th style={{ padding: "0.3rem 0" }}>Fuel</th>
                  <th>Demand</th>
                  <th>Served</th>
                  <th>Service Level</th>
                </tr>
              </thead>
              <tbody>
                {fuels.map((f) => {
                  const entry = reg.fuels[f];
                  if (!entry) return null;
                  const svcPct = (entry.service_level * 100).toFixed(1);
                  const isDegraded = entry.service_level < 0.95;
                  return (
                    <tr key={f} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                      <td style={{ padding: "0.4rem 0", fontWeight: 500 }}>{f}</td>
                      <td>{liters.format(entry.demand_liters)} L</td>
                      <td>{liters.format(entry.served_liters)} L</td>
                      <td>
                        <span style={{ color: isDegraded ? "#f85149" : "#3fb950", fontWeight: 600 }}>
                          {svcPct}%
                        </span>
                        {entry.unmet_liters > 0 && (
                          <small style={{ color: "#f85149", display: "block", fontSize: "0.75rem" }}>
                            Unmet: {liters.format(entry.unmet_liters)} L
                          </small>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ))}
      </div>
    </div>
  );
}
