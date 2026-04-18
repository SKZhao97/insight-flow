from __future__ import annotations

"""
Module 06 validation script.

This script executes the final MVP proof points:
1. end-to-end ingest -> report integration
2. workflow checkpoint recovery
3. reviewer loop behavior
4. citation/source trace validation

The script writes a JSON proof artifact under runtime_exports/validation so the
validation result is preserved outside terminal history.
"""

from datetime import datetime, timedelta
import json
from pathlib import Path
import uuid
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models.document import Document
from app.db.models.report import Report, ReportItem
from app.db.models.summary import Summary
from app.db.models.workflow import WorkflowEvent, WorkflowRun
from app.db.session import SessionLocal
from app.main import app
from app.testing.cleanup import TestDataTracker, reset_application_data


VALIDATION_DIR = Path("runtime_exports/validation")


def _create_manual_document(client: TestClient, *, title: str, content: str, request_suffix: str) -> UUID:
    response = client.post(
        "/documents/manual-text",
        headers={
            "X-Request-ID": f"m06-create-{request_suffix}",
            "X-Trace-ID": f"m06-create-{request_suffix}",
        },
        json={"title": title, "content": content},
    )
    response.raise_for_status()
    return UUID(response.json()["id"])


def _process_document(client: TestClient, document_id: UUID, request_suffix: str) -> dict:
    response = client.post(
        f"/documents/{document_id}/process",
        headers={
            "X-Request-ID": f"m06-process-{request_suffix}",
            "X-Trace-ID": f"m06-process-{request_suffix}",
        },
    )
    response.raise_for_status()
    return response.json()


def _run_workflow(client: TestClient, *, week_start: datetime, week_end: datetime, document_ids: list[UUID], suffix: str) -> dict:
    response = client.post(
        "/workflows/weekly-report/run",
        headers={"X-Request-ID": f"m06-run-{suffix}", "X-Trace-ID": f"m06-run-{suffix}"},
        json={
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "input_document_ids": [str(document_id) for document_id in document_ids],
        },
    )
    response.raise_for_status()
    return response.json()


def _resume_workflow(client: TestClient, workflow_run_id: str, suffix: str) -> dict:
    response = client.post(
        f"/workflows/{workflow_run_id}/resume",
        headers={"X-Request-ID": f"m06-resume-{suffix}", "X-Trace-ID": f"m06-resume-{suffix}"},
    )
    response.raise_for_status()
    return response.json()


def _validate_citation_chain(report_id: UUID) -> dict:
    with SessionLocal() as db:
        report = db.get(Report, report_id)
        assert report is not None, f"report {report_id} not found"
        items = list(db.scalars(select(ReportItem).where(ReportItem.report_id == report_id)).all())
        assert items, "report has no report_items"

        mismatches: list[str] = []
        for item in items:
            summary = db.get(Summary, item.summary_id)
            assert summary is not None, f"summary {item.summary_id} missing"
            if summary.document_id != item.document_id:
                mismatches.append(str(item.id))
            assert item.source_url, f"report_item {item.id} missing source_url"

        return {
            "report_id": str(report.id),
            "report_item_count": len(items),
            "all_source_urls_present": all(item.source_url for item in items),
            "mismatch_count": len(mismatches),
            "mismatch_item_ids": mismatches,
        }


def _load_workflow_run_state(workflow_run_id: UUID) -> dict:
    with SessionLocal() as db:
        workflow_run = db.get(WorkflowRun, workflow_run_id)
        assert workflow_run is not None, f"workflow_run {workflow_run_id} not found"
        return {
            "workflow_run_id": str(workflow_run.id),
            "status": workflow_run.status,
            "retry_count": workflow_run.retry_count,
            "state_json": workflow_run.state_json,
        }


def _load_workflow_event_counts(workflow_run_id: UUID) -> dict[str, int]:
    with SessionLocal() as db:
        events = list(
            db.scalars(
                select(WorkflowEvent).where(WorkflowEvent.workflow_run_id == workflow_run_id)
            ).all()
        )
        counts: dict[str, int] = {}
        for event in events:
            counts[event.node_name] = counts.get(event.node_name, 0) + 1
        return counts


