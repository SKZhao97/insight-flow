from __future__ import annotations

"""
Minimal demo flow for Insight Flow MVP.

This script creates a few manual documents, processes them, runs the weekly
workflow until the human-edit checkpoint, resumes it, and prints the resulting
artifact identifiers. The goal is a repeatable demo for local development.
"""

from datetime import datetime, timedelta
from pathlib import Path
import uuid
from uuid import UUID

from fastapi.testclient import TestClient

from app.db.models.document import Document
from app.db.session import SessionLocal
from app.main import app
from app.testing.cleanup import TestDataTracker, reset_application_data


def _create_manual_document(client: TestClient, *, title: str, content: str) -> UUID:
    response = client.post(
        "/documents/manual-text",
        headers={"X-Request-ID": f"demo-{title[:8]}", "X-Trace-ID": f"demo-{title[:8]}"},
        json={"title": title, "content": content},
    )
    response.raise_for_status()
    return UUID(response.json()["id"])


def _process_document(client: TestClient, document_id: UUID) -> None:
    response = client.post(
        f"/documents/{document_id}/process",
        headers={"X-Request-ID": f"process-{document_id}", "X-Trace-ID": f"process-{document_id}"},
    )
    response.raise_for_status()


def _set_document_created_at(document_id: UUID, created_at: datetime) -> None:
    with SessionLocal() as db:
        document = db.get(Document, document_id)
        assert document is not None, f"document {document_id} not found"
        document.created_at = created_at
        document.published_at = created_at
        db.commit()


def main() -> None:
    week_start = datetime(2026, 5, 4, 9, 0, 0).astimezone()
    week_end = week_start + timedelta(days=6, hours=23)
    namespace = f"demo-{uuid.uuid4().hex[:8]}"
    tracker = TestDataTracker()
    reset_application_data(session_factory=SessionLocal, delete_runtime_files=False)

    try:
        with TestClient(app) as client:
            document_ids = [
                _create_manual_document(
                    client,
                    title=f"[{namespace}] OpenAI released a new coding workflow update",
                    content=(
                        f"Namespace marker {namespace}. "
                        "OpenAI introduced a new coding workflow update for agentic development. "
                        "The update focuses on repeatable execution logs, better checkpointing, "
                        "and more reliable developer handoff patterns. Teams described stronger "
                        "handoff quality, more stable report export, and easier recovery after "
                        "interrupted coding sessions. The release also highlighted durable "
                        "workflow state and explicit evidence tracking for AI-assisted delivery."
                    ),
                ),
                _create_manual_document(
                    client,
                    title=f"[{namespace}] Anthropic improved Claude Code collaboration loops",
                    content=(
                        f"Namespace marker {namespace}. "
                        "Anthropic improved Claude Code collaboration loops with stronger review "
                        "patterns, clearer tool traces, and better context recovery. The changes "
                        "were framed around multi-step engineering work, durable reasoning state, "
                        "cleaner debugging logs, and lower friction when resuming interrupted tasks. "
                        "The announcement also emphasized reliable checkpoint recovery."
                    ),
                ),
                _create_manual_document(
                    client,
                    title=f"[{namespace}] Cursor expanded AI coding workflow integrations",
                    content=(
                        f"Namespace marker {namespace}. "
                        "Cursor expanded AI coding workflow integrations and emphasized project "
                        "memory, multi-step execution, and easier report export. The product team "
                        "described stronger project memory, clearer artifact lineage, structured "
                        "report outputs, and smoother transitions between autonomous steps and "
                        "human review checkpoints."
                    ),
                ),
            ]

            for index, document_id in enumerate(document_ids):
                tracker.track_document(document_id)
                _process_document(client, document_id)
                _set_document_created_at(document_id, week_start + timedelta(hours=index))

            run_response = client.post(
                "/workflows/weekly-report/run",
                headers={"X-Request-ID": "demo-run", "X-Trace-ID": "demo-run"},
                json={
                    "week_start": week_start.isoformat(),
                    "week_end": week_end.isoformat(),
                    "input_document_ids": [str(document_id) for document_id in document_ids],
                },
            )
            run_response.raise_for_status()
            run_payload = run_response.json()
            tracker.track_workflow_run(UUID(run_payload["workflow_run_id"]))

            resume_response = client.post(
                f"/workflows/{run_payload['workflow_run_id']}/resume",
                headers={"X-Request-ID": "demo-resume", "X-Trace-ID": "demo-resume"},
            )
            resume_response.raise_for_status()
            resume_payload = resume_response.json()
            tracker.track_report(UUID(resume_payload["report_id"]))
            tracker.track_file(resume_payload["exported_markdown_path"])

            report_trace_response = client.get(
                f"/reports/{resume_payload['report_id']}/trace",
                headers={"X-Request-ID": "demo-trace", "X-Trace-ID": "demo-trace"},
            )
            report_trace_response.raise_for_status()
            trace_payload = report_trace_response.json()

            exported_path = Path(resume_payload["exported_markdown_path"])

        print("demo_workflow_run_id", run_payload["workflow_run_id"])
        print("demo_report_id", resume_payload["report_id"])
        print("demo_final_status", resume_payload["status"])
        print("demo_trace_item_count", len(trace_payload["items"]))
        print("demo_exported_path", exported_path)
        print("demo_export_exists", exported_path.exists())
    finally:
        tracker.cleanup(session_factory=SessionLocal, delete_files=False)



if __name__ == "__main__":
    main()
