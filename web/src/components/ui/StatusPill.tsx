import { statusClass } from "../../lib/format";

export default function StatusPill({ status, className = "" }: { status: string; className?: string }) {
  return <span className={`status-pill ${statusClass(status)} ${className}`.trim()}>{status}</span>;
}
