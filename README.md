# Insight Flow

Insight Flow is an AI-assisted research workflow system for tracking AI / AI coding updates, turning incoming material into durable research assets, and drafting weekly reports with traceable evidence.

## Repository Layout

- `backend/`
  FastAPI service, SQLAlchemy models, LangGraph workflow, migrations, demo and validation scripts
- `frontend/`
  Vite + React workbench for sources, documents, workflow runs, and reports
- `docs/`
  Product, architecture, planning, and execution records

## MVP Capabilities

- Multi-source ingestion:
  `RSS`, `URL`, `manual_text`
- Processing pipeline:
  fetch, normalize, quality score, dedup, summary, chunking, embeddings
- Weekly workflow:
  cluster build, history retrieval, context pack, draft, reviewer, human edit, export
- Traceability:
  request IDs, workflow events, checkpoint persistence, report trace API

## Prerequisites

- Python `3.11+`
- Node.js `18+`
- PostgreSQL with `pgvector`

Default backend database URL is:

```bash
postgresql+psycopg:///insight_flow
```

If you use a different database, update `backend/.env`.

## Backend Setup

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Vite proxies API calls to `http://127.0.0.1:8000`.

## Demo Script

Run a minimal local MVP demo:

```bash
cd backend
. .venv/bin/activate
python scripts/run_demo_flow.py
```

The script will:

- create demo manual documents
- process them
- run the weekly workflow
- resume after the human-edit checkpoint
- print the exported report path

## Module 06 Validation

Run the final MVP validation suite:

```bash
cd backend
. .venv/bin/activate
python scripts/run_module_06_validation.py
```

This validation covers:

- end-to-end ingest to report
- workflow checkpoint recovery
- reviewer corrective loop
- citation and source trace validation

It also writes a JSON proof artifact under:

```text
backend/runtime_exports/validation/
```

Both demo / validation scripts reset application data before execution and clean
up temporary database records afterwards so older runs do not pollute dedup or
retrieval behavior.

## Pytest

Run the backend integration tests:

```bash
cd backend
. .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

The pytest fixture also resets application data before and after each test so
the integration suite runs against an isolated database state.

## Useful Endpoints

- `GET /health`
- `GET /sources`
- `GET /documents`
- `POST /documents/{document_id}/process`
- `POST /workflows/weekly-report/run`
- `POST /workflows/{workflow_run_id}/resume`
- `GET /reports`
- `GET /reports/{report_id}`
- `GET /reports/{report_id}/markdown`
- `GET /reports/{report_id}/trace`

## Documentation Entry

Start with:

- [docs/README.md](docs/README.md)

Execution records:

- [docs/planning/insight_flow_module_03_execution_log.md](docs/planning/insight_flow_module_03_execution_log.md)
- [docs/planning/insight_flow_module_04_execution_log.md](docs/planning/insight_flow_module_04_execution_log.md)
- [docs/planning/insight_flow_module_05_execution_log.md](docs/planning/insight_flow_module_05_execution_log.md)
- [docs/planning/insight_flow_module_06_execution_log.md](docs/planning/insight_flow_module_06_execution_log.md)
- [docs/planning/insight_flow_strict_self_review.md](docs/planning/insight_flow_strict_self_review.md)
