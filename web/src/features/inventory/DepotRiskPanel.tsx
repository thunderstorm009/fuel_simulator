import type { DepotRisk } from "../../types/api";
import { quantity } from "../../lib/format";

export default function DepotRiskPanel({ risks }: { risks: DepotRisk[] }) {
  if (risks.length === 0) {
    return (
      <div className="empty-note">
        No active depot supply bottlenecks or forward deficits calculated.
      </div>
    );
  }

  return (
    <div className="depot-risk-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1rem" }}>
      {risks.map((risk) => {
        const isDeficit = risk.net_cover_liters < 0;
        const bottleneckBadgeClass = isDeficit
          ? "status-pill status-pill-critical"
          : risk.is_bottleneck
          ? "status-pill status-pill-high"
          : "status-pill status-pill-ok";
        const bottleneckText = isDeficit
          ? "SUPPLY DEFICIT"
          : risk.is_bottleneck
          ? "BOTTLENECK"
          : "COVER SECURE";

        return (
          <article
            className="depot-card"
            key={`${risk.depot_id}-${risk.fuel_type}`}
            style={{ borderLeft: isDeficit ? "4px solid var(--color-critical, #e53e3e)" : undefined }}
          >
            <div className="entity-heading">
              <div>
                <h3>{risk.depot_name || risk.depot_id}</h3>
                <p>{risk.fuel_type}</p>
              </div>
              <span className={bottleneckBadgeClass}>{bottleneckText}</span>
            </div>
            <dl>
              <div className="depot-fuel">
                <dt>Current stock</dt>
                <dd>{quantity(risk.current_inventory)} L</dd>
              </div>
              <div className="depot-fuel">
                <dt>24h arrivals</dt>
                <dd>{quantity(risk.scheduled_arrivals)} L</dd>
              </div>
              <div className="depot-fuel">
                <dt>Projected 24h demand</dt>
                <dd>{quantity(risk.projected_demand)} L</dd>
              </div>
              <div className="depot-fuel">
                <dt>Net 24h cover</dt>
                <dd style={{ color: isDeficit ? "var(--color-critical, #e53e3e)" : "inherit", fontWeight: 600 }}>
                  {risk.net_cover_liters > 0 ? "+" : ""}
                  {quantity(risk.net_cover_liters)} L
                </dd>
              </div>
              <div className="depot-fuel">
                <dt>Cover runway</dt>
                <dd>{risk.cover_hours >= 999 ? "∞" : `${risk.cover_hours.toFixed(1)}h`}</dd>
              </div>
              <div className="depot-fuel">
                <dt>Dispatch utilization</dt>
                <dd>{(risk.dispatch_utilization * 100).toFixed(0)}%</dd>
              </div>
            </dl>
          </article>
        );
      })}
    </div>
  );
}
