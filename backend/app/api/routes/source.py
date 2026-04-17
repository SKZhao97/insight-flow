from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.schemas.source import RSSSourceCreateRequest, SourceListItem
from app.core.logging import get_logger
from app.db.session import get_db
from app.services.source_service import create_rss_source, list_sources


logger = get_logger(__name__)
router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceListItem])
def get_sources(db: Session = Depends(get_db)) -> list[SourceListItem]:
    sources = list_sources(db)
    logger.info("sources.list returned_count=%s", len(sources))
    return [SourceListItem.model_validate(source) for source in sources]


@router.post("/rss", response_model=SourceListItem, status_code=status.HTTP_201_CREATED)
def create_rss_source_endpoint(
    payload: RSSSourceCreateRequest,
    db: Session = Depends(get_db),
) -> SourceListItem:
    source = create_rss_source(db, payload)
    return SourceListItem.model_validate(source)
