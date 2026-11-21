import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Header from "../components/layout/Header";
import PageNavigation, { type Page } from "../components/layout/PageNavigation";
import DashboardPage from "../features/dashboard/DashboardPage";
import RecommendationsPage from "../features/allocations/RecommendationsPage";
import ShortageRiskPage from "../features/shortage-risk/ShortageRiskPage";
import HealthPage from "../features/system-health/HealthPage";
import { fetchDepotRisks, fetchEvents, fetchHealth, fetchRisks, fetchState, fetchTrajectory } from "../services/api";
import type { Fuel } from "../types/api";
import { localTime } from "../lib/format";

export default function App() {
  const [page, setPage] = useState<Page>("overview");
  const [selected, setSelected] = useState<{ stationId: string; fuel: Fuel } | null>(null);
  const [operatorToken, setOperatorToken] = useState("");
  const stateQuery = useQuery({ queryKey: ["state"], queryFn: fetchState, refetchInterval: 3000 });
  const eventsQuery = useQuery({ queryKey: ["events"], queryFn: fetchEvents, refetchInterval: 3000 });
  const risksQuery = useQuery({ queryKey: ["risks"], queryFn: fetchRisks, refetchInterval: 3000 });
  const healthQuery = useQuery({ queryKey: ["health"], queryFn: fetchHealth, refetchInterval: 5000 });
  const depotRisksQuery = useQuery({ queryKey: ["depotRisks"], queryFn: fetchDepotRisks, refetchInterval: 3000 });
  const trajectoryQuery = useQuery({
    queryKey: ["trajectory", selected?.stationId, selected?.fuel],
    queryFn: () => fetchTrajectory(selected!.stationId, selected!.fuel),
    enabled: selected !== null,
    refetchInterval: 3000,
  });

  const state = stateQuery.data;
  const snapshot = state?.snapshot;
  const events = eventsQuery.data?.events ?? snapshot?.events ?? [];
  const incidents = eventsQuery.data?.incidents ?? [];
  const depotRisks = depotRisksQuery.data?.depot_risks ?? [];
  const apiUnavailable = stateQuery.isError || eventsQuery.isError || (page === "risk" && risksQuery.isError);

  return (
    <main className="page-shell">
      <Header status={state?.data_status} ageSeconds={state?.data_age_seconds} />
      <PageNavigation page={page} onChange={setPage} />
      {apiUnavailable && <div className="notice notice-warning" role="status"><strong>API unreachable.</strong> Showing the last received state while polling continues.</div>}
      {healthQuery.data && healthQuery.data.status !== "HEALTHY" && <div className="notice notice-degraded" role="status"><strong>System is {healthQuery.data.status.toLowerCase()}.</strong> Review the System health view for component status and data age.</div>}
      {state && (state.stale || state.data_status !== "HEALTHY") && (
        <div className="notice notice-degraded" role="status">
          <strong>Data is {state.data_status.toLowerCase()}.</strong> The snapshot is {Math.floor(state.data_age_seconds)} seconds old{state.stale ? " and marked stale by the simulator" : ""}.
        </div>
      )}
      {state?.speed_warning && (
        <div className="notice notice-warning" role="status">
          <strong>High simulation speed detected ({state.ticks_per_second?.toFixed(2)} ticks/sec).</strong> Recommendations may expire before operator approval.
        </div>
      )}
      {page === "health" ? (
        <HealthPage report={healthQuery.data} loading={healthQuery.isLoading} error={healthQuery.isError} />
      ) : !snapshot ? (
        <section className="empty-state panel">
          <p className="eyebrow">LIVE SIMULATOR SNAPSHOT</p>
          <h2>{apiUnavailable ? "API unreachable" : "Waiting for the first snapshot"}</h2>
          <p>{apiUnavailable ? "No saved state is available yet. The dashboard will reconnect automatically." : "The worker is collecting simulator state."}</p>
        </section>
      ) : page === "recommendations" ? (
        <RecommendationsPage token={operatorToken} onTokenChange={setOperatorToken} />
      ) : page === "risk" ? (
        <ShortageRiskPage
          stations={snapshot.stations}
          forecasts={risksQuery.data?.forecasts ?? []}
          trajectory={trajectoryQuery.data}
          selected={selected}
          onSelect={(stationId, fuel) => setSelected({ stationId, fuel })}
          onClose={() => setSelected(null)}
        />
      ) : (
        <DashboardPage snapshot={snapshot} events={events} incidents={incidents} depotRisks={depotRisks} />
      )}
      {state && <footer className="page-footer">All information is simulated. Last successful refresh {localTime(state.fetched_at)}.</footer>}
    </main>
  );
}
