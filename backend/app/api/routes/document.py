from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas.document import DocumentListItem, ManualTextIngestRequest, URLIngestRequest
from app.core.logging import get_logger
from app.db.session import get_db
from app.services.document_service import (
    DocumentConflictError,
    SourceNotFoundError,
    create_manual_text_document,
    create_url_document,
    list_documents,
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
