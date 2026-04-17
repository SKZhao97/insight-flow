from enum import StrEnum


class AppEnv(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class SourceType(StrEnum):
    RSS = "rss"
    MANUAL = "manual"


class SourceStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class DocumentIngestType(StrEnum):
    RSS = "rss"
    URL = "url"
    MANUAL_TEXT = "manual_text"


class DocumentExtractionMethod(StrEnum):
    LOCAL = "local"
    FALLBACK_JINA = "fallback_jina"
    FALLBACK_FIRECRAWL = "fallback_firecrawl"


class DocumentStatus(StrEnum):
    INGESTED = "ingested"
    NORMALIZED = "normalized"
    FAILED = "failed"


class DocumentQualityStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED_LOW_VALUE = "rejected_low_value"


class DocumentDedupStatus(StrEnum):
    PENDING = "pending"
    PRIMARY = "primary"
    SUPPORTING = "supporting"
    DUPLICATE = "duplicate"


class DocumentRelationType(StrEnum):
    SUPPORTING_SOURCE = "supporting_source"
    NEAR_DUPLICATE = "near_duplicate"


class SummaryStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"


class ClusterType(StrEnum):
    WEEKLY_EVENT = "weekly_event"


class ClusterStatus(StrEnum):
    ACTIVE = "active"
    DISCARDED = "discarded"


class ReportType(StrEnum):
    WEEKLY = "weekly"


class ReportStatus(StrEnum):
    DRAFT = "draft"
    EDITING = "editing"
    FINALIZED = "finalized"
    EXPORTED = "exported"


class ReportItemType(StrEnum):
    EVENT = "event"
    SUPPORTING_EVIDENCE = "supporting_evidence"


class WorkflowType(StrEnum):
    WEEKLY_REPORT = "weekly_report"


class WorkflowStatus(StrEnum):
    RUNNING = "running"
    WAITING_HUMAN_EDIT = "waiting_human_edit"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_MANUAL_INTERVENTION = "needs_manual_intervention"


class WorkflowEventStatus(StrEnum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
