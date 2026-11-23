import type { Snapshot } from "../../types/api";

const liters = new Intl.NumberFormat("en-BD", { maximumFractionDigits: 0 });

export default function IncomingSupplyView({ snapshot }: { snapshot: Snapshot }) {
  const currentTick = snapshot.instance.tick;
  const arrivals = snapshot.supply_arrivals || [];
  const allocations = snapshot.allocations || [];

  // In-transit allocations
  const inTransit = allocations.filter(
    (a) => a.status === "IN_TRANSIT" || a.status === "PENDING"
  );

  return (
    <div className="incoming-supply-page">
      <section className="overview-heading">
        <div>
          <p className="eyebrow">SUPPLY CHAIN PIPELINE</p>
          <h2>Incoming Supply & In-Transit Shipments</h2>
          <p className="muted">
            Authoritative timeline of scheduled depot supply arrivals and depot-to-station allocations.
          </p>
        </div>
        <span className="status-pill status-simulated">SIMULATED</span>
      </section>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
        {/* Depot Supply Arrivals */}
        <section className="panel section-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">DEPOT RESUPPLY</p>
              <h3>Scheduled Depot Supply Arrivals</h3>
            </div>
            <span className="count-badge">{arrivals.length}</span>
          </div>

          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Arrival ID</th>
                  <th>Depot</th>
                  <th>Fuel</th>
                  <th>Quantity</th>
                  <th>Planned Tick</th>
                  <th>ETA Status</th>
                </tr>
              </thead>
              <tbody>
                {arrivals.map((arr) => {
                  const isDelayed = arr.status === "DELAYED";
                  const arrivalTick = arr.actual_tick ?? arr.planned_tick;
                  const deltaTicks = arrivalTick - currentTick;
                  return (
                    <tr key={arr.id}>
                      <td><code>{arr.id}</code></td>
                      <td>{arr.depot_id}</td>
                      <td>{arr.fuel_type}</td>
                      <td>{liters.format(arr.quantity)} L</td>
                      <td>Tick {arr.planned_tick}</td>
                      <td>
                        <span
                          className={`status-pill ${
                            isDelayed
                              ? "status-offline"
                              : arr.status === "ARRIVED"
                              ? "status-healthy"
                              : "status-degraded"
                          }`}
                        >
                          {arr.status}
                        </span>
                        {deltaTicks > 0 && (
                          <small style={{ display: "block", color: "#8b949e", fontSize: "0.75rem" }}>
                            In {deltaTicks} ticks
                          </small>
                        )}
                      </td>
                    </tr>
                  );
                })}
                {arrivals.length === 0 && (
                  <tr>
                    <td colSpan={6} className="empty-note">No scheduled depot arrivals recorded.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* In-Transit Allocations */}
        <section className="panel section-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">DEPOT TO STATION</p>
              <h3>In-Transit Station Shipments</h3>
            </div>
            <span className="count-badge">{inTransit.length}</span>
          </div>

          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Allocation ID</th>
                  <th>Origin &rarr; Destination</th>
                  <th>Fuel</th>
                  <th>Volume</th>
                  <th>ETA Tick</th>
                  <th>Progress</th>
                </tr>
              </thead>
              <tbody>
                {inTransit.map((alloc) => {
                  const eta = alloc.expected_arrival_tick ?? currentTick + 1;
                  const remaining = eta - currentTick;
                  return (
                    <tr key={alloc.id}>
                      <td><code>#{alloc.id}</code></td>
                      <td>
                        <strong>{alloc.source_depot_id}</strong> &rarr; {alloc.destination_station_id}
                        <small style={{ display: "block", color: "#8b949e" }}>Route: {alloc.route_id}</small>
                      </td>
                      <td>{alloc.fuel_type}</td>
                      <td>{liters.format(alloc.quantity)} L</td>
                      <td>
                        <strong>Tick {eta}</strong>
                        <small style={{ display: "block", color: remaining <= 2 ? "#3fb950" : "#8b949e" }}>
                          {remaining <= 0 ? "Arriving now" : `In ${remaining} ticks`}
                        </small>
                      </td>
                      <td>
                        <span className="status-pill status-healthy">{alloc.status}</span>
                      </td>
                    </tr>
                  );
                })}
                {inTransit.length === 0 && (
                  <tr>
                    <td colSpan={6} className="empty-note">No station allocations currently in transit.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}
