export type Source = {
  id: string;
  type: string;
  name: string;
  config_json: Record<string, unknown>;
  status: string;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
};

export type Document = {
  id: string;
  source_id: string | null;
  ingest_type: string;
  url: string | null;
  canonical_url: string | null;
  title: string;
  author: string | null;
  published_at: string | null;
  language: string | null;
  content_hash: string;
  extraction_method: string;
  quality_status: string;
  dedup_status: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type ReportListItem = {
  id: string;
  type: string;
  title: string;
  window_start: string;
  window_end: string;
  status: string;
  version: number;
  generated_by_run_id: string | null;
  created_at: string;
  updated_at: string;
};

export type ReportItemView = {
  id: string;
  summary_id: string;
  document_id: string;
  cluster_id: string | null;
  source_url: string;
  item_type: string;
  position: number;
  created_at: string;
};

export type ReportDetail = ReportListItem & {
  content_md: string;
  items: ReportItemView[];
};

export type WorkflowRun = {
  id: string;
  workflow_type: string;
  status: string;
  week_start: string | null;
  week_end: string | null;
  retry_count: number;
  started_at: string;
  finished_at: string | null;
  created_at: string;
  updated_at: string;
};
