import type { Route } from "../../types/api";
import { quantity } from "../../lib/format";
import StatusPill from "../../components/ui/StatusPill";

export default function RoutesPanel({ routes }: { routes: Route[] }) {
  return (
    <section className="panel section-panel">
      <div className="section-heading"><div><p className="eyebrow">NETWORK ACCESS</p><h2>Routes</h2></div><span className="count-badge">{routes.length}</span></div>
      <div className="route-list">{routes.map((route) => (
        <article className="route-row" key={route.id}>
          <div className="route-line"><span>{route.source_depot_id}</span><span className="route-arrow">→</span><span>{route.destination_station_id}</span></div>
          <div className="route-meta"><span>{route.transit_ticks} ticks</span><span>Max {quantity(route.max_shipment)} L</span><StatusPill status={route.status} /></div>
        </article>
      ))}</div>
    </section>
  );
}
