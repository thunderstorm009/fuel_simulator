export type Fuel = "DIESEL" | "PETROL" | "OCTANE";
export type DataStatus = "HEALTHY" | "DEGRADED" | "OFFLINE";

export interface HealthComponent {
  status: DataStatus;
  age_seconds: number | null;
}

export interface HealthResponse {
  status: DataStatus;
  components: Record<string, HealthComponent>;
  last_check_at: string;
  latency: { p95_seconds: number; error_rate: number };
  simulated: true;
}

export interface InventoryEntity {
  id: string;
  name: string;
  status: string;
  capacity: Partial<Record<Fuel, number>>;
  inventory: Partial<Record<Fuel, number>>;
  region_id?: string;
  demand_profile?: string;
  demand_multiplier?: number;
}

export interface SimulatorEvent {
  id: number;
  type: string;
  start_tick: number;
  end_tick: number;
  status: string;
  parameters: Record<string, unknown>;
}

export interface Incident {
  id: number;
  type: string;
  severity: string;
  detected_at?: string;
}

export interface Route {
  id: string;
  source_depot_id: string;
  destination_station_id: string;
  transit_ticks: number;
  max_shipment: number;
  status: string;
}

export interface Snapshot {
  instance: {
    tick: number;
    sim_time: string;
    tick_minutes: number;
    status: string;
  };
  regions: Array<{ id: string; name: string; demand_factor: number }>;
  depots: InventoryEntity[];
  stations: InventoryEntity[];
  routes: Route[];
  events: SimulatorEvent[];
  metrics: {
    served_demand_liters: number;
    unmet_demand_liters: number;
    service_level: number;
    allocation_liters: number;
    allocation_failures: number;
  };
}

export interface StateResponse {
  snapshot: Snapshot;
  fetched_at: string;
  data_age_seconds: number;
  data_status: DataStatus;
  stale: boolean;
  ticks_per_second?: number;
  snapshot_age_ticks?: number;
  speed_warning?: boolean;
  simulated: true;
}

export interface DepotRisk {
  depot_id: string;
  depot_name?: string;
  fuel_type: Fuel;
  tick: number;
  current_inventory: number;
  scheduled_arrivals: number;
  committed_allocations: number;
  projected_demand: number;
  net_cover_liters: number;
  cover_hours: number;
  is_bottleneck: boolean;
  dispatch_utilization: number;
  evidence: Record<string, unknown>;
}

export interface DepotRiskResponse {
  depot_risks: DepotRisk[];
  count: number;
  fetched_at: string;
  data_age_seconds: number;
  data_status: DataStatus;
  stale: boolean;
  simulated: true;
}

export interface EventsResponse {
  events: SimulatorEvent[];
  incidents: Incident[];
  data_status: DataStatus;
  data_age_seconds: number;
  simulated: true;
}

export interface RiskForecast {
  station_id: string;
  fuel_type: Fuel;
  tick: number;
  hours_to_stockout: number | null;
  p10: number;
  p50: number;
  p90: number;
  stockout_prob_24h: number;
  confidence: number;
  risk_level: "critical" | "high" | "medium" | "ok";
  needs_review: boolean;
  source: string;
  drivers: {
    demand_multiplier: number;
    recent_ratio: number;
    history_ticks: number;
    arrivals: Array<{ tick: number; quantity: number }>;
  };
}

export interface RiskResponse {
  forecasts: RiskForecast[];
  data_status: DataStatus;
  data_age_seconds: number;
  stale: boolean;
  simulated: true;
}

export interface TrajectoryPoint {
  tick_offset: number;
  mean_inventory: number;
  p10_inventory: number;
  p90_inventory: number;
}

export interface TrajectoryResponse extends RiskForecast {
  trajectory: TrajectoryPoint[];
  data_status: DataStatus;
  data_age_seconds: number;
  stale: boolean;
  simulated: true;
}

export interface AllocationRequest {
  source_depot_id: string;
  destination_station_id: string;
  route_id: string;
  fuel_type: Fuel;
  quantity: number;
  idempotency_key: string;
}

export interface Recommendation {
  id: string;
  status: string;
  policy_used: string;
  fallback_used: boolean;
  depot_id: string;
  station_id: string;
  route_id: string;
  fuel_type: Fuel;
  quantity: number;
  idempotency_key: string;
  request_body: AllocationRequest;
  explanation_json: {
    drivers: Record<string, unknown>;
    constraints_applied: Array<Record<string, unknown>>;
    alternatives: Array<Record<string, unknown>>;
    risk_before: Record<string, unknown>;
    risk_after: Record<string, unknown>;
    confidence: number;
    data_status: string;
  };
  created_tick: number;
  expires_tick: number;
  failure_reason?: string | null;
  sim_allocation_id?: number | null;
}

export interface Decision {
  id: number;
  recommendation_id: string;
  actor: string;
  action: "approve" | "reject";
  reason?: string | null;
  at: string;
  status: string;
  station_id: string;
  fuel_type: Fuel;
  quantity: number;
  route_id: string;
}
