import { useQuery } from "@tanstack/react-query";
import { fetchEvaluation } from "../../services/api";

const liters = new Intl.NumberFormat("en-BD", { maximumFractionDigits: 0 });

export default function EvaluationPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["evaluation-summary"],
    queryFn: fetchEvaluation,
    refetchInterval: 10000,
  });

  const scenarios = data?.scenarios || [];
  const backtest = data?.backtest?.aggregate || {};

  return (
    <div className="evaluation-page">
      <section className="overview-heading">
        <div>
          <p className="eyebrow">OFFLINE BENCHMARK EVALUATION</p>
          <h2>Policy Performance & Backtest Calibration</h2>
          <p className="muted">
            Independent offline evaluation across 9 stress scenarios comparing Heuristic, Naive, and Do-Nothing policies.
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <span className="status-pill status-simulated">SIMULATED</span>
          <span className="status-pill status-healthy">MODEL v{data?.model_version || "1.1.0"}</span>
          <span className="status-pill status-healthy">POLICY v{data?.policy_version || "2.0.0"}</span>
        </div>
      </section>

      {isLoading && <p className="muted">Loading benchmark evaluation data...</p>}
      {isError && <p className="notice notice-warning">Failed to load offline evaluation results.</p>}

      {/* Demand Forecast Backtest Calibration Summary */}
      <section className="panel section-panel" style={{ marginBottom: "1.5rem" }}>
        <div className="section-heading">
          <div>
            <p className="eyebrow">EMPIRICAL ACCURACY</p>
            <h3>Demand Forecast Backtesting (P10 - P90 Calibration)</h3>
          </div>
          <span className="status-pill status-healthy">Envelope: {data?.calibration_ratio_envelope || "[0.8, 1.25]"}</span>
        </div>

        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Forecast Horizon</th>
                <th>Evaluation Window</th>
                <th>Mean Absolute Percentage Error (MAPE)</th>
                <th>Forecast Bias</th>
                <th>P10–P90 Coverage</th>
                <th>Target Coverage</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(backtest).map(([hKey, metrics]) => (
                <tr key={hKey}>
                  <td><strong>{hKey.toUpperCase()} Horizon</strong></td>
                  <td>{hKey === "1h" ? "4 ticks" : hKey === "6h" ? "24 ticks" : hKey === "12h" ? "48 ticks" : "96 ticks"}</td>
                  <td>
                    <span style={{ color: metrics.mape < 0.05 ? "#3fb950" : "#d29922", fontWeight: 600 }}>
                      {(metrics.mape * 100).toFixed(2)}%
                    </span>
                  </td>
                  <td>{(metrics.bias * 100).toFixed(2)}%</td>
                  <td>
                    <span style={{ fontWeight: 600 }}>{(metrics.interval_coverage * 100).toFixed(1)}%</span>
                  </td>
                  <td style={{ color: "#8b949e" }}>80.0% nominal</td>
                </tr>
              ))}
              {Object.keys(backtest).length === 0 && (
                <tr>
                  <td colSpan={6} className="empty-note">Backtest calibration metrics unavailable.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Scenario Policy Benchmark Table */}
      <section className="panel section-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">DETERMINISTIC BENCHMARKS</p>
            <h3>Scenario Stress Benchmark Results</h3>
          </div>
          <span className="count-badge">{scenarios.length} runs</span>
        </div>

        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Scenario</th>
                <th>Policy</th>
                <th>Run</th>
                <th>Service Level</th>
                <th>Unmet Liters</th>
                <th>Served Liters</th>
                <th>Allocated Liters</th>
                <th>Failures</th>
                <th>Stockouts</th>
              </tr>
            </thead>
            <tbody>
              {scenarios.map((sc, idx) => {
                const isHeuristic = sc.policy === "heuristic";
                const isNone = sc.policy === "none";
                return (
                  <tr
                    key={idx}
                    style={{
                      background: isHeuristic ? "rgba(63, 185, 80, 0.05)" : isNone ? "rgba(248, 81, 73, 0.03)" : "transparent",
                    }}
                  >
                    <td><code>{sc.scenario}</code></td>
                    <td>
                      <span
                        className={`status-pill ${
                          isHeuristic ? "status-healthy" : isNone ? "status-offline" : "status-degraded"
                        }`}
                      >
                        {sc.policy}
                      </span>
                    </td>
                    <td>R{sc.run}</td>
                    <td>
                      <strong style={{ color: sc.service_level >= 0.99 ? "#3fb950" : sc.service_level > 0.8 ? "#d29922" : "#f85149" }}>
                        {(sc.service_level * 100).toFixed(1)}%
                      </strong>
                    </td>
                    <td>{liters.format(sc.unmet_demand_liters)} L</td>
                    <td>{liters.format(sc.served_demand_liters)} L</td>
                    <td>{liters.format(sc.allocation_liters)} L</td>
                    <td>{sc.allocation_failures}</td>
                    <td>
                      <span style={{ color: sc.station_tick_stockouts > 0 ? "#f85149" : "#8b949e" }}>
                        {sc.station_tick_stockouts}
                      </span>
                    </td>
                  </tr>
                );
              })}
              {scenarios.length === 0 && (
                <tr>
                  <td colSpan={9} className="empty-note">No scenario benchmark runs available.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
