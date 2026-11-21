export type Page =
  | "overview"
  | "network"
  | "risk"
  | "recommendations"
  | "supply"
  | "alerts"
  | "evaluation"
  | "health";

export default function PageNavigation({ page, onChange }: { page: Page; onChange: (next: Page) => void }) {
  return (
    <nav className="page-navigation" aria-label="Platform views">
      <button className={page === "overview" ? "active" : ""} onClick={() => onChange("overview")}>Overview</button>
      <button className={page === "network" ? "active" : ""} onClick={() => onChange("network")}>Network view</button>
      <button className={page === "risk" ? "active" : ""} onClick={() => onChange("risk")}>Stockout risk</button>
      <button className={page === "recommendations" ? "active" : ""} onClick={() => onChange("recommendations")}>Recommendations</button>
      <button className={page === "supply" ? "active" : ""} onClick={() => onChange("supply")}>Incoming supply</button>
      <button className={page === "alerts" ? "active" : ""} onClick={() => onChange("alerts")}>Alert center</button>
      <button className={page === "evaluation" ? "active" : ""} onClick={() => onChange("evaluation")}>Evaluation</button>
      <button className={page === "health" ? "active" : ""} onClick={() => onChange("health")}>System health</button>
    </nav>
  );
}
