import { Link } from "react-router-dom";

import { api } from "../lib/api";
import { formatDateTime } from "../lib/format";
import { useAsyncResource } from "../hooks/useAsyncResource";
import { ErrorView, LoadingView } from "../ui/StateViews";

export function DashboardPage() {
  const sources = useAsyncResource(api.listSources, []);
  const documents = useAsyncResource(api.listDocuments, []);
  const reports = useAsyncResource(api.listReports, []);
  const workflowRuns = useAsyncResource(api.listWorkflowRuns, []);

  if (sources.loading || documents.loading || reports.loading || workflowRuns.loading) {
    return <LoadingView label="Loading dashboard" />;
  }

  if (sources.error || documents.error || reports.error || workflowRuns.error) {
    return <ErrorView message={sources.error || documents.error || reports.error || workflowRuns.error || "unknown error"} />;
  }

  const latestReport = reports.data?.[0];
  const latestWorkflow = workflowRuns.data?.[0];

  return (
    <div className="dashboard-grid">
      <section className="hero-card">
        <p className="eyebrow">Module 05</p>
        <h2>Operational overview for the weekly research workflow.</h2>
        <p className="muted-copy">
          The frontend is now connected to the current backend read paths so you can inspect sources,
          documents, generated reports, and workflow runs from one workbench.
        </p>
      </section>

      <section className="metric-card">
        <span className="metric-label">Sources</span>
        <strong>{sources.data?.length ?? 0}</strong>
      </section>
      <section className="metric-card">
        <span className="metric-label">Documents</span>
        <strong>{documents.data?.length ?? 0}</strong>
      </section>
      <section className="metric-card">
        <span className="metric-label">Reports</span>
        <strong>{reports.data?.length ?? 0}</strong>
      </section>
      <section className="metric-card">
        <span className="metric-label">Workflow Runs</span>
        <strong>{workflowRuns.data?.length ?? 0}</strong>
      </section>

      <section className="summary-card">
        <p className="eyebrow">Latest Report</p>
        {latestReport ? (
          <>
            <h3>{latestReport.title}</h3>
            <p className="muted-copy">{formatDateTime(latestReport.window_start)}</p>
            <Link to={`/reports/${latestReport.id}`} className="text-link">
              Open report
            </Link>
          </>
        ) : (
          <p className="muted-copy">No report generated yet.</p>
        )}
      </section>

      <section className="summary-card">
        <p className="eyebrow">Latest Workflow</p>
        {latestWorkflow ? (
          <>
            <h3>{latestWorkflow.status}</h3>
            <p className="muted-copy">{formatDateTime(latestWorkflow.started_at)}</p>
            <Link to="/workflow-runs" className="text-link">
              Inspect runs
            </Link>
          </>
        ) : (
          <p className="muted-copy">No workflow runs recorded yet.</p>
        )}
      </section>
    </div>
  );
}
