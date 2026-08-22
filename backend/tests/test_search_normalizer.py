import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).parents[2] / "dify" / "code" / "normalize_search_results.py"
)
SPEC = importlib.util.spec_from_file_location("normalize_search_results", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_normalizer_deduplicates_urls_and_preserves_query_provenance():
    output = MODULE.main(
        raw_results=[
            {
                "results": [
                    {
                        "title": "Example report",
                        "url": "https://example.com/report/?utm_source=test",
                        "content": "A relevant source excerpt for the decision.",
                        "score": 0.72,
                    }
                ]
            },
            {
                "results": [
                    {
                        "title": "Same report",
                        "url": "https://EXAMPLE.com/report?gclid=tracking",
                        "content": "The same source returned by another query.",
                        "score": 0.91,
                    }
                ]
            },
        ],
        query_ids=["RQ-001", "RQ-002"],
        researched_at="2026-08-22T00:00:00Z",
    )["source_manifest"]

    assert output["research_status"] == "complete"
    assert len(output["sources"]) == 1
    assert output["sources"][0]["source_id"] == "SRC-001"
    assert output["sources"][0]["url"] == "https://example.com/report"
    assert output["sources"][0]["query_ids"] == ["RQ-001", "RQ-002"]
    assert output["sources"][0]["relevance_score"] == 0.91


def test_normalizer_rejects_non_https_and_marks_partial_search():
    output = MODULE.main(
        raw_results=[
            {"results": [{"title": "Unsafe", "url": "http://example.com"}]},
            {"results": []},
        ],
        query_ids=["RQ-001", "RQ-002"],
        researched_at="2026-08-22T00:00:00Z",
    )["source_manifest"]

    assert output["research_status"] == "unavailable"
    assert output["sources"] == []
    assert output["failed_query_ids"] == ["RQ-001", "RQ-002"]

