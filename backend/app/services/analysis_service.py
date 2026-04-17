from __future__ import annotations

import re
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.enums import SummaryStatus
from app.db.models.document import Document
from app.db.models.summary import Summary


logger = get_logger(__name__)

PROMPT_VERSION = "m03_analysis_v1"
MODEL_NAME = "heuristic-local-v1"

KEYWORD_TAG_MAP = {
    "openai": "openai",
    "anthropic": "anthropic",
    "claude": "claude",
    "gpt": "gpt",
    "cursor": "cursor",
    "windsurf": "windsurf",
    "copilot": "copilot",
    "agent": "agent",
    "benchmark": "benchmark",
    "release": "release",
    "model": "model",
    "inference": "inference",
    "coding": "ai_coding",
    "code": "ai_coding",
}

BILINGUAL_TERM_MAP = {
    "agent": "智能体",
    "inference": "推理",
    "benchmark": "基准测试",
    "context window": "上下文窗口",
    "code generation": "代码生成",
    "reasoning": "推理能力",
}


def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?。！？])\s+", text.strip())
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def _extract_key_points(text: str) -> list[str]:
    sentences = _split_sentences(text)
    if sentences:
        return sentences[: min(3, len(sentences))]
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    return paragraphs[: min(3, len(paragraphs))]


def _derive_tags(text: str) -> list[str]:
    lowered = text.lower()
    tags: list[str] = []
    for needle, tag in KEYWORD_TAG_MAP.items():
        if needle in lowered and tag not in tags:
            tags.append(tag)
    return tags[:5] or ["general"]


def _derive_category(tags: list[str]) -> str:
    if "ai_coding" in tags:
        return "ai_coding"
    if any(tag in tags for tag in {"openai", "anthropic", "gpt", "claude", "model"}):
        return "model_updates"
    if "benchmark" in tags:
        return "evaluation"
    return "industry_updates"


def _derive_bilingual_terms(text: str) -> list[dict[str, str]]:
    lowered = text.lower()
    terms: list[dict[str, str]] = []
    for english, chinese in BILINGUAL_TERM_MAP.items():
        if english in lowered:
            terms.append({"en": english, "zh": chinese})
    return terms


def _build_short_summary(text: str) -> str:
    key_points = _extract_key_points(text)
    if key_points:
        summary = " ".join(key_points[:2])
    else:
        summary = text[:280]
    return summary[:400]


def upsert_document_summary(db: Session, document: Document, quality_score: int | None) -> Summary:
    content = (document.cleaned_content or "").strip()
    key_points = _extract_key_points(content)
    tags = _derive_tags(content)
    category = _derive_category(tags)
    bilingual_terms = _derive_bilingual_terms(content)
    short_summary = _build_short_summary(content)

    stmt = (
        select(Summary)
        .where(Summary.document_id == document.id)
        .where(Summary.prompt_version == PROMPT_VERSION)
        .where(Summary.model_name == MODEL_NAME)
    )
    summary = db.scalar(stmt)
    if summary is None:
        summary = Summary(
            document_id=document.id,
            short_summary=short_summary,
            key_points=key_points,
            tags=tags,
            category=category,
            bilingual_terms=bilingual_terms,
            quality_score=quality_score,
            prompt_version=PROMPT_VERSION,
            model_name=MODEL_NAME,
            status=SummaryStatus.COMPLETED.value,
        )
        db.add(summary)
    else:
        summary.short_summary = short_summary
        summary.key_points = key_points
        summary.tags = tags
        summary.category = category
        summary.bilingual_terms = bilingual_terms
        summary.quality_score = quality_score
        summary.status = SummaryStatus.COMPLETED.value

    db.commit()
    db.refresh(summary)

    logger.info(
        "document.summary.upserted document_id=%s summary_id=%s category=%s tag_count=%s",
        document.id,
        summary.id,
        summary.category,
        len(summary.tags),
    )
    return summary
