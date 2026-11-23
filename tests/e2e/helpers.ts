/**
 * E2E test helpers for simulator admin controls and API state synchronization.
 * Tests use /admin endpoints to set up deterministic conditions; application code never calls /admin.
 */

const rawSim = process.env.PLAYWRIGHT_SIM_URL || process.env.SIM_BASE_URL || "http://localhost:8000";
const SIM_URL = rawSim.replace("simulator:", "localhost:");

const rawApi = process.env.PLAYWRIGHT_API_URL || process.env.API_BASE_URL || "http://localhost:8101";
const API_URL = rawApi.replace("api:", "localhost:");

export async function pauseSimulator(): Promise<void> {
  try {
    await fetch(`${SIM_URL}/admin/pause`, { method: "POST" });
  } catch (err) {
    console.warn("Failed to pause simulator:", err);
  }
}

export async function stepSimulator(steps = 1): Promise<void> {
  for (let i = 0; i < steps; i++) {
    await fetch(`${SIM_URL}/admin/step`, { method: "POST" });
  }
}

export async function injectDemandSpike(
  stationId: string,
  surgeFactor = 2.5,
  ticks = 10,
): Promise<void> {
  const payload = {
    type: "demand_spike",
    start_tick: 0,
    end_tick: ticks,
    station_id: stationId,
    surge_factor: surgeFactor,
  };
  await fetch(`${SIM_URL}/admin/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function injectFault(
  faultType: "unavailable" | "latency" | "stale_data",
  durationSeconds = 15,
): Promise<void> {
  const payload = {
    type: faultType,
    duration_seconds: durationSeconds,
    parameters: faultType === "latency" ? { delay_ms: 3000 } : {},
  };
  await fetch(`${SIM_URL}/admin/faults`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function clearFaults(): Promise<void> {
  try {
    await fetch(`${SIM_URL}/admin/faults/clear`, { method: "POST" });
  } catch (err) {
    console.warn("Failed to clear simulator faults:", err);
  }
}

export async function waitForWorkerIngest(waitMs = 2000): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, waitMs));
}
