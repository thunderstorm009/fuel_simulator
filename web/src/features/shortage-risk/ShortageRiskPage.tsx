import { lazy, Suspense } from "react";
import type { Fuel, InventoryEntity, RiskForecast, TrajectoryResponse } from "../../types/api";
import { riskClass } from "../../lib/format";
import StatusPill from "../../components/ui/StatusPill";

const TrajectoryDrawer = lazy(() => import("./TrajectoryDrawer"));
const fuels: Fuel[] = ["DIESEL", "PETROL", "OCTANE"];

function RiskMatrix({
  stations,
  forecasts,
  selected,
  onSelect,
}: {
  stations: InventoryEntity[];
  forecasts: RiskForecast[];
  selected: { stationId: string; fuel: Fuel } | null;
  onSelect: (stationId: string, fuel: Fuel) => void;
}) {
  const byPair = new Map(forecasts.map((row) => [`${row.station_id}:${row.fuel_type}`, row]));
  return (
    <div className="table-scroll">
      <table className="risk-matrix">
        <thead><tr><th>Station</th>{fuels.map((fuel) => <th key={fuel}>{fuel}</th>)}</tr></thead>
        <tbody>{stations.map((station) => (
          <tr key={station.id}>
            <th scope="row"><span className="entity-name">{station.name}</span><span className="entity-meta">{station.region_id}</span></th>
            {fuels.map((fuel) => {
              const forecast = byPair.get(`${station.id}:${fuel}`);
              const active = selected?.stationId === station.id && selected.fuel === fuel;
              return (
                <td key={fuel}>
                  <button className={`risk-cell ${forecast ? riskClass(forecast.risk_level) : "risk-pending"} ${active ? "selected" : ""}`} onClick={() => onSelect(station.id, fuel)} disabled={!forecast}>
                    <strong>{forecast?.risk_level ?? "PENDING"}</strong>
                    <span>{forecast?.hours_to_stockout == null ? ">24h" : `${forecast.hours_to_stockout.toFixed(1)}h`} to stockout</span>
                    {forecast && <span>{Math.round(forecast.stockout_prob_24h * 100)}% · {Math.round(forecast.confidence * 100)}% confidence</span>}
                    {forecast?.needs_review && <em>Needs review</em>}
                  </button>
                </td>
              );
            })}
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}

export default function ShortageRiskPage({
  stations,
  forecasts,
  trajectory,
  selected,
  onSelect,
  onClose,
}: {
  stations: InventoryEntity[];
  forecasts: RiskForecast[];
  trajectory: TrajectoryResponse | undefined;
  selected: { stationId: string; fuel: Fuel } | null;
  onSelect: (stationId: string, fuel: Fuel) => void;
  onClose: () => void;
}) {
  const alerts = forecasts.filter((item) => item.risk_level === "critical" || item.risk_level === "high");
  const selectedStation = stations.find((station) => station.id === selected?.stationId);
  return <>
    <section className="overview-heading">
      <div><p className="eyebrow">DEMAND FORECAST</p><h2>Stockout risk</h2><p className="muted">24-hour projection with uncertainty from profile noise and rate variation.</p></div>
      <div className="metric-card"><span className="metric-label">PAIRS TRACKED</span><strong>{forecasts.length}</strong><span>station and fuel combinations</span></div>
    </section>
    <section className="panel section-panel">
      <div className="section-heading"><div><p className="eyebrow">RISK MATRIX</p><h2>Hours to stockout</h2></div><span className="section-note">Select a cell to inspect the projection band</span></div>
      <RiskMatrix stations={stations} forecasts={forecasts} selected={selected} onSelect={onSelect} />
    </section>
    <div className="lower-grid risk-lower-grid">
      <section className="panel section-panel">
        <div className="section-heading"><div><p className="eyebrow">ALERTS</p><h2>High and critical pairs</h2></div><span className="count-badge">{alerts.length}</span></div>
        <div className="event-list">
          {alerts.map((item) => {
            const station = stations.find((candidate) => candidate.id === item.station_id);
            return <button className="risk-alert" key={`${item.station_id}-${item.fuel_type}`} onClick={() => onSelect(item.station_id, item.fuel_type)}><strong>{station?.name ?? item.station_id} · {item.fuel_type}</strong><StatusPill status={item.risk_level} className={riskClass(item.risk_level)} /><small>{item.hours_to_stockout == null ? ">24h" : `${item.hours_to_stockout.toFixed(1)}h`} · {Math.round(item.stockout_prob_24h * 100)}% probability</small></button>;
          })}
          {alerts.length === 0 && <p className="empty-note">No high or critical stockout risks.</p>}
        </div>
      </section>
      {selected && selectedStation && <Suspense fallback={<aside className="trajectory-drawer panel">Loading chart…</aside>}><TrajectoryDrawer station={selectedStation} fuel={selected.fuel} record={trajectory} onClose={onClose} /></Suspense>}
    </div>
  </>;
}