def _set_document_created_at(document_id: UUID, created_at: datetime) -> None:
    with SessionLocal() as db:
        document = db.get(Document, document_id)
        assert document is not None, f"document {document_id} not found"
        document.created_at = created_at
        document.published_at = created_at
        db.commit()


def _write_proof_artifact(results: dict) -> Path:
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    file_path = VALIDATION_DIR / f"module_06_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    file_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return file_path


def main() -> None:
    scenario_1_week_start = datetime(2026, 5, 11, 9, 0, 0).astimezone()
    scenario_1_week_end = scenario_1_week_start + timedelta(days=6, hours=23)
    scenario_2_week_start = datetime(2026, 5, 25, 9, 0, 0).astimezone()
    scenario_2_week_end = scenario_2_week_start + timedelta(days=6, hours=23)
    namespace = f"validation-{uuid.uuid4().hex[:8]}"
    tracker = TestDataTracker()
    reset_application_data(session_factory=SessionLocal, delete_runtime_files=False)

    try:
        with TestClient(app) as client:
            # Scenario 1: regular end-to-end workflow with a historical document.
            historical_id = _create_manual_document(
                client,
                title=f"[{namespace}] Historical note about AI coding workflow memory",
                content=(
                    f"Namespace marker {namespace}. "
                    "Last month, AI coding platforms started emphasizing durable workflow memory, "
                    "execution logs, and report traceability. Product teams described longer task "
                    "continuity, better recovery after interruptions, and improved evidence reuse "
                    "across weekly reporting flows."
                ),
                request_suffix="historical",
            )
            current_ids = [
                _create_manual_document(
                    client,
                    title=f"[{namespace}] AI coding tools improve workflow traceability",
                    content=(
                        f"Namespace marker {namespace}. "
                        "Several AI coding tools improved workflow traceability, structured logs, "
                        "and checkpoint recovery for longer engineering tasks. The updates focused "
                        "on persistent execution records, clearer task-level provenance, better "
                        "handoffs between automated steps and human review, and stronger report "
                        "export paths for weekly research workflows."
                    ),
                    request_suffix="current-a",
                ),
                _create_manual_document(
                    client,
                    title=f"[{namespace}] Agentic coding products focus on report export",
                    content=(
                        f"Namespace marker {namespace}. "
                        "Agentic coding products increasingly focus on structured report export, "
                        "explicit evidence packs, and durable workflow review checkpoints. Vendor "
                        "messaging emphasized artifact lineage, repeatable workflow state, and "
                        "reliable context recall for long-running engineering research tasks."
                    ),
                    request_suffix="current-b",
                ),
            ]
            all_ids = [historical_id, *current_ids]
            for document_id in all_ids:
                tracker.track_document(document_id)
            for index, document_id in enumerate(all_ids):
                _process_document(client, document_id, f"scenario-1-{index}")
            _set_document_created_at(historical_id, scenario_1_week_start - timedelta(days=21))
            for index, document_id in enumerate(current_ids):
                _set_document_created_at(document_id, scenario_1_week_start + timedelta(hours=index))

            run_payload = _run_workflow(
                client,
                week_start=scenario_1_week_start,
                week_end=scenario_1_week_end,
                document_ids=current_ids,
                suffix="scenario-1",
            )
            tracker.track_workflow_run(UUID(run_payload["workflow_run_id"]))
            checkpoint_state = _load_workflow_run_state(UUID(run_payload["workflow_run_id"]))
            resume_payload = _resume_workflow(client, run_payload["workflow_run_id"], "scenario-1")
            tracker.track_report(UUID(resume_payload["report_id"]))
            tracker.track_file(resume_payload["exported_markdown_path"])
            trace_response = client.get(
                f"/reports/{resume_payload['report_id']}/trace",
                headers={"X-Request-ID": "m06-trace-scenario-1", "X-Trace-ID": "m06-trace-scenario-1"},
            )
            trace_response.raise_for_status()
            citation_validation = _validate_citation_chain(UUID(resume_payload["report_id"]))

            # Scenario 2: reviewer loop with intentionally overclaiming language.
            reviewer_doc_ids = [
                _create_manual_document(
                    client,
                    title=f"[{namespace}] Revolutionary AI coding update changes everything",
                    content=(
                        f"Namespace marker {namespace}. "
                        "This revolutionary AI coding update completely solves debugging and "
                        "彻底颠覆 engineering collaboration according to early observers. The "
                        "announcement repeatedly called the release revolutionary, final, and "
                        "transformational for every engineering team. It also claimed complete "
                        "automation of difficult maintenance tasks and total elimination of review work."
                    ),
                    request_suffix="reviewer-a",
                ),
                _create_manual_document(
                    client,
                    title=f"[{namespace}] Revolutionary agent update completely solves debugging",
                    content=(
                        f"Namespace marker {namespace}. "
                        "Analysts called the update revolutionary and claimed it completely solves "
                        "debugging for every engineering team. Marketing material used absolute "
                        "language, promised total elimination of debugging toil, and described a "
                        "once-and-for-all breakthrough for software delivery organizations."
                    ),
                    request_suffix="reviewer-b",
                ),
            ]
            for document_id in reviewer_doc_ids:
                tracker.track_document(document_id)
            for index, document_id in enumerate(reviewer_doc_ids):
                _process_document(client, document_id, f"scenario-2-{index}")
                _set_document_created_at(document_id, scenario_2_week_start + timedelta(hours=index))

            reviewer_run_payload = _run_workflow(
                client,
                week_start=scenario_2_week_start,
                week_end=scenario_2_week_end,
                document_ids=reviewer_doc_ids,
                suffix="scenario-2",
            )
            tracker.track_workflow_run(UUID(reviewer_run_payload["workflow_run_id"]))
            reviewer_state = _load_workflow_run_state(UUID(reviewer_run_payload["workflow_run_id"]))
            reviewer_event_counts = _load_workflow_event_counts(UUID(reviewer_run_payload["workflow_run_id"]))

        assert checkpoint_state["status"] == "waiting_human_edit", checkpoint_state
        assert checkpoint_state["state_json"].get("human_edit_status") == "waiting", checkpoint_state
        assert resume_payload["status"] == "completed", resume_payload
        assert Path(resume_payload["exported_markdown_path"]).exists(), resume_payload
        assert citation_validation["report_item_count"] > 0, citation_validation
        assert citation_validation["mismatch_count"] == 0, citation_validation
        assert reviewer_state["status"] == "waiting_human_edit", reviewer_state
        assert reviewer_state["state_json"].get("review_decision") == "pass", reviewer_state
        assert reviewer_state["state_json"].get("retry_count") == 1, reviewer_state
        assert reviewer_event_counts.get("draft_weekly_report") == 2, reviewer_event_counts
        assert reviewer_event_counts.get("review_evidence") == 2, reviewer_event_counts

        results = {
            "executed_at": datetime.now().astimezone().isoformat(),
            "scenario_1": {
                "run_payload": run_payload,
                "checkpoint_state": checkpoint_state,
                "resume_payload": resume_payload,
                "trace_api_payload": trace_response.json(),
                "citation_validation": citation_validation,
                "export_file_exists": Path(resume_payload["exported_markdown_path"]).exists(),
            },
            "scenario_2": {
                "run_payload": reviewer_run_payload,
                "workflow_run_state": reviewer_state,
                "workflow_event_counts": reviewer_event_counts,
                "expected_reviewer_loop": {
                    "final_status": reviewer_state["status"],
                    "review_decision": reviewer_state["state_json"].get("review_decision"),
                    "retry_count": reviewer_state["state_json"].get("retry_count"),
                    "human_edit_status": reviewer_state["state_json"].get("human_edit_status"),
                },
            },
        }

        proof_path = _write_proof_artifact(results)
        print("module_06_validation_proof", proof_path)
        print("scenario_1_final_status", results["scenario_1"]["resume_payload"]["status"])
        print("scenario_1_export_exists", results["scenario_1"]["export_file_exists"])
        print("scenario_1_trace_items", len(results["scenario_1"]["trace_api_payload"]["items"]))
        print("scenario_2_review_decision", results["scenario_2"]["expected_reviewer_loop"]["review_decision"])
        print("scenario_2_retry_count", results["scenario_2"]["expected_reviewer_loop"]["retry_count"])
    finally:
        tracker.cleanup(session_factory=SessionLocal, delete_files=True)


if __name__ == "__main__":
    main()
