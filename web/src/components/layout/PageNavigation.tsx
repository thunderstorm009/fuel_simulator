export type Page = "overview" | "risk" | "recommendations" | "health";

export default function PageNavigation({ page, onChange }: { page: Page; onChange: (next: Page) => void }) {
  return (
    <nav className="page-navigation" aria-label="Platform views">
      <button className={page === "overview" ? "active" : ""} onClick={() => onChange("overview")}>Overview</button>
      <button className={page === "risk" ? "active" : ""} onClick={() => onChange("risk")}>Stockout risk</button>
      <button className={page === "recommendations" ? "active" : ""} onClick={() => onChange("recommendations")}>Recommendations</button>
      <button className={page === "health" ? "active" : ""} onClick={() => onChange("health")}>System health</button>
    </nav>
  );
}
