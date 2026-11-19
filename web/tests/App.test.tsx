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
  request_body: { idempotency_key: "rec-test-key" },
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
});
