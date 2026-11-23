import { useState, useEffect } from "react";

interface TourStep {
  title: string;
  category: string;
  description: string;
  pointer: string;
}

const TOUR_STEPS: TourStep[] = [
  {
    title: "Live Operations & Simulator HUD",
    category: "OBSERVE",
    description:
      "Monitor the simulation clock, current tick, speed ratio, and data freshness. The SIMULATED pill clearly designates non-production telemetry.",
    pointer: "Header HUD (top right) shows active tick, simulation speed, and data age.",
  },
  {
    title: "Predictive Shortage Risk & Monte Carlo",
    category: "PREDICT",
    description:
      "Station risk matrix evaluates 24-hour stockout probability, stochastic P10/P50/P90 inventory runways, and event-aware demand multipliers.",
    pointer: "Navigate to 'Shortage Risk' to inspect station trajectories and probability bands.",
  },
  {
    title: "Human Approval & What-If Counterfactuals",
    category: "DECIDE & APPROVE",
    description:
      "Pure heuristic and LP optimizer generate non-destructive allocation recommendations. Test before-and-after scenarios in the What-If simulator before granting human approval.",
    pointer: "Navigate to 'Recommendations' to review proposals, explanations, and approval controls.",
  },
  {
    title: "Alert Center & Incident Management",
    category: "DETECT & ACT",
    description:
      "Deduplicated detection log tracks demand anomalies, route disruptions, station outages, and circuit-breaker activations with plain-language summaries.",
    pointer: "Navigate to 'Alert Center' to view active and resolved incidents with export capabilities.",
  },
  {
    title: "Resilient Operations & Auto-Rollback",
    category: "RECOVER",
    description:
      "Multi-policy switching with automated fallback to heuristic on violation or timeout. 2.93s database recovery and continuous SSE push invalidation.",
    pointer: "Footer displays active policy and tag. Drill backup/restore with make test-e2e.",
  },
];

export default function GuidedTour() {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);

  useEffect(() => {
    const seen = localStorage.getItem("platform_tour_dismissed");
    if (!seen) {
      setOpen(true);
    }
  }, []);

  const handleDismiss = () => {
    localStorage.setItem("platform_tour_dismissed", "true");
    setOpen(false);
  };

  const handleReset = () => {
    setStep(0);
    setOpen(true);
  };

  if (!open) {
    return (
      <aside aria-label="Guided Tour Toggle" style={{ padding: "0.25rem 1rem", textAlign: "right" }}>
        <button
          className="text-button"
          onClick={handleReset}
          style={{ fontSize: "0.75rem", color: "#58a6ff", cursor: "pointer", textDecoration: "underline" }}
          aria-label="Interactive Judging Tour"
        >
          ✦ Interactive Judging Tour
        </button>
      </aside>
    );
  }

  const current = TOUR_STEPS[step];

  return (
    <section
      role="region"
      aria-label="Judging Demo Walkthrough"
      className="panel"
      style={{
        margin: "0.5rem 1rem",
        padding: "0.85rem 1.25rem",
        border: "1px solid #388bfd",
        backgroundColor: "#0d1b2a",
        borderRadius: "6px",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
            <span className="status-pill status-healthy" style={{ fontSize: "0.65rem", padding: "0.1rem 0.35rem" }}>
              DEMO STEP {step + 1} OF {TOUR_STEPS.length}
            </span>
            <span style={{ fontSize: "0.75rem", color: "#c9d1d9", fontWeight: "bold" }}>
              {current.category}
            </span>
          </div>
          <h2 style={{ margin: "0.2rem 0", fontSize: "1.05rem", color: "#f0f6fc" }}>
            {current.title}
          </h2>
          <p style={{ margin: "0.25rem 0", fontSize: "0.85rem", color: "#c9d1d9", lineHeight: 1.4 }}>
            {current.description}
          </p>
          <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.75rem", color: "#58a6ff", fontStyle: "italic" }}>
            💡 {current.pointer}
          </p>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", minWidth: "120px" }}>
          <div style={{ display: "flex", gap: "0.3rem" }}>
            <button
              className="action-button secondary"
              style={{ padding: "0.2rem 0.5rem", fontSize: "0.75rem" }}
              disabled={step === 0}
              onClick={() => setStep((s) => Math.max(0, s - 1))}
              aria-label="Previous tour step"
            >
              Prev
            </button>
            <button
              className="action-button"
              style={{ padding: "0.2rem 0.5rem", fontSize: "0.75rem" }}
              onClick={() => {
                if (step < TOUR_STEPS.length - 1) {
                  setStep((s) => s + 1);
                } else {
                  handleDismiss();
                }
              }}
              aria-label={step === TOUR_STEPS.length - 1 ? "Finish tour" : "Next tour step"}
            >
              {step === TOUR_STEPS.length - 1 ? "Finish" : "Next"}
            </button>
          </div>
          <button
            className="text-button"
            style={{ fontSize: "0.7rem", color: "#8b949e", textAlign: "center" }}
            onClick={handleDismiss}
            aria-label="Dismiss guided tour"
          >
            Dismiss
          </button>
        </div>
      </div>
    </section>
  );
}
