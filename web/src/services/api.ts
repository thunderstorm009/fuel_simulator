import type {
  Decision,
  EventsResponse,
  Fuel,
  HealthResponse,
  Recommendation,
  RiskResponse,
  StateResponse,
  TrajectoryResponse,
} from "../types/api";

const apiBase = (import.meta.env.VITE_API_URL || "http://localhost:8101").replace(/\/$/, "");

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new Error(`API returned ${response.status}`);
  }
  return (await response.json()) as T;
}

async function postJson<T>(path: string, token: string, body?: unknown): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "X-Operator-Token": token,
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => undefined) as { detail?: string } | undefined;
    throw new Error(detail?.detail || `API returned ${response.status}`);
  }
  return (await response.json()) as T;
}

export const fetchState = (): Promise<StateResponse> => getJson<StateResponse>("/api/state");
export const fetchEvents = (): Promise<EventsResponse> => getJson<EventsResponse>("/api/events");
export const fetchRisks = (): Promise<RiskResponse> => getJson<RiskResponse>("/api/risks");
export const fetchHealth = (): Promise<HealthResponse> => getJson<HealthResponse>("/api/health");
export const fetchTrajectory = (stationId: string, fuel: Fuel): Promise<TrajectoryResponse> =>
  getJson<TrajectoryResponse>(`/api/risks/${encodeURIComponent(stationId)}/${fuel}/trajectory`);
export const fetchRecommendations = async (): Promise<Recommendation[]> =>
  (await getJson<{ recommendations: Recommendation[] }>("/api/recommendations")).recommendations;
export const fetchDecisions = async (): Promise<Decision[]> =>
  (await getJson<{ decisions: Decision[] }>("/api/decisions")).decisions;
export const approveRecommendation = (id: string, token: string): Promise<{ status: string }> =>
  postJson(`/api/recommendations/${encodeURIComponent(id)}/approve`, token);
export const rejectRecommendation = (id: string, token: string, reason: string): Promise<{ status: string }> =>
  postJson(`/api/recommendations/${encodeURIComponent(id)}/reject`, token, { reason });
