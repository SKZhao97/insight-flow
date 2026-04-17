from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas.document import DocumentListItem, ManualTextIngestRequest, URLIngestRequest
from app.api.schemas.process import DocumentProcessResult
from app.core.logging import get_logger
from app.db.session import get_db
from app.services.document_service import (
    DocumentConflictError,
    SourceNotFoundError,
    create_manual_text_document,
    create_url_document,
    list_documents,
)
from app.services.fetch_service import DocumentFetchError
from app.services.ingest_processing_service import (
    DocumentNotFoundError,
    fetch_and_normalize_document,
    process_document_pipeline,
)


logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentListItem])
def get_documents(db: Session = Depends(get_db)) -> list[DocumentListItem]:
    documents = list_documents(db)
    logger.info("documents.list returned_count=%s", len(documents))
    return [DocumentListItem.model_validate(document) for document in documents]


@router.post("/url", response_model=DocumentListItem, status_code=status.HTTP_201_CREATED)
def ingest_url_document_endpoint(
    payload: URLIngestRequest,
    db: Session = Depends(get_db),
) -> DocumentListItem:
    try:
        document = create_url_document(db, payload)
    except SourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DocumentConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return DocumentListItem.model_validate(document)


@router.post("/manual-text", response_model=DocumentListItem, status_code=status.HTTP_201_CREATED)
def ingest_manual_text_document_endpoint(
    payload: ManualTextIngestRequest,
    db: Session = Depends(get_db),
) -> DocumentListItem:
    try:
        document = create_manual_text_document(db, payload)
    except SourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return DocumentListItem.model_validate(document)


@router.post("/{document_id}/normalize", response_model=DocumentListItem)
def fetch_and_normalize_document_endpoint(
    document_id: UUID,
    db: Session = Depends(get_db),
) -> DocumentListItem:
    try:
        document = fetch_and_normalize_document(db, document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (DocumentFetchError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return DocumentListItem.model_validate(document)


@router.post("/{document_id}/process", response_model=DocumentProcessResult)
def process_document_pipeline_endpoint(
    document_id: UUID,
    db: Session = Depends(get_db),
) -> DocumentProcessResult:
    try:
        result = process_document_pipeline(db, document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (DocumentFetchError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return DocumentProcessResult(
        document_id=result.document.id,
        status=result.document.status,
        quality_status=result.document.quality_status,
        dedup_status=result.document.dedup_status,
        summary_id=result.summary.id if result.summary else None,
        chunk_count=result.chunk_count,
        summary_embedding_count=result.summary_embedding_count,
        skipped_reason=result.skipped_reason,
    )
