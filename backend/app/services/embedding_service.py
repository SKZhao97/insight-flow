from __future__ import annotations

import hashlib
import math
import re
from typing import Iterable

from app.core.logging import get_logger
from app.db.types import EMBEDDING_DIM


logger = get_logger(__name__)

EMBEDDING_MODEL_NAME = "hash-embedding-v1"


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_+-]+", text.lower())


def embed_text(text: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIM
    tokens = _tokenize(text)
    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        idx_a = int.from_bytes(digest[:4], "big") % EMBEDDING_DIM
        idx_b = int.from_bytes(digest[4:8], "big") % EMBEDDING_DIM
        sign_a = 1.0 if digest[8] % 2 == 0 else -1.0
        sign_b = 1.0 if digest[9] % 2 == 0 else -1.0
        vector[idx_a] += sign_a
        vector[idx_b] += 0.5 * sign_b

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    normalized = [value / norm for value in vector]
    return normalized


def cosine_similarity(vec_a: Iterable[float], vec_b: Iterable[float]) -> float:
    list_a = list(vec_a)
    list_b = list(vec_b)
    if not list_a or not list_b or len(list_a) != len(list_b):
        return 0.0
    return sum(a * b for a, b in zip(list_a, list_b))


def log_embedding_created(target_type: str, target_id, source: str) -> None:
    logger.info(
        "embedding.created target_type=%s target_id=%s embedding_model=%s source=%s",
        target_type,
        target_id,
        EMBEDDING_MODEL_NAME,
        source,
    )
