import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Fuel, InventoryEntity, TrajectoryResponse } from "../../types/api";

const numberFormat = new Intl.NumberFormat("en-BD", { maximumFractionDigits: 0 });

export default function TrajectoryDrawer({
  station,
  fuel,
  record,
  onClose,
}: {
  station: InventoryEntity;
  fuel: Fuel;
  record: TrajectoryResponse | undefined;
  onClose: () => void;
}) {
  const level = record?.risk_level ?? "pending";
  return (
    <aside className="trajectory-drawer panel" aria-label="Stockout projection">
      <div className="section-heading">
        <div><p className="eyebrow">SIMULATED PROJECTION</p><h3>{station.name} · {fuel}</h3></div>
        <button className="close-button" onClick={onClose} aria-label="Close projection">×</button>
      </div>
      {!record ? <p className="muted">Loading the latest forecast…</p> : <>
        <div className="drawer-summary">
          <span className={`status-pill risk-${level}`}>{level}</span>
          <strong>{record.hours_to_stockout == null ? ">24h" : `${record.hours_to_stockout.toFixed(1)}h`}</strong>
          <span>{Math.round(record.stockout_prob_24h * 100)}% stockout probability</span>
          {record.needs_review && <em>Needs review</em>}
        </div>
        <div className="trajectory-chart" role="img" aria-label="Projected inventory with 10th and 90th percentile band">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={record.trajectory} margin={{ top: 10, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27384a" />
              <XAxis dataKey="tick_offset" stroke="#8fa0b2" tickLine={false} axisLine={false} />
              <YAxis stroke="#8fa0b2" tickLine={false} axisLine={false} width={54} />
              <Tooltip formatter={(value) => `${numberFormat.format(Number(value))} L`} labelFormatter={(tick) => `Tick +${tick}`} />
              <Area type="monotone" dataKey="p90_inventory" stroke="#63b3a1" fill="#63b3a1" fillOpacity={0.12} name="P90 inventory" />
              <Area type="monotone" dataKey="p10_inventory" stroke="#e8a264" fill="#e8a264" fillOpacity={0.18} name="P10 inventory" />
              <Area type="monotone" dataKey="mean_inventory" stroke="#8bc2ff" fill="none" strokeWidth={2} name="Mean inventory" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <dl className="driver-list">
          <div><dt>Demand multiplier</dt><dd>{record.drivers.demand_multiplier.toFixed(2)}×</dd></div>
          <div><dt>Recent demand ratio</dt><dd>{record.drivers.recent_ratio.toFixed(2)}×</dd></div>
          <div><dt>History used</dt><dd>{record.drivers.history_ticks} ticks</dd></div>
          <div><dt>Known station arrivals</dt><dd>{record.drivers.arrivals.reduce((sum, item) => sum + item.quantity, 0).toLocaleString()} L</dd></div>
        </dl>
      </>}
    </aside>
  );
}
