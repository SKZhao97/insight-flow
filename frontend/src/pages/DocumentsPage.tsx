import { api } from "../lib/api";
import { formatDateTime, humanizeToken } from "../lib/format";
import { useAsyncResource } from "../hooks/useAsyncResource";
import { PageSection } from "../ui/PageSection";
import { ErrorView, LoadingView } from "../ui/StateViews";

export function DocumentsPage() {
  const { data, loading, error } = useAsyncResource(api.listDocuments, []);

  if (loading) return <LoadingView label="Loading documents" />;
  if (error) return <ErrorView message={error} />;

  return (
    <PageSection
      title="Documents"
      description="Ingested items and their current normalization, quality, and dedup state."
    >
      <div className="table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Ingest</th>
              <th>Status</th>
              <th>Quality</th>
              <th>Dedup</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((document) => (
              <tr key={document.id}>
                <td>
                  <div className="stacked-cell">
                    <strong>{document.title}</strong>
                    <span className="muted-copy">{document.url ?? document.canonical_url ?? "-"}</span>
                  </div>
                </td>
                <td>{humanizeToken(document.ingest_type)}</td>
                <td><span className="pill">{document.status}</span></td>
                <td><span className="pill subtle">{document.quality_status}</span></td>
                <td><span className="pill subtle">{document.dedup_status}</span></td>
                <td>{formatDateTime(document.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </PageSection>
  );
}
