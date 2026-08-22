import asyncio
import json

import httpx
import pytest

from app.config import Settings
from app.models import BusinessGoal, GrowthBrief
from app.services import (
    DifyInsightService,
    InsightServiceError,
    MockInsightService,
)


BRIEF = GrowthBrief(
    product="AI Translation Earbuds",
    product_description="Real-time AI translation earbuds for cross-language communication.",
    target_market="United States",
    target_audience="Frequent international business travelers",
    business_goal=BusinessGoal.USER_ACQUISITION,
    additional_context="Entering the US market; test Reddit and TikTok.",
)


class StubAsyncClient:
    def __init__(self, response: httpx.Response):
        self.response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None

    async def post(self, url, json, headers):
        assert url == "https://api.dify.ai/v1/workflows/run"
        assert json["inputs"]["business_goal"] == "User Acquisition"
        assert json["response_mode"] == "blocking"
        assert headers["Authorization"].startswith("Bearer ")
        return self.response


def make_response(payload: dict, status_code: int = 200) -> httpx.Response:
    request = httpx.Request("POST", "https://api.dify.ai/v1/workflows/run")
    return httpx.Response(status_code, json=payload, request=request)


def install_stub(monkeypatch, response: httpx.Response) -> None:
    monkeypatch.setattr(
        "app.services.httpx.AsyncClient",
        lambda **kwargs: StubAsyncClient(response),
    )


def valid_outputs() -> tuple[dict, dict]:
    mock_result = asyncio.run(MockInsightService().generate(BRIEF))
    return (
        mock_result.context.model_dump(mode="json"),
        mock_result.user_insight.model_dump(mode="json"),
    )


def valid_strategy_outputs() -> dict:
    result = asyncio.run(MockInsightService().generate_strategy(BRIEF))
    return {
        "context": result.context.model_dump(mode="json"),
        "user_insight": result.user_insight.model_dump(mode="json"),
        "market_hypothesis": result.market_hypothesis.model_dump(mode="json"),
        "value_proposition": result.value_proposition.model_dump(mode="json"),
    }


def test_dify_service_accepts_object_outputs(monkeypatch) -> None:
    context, user_insight = valid_outputs()
    install_stub(
        monkeypatch,
        make_response(
            {
                "workflow_run_id": "run-object-output",
                "data": {
                    "status": "succeeded",
                    "outputs": {"context": context, "user_insight": user_insight},
                },
            }
        ),
    )

    result = asyncio.run(
        DifyInsightService(Settings(app_mode="dify", dify_api_key="app-test-key")).generate(BRIEF)
    )

    assert result.mode == "dify"
    assert result.request_id == "run-object-output"
    assert result.context.primary_goal == BusinessGoal.USER_ACQUISITION


def test_dify_service_accepts_json_encoded_outputs(monkeypatch) -> None:
    context, user_insight = valid_outputs()
    install_stub(
        monkeypatch,
        make_response(
            {
                "task_id": "task-string-output",
                "data": {
                    "status": "succeeded",
                    "outputs": {
                        "context": json.dumps(context),
                        "user_insight": json.dumps(user_insight),
                    },
                },
            }
        ),
    )

    result = asyncio.run(
        DifyInsightService(Settings(app_mode="dify", dify_api_key="app-test-key")).generate(BRIEF)
    )

    assert result.request_id == "task-string-output"
    assert result.user_insight.confidence == "medium"


def test_dify_service_rejects_failed_workflow(monkeypatch) -> None:
    install_stub(
        monkeypatch,
        make_response(
            {
                "workflow_run_id": "run-failed",
                "data": {
                    "status": "failed",
                    "error": "Provider request failed",
                    "outputs": {},
                },
            }
        ),
    )

    with pytest.raises(InsightServiceError, match="could not complete"):
        asyncio.run(
            DifyInsightService(Settings(app_mode="dify", dify_api_key="app-test-key")).generate(
                BRIEF
            )
        )


def test_dify_service_rejects_missing_job_dimension(monkeypatch) -> None:
    context, user_insight = valid_outputs()
    for job in user_insight["jobs_to_be_done"]:
        job["dimension"] = "functional"
    install_stub(
        monkeypatch,
        make_response(
            {
                "workflow_run_id": "run-invalid-contract",
                "data": {
                    "status": "succeeded",
                    "outputs": {"context": context, "user_insight": user_insight},
                },
            }
        ),
    )

    with pytest.raises(InsightServiceError, match="unexpected response shape"):
        asyncio.run(
            DifyInsightService(Settings(app_mode="dify", dify_api_key="app-test-key")).generate(
                BRIEF
            )
        )


def test_dify_service_accepts_v03_strategy_outputs(monkeypatch) -> None:
    install_stub(
        monkeypatch,
        make_response(
            {
                "workflow_run_id": "run-v03-strategy",
                "data": {
                    "status": "succeeded",
                    "outputs": valid_strategy_outputs(),
                },
            }
        ),
    )

    result = asyncio.run(
        DifyInsightService(
            Settings(app_mode="dify", dify_api_key="app-test-key")
        ).generate_strategy(BRIEF)
    )

    assert result.request_id == "run-v03-strategy"
    assert result.market_hypothesis.confidence == "medium"
    assert result.quality_review.status == "passed"


def test_dify_service_rejects_missing_v03_module(monkeypatch) -> None:
    outputs = valid_strategy_outputs()
    outputs.pop("value_proposition")
    install_stub(
        monkeypatch,
        make_response(
            {
                "workflow_run_id": "run-v03-incomplete",
                "data": {"status": "succeeded", "outputs": outputs},
            }
        ),
    )

    with pytest.raises(InsightServiceError, match="unexpected response shape"):
        asyncio.run(
            DifyInsightService(
                Settings(app_mode="dify", dify_api_key="app-test-key")
            ).generate_strategy(BRIEF)
        )
