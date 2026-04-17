from __future__ import annotations

import re
import time
from dataclasses import dataclass

import httpx
import trafilatura

from app.core.config import settings
from app.core.logging import get_logger
from app.db.enums import DocumentExtractionMethod


logger = get_logger(__name__)


class DocumentFetchError(ValueError):
    pass


@dataclass(slots=True)
class FetchResult:
    raw_content: str
    cleaned_content: str
    extraction_method: str
    title: str | None = None
    author: str | None = None
    language: str | None = None


def _extract_title_from_html(html: str) -> str | None:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    title = re.sub(r"\s+", " ", match.group(1)).strip()
    return title or None


def _fetch_with_httpx(url: str) -> FetchResult:
    started_at = time.perf_counter()
    headers = {"User-Agent": settings.fetch_user_agent}

    with httpx.Client(
        follow_redirects=True,
        timeout=settings.fetch_timeout_seconds,
        headers=headers,
    ) as client:
        response = client.get(url)
        response.raise_for_status()
        html = response.text

    cleaned_content = trafilatura.extract(
        html,
        url=url,
        include_comments=False,
        include_tables=True,
        favor_precision=True,
    )
    if not cleaned_content:
        raise DocumentFetchError(f"trafilatura extraction returned empty content for {url}")

    elapsed_ms = (time.perf_counter() - started_at) * 1000
    logger.info(
        "document.fetch.success strategy=httpx_trafilatura url=%s elapsed_ms=%.2f content_length=%s",
        url,
        elapsed_ms,
        len(cleaned_content),
    )
    return FetchResult(
        raw_content=html,
        cleaned_content=cleaned_content,
        extraction_method=DocumentExtractionMethod.LOCAL.value,
        title=_extract_title_from_html(html),
    )


def _fetch_with_jina(url: str) -> FetchResult:
    if not settings.jina_reader_base_url:
        raise DocumentFetchError("jina reader fallback is not configured")

    started_at = time.perf_counter()
    base_url = settings.jina_reader_base_url.rstrip("/")
    target_url = f"{base_url}/{url}"
    headers = {"User-Agent": settings.fetch_user_agent}

    with httpx.Client(
        follow_redirects=True,
        timeout=settings.fetch_timeout_seconds,
        headers=headers,
    ) as client:
        response = client.get(target_url)
        response.raise_for_status()
        markdown = response.text.strip()

    if not markdown:
        raise DocumentFetchError(f"jina reader returned empty content for {url}")

    elapsed_ms = (time.perf_counter() - started_at) * 1000
    logger.info(
        "document.fetch.success strategy=jina_reader url=%s elapsed_ms=%.2f content_length=%s",
        url,
        elapsed_ms,
        len(markdown),
    )
    return FetchResult(
        raw_content=markdown,
        cleaned_content=markdown,
        extraction_method=DocumentExtractionMethod.FALLBACK_JINA.value,
    )


def _fetch_with_firecrawl(url: str) -> FetchResult:
    if not settings.firecrawl_base_url or not settings.firecrawl_api_key:
        raise DocumentFetchError("firecrawl fallback is not configured")

    started_at = time.perf_counter()
    headers = {
        "Authorization": f"Bearer {settings.firecrawl_api_key}",
        "Content-Type": "application/json",
        "User-Agent": settings.fetch_user_agent,
    }
    payload = {"url": url, "formats": ["markdown"]}

    with httpx.Client(
        follow_redirects=True,
        timeout=settings.fetch_timeout_seconds,
        headers=headers,
    ) as client:
        response = client.post(settings.firecrawl_base_url, json=payload)
        response.raise_for_status()
        body = response.json()

    markdown = (
        body.get("data", {}).get("markdown")
        or body.get("markdown")
        or body.get("content")
        or ""
    ).strip()
    if not markdown:
        raise DocumentFetchError(f"firecrawl returned empty content for {url}")

    elapsed_ms = (time.perf_counter() - started_at) * 1000
    logger.info(
        "document.fetch.success strategy=firecrawl url=%s elapsed_ms=%.2f content_length=%s",
        url,
        elapsed_ms,
        len(markdown),
    )
    return FetchResult(
        raw_content=markdown,
        cleaned_content=markdown,
        extraction_method=DocumentExtractionMethod.FALLBACK_FIRECRAWL.value,
    )


def fetch_document_content(url: str) -> FetchResult:
    logger.info("document.fetch.started url=%s", url)
    fetchers = (_fetch_with_httpx, _fetch_with_jina, _fetch_with_firecrawl)
    last_error: Exception | None = None

    for fetcher in fetchers:
        try:
            return fetcher(url)
        except Exception as exc:
            last_error = exc
            logger.warning(
                "document.fetch.attempt_failed strategy=%s url=%s error=%s",
                fetcher.__name__,
                url,
                exc,
            )

    raise DocumentFetchError(f"all fetch strategies failed for {url}") from last_error
