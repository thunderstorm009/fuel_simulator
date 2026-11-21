import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../src/app/App";

const recommendation = {
  id: "123e4567-e89b-12d3-a456-426614174000",
  status: "PROPOSED",
  policy_used: "heuristic",
  fallback_used: false,
  depot_id: "depot-gazipur",
  station_id: "station-mirpur",
  route_id: "route-gazipur-mirpur",
  fuel_type: "DIESEL",
  quantity: 3000,
  idempotency_key: "rec-test-key",
  request_body: {
    source_depot_id: "depot-gazipur",
    destination_station_id: "station-mirpur",
    route_id: "route-gazipur-mirpur",
    fuel_type: "DIESEL",
    quantity: 3000,
    idempotency_key: "rec-test-key",
  },
  explanation_json: {
    drivers: { arrival_tick: 10, demand_multiplier: 1, recent_ratio: 1, delayed_supply: [] },
    constraints_applied: [],
    alternatives: [],
    risk_before: { hours_to_stockout: 6, stockout_probability_24h: 0.8, risk_level: "critical" },
    risk_after: { hours_to_stockout: 12, stockout_probability_24h: 0.3, risk_level: "high" },
    confidence: 0.9,
    data_status: "HEALTHY",
  },
  created_tick: 1,
  expires_tick: 5,
};

function jsonResponse(body: unknown, status = 200) {
  return { ok: status < 400, status, json: async () => body };
}

function stateResponse(dataStatus = "HEALTHY", stale = false) {
  return {
    snapshot: {
      instance: { tick: 1, sim_time: "2026-01-01T00:00:00Z", tick_minutes: 15, status: "PAUSED" },
      regions: [], depots: [], stations: [], routes: [], events: [],
      metrics: { served_demand_liters: 0, unmet_demand_liters: 0, service_level: 1, allocation_liters: 0, allocation_failures: 0 },
    },
    fetched_at: "2026-01-01T00:00:00Z",
    data_age_seconds: 20,
    data_status: dataStatus,
    stale,
    simulated: true,
  };
}

function renderApp() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return {
    client,
    ...render(<QueryClientProvider client={client}><App /></QueryClientProvider>),
  };
}

