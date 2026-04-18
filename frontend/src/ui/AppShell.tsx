import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/sources", label: "Sources" },
  { to: "/documents", label: "Documents" },
  { to: "/reports", label: "Reports" },
  { to: "/workflow-runs", label: "Workflow Runs" },
];

export function AppShell() {
  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="brand-block">
          <p className="eyebrow">Insight Flow</p>
          <h1>Research Workbench</h1>
          <p className="muted-copy">
            A stateful workflow console for ingestion, retrieval, drafting, review, and export.
          </p>
        </div>

        <nav className="nav-list">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? "nav-item is-active" : "nav-item")}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
