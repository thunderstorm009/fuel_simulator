import type { Fuel, InventoryEntity } from "../../types/api";
import { quantity } from "../../lib/format";

const fuels: Fuel[] = ["DIESEL", "PETROL", "OCTANE"];

function InventoryCell({ entity, fuel }: { entity: InventoryEntity; fuel: Fuel }) {
  const capacity = entity.capacity[fuel] ?? 0;
  const inventory = entity.inventory[fuel] ?? 0;
  const percent = capacity > 0 ? Math.min(100, Math.max(0, (inventory / capacity) * 100)) : 0;
  const level = percent <= 20 ? "low" : percent <= 40 ? "watch" : "normal";
  return (
    <td>
      <div className="inventory-value"><strong>{quantity(inventory)} L</strong><span>of {quantity(capacity)} L</span></div>
      <div className={`meter meter-${level}`} role="meter" aria-label={`${fuel} inventory`} aria-valuenow={percent} aria-valuemin={0} aria-valuemax={100}>
        <span style={{ width: `${percent}%` }} />
      </div>
    </td>
  );
}

export default function InventoryMatrix({ stations }: { stations: InventoryEntity[] }) {
  return (
    <div className="table-scroll">
      <table>
        <thead><tr><th>Station</th>{fuels.map((fuel) => <th key={fuel}>{fuel}</th>)}</tr></thead>
        <tbody>{stations.map((station) => (
          <tr key={station.id}>
            <th scope="row"><span className="entity-name">{station.name}</span><span className="entity-meta">{station.demand_profile} · {station.region_id}</span></th>
            {fuels.map((fuel) => <InventoryCell key={fuel} entity={station} fuel={fuel} />)}
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}
