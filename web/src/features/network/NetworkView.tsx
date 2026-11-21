import type { Snapshot } from "../../types/api";

const liters = new Intl.NumberFormat("en-BD", { maximumFractionDigits: 0 });

export default function NetworkView({ snapshot }: { snapshot: Snapshot }) {
  const depots = snapshot.depots || [];
  const stations = snapshot.stations || [];
  const routes = snapshot.routes || [];
  const inTransitAllocs = (snapshot.allocations || []).filter(
    (a) => a.status === "IN_TRANSIT" || a.status === "PENDING"
  );

  return (
    <div className="network-view-page">
      <section className="overview-heading">
        <div>
          <p className="eyebrow">TOPOLOGY SCHEMATIC</p>
          <h2>Fuel Network Topology & Transport Corridors</h2>
          <p className="muted">
            Live visualization of refinery supply depots, transport corridors, stations, and in-transit volume.
          </p>
        </div>
        <span className="status-pill status-simulated">SIMULATED</span>
      </section>

      {/* Corridor Status Legend */}
      <div
        className="panel"
        style={{
          display: "flex",
          gap: "1.5rem",
          padding: "0.75rem 1rem",
          marginBottom: "1rem",
          fontSize: "0.85rem",
          flexWrap: "wrap",
        }}
      >
        <span>
          <strong style={{ color: "#3fb950" }}>● OPEN / AVAILABLE:</strong> Normal operating capacity
        </span>
        <span>
          <strong style={{ color: "#d29922" }}>● CONSTRAINED:</strong> Reduced throughput / maintenance
        </span>
        <span>
          <strong style={{ color: "#f85149" }}>● OUTAGE / DISRUPTED:</strong> Inoperable / route blocked
        </span>
        <span>
          <strong style={{ color: "#58a6ff" }}>&rarr; IN-TRANSIT:</strong> Shipments en route with live ETA
        </span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.2fr 1fr", gap: "1.5rem", alignItems: "start" }}>
        {/* Depots Column */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <h3 style={{ borderBottom: "2px solid #30363d", paddingBottom: "0.5rem" }}>
            Supply Depots ({depots.length})
          </h3>
          {depots.map((d) => {
            const isConstrained = d.status === "CONSTRAINED";
            const dieselStock = d.inventory.DIESEL ?? 0;
            const petrolStock = d.inventory.PETROL ?? 0;
            const octaneStock = d.inventory.OCTANE ?? 0;
            return (
              <div
                key={d.id}
                className="panel"
                style={{
                  borderLeft: `4px solid ${isConstrained ? "#d29922" : "#3fb950"}`,
                  padding: "0.85rem",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <strong>{d.name}</strong>
                  <span className={`status-pill ${isConstrained ? "status-degraded" : "status-healthy"}`}>
                    {d.status}
                  </span>
                </div>
                <small className="muted">ID: <code>{d.id}</code></small>
                <div style={{ marginTop: "0.5rem", fontSize: "0.8rem", display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.25rem" }}>
                  <div>Diesel: <strong>{liters.format(dieselStock)}</strong></div>
                  <div>Petrol: <strong>{liters.format(petrolStock)}</strong></div>
                  <div>Octane: <strong>{liters.format(octaneStock)}</strong></div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Transport Corridors / Routes Column */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          <h3 style={{ borderBottom: "2px solid #30363d", paddingBottom: "0.5rem" }}>
            Transport Corridors ({routes.length})
          </h3>
          {routes.map((r) => {
            const isDisrupted = r.status === "DISRUPTED" || r.status === "BLOCKED";
            const allocsOnRoute = inTransitAllocs.filter((a) => a.route_id === r.id);
            return (
              <div
                key={r.id}
                className="panel"
                style={{
                  padding: "0.75rem",
                  borderLeft: `4px solid ${isDisrupted ? "#f85149" : "#58a6ff"}`,
                  background: isDisrupted ? "rgba(248, 81, 73, 0.05)" : "rgba(255, 255, 255, 0.02)",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>
                    {r.source_depot_id} &rarr; {r.destination_station_id}
                  </span>
                  <span className={`status-pill ${isDisrupted ? "status-offline" : "status-healthy"}`}>
                    {r.status}
                  </span>
                </div>
                <div style={{ fontSize: "0.8rem", color: "#8b949e", marginTop: "0.2rem" }}>
                  Route <code>{r.id}</code> &bull; Transit: {r.transit_ticks} ticks &bull; Max limit: {liters.format(r.max_shipment)} L
                </div>

                {allocsOnRoute.length > 0 && (
                  <div style={{ marginTop: "0.5rem", padding: "0.35rem 0.5rem", background: "rgba(88, 166, 255, 0.1)", borderRadius: "4px", fontSize: "0.8rem" }}>
                    {allocsOnRoute.map((a) => (
                      <div key={a.id} style={{ color: "#58a6ff" }}>
                        &bull; Active shipment #{a.id}: {liters.format(a.quantity)} L {a.fuel_type} (ETA tick {a.expected_arrival_tick})
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Stations Column */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <h3 style={{ borderBottom: "2px solid #30363d", paddingBottom: "0.5rem" }}>
            Destination Stations ({stations.length})
          </h3>
          {stations.map((s) => {
            const isOutage = s.status === "OUTAGE";
            const dieselStock = s.inventory.DIESEL ?? 0;
            const dieselCap = s.capacity.DIESEL ?? 1;
            const dieselPct = Math.round((dieselStock / dieselCap) * 100);
            return (
              <div
                key={s.id}
                className="panel"
                style={{
                  borderLeft: `4px solid ${isOutage ? "#f85149" : "#3fb950"}`,
                  padding: "0.85rem",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <strong>{s.name}</strong>
                  <span className={`status-pill ${isOutage ? "status-offline" : "status-healthy"}`}>
                    {s.status}
                  </span>
                </div>
                <small className="muted">ID: <code>{s.id}</code> &bull; Profile: {s.demand_profile}</small>
                <div style={{ marginTop: "0.5rem", fontSize: "0.8rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span>Diesel Fill:</span>
                    <strong>{dieselPct}% ({liters.format(dieselStock)} L)</strong>
                  </div>
                  <div className="meter meter-risk" style={{ height: "6px", margin: "0.2rem 0 0.4rem 0" }}>
                    <span style={{ width: `${Math.min(100, dieselPct)}%`, background: dieselPct < 25 ? "#f85149" : "#3fb950" }} />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