describe("operator application", () => {
  let recommendations: typeof recommendation[];
  let decisions: unknown[];
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    recommendations = [{ ...recommendation }];
    decisions = [];
    fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/state")) return jsonResponse(stateResponse());
      if (url.endsWith("/api/events")) return jsonResponse({ events: [], incidents: [], data_status: "HEALTHY", data_age_seconds: 0, simulated: true });
      if (url.endsWith("/api/risks")) return jsonResponse({ forecasts: [], data_status: "HEALTHY", data_age_seconds: 0, stale: false, simulated: true });
      if (url.endsWith("/api/depots/risk")) return jsonResponse({ depot_risks: [], count: 0, data_status: "HEALTHY", data_age_seconds: 0, stale: false, simulated: true });
      if (url.endsWith("/api/health")) return jsonResponse({
        status: "DEGRADED",
        components: {
          backend: { status: "HEALTHY", age_seconds: 0 },
          database: { status: "HEALTHY", age_seconds: null },
          simulator: { status: "DEGRADED", age_seconds: 19 },
          predictor: { status: "OFFLINE", age_seconds: null },
          decision_engine: { status: "HEALTHY", age_seconds: 1 },
        },
        last_check_at: "2026-01-01T00:00:00Z",
        latency: { p95_seconds: 0.02, error_rate: 0.01 },
        simulated: true,
      });
      if (url.endsWith("/api/recommendations")) return jsonResponse({ recommendations });
      if (url.endsWith("/api/decisions")) return jsonResponse({ decisions });
      if (url.endsWith("/approve") && init?.method === "POST") {
        recommendations = recommendations.map((item) => ({ ...item, status: "APPROVED" }));
        decisions = [{ id: 1, recommendation_id: recommendation.id, actor: "operator", action: "approve", reason: null, at: "2026-01-01T00:00:00Z", status: "APPROVED", station_id: recommendation.station_id, fuel_type: "DIESEL", quantity: 3000, route_id: recommendation.route_id }];
        return jsonResponse({ status: "APPROVED" });
      }
      return jsonResponse({ detail: "not found" }, 404);
    });
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("keeps dashboard, risk, and recommendation views reachable with simulated and stale labels", async () => {
    fetchMock.mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/state")) return jsonResponse(stateResponse("DEGRADED", true));
      if (url.endsWith("/api/events")) return jsonResponse({ events: [], incidents: [], data_status: "DEGRADED", data_age_seconds: 20, simulated: true });
      if (url.endsWith("/api/risks")) return jsonResponse({ forecasts: [], data_status: "DEGRADED", data_age_seconds: 20, stale: true, simulated: true });
      if (url.endsWith("/api/depots/risk")) return jsonResponse({ depot_risks: [], count: 0, data_status: "DEGRADED", data_age_seconds: 20, stale: true, simulated: true });
      if (url.endsWith("/api/recommendations")) return jsonResponse({ recommendations: [] });
      if (url.endsWith("/api/decisions")) return jsonResponse({ decisions: [] });
      return jsonResponse({ detail: "not found" }, 404);
    });
    renderApp();

    expect(await screen.findByRole("heading", { name: "Supply overview" })).toBeInTheDocument();
    expect(screen.getByText("SIMULATED")).toBeInTheDocument();
    expect(screen.getByText(/marked stale by the simulator/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Stockout risk" }));
    expect(await screen.findByRole("heading", { name: "Stockout risk" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Recommendations" }));
    expect(await screen.findByText("No recommendations have been generated yet.")).toBeInTheDocument();
  });

  it("keeps the operator token in memory and sends it only with approval", async () => {
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
    renderApp();
    await screen.findByRole("heading", { name: "Supply overview" });
    fireEvent.click(screen.getByRole("button", { name: "Recommendations" }));
    await screen.findByRole("heading", { name: "DIESEL · station-mirpur" });
    fireEvent.change(screen.getByLabelText("Operator token"), { target: { value: "session-only-token" } });
    fireEvent.click(screen.getByRole("button", { name: "Approve allocation" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/recommendations/123e4567-e89b-12d3-a456-426614174000/approve"),
      expect.objectContaining({ method: "POST", headers: expect.objectContaining({ "X-Operator-Token": "session-only-token" }) }),
    ));
    expect(confirm).toHaveBeenCalledOnce();
    expect(window.localStorage.getItem("operator-token")).toBeNull();
    expect(await screen.findByText("Recommendation approved.")).toBeInTheDocument();
  });

  it("shows each recommendation ID beside its exact persisted request quantity and key", async () => {
    const primary = {
      ...recommendation,
      id: "1cb05b67-3440-45e5-a6d8-398482678d8c",
      quantity: 6000,
      depot_id: "depot-patiya",
      station_id: "station-coxsbazar",
      route_id: "route-patiya-coxsbazar",
      fuel_type: "DIESEL",
      idempotency_key: "rec-cd2db2c8-5d87-4bc7-876c-d06373049a8a",
      request_body: {
        source_depot_id: "depot-patiya",
        destination_station_id: "station-coxsbazar",
        route_id: "route-patiya-coxsbazar",
        fuel_type: "DIESEL",
        quantity: 6000,
        idempotency_key: "rec-cd2db2c8-5d87-4bc7-876c-d06373049a8a",
      },
    };
    const sibling = {
      ...primary,
      id: "dab6db72-4f94-4b09-a167-d1dea8c1f2fc",
      quantity: 1543.5502472239223,
      idempotency_key: "rec-9a2da662-644a-4256-ab25-41695ffb753e",
      request_body: {
        ...primary.request_body,
        quantity: 1543.5502472239223,
        idempotency_key: "rec-9a2da662-644a-4256-ab25-41695ffb753e",
      },
    };
    recommendations = [primary, sibling];
    renderApp();

    fireEvent.click(await screen.findByRole("button", { name: "Recommendations" }));
    expect(await screen.findByText(primary.id)).toBeInTheDocument();
    expect(screen.getByText(sibling.id)).toBeInTheDocument();
    expect(screen.getByText("6,000 L from depot-patiya · Route route-patiya-coxsbazar")).toBeInTheDocument();
    expect(screen.getByText("1,543.5502472239223 L from depot-patiya · Route route-patiya-coxsbazar")).toBeInTheDocument();
    expect(screen.getByText(primary.idempotency_key)).toBeInTheDocument();
    expect(screen.getByText(sibling.idempotency_key)).toBeInTheDocument();
    const primaryCard = screen.getByText(primary.id).closest("article");
    expect(primaryCard).not.toBeNull();
    fireEvent.click(primaryCard!.querySelector("button.text-button")!);
    expect(primaryCard!.querySelector("pre")?.textContent).toBe(JSON.stringify(primary.request_body, null, 2));
  });

  it("blocks operator decisions when stored summary fields differ from the persisted request", async () => {
    recommendations = [{
      ...recommendation,
      quantity: 6000,
      request_body: { ...recommendation.request_body, quantity: 1543.5502472239223 },
    }];
    renderApp();

    fireEvent.click(await screen.findByRole("button", { name: "Recommendations" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("do not match its allocation request");
    expect(screen.queryByRole("button", { name: "Approve allocation" })).not.toBeInTheDocument();
  });

  it("fails closed without crashing when an API recommendation has a malformed request body", async () => {
    recommendations = [{
      ...recommendation,
      request_body: null as unknown as typeof recommendation.request_body,
    }];
    renderApp();

    fireEvent.click(await screen.findByRole("button", { name: "Recommendations" }));
    expect(await screen.findByText("Allocation request unavailable")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("do not match its allocation request");
    expect(screen.queryByRole("button", { name: "Approve allocation" })).not.toBeInTheDocument();
  });

  it("shows component status and performance on the system health page", async () => {
    renderApp();
    await screen.findByRole("heading", { name: "Supply overview" });
    expect(screen.getByText("System is degraded.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "System health" }));
    expect(await screen.findByRole("heading", { name: "System health" })).toBeInTheDocument();
    expect(screen.getByText("Predictor")).toBeInTheDocument();
    expect(screen.getByText("OFFLINE")).toBeInTheDocument();
    expect(screen.getByText(/5xx error rate: 1.00%/)).toBeInTheDocument();
  });
});
