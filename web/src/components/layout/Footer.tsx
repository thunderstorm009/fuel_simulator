interface FooterProps {
  lastRefresh?: string;
}

export default function Footer({ lastRefresh }: FooterProps) {
  return (
    <footer className="page-footer" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.75rem 1rem", borderTop: "1px solid #30363d", marginTop: "1rem", fontSize: "0.8rem", color: "#8b949e" }}>
      <div>
        <strong>Fuel Intelligence &amp; Resilience Platform</strong> &bull; Model v1.1.0 &bull; Policy v2.1.0 &bull; Tag: <code>sprint-10</code>
      </div>
      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
        {lastRefresh && <span>Last refresh: {lastRefresh}</span>}
        <span className="status-pill status-simulated" style={{ fontSize: "0.7rem", padding: "0.15rem 0.4rem" }}>
          SIMULATED
        </span>
      </div>
    </footer>
  );
}
