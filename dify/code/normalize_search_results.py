"""Deterministic Dify Code-node logic for V0.5 search provenance.

The Code node receives one Tavily JSON result per research question. It creates
canonical URLs and source IDs before any LLM sees the source manifest, so later
nodes cannot silently invent a source identity.
"""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_KEYS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "referrer",
}


def _as_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _canonical_url(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parts = urlsplit(value.strip())
    except ValueError:
        return None
    if parts.scheme.lower() != "https" or not parts.hostname:
        return None

    query = [
        (key, item)
        for key, item in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in TRACKING_KEYS
    ]
    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit(("https", parts.netloc.lower(), path, urlencode(query), ""))


def _score(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def main(
    raw_results: list[Any],
    query_ids: list[str],
    researched_at: str,
    failed_query_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Return a Dify-compatible Source Manifest output."""

    failures = list(dict.fromkeys(failed_query_ids or []))
    retained: dict[str, dict[str, Any]] = {}

    for query_index, raw in enumerate(raw_results[:5]):
        query_id = query_ids[query_index] if query_index < len(query_ids) else None
        payload = _as_object(raw)
        results = payload.get("results")
        if not isinstance(results, list):
            if query_id and query_id not in failures:
                failures.append(query_id)
            continue

        accepted_for_query = 0
        for item in results[:5]:
            if not isinstance(item, dict):
                continue
            canonical = _canonical_url(item.get("url"))
            if canonical is None:
                continue
            accepted_for_query += 1
            if canonical in retained:
                if query_id and query_id not in retained[canonical]["query_ids"]:
                    retained[canonical]["query_ids"].append(query_id)
                retained[canonical]["relevance_score"] = max(
                    retained[canonical]["relevance_score"], _score(item.get("score"))
                )
                continue

            domain = urlsplit(canonical).hostname or ""
            retained[canonical] = {
                "source_id": "",
                "title": str(item.get("title") or domain)[:300],
                "url": canonical,
                "domain": domain,
                "publisher": None,
                "published_at": item.get("published_date") or None,
                "retrieved_at": researched_at,
                "query_ids": [query_id] if query_id else [],
                "source_class": "unknown",
                "relevance_score": _score(item.get("score")),
                "freshness": "unknown",
                "snippet": str(item.get("content") or "No search snippet was returned.")[:1200],
                "limitations": ["Source classification and publication date require evaluation."],
            }
        if query_id and accepted_for_query == 0 and query_id not in failures:
            failures.append(query_id)

    sources = list(retained.values())[:10]
    for index, source in enumerate(sources, 1):
        source["source_id"] = f"SRC-{index:03d}"

    if not sources:
        status = "unavailable"
    elif failures:
        status = "partial"
    else:
        status = "complete"

    return {
        "source_manifest": {
            "research_status": status,
            "researched_at": researched_at,
            "sources": sources,
            "failed_query_ids": failures,
        }
    }

