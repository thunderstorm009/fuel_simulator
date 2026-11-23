import type {
  Decision,
  DepotRiskResponse,
  EventsResponse,
  Fuel,
  HealthResponse,
  Recommendation,
  RiskResponse,
  StateResponse,
  TrajectoryResponse,
  WhatIfCandidate,
  WhatIfResponse,
  RegionalDemandResponse,
  IncidentsResponse,
  EvaluationResponse,
} from "../types/api";

const apiBase = (import.meta.env.VITE_API_URL || "http://localhost:8101").replace(/\/$/, "");

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new Error(`API returned ${response.status}`);
  }
  return (await response.json()) as T;
}

async function postJson<T>(path: string, token: string, body?: unknown, operatorName?: string): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "X-Operator-Token": token,
      ...(operatorName ? { "X-Operator-Name": operatorName } : {}),
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
export const approveRecommendation = (id: string, token: string, operatorName?: string): Promise<{ status: string }> =>
  postJson(`/api/recommendations/${encodeURIComponent(id)}/approve`, token, undefined, operatorName);
export const rejectRecommendation = (
  id: string,
  token: string,
  reason: string,
  operatorName?: string,
): Promise<{ status: string }> =>
  postJson(`/api/recommendations/${encodeURIComponent(id)}/reject`, token, { reason }, operatorName);
export const fetchDepotRisks = (): Promise<DepotRiskResponse> =>
  getJson<DepotRiskResponse>("/api/depots/risk");
export const fetchWhatIf = async (candidate: WhatIfCandidate): Promise<WhatIfResponse> => {
  const response = await fetch(`${apiBase}/api/whatif`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(candidate),
  });
  if (!response.ok) {
    const detail = (await response.json().catch(() => undefined)) as { detail?: string } | undefined;
    throw new Error(detail?.detail || `API returned ${response.status}`);
  }
  return (await response.json()) as WhatIfResponse;
};
export const fetchRegionalDemand = (): Promise<RegionalDemandResponse> =>
  getJson<RegionalDemandResponse>("/api/regional-demand");
export const fetchIncidentsList = (status: "all" | "open" | "resolved" = "all"): Promise<IncidentsResponse> =>
  getJson<IncidentsResponse>(`/api/incidents?status=${status}`);
export const fetchIncidentSummary = (
  id: number,
): Promise<{ incident_id: number; summary: string; source: string; label: string; simulated: boolean }> =>
  getJson<{ incident_id: number; summary: string; source: string; label: string; simulated: boolean }>(
    `/api/incidents/${id}/summary`,
  );
export const fetchEvaluation = (): Promise<EvaluationResponse> =>
  getJson<EvaluationResponse>("/api/evaluation/summary");

export interface VersionResponse {
  git_sha: string;
  tag: string;
  build_time: string;
  model_version: string;
  policy_version: string;
  active_policy: string;
  simulated: boolean;
}

export const fetchVersion = (): Promise<VersionResponse> =>
  getJson<VersionResponse>("/api/version");
