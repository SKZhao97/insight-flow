from __future__ import annotations

import uuid
from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.db.models.document import Document
from app.db.session import SessionLocal
from app.main import app
from app.testing.cleanup import TestDataTracker, reset_application_data


@dataclass(slots=True)
class TestHarness:
    client: TestClient
    tracker: TestDataTracker
    namespace: str
    scenario_counter: int = 0

    def _headers(self, suffix: str) -> dict[str, str]:
        return {
            "X-Request-ID": f"{self.namespace}-{suffix}",
            "X-Trace-ID": f"{self.namespace}-{suffix}",
        }

    def create_manual_document(self, *, title: str, content: str) -> UUID:
        response = self.client.post(
            "/documents/manual-text",
            headers=self._headers(f"create-{self.scenario_counter}"),
            json={
                "title": f"[{self.namespace}] {title}",
                "content": f"Namespace marker {self.namespace}. {content}",
            },
        )
        response.raise_for_status()
        document_id = UUID(response.json()["id"])
        self.tracker.track_document(document_id)
        self.scenario_counter += 1
        return document_id

    def process_document(self, document_id: UUID) -> dict:
        response = self.client.post(
            f"/documents/{document_id}/process",
            headers=self._headers(f"process-{document_id}"),
        )
        response.raise_for_status()
        return response.json()

    def set_document_time(self, document_id: UUID, created_at: datetime) -> None:
        with SessionLocal() as db:
            document = db.get(Document, document_id)
            assert document is not None
            document.created_at = created_at
            document.published_at = created_at
            db.commit()


@pytest.fixture()
def harness() -> Generator[TestHarness, None, None]:
    namespace = f"pytest-{uuid.uuid4().hex[:8]}"
    tracker = TestDataTracker()
    reset_application_data(session_factory=SessionLocal, delete_runtime_files=True)
    with TestClient(app) as client:
        yield TestHarness(client=client, tracker=tracker, namespace=namespace)
    tracker.cleanup(session_factory=SessionLocal, delete_files=True)
    reset_application_data(session_factory=SessionLocal, delete_runtime_files=True)
