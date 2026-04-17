from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas.source import RSSSourceCreateRequest
from app.core.logging import get_logger
from app.db.enums import SourceStatus, SourceType
from app.db.models.source import Source


logger = get_logger(__name__)


def list_sources(db: Session) -> list[Source]:
    stmt = select(Source).order_by(Source.created_at.desc())
    return list(db.scalars(stmt).all())


def create_rss_source(db: Session, payload: RSSSourceCreateRequest) -> Source:
    source = Source(
        type=SourceType.RSS.value,
        name=payload.name.strip(),
        config_json={
            "feed_url": str(payload.feed_url),
            "polling_interval_minutes": payload.polling_interval_minutes,
            "tags": payload.tags,
        },
        status=SourceStatus.ACTIVE.value,
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    logger.info(
        "source.created source_id=%s source_type=%s feed_url=%s",
        source.id,
        source.type,
        source.config_json["feed_url"],
    )
    return source
