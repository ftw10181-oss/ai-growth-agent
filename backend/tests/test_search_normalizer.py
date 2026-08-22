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


def test_normalizer_accepts_iteration_wrappers_and_unix_timestamp():
    output = MODULE.main(
        raw_results=[
            {
                "query_id": "RQ-001",
                "search_result": {
                    "results": [
                        {
                            "title": "Official product guide",
                            "url": "https://example.com/guide",
                            "content": "A sufficiently long source excerpt for evaluation.",
                            "score": 0.84,
                        }
                    ]
                },
            }
        ],
        query_ids=[{"question_id": "RQ-001"}],
        researched_at=1787356800,
    )["source_manifest"]

    assert output["research_status"] == "complete"
    assert output["researched_at"] == "2026-08-22T00:00:00Z"
    assert output["sources"][0]["query_ids"] == ["RQ-001"]


def test_normalizer_accepts_dify_json_message_array():
    output = MODULE.main(
        raw_results=[
            {
                "query_id": "RQ-001",
                "search_result": [
                    {
                        "query": "translation earbuds business travelers US",
                        "results": [
                            {
                                "title": "Market report",
                                "url": "https://example.com/market-report",
                                "content": "Evidence returned by Tavily.",
                                "score": 0.77,
                            }
                        ],
                    }
                ],
            }
        ],
        query_ids=[{"question_id": "RQ-001"}],
        researched_at="2026-08-22T00:00:00Z",
    )["source_manifest"]

    assert output["research_status"] == "complete"
    assert output["failed_query_ids"] == []
    assert output["sources"][0]["title"] == "Market report"


def test_normalizer_accepts_stringified_json_message_array():
    output = MODULE.main(
        raw_results=[
            {
                "query_id": "RQ-001",
                "search_result": (
                    '[{"results":[{"title":"Official guide",'
                    '"url":"https://example.com/official",'
                    '"content":"Primary-source excerpt.","score":0.93}]}]'
                ),
            }
        ],
        query_ids=[{"question_id": "RQ-001"}],
        researched_at="2026-08-22T00:00:00Z",
    )["source_manifest"]

    assert output["research_status"] == "complete"
    assert output["sources"][0]["url"] == "https://example.com/official"


def test_normalizer_balances_global_source_budget_across_queries():
    raw_results = []
    query_ids = []
    for query_index in range(1, 6):
        query_id = f"RQ-{query_index:03d}"
        query_ids.append({"question_id": query_id})
        raw_results.append(
            {
                "query_id": query_id,
                "search_result": {
                    "results": [
                        {
                            "title": f"Query {query_index} result {result_index}",
                            "url": (
                                "https://example.com/"
                                f"q{query_index}-result-{result_index}"
                            ),
                            "content": "Search evidence.",
                            "score": 1 - (result_index / 10),
                        }
                        for result_index in range(1, 6)
                    ]
                },
            }
        )

    output = MODULE.main(
        raw_results=raw_results,
        query_ids=query_ids,
        researched_at="2026-08-22T00:00:00Z",
    )["source_manifest"]

    assert len(output["sources"]) == 10
    retained_query_ids = [
        query_id
        for source in output["sources"]
        for query_id in source["query_ids"]
    ]
    assert set(retained_query_ids) == {
        "RQ-001",
        "RQ-002",
        "RQ-003",
        "RQ-004",
        "RQ-005",
    }
    assert all(retained_query_ids.count(query_id) == 2 for query_id in set(retained_query_ids))
