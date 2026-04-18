import { Link } from "react-router-dom";

import { api } from "../lib/api";
import { formatWindow } from "../lib/format";
import { useAsyncResource } from "../hooks/useAsyncResource";
import { PageSection } from "../ui/PageSection";
import { ErrorView, LoadingView } from "../ui/StateViews";

export function ReportsPage() {
  const { data, loading, error } = useAsyncResource(api.listReports, []);

  if (loading) return <LoadingView label="Loading reports" />;
  if (error) return <ErrorView message={error} />;

  return (
    <PageSection
      title="Reports"
      description="Generated weekly reports available for inspection and later editing."
    >
      <div className="card-grid">
        {data?.map((report) => (
          <article key={report.id} className="report-card">
            <p className="eyebrow">{report.status}</p>
            <h3>{report.title}</h3>
            <p className="muted-copy">{formatWindow(report.window_start, report.window_end)}</p>
            <Link to={`/reports/${report.id}`} className="text-link">
              Open detail
            </Link>
          </article>
        ))}
      </div>
    </PageSection>
  );
}
