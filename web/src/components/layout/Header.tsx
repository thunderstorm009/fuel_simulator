import type { DataStatus } from "../../types/api";
import StatusPill from "../ui/StatusPill";

export default function Header({
  status,
  ageSeconds,
  alertCount = 0,
  onAlertClick,
}: {
  status?: DataStatus;
  ageSeconds?: number;
  alertCount?: number;
  onAlertClick?: () => void;
}) {
  return (
    <header className="topbar">
      <div className="brand-mark">FS</div>
      <div className="brand-copy">
        <p className="eyebrow">OPERATIONS PLATFORM</p>
        <h1>Fuel Supply Intelligence</h1>
      </div>
      <div className="topbar-meta">
        <span className="simulated">SIMULATED</span>
        {alertCount > 0 && (
          <button
            onClick={onAlertClick}
            className="alert-bell-badge"
            title={`${alertCount} open alerts`}
            style={{
              background: "#da3633",
              color: "#fff",
              border: "none",
              borderRadius: "12px",
              padding: "2px 8px",
              fontSize: "0.8rem",
              fontWeight: 600,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            🔔 {alertCount}
          </button>
        )}
        {status && <StatusPill status={status} />}
        {ageSeconds !== undefined && <span className="data-age">{Math.max(0, Math.floor(ageSeconds))}s old</span>}
      </div>
    </header>
  );
}
