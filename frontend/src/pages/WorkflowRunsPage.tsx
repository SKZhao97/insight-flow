import { api } from "../lib/api";
import { formatDateTime, formatWindow, humanizeToken } from "../lib/format";
import { useAsyncResource } from "../hooks/useAsyncResource";
import { PageSection } from "../ui/PageSection";
import { ErrorView, LoadingView } from "../ui/StateViews";

export function WorkflowRunsPage() {
  const { data, loading, error } = useAsyncResource(api.listWorkflowRuns, []);

  if (loading) return <LoadingView label="Loading workflow runs" />;
  if (error) return <ErrorView message={error} />;

  return (
    <PageSection
      title="Workflow Runs"
      description="Operational trace of weekly-report workflow executions."
    >
      <div className="table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Status</th>
              <th>Window</th>
              <th>Retries</th>
              <th>Started</th>
              <th>Finished</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((run) => (
              <tr key={run.id}>
                <td>{humanizeToken(run.workflow_type)}</td>
                <td><span className="pill">{run.status}</span></td>
                <td>{formatWindow(run.week_start, run.week_end)}</td>
                <td>{run.retry_count}</td>
                <td>{formatDateTime(run.started_at)}</td>
                <td>{formatDateTime(run.finished_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </PageSection>
  );
}
