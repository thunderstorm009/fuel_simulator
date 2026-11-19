import type { Incident, Snapshot, SimulatorEvent } from "../../types/api";
import { localTime, quantity } from "../../lib/format";
import DepotsPanel from "../inventory/DepotsPanel";
import InventoryMatrix from "../inventory/InventoryMatrix";
import EventsPanel from "../incidents/EventsPanel";
import RoutesPanel from "../network/RoutesPanel";

export default function DashboardPage({ snapshot, events, incidents }: { snapshot: Snapshot; events: SimulatorEvent[]; incidents: Incident[] }) {
  const serviceLevel = Math.round(snapshot.metrics.service_level * 100);
  return <>
    <section className="overview-heading">
      <div>
        <p className="eyebrow">CURRENT NETWORK STATE</p>
        <h2>Supply overview</h2>
        <p className="muted">Simulator time {localTime(snapshot.instance.sim_time)} · Tick {snapshot.instance.tick} · {snapshot.instance.tick_minutes} minutes per tick</p>
      </div>
      <div className="metric-card"><span className="metric-label">SERVICE LEVEL</span><strong>{serviceLevel}%</strong><span>{quantity(snapshot.metrics.unmet_demand_liters)} L unmet demand</span></div>
    </section>
    <section className="panel section-panel">
      <div className="section-heading"><div><p className="eyebrow">ON-HAND INVENTORY</p><h2>Stations by fuel</h2></div><span className="section-note">Inventory shown against station capacity</span></div>
      <InventoryMatrix stations={snapshot.stations} />
    </section>
    <section className="panel section-panel">
      <div className="section-heading"><div><p className="eyebrow">DEPOT INVENTORY</p><h2>Supply sources</h2></div><span className="section-note">On-hand liters by fuel type</span></div>
      <DepotsPanel depots={snapshot.depots} />
    </section>
    <div className="lower-grid"><RoutesPanel routes={snapshot.routes} /><EventsPanel events={events} incidents={incidents} /></div>
  </>;
}
