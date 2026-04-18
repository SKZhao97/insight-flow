import { useMemo } from "react";
import { useParams } from "react-router-dom";

import { api } from "../lib/api";
import { useAsyncResource } from "../hooks/useAsyncResource";
import { PageSection } from "../ui/PageSection";
import { ErrorView, LoadingView } from "../ui/StateViews";

export function ReportDetailPage() {
  const { reportId } = useParams();
  const loader = useMemo(() => {
    return () => {
      if (!reportId) {
        throw new Error("report id is required");
      }
      return api.getReport(reportId);
    };
  }, [reportId]);

  const { data, loading, error } = useAsyncResource(loader, [loader]);

  if (loading) return <LoadingView label="Loading report detail" />;
  if (error) return <ErrorView message={error} />;
  if (!data) return <ErrorView message="report not found" />;

  return (
    <PageSection
      title={data.title}
      description="Markdown draft and its item-level citation references."
    >
      <div className="report-detail-grid">
        <article className="markdown-card">
          <div className="markdown-toolbar">
            <a href={`/reports/${data.id}/markdown`} className="text-link">
              Download markdown
            </a>
          </div>
          <pre>{data.content_md}</pre>
        </article>
        <aside className="table-card compact">
          <h3>Report Items</h3>
          <ul className="reference-list">
            {data.items.map((item) => (
              <li key={item.id}>
                <span className="mono-cell">{item.item_type}</span>
                <a href={item.source_url} target="_blank" rel="noreferrer">
                  {item.source_url}
                </a>
              </li>
            ))}
          </ul>
        </aside>
      </div>
    </PageSection>
  );
}
