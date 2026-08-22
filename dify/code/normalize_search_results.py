"""Deterministic Dify Code-node logic for V0.5 search provenance.

The Code node receives one Tavily JSON result per research question. It creates
canonical URLs and source IDs before any LLM sees the source manifest, so later
nodes cannot silently invent a source identity.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
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
    if isinstance(value, list):
        # Dify can aggregate a tool's JSON messages into a one-item array inside
        # an Iteration node. Some plugin/runtime combinations expose Tavily's
        # result list directly instead. Accept both representations.
        for item in value:
            candidate = _as_object(item)
            if isinstance(candidate.get("results"), list):
                return candidate
        if value and all(isinstance(item, dict) for item in value):
            if any(isinstance(item.get("url"), str) for item in value):
                return {"results": value}
        return {}
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return _as_object(parsed)
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


def _researched_at(value: Any) -> str:
    """Convert Dify's ``sys.timestamp`` or an ISO value to UTC ISO 8601."""

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat().replace(
            "+00:00", "Z"
        )
    if isinstance(value, str):
        stripped = value.strip()
        try:
            return datetime.fromtimestamp(float(stripped), tz=timezone.utc).isoformat().replace(
                "+00:00", "Z"
            )
        except ValueError:
            if stripped:
                return stripped
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _query_id(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and isinstance(value.get("question_id"), str):
        return value["question_id"]
    return None


def main(
    raw_results: list[Any],
    researched_at: Any,
    query_ids: list[Any] | None = None,
    failed_query_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Return a Dify-compatible Source Manifest output."""

    failures = list(dict.fromkeys(failed_query_ids or []))
    candidate_groups: list[tuple[str | None, list[dict[str, Any]]]] = []
    query_ids = query_ids or []
    retrieval_time = _researched_at(researched_at)

    for query_index, raw in enumerate(raw_results[:5]):
        fallback_query_id = (
            _query_id(query_ids[query_index]) if query_index < len(query_ids) else None
        )
        wrapped = _as_object(raw)
        query_id = _query_id(wrapped.get("query_id")) or fallback_query_id
        payload = (
            _as_object(wrapped.get("search_result"))
            if "search_result" in wrapped
            else wrapped
        )
        results = payload.get("results")
        if not isinstance(results, list):
            if query_id and query_id not in failures:
                failures.append(query_id)
            continue

        candidates_for_query: dict[str, dict[str, Any]] = {}
        for item in results[:5]:
            if not isinstance(item, dict):
                continue
            canonical = _canonical_url(item.get("url"))
            if canonical is None:
                continue
            if canonical in candidates_for_query:
                candidates_for_query[canonical]["relevance_score"] = max(
                    candidates_for_query[canonical]["relevance_score"],
                    _score(item.get("score")),
                )
                continue

            domain = urlsplit(canonical).hostname or ""
            candidates_for_query[canonical] = {
                "canonical_url": canonical,
                "source_id": "",
                "title": str(item.get("title") or domain)[:300],
                "url": canonical,
                "domain": domain,
                "publisher": None,
                "published_at": item.get("published_date") or None,
                "retrieved_at": retrieval_time,
                "query_ids": [query_id] if query_id else [],
                "source_class": "unknown",
                "relevance_score": _score(item.get("score")),
                "freshness": "unknown",
                "snippet": str(item.get("content") or "No search snippet was returned.")[:1200],
                "limitations": ["Source classification and publication date require evaluation."],
            }
        if query_id and not candidates_for_query and query_id not in failures:
            failures.append(query_id)
        candidate_groups.append((query_id, list(candidates_for_query.values())))

    # Retain sources in rank-by-query order instead of letting the first query
    # consume the global cap. With five questions and a ten-source budget this
    # normally preserves the top two results for every question. Later ranks
    # fill gaps when URLs are duplicated or a query returns fewer results.
    retained: dict[str, dict[str, Any]] = {}
    max_rank = max((len(group) for _, group in candidate_groups), default=0)
    for rank in range(max_rank):
        for query_id, group in candidate_groups:
            if rank >= len(group):
                continue
            candidate = group[rank]
            canonical = candidate["canonical_url"]
            if canonical in retained:
                if query_id and query_id not in retained[canonical]["query_ids"]:
                    retained[canonical]["query_ids"].append(query_id)
                retained[canonical]["relevance_score"] = max(
                    retained[canonical]["relevance_score"],
                    candidate["relevance_score"],
                )
                continue
            if len(retained) >= 10:
                continue
            retained[canonical] = candidate

    sources = list(retained.values())
    for index, source in enumerate(sources, 1):
        source.pop("canonical_url", None)
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
            "researched_at": retrieval_time,
            "sources": sources,
            "failed_query_ids": failures,
        }
    }
