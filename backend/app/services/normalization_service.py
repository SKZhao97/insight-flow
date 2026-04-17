from __future__ import annotations

import hashlib
import re

from app.core.logging import get_logger


logger = get_logger(__name__)


class DocumentNormalizationError(ValueError):
    pass


def normalize_text(content: str) -> str:
    text = content.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    lines = [line.strip() for line in text.split("\n")]
    collapsed = "\n".join(lines)
    collapsed = re.sub(r"\n{3,}", "\n\n", collapsed)
    normalized = collapsed.strip()

    if not normalized:
        raise DocumentNormalizationError("normalized content is empty")

    logger.info(
        "document.normalize.completed input_length=%s output_length=%s",
        len(content),
        len(normalized),
    )
    return normalized


def compute_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
