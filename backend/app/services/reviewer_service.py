from __future__ import annotations

"""Evidence-review services for the weekly report workflow."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.models.document import DocumentChunk
from app.db.models.report import Report, ReportItem
from app.db.models.summary import Summary
from app.db.models.workflow import ContextPack


logger = get_logger(__name__)


@dataclass(slots=True)
class ReviewResult:
    """Structured reviewer output that can drive graph routing decisions."""

    decision: str
    checks: dict


def review_report_evidence(
    db: Session,
    *,
    report: Report,
    context_pack: ContextPack,
) -> ReviewResult:
    """
    Review one drafted report against explicit evidence-oriented checks.

    The reviewer is intentionally rule-based in the MVP. We want decisions that
    are stable, explainable, and easy to inspect before swapping this node to an
    LLM-backed reviewer in a later phase.
    """
    items = list(db.scalars(select(ReportItem).where(ReportItem.report_id == report.id)).all())
    evidence_chunks = context_pack.context_json.get("evidence_chunks", [])
    historical_summaries = context_pack.context_json.get("historical_summaries", [])

    source_urls = [item.source_url for item in items]
    source_diversity = len(set(source_urls))
    numeric_support_present = any(char.isdigit() for char in report.content_md)
    evidence_traceable = len(items) > 0 and all(item.source_url for item in items)
    language_overclaim = any(
        phrase in report.content_md.lower()
        for phrase in ["彻底颠覆", "完全解决", "revolutionary", "completely solves"]
    )

    checks = {
        # The checkbox-style output is deliberate. Downstream routing should be
        # driven by structured evidence checks rather than by free-form critique.
        "numeric_support_present": numeric_support_present or len(evidence_chunks) > 0,
        "source_diversity_sufficient": source_diversity >= 2 or len(historical_summaries) >= 2,
        "evidence_traceable": evidence_traceable,
        "language_overclaim": language_overclaim,
    }

    if not checks["evidence_traceable"] or len(evidence_chunks) == 0:
        decision = "need_more_evidence"
    elif checks["language_overclaim"]:
        decision = "conclusion_too_strong"
    elif not checks["source_diversity_sufficient"]:
        decision = "too_redundant"
    else:
        decision = "pass"

    logger.info(
        "review.completed report_id=%s decision=%s evidence_traceable=%s source_diversity_sufficient=%s language_overclaim=%s",
        report.id,
        decision,
        checks["evidence_traceable"],
        checks["source_diversity_sufficient"],
        checks["language_overclaim"],
    )
    return ReviewResult(decision=decision, checks=checks)
