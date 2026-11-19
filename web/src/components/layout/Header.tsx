import type { DataStatus } from "../../types/api";
import StatusPill from "../ui/StatusPill";

export default function Header({ status, ageSeconds }: { status?: DataStatus; ageSeconds?: number }) {
  return (
    <header className="topbar">
      <div className="brand-mark">FS</div>
      <div className="brand-copy">
        <p className="eyebrow">OPERATIONS PLATFORM</p>
        <h1>Fuel Supply Intelligence</h1>
      </div>
      <div className="topbar-meta">
        <span className="simulated">SIMULATED</span>
        {status && <StatusPill status={status} />}
        {ageSeconds !== undefined && <span className="data-age">{Math.max(0, Math.floor(ageSeconds))}s old</span>}
      </div>
    </header>
  );
}
