import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import RegionalDemandPanel from "../src/features/demand/RegionalDemandPanel";
import IncomingSupplyView from "../src/features/inventory/IncomingSupplyView";
import AlertCenterPage from "../src/features/alerts/AlertCenterPage";
import NetworkView from "../src/features/network/NetworkView";
import EvaluationPage from "../src/features/evaluation/EvaluationPage";
import type { Snapshot } from "../src/types/api";

function jsonResponse(body: unknown, status = 200) {
  return { ok: status < 400, status, json: async () => body };
}

const mockSnapshot: Snapshot = {
  instance: { tick: 10, sim_time: "2026-01-01T12:00:00Z", tick_minutes: 15, status: "RUNNING" },
  regions: [{ id: "region-dhaka", name: "Dhaka Region", demand_factor: 1.2 }],
  depots: [
    {
      id: "depot-dhaka",
      name: "Dhaka Central Depot",
      status: "OPEN",
      capacity: { DIESEL: 100000, PETROL: 80000, OCTANE: 50000 },
      inventory: { DIESEL: 45000, PETROL: 30000, OCTANE: 20000 },
    },
  ],
  stations: [
    {
      id: "station-mirpur",
      name: "Mirpur Station",
      status: "OPEN",
      demand_profile: "urban_high",
      capacity: { DIESEL: 50000, PETROL: 40000, OCTANE: 30000 },
      inventory: { DIESEL: 15000, PETROL: 20000, OCTANE: 10000 },
    },
  ],
  routes: [
    {
      id: "route-dhaka-mirpur",
      source_depot_id: "depot-dhaka",
      destination_station_id: "station-mirpur",
      transit_ticks: 4,
      max_shipment: 10000,
      status: "AVAILABLE",
    },
  ],
  supply_arrivals: [
    {
      id: "arr-1",
      depot_id: "depot-dhaka",
      fuel_type: "DIESEL",
      quantity: 20000,
      planned_tick: 15,
      actual_tick: 15,
      status: "SCHEDULED",
    },
  ],
  allocations: [
    {
      id: 101,
      idempotency_key: "rec-test-alloc",
      source_depot_id: "depot-dhaka",
      destination_station_id: "station-mirpur",
      route_id: "route-dhaka-mirpur",
      fuel_type: "DIESEL",
      quantity: 6000,
      created_tick: 8,
      departure_tick: 9,
      expected_arrival_tick: 13,
      actual_arrival_tick: null,
      status: "IN_TRANSIT",
      failure_reason: null,
    },
  ],
  events: [],
  metrics: {
    served_demand_liters: 10000,
    unmet_demand_liters: 0,
    service_level: 1.0,
    allocation_liters: 6000,
    allocation_failures: 0,
  },
};

describe("Sprint 9 Operator Views", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("renders RegionalDemandPanel with regional aggregation data", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/api/regional-demand")) {
        return jsonResponse({
          regional_demand: [
            {
              region_id: "region-dhaka",
              region_name: "Dhaka Region",
              demand_factor: 1.2,
              station_count: 2,
              fuels: {
                DIESEL: { demand_liters: 5000, served_liters: 5000, unmet_liters: 0, service_level: 1.0 },
              },
            },
          ],
          window_ticks: 24,
          data_age_seconds: 5,
          data_status: "HEALTHY",
          stale: false,
          simulated: true,
        }) as unknown as Response;
      }
      return jsonResponse({}, 404) as unknown as Response;
    });

    render(
      <QueryClientProvider client={queryClient}>
        <RegionalDemandPanel />
      </QueryClientProvider>
    );

    expect(await screen.findByText("Dhaka Region")).toBeDefined();
    expect(screen.getByText("Multiplier: 1.20×")).toBeDefined();
    expect(screen.getByText("100.0%")).toBeDefined();
  });

  it("renders IncomingSupplyView with scheduled arrivals and in-transit shipments", () => {
    render(<IncomingSupplyView snapshot={mockSnapshot} />);

    expect(screen.getByText("arr-1")).toBeDefined();
    expect(screen.getByText("SCHEDULED")).toBeDefined();
    expect(screen.getByText("#101")).toBeDefined();
    expect(screen.getByText("Tick 13")).toBeDefined();
  });

  it("renders NetworkView with depots, transport corridors, and stations", () => {
    render(<NetworkView snapshot={mockSnapshot} />);

    expect(screen.getByText("Dhaka Central Depot")).toBeDefined();
    expect(screen.getByText("depot-dhaka → station-mirpur")).toBeDefined();
    expect(screen.getByText("AVAILABLE")).toBeDefined();
    expect(screen.getByText("Mirpur Station")).toBeDefined();
  });

  it("renders AlertCenterPage and lists incidents", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/api/incidents")) {
        return jsonResponse({
          incidents: [
            {
              id: 1,
              type: "calibration_drift",
              severity: "warning",
              detected_at: "2026-01-01T12:00:00Z",
              resolved_at: null,
              detail: {
                entity_id: "station-mirpur:DIESEL",
                explanation: "Forecast calibration ratio drifted outside [0.8, 1.25].",
                recovery_condition: "Ratio returns to envelope.",
                evidence: { direction: "SURGE", mean_ratio: 1.35 },
              },
            },
          ],
          count: 1,
          status_filter: "all",
          simulated: true,
        }) as unknown as Response;
      }
      return jsonResponse({}, 404) as unknown as Response;
    });

    render(
      <QueryClientProvider client={queryClient}>
        <AlertCenterPage />
      </QueryClientProvider>
    );

    expect(await screen.findByText("CALIBRATION DRIFT")).toBeDefined();
    expect(screen.getByText(/Forecast calibration ratio drifted outside/)).toBeDefined();
    expect(screen.getByText("Active / Open")).toBeDefined();
  });

  it("renders EvaluationPage with backtest calibration and scenario results", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/api/evaluation/summary")) {
        return jsonResponse({
          evaluation_type: "offline_benchmark",
          model_version: "1.1.0",
          policy_version: "2.0.0",
          scenarios: [
            {
              scenario: "baseline",
              policy: "heuristic",
              run: 1,
              ticks: 20,
              service_level: 1.0,
              unmet_demand_liters: 0,
              served_demand_liters: 12860,
              allocation_liters: 15238,
              allocation_failures: 0,
              station_tick_stockouts: 0,
              elapsed_seconds: 1.2,
            },
          ],
          backtest: {
            model_version: "1.1.0",
            policy_version: "2.0.0",
            aggregate: {
              "1h": { mape: 0.0307, bias: 0.0001, interval_coverage: 0.9149 },
            },
          },
          calibration_ratio_envelope: "[0.8, 1.25]",
          simulated: true,
        }) as unknown as Response;
      }
      return jsonResponse({}, 404) as unknown as Response;
    });

    render(
      <QueryClientProvider client={queryClient}>
        <EvaluationPage />
      </QueryClientProvider>
    );

    expect(await screen.findByText("1H Horizon")).toBeDefined();
    expect(screen.getByText("3.07%")).toBeDefined();
    expect(screen.getByText("91.5%")).toBeDefined();
    expect(screen.getByText("baseline")).toBeDefined();
  });
});
