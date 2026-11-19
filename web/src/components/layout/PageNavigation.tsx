export type Page = "overview" | "risk" | "recommendations";

export default function PageNavigation({ page, onChange }: { page: Page; onChange: (next: Page) => void }) {
  return (
    <nav className="page-navigation" aria-label="Platform views">
      <button className={page === "overview" ? "active" : ""} onClick={() => onChange("overview")}>Overview</button>
      <button className={page === "risk" ? "active" : ""} onClick={() => onChange("risk")}>Stockout risk</button>
      <button className={page === "recommendations" ? "active" : ""} onClick={() => onChange("recommendations")}>Recommendations</button>
    </nav>
  );
}
