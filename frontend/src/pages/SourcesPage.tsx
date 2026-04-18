import { api } from "../lib/api";
import { formatDateTime, humanizeToken } from "../lib/format";
import { useAsyncResource } from "../hooks/useAsyncResource";
import { PageSection } from "../ui/PageSection";
import { ErrorView, LoadingView } from "../ui/StateViews";

export function SourcesPage() {
  const { data, loading, error } = useAsyncResource(api.listSources, []);

  if (loading) return <LoadingView label="Loading sources" />;
  if (error) return <ErrorView message={error} />;

  return (
    <PageSection
      title="Sources"
      description="Configured upstream feeds and ingestion entry points."
    >
      <div className="table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Status</th>
              <th>Last Synced</th>
              <th>Feed URL</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((source) => (
              <tr key={source.id}>
                <td>{source.name}</td>
                <td>{humanizeToken(source.type)}</td>
                <td><span className="pill">{source.status}</span></td>
                <td>{formatDateTime(source.last_synced_at)}</td>
                <td className="mono-cell">{String(source.config_json.feed_url ?? "-")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </PageSection>
  );
}
