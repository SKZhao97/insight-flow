from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID

from app.db.session import SessionLocal
from app.db.models.workflow import WorkflowEvent
from app.services.workflow_service import get_workflow_run_or_raise


def test_weekly_workflow_end_to_end_and_trace(harness) -> None:
    week_start = datetime(2026, 6, 8, 9, 0, 0).astimezone()
    week_end = week_start + timedelta(days=6, hours=23)

    historical_id = harness.create_manual_document(
        title="Historical AI coding memory note",
        content=(
            "Teams previously emphasized durable workflow memory, stable execution logs, "
            "and explicit evidence recall across weekly research reporting."
        ),
    )
    current_a = harness.create_manual_document(
        title="AI coding tools improve checkpoint recovery",
        content=(
            "Several AI coding tools improved checkpoint recovery, clearer task provenance, "
            "and more stable report export for long-running engineering workflows."
        ),
    )
    current_b = harness.create_manual_document(
        title="Agentic coding products improve evidence traceability",
        content=(
            "Agentic coding products improved evidence traceability, context recall, and "
            "handoff quality between automated steps and human review."
        ),
    )

    for document_id in [historical_id, current_a, current_b]:
        harness.process_document(document_id)

    harness.set_document_time(historical_id, week_start - timedelta(days=21))
    harness.set_document_time(current_a, week_start + timedelta(hours=1))
    harness.set_document_time(current_b, week_start + timedelta(hours=2))

    run_response = harness.client.post(
        "/workflows/weekly-report/run",
        headers=harness._headers("run-s1"),
        json={
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "input_document_ids": [str(current_a), str(current_b)],
        },
    )
    run_response.raise_for_status()
    run_payload = run_response.json()
    harness.tracker.track_workflow_run(UUID(run_payload["workflow_run_id"]))

    assert run_payload["status"] == "waiting_human_edit"
    assert run_payload["human_edit_status"] == "waiting"

    resume_response = harness.client.post(
        f"/workflows/{run_payload['workflow_run_id']}/resume",
        headers=harness._headers("resume-s1"),
    )
    resume_response.raise_for_status()
    resume_payload = resume_response.json()
    harness.tracker.track_report(UUID(resume_payload["report_id"]))
    harness.tracker.track_file(resume_payload["exported_markdown_path"])

    assert resume_payload["status"] == "completed"
    assert Path(resume_payload["exported_markdown_path"]).exists()

    trace_response = harness.client.get(
        f"/reports/{resume_payload['report_id']}/trace",
        headers=harness._headers("trace-s1"),
    )
    trace_response.raise_for_status()
    trace_payload = trace_response.json()

    assert len(trace_payload["items"]) == 2
    for item in trace_payload["items"]:
        assert harness.namespace in item["document_title"]
        assert item["source_url"]


def test_reviewer_loop_updates_retry_count_and_stops_at_human_edit(harness) -> None:
    week_start = datetime(2026, 6, 22, 9, 0, 0).astimezone()
    week_end = week_start + timedelta(days=6, hours=23)

    historical = harness.create_manual_document(
        title="Historical AI coding workflow evidence note",
        content=(
            "Earlier AI coding platform updates emphasized benchmark gains, clearer provenance, "
            "and persistent workflow evidence for engineering review systems."
        ),
    )
    doc_a = harness.create_manual_document(
        title="Revolutionary AI coding update changes everything",
        content=(
            "This revolutionary AI coding update completely solves debugging and彻底颠覆 "
            "engineering collaboration. The release claims total elimination of review work "
            "and once-and-for-all automation of difficult maintenance tasks."
        ),
    )
    doc_b = harness.create_manual_document(
        title="Revolutionary agent update completely solves debugging",
        content=(
            "Analysts called the release revolutionary and said it completely solves debugging "
            "for every engineering team, with total elimination of toil and final transformation."
        ),
    )

    harness.process_document(historical)
    harness.set_document_time(historical, week_start - timedelta(days=14))

    for index, document_id in enumerate([doc_a, doc_b]):
        harness.process_document(document_id)
        harness.set_document_time(document_id, week_start + timedelta(hours=index))

    run_response = harness.client.post(
        "/workflows/weekly-report/run",
        headers=harness._headers("run-s2"),
        json={
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "input_document_ids": [str(doc_a), str(doc_b)],
        },
    )
    run_response.raise_for_status()
    run_payload = run_response.json()
    harness.tracker.track_workflow_run(UUID(run_payload["workflow_run_id"]))
    harness.tracker.track_report(UUID(run_payload["report_id"]))

    with SessionLocal() as db:
        workflow_run = get_workflow_run_or_raise(db, UUID(run_payload["workflow_run_id"]))
        workflow_events = [
            event
            for event in db.query(WorkflowEvent)
            .filter(WorkflowEvent.workflow_run_id == UUID(run_payload["workflow_run_id"]))
            .all()
        ]
        node_counts: dict[str, int] = {}
        for event in workflow_events:
            node_counts[event.node_name] = node_counts.get(event.node_name, 0) + 1

        assert workflow_run.status == "waiting_human_edit"
        assert workflow_run.retry_count == 1
        assert workflow_run.state_json["review_decision"] == "pass"
        assert workflow_run.state_json["human_edit_status"] == "waiting"
        assert node_counts["draft_weekly_report"] == 2
        assert node_counts["review_evidence"] == 2


def test_error_response_keeps_trace_ids(harness) -> None:
    response = harness.client.post(
        "/documents/manual-text",
        headers={"X-Request-ID": f"{harness.namespace}-bad", "X-Trace-ID": f"{harness.namespace}-bad"},
        json={"title": "bad"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["detail"] == "request_validation_failed"
    assert payload["request_id"] == f"{harness.namespace}-bad"
    assert payload["trace_id"] == f"{harness.namespace}-bad"
