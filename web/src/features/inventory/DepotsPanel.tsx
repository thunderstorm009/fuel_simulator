import type { Fuel, InventoryEntity } from "../../types/api";
import { quantity } from "../../lib/format";
import StatusPill from "../../components/ui/StatusPill";

const fuels: Fuel[] = ["DIESEL", "PETROL", "OCTANE"];

export default function DepotsPanel({ depots }: { depots: InventoryEntity[] }) {
  return (
    <div className="depot-list">
      {depots.map((depot) => (
        <article className="depot-card" key={depot.id}>
          <div className="entity-heading">
            <div><h3>{depot.name}</h3><p>{depot.region_id}</p></div>
            <StatusPill status={depot.status} />
          </div>
          <dl>{fuels.map((fuel) => (
            <div className="depot-fuel" key={fuel}>
              <dt>{fuel}</dt>
              <dd>{quantity(depot.inventory[fuel])} <span>/ {quantity(depot.capacity[fuel])} L</span></dd>
            </div>
          ))}</dl>
        </article>
      ))}
    </div>
  );
}
