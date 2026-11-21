import type { DepotRisk, Incident, Snapshot, SimulatorEvent } from "../../types/api";
import { localTime, quantity } from "../../lib/format";
import DepotsPanel from "../inventory/DepotsPanel";
import DepotRiskPanel from "../inventory/DepotRiskPanel";
import InventoryMatrix from "../inventory/InventoryMatrix";
import EventsPanel from "../incidents/EventsPanel";
import RoutesPanel from "../network/RoutesPanel";
import RegionalDemandPanel from "../demand/RegionalDemandPanel";

export default function DashboardPage({
  snapshot,
  events,
  incidents,
  depotRisks = [],
}: {
  snapshot: Snapshot;
  events: SimulatorEvent[];
  incidents: Incident[];
  depotRisks?: DepotRisk[];
}) {
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
    {depotRisks.length > 0 && (
      <section className="panel section-panel">
        <div className="section-heading">
          <div><p className="eyebrow">DEPOT SUPPLY RISK</p><h2>24-Hour Forward Supply Cover</h2></div>
          <span className="section-note">Projected net inventory runway after committed shipments</span>
        </div>
        <DepotRiskPanel risks={depotRisks} />
      </section>
    )}
    <RegionalDemandPanel />
    <div className="lower-grid"><RoutesPanel routes={snapshot.routes} /><EventsPanel events={events} incidents={incidents} /></div>
  </>;
}
