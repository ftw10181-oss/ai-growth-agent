import json
from abc import ABC, abstractmethod
from typing import Any
from uuid import uuid4

import httpx
from pydantic import ValidationError

from .config import Settings
from .models import GrowthBrief, UserInsightResponse


class InsightServiceError(RuntimeError):
    """A safe, client-facing service error."""


class InsightService(ABC):
    @abstractmethod
    async def generate(self, brief: GrowthBrief) -> UserInsightResponse:
        raise NotImplementedError


class MockInsightService(InsightService):
    async def generate(self, brief: GrowthBrief) -> UserInsightResponse:
        context = {
            "brief_summary": (
                f"{brief.product} is being positioned for {brief.target_audience} in "
                f"{brief.target_market}. The immediate growth goal is {brief.business_goal.value}, "
                "so the first analysis should test high-friction situations and the value of faster communication."
            ),
            "product_category": "AI-enabled translation hardware",
            "target_market": brief.target_market,
            "target_audience": brief.target_audience,
            "growth_stage": "new_market_entry",
            "primary_goal": brief.business_goal.value,
            "known_constraints": ["Competitors have an established Amazon presence"],
            "channel_signals": ["Reddit", "TikTok"],
            "assumptions": [
                "The product supports sufficiently fast two-way translation for live conversation.",
                "The initial audience experiences language friction often enough to seek a dedicated device."
            ],
            "ambiguities": [
                "Supported languages, price point, accuracy, privacy model, and offline capability are not specified."
            ]
        }
        user_insight = {
            "target_user": {
                "primary_segment": "US-based international business travelers who regularly join unscripted multilingual conversations",
                "rationale": "Their communication stakes and repeated travel create observable moments where translation friction may justify a dedicated device."
            },
            "jobs_to_be_done": [
                {"job": "When a business conversation shifts languages, I want to understand and respond without interrupting the flow, so I can keep the meeting productive.", "dimension": "functional", "why_it_matters": "Live conversational continuity is the clearest product-value hypothesis."},
                {"job": "When I speak with a new international contact, I want confidence that I understood the nuance, so I can avoid an embarrassing mistake.", "dimension": "emotional", "why_it_matters": "Reduced anxiety may be more motivating than translation speed alone."},
                {"job": "When colleagues see me operating across languages, I want to appear prepared and respectful, so I can build trust quickly.", "dimension": "social", "why_it_matters": "Professional credibility can shape willingness to adopt visible hardware."}
            ],
            "pain_points": [
                {"insight": "Pausing to type into a phone breaks eye contact and conversational rhythm.", "why_it_matters": "Hands-free interaction can be tested against familiar phone-based workarounds."},
                {"insight": "Fast group conversations may move on before a translated response is ready.", "why_it_matters": "Perceived latency is likely a critical activation criterion."},
                {"insight": "Travelers may be unsure whether translations preserve business-specific nuance.", "why_it_matters": "Trust and error recovery should appear in onboarding and proof points."}
            ],
            "purchase_motivations": [
                {"insight": "A near-term trip with several multilingual meetings creates urgency.", "why_it_matters": "Trip planning offers a concrete acquisition moment."},
                {"insight": "Reducing dependence on interpreters or phone handoffs feels operationally efficient.", "why_it_matters": "Convenience may support a productivity-oriented value proposition."},
                {"insight": "A low-risk trial can demonstrate performance in the buyer's own accent and vocabulary.", "why_it_matters": "Experiential proof may overcome abstract feature comparisons."}
            ],
            "adoption_barriers": [
                {"insight": "Concern that a visible device feels awkward or impolite in a meeting.", "why_it_matters": "The product needs a socially acceptable usage ritual."},
                {"insight": "Privacy concerns about recording confidential conversations.", "why_it_matters": "Data handling may block enterprise or executive use."},
                {"insight": "Uncertainty about accuracy across accents, jargon, and noisy rooms.", "why_it_matters": "Generic accuracy claims will not answer situational risk."}
            ],
            "typical_scenarios": [
                {"insight": "An informal conversation begins after a conference session without an interpreter present.", "why_it_matters": "Spontaneous networking highlights speed and portability."},
                {"insight": "A traveler visits a supplier site where several participants prefer the local language.", "why_it_matters": "Multi-party and noisy-environment behavior becomes testable."},
                {"insight": "Two attendees clarify a sensitive contract detail during a meal or taxi ride.", "why_it_matters": "Privacy, nuance, and discreet use converge in a high-stakes moment."}
            ],
            "research_questions": [
                "Tell me about the last time language friction changed the outcome of a business conversation.",
                "What translation workaround did you use, and where did it fail?",
                "What would you need to observe before trusting a wearable translator in a meeting?",
                "In which situations would wearing or sharing earbuds feel unacceptable?"
            ],
            "assumptions_to_validate": context["assumptions"],
            "confidence": "medium"
        }
        return UserInsightResponse(
            request_id=str(uuid4()), mode="mock", context=context, user_insight=user_insight
        )


def _parse_object(value: Any, name: str) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise InsightServiceError(f"Dify returned invalid JSON for '{name}'.") from exc
    return value


class DifyInsightService(InsightService):
    def __init__(self, settings: Settings):
        self.settings = settings

    async def generate(self, brief: GrowthBrief) -> UserInsightResponse:
        url = f"{self.settings.dify_base_url.rstrip('/')}/workflows/run"
        payload = {
            "inputs": brief.model_dump(mode="json"),
            "response_mode": "blocking",
            "user": "portfolio-demo"
        }
        headers = {
            "Authorization": f"Bearer {self.settings.dify_api_key}",
            "Content-Type": "application/json"
        }
        try:
            async with httpx.AsyncClient(timeout=self.settings.dify_timeout_seconds) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise InsightServiceError("The AI workflow timed out. Please try again.") from exc
        except httpx.HTTPStatusError as exc:
            raise InsightServiceError("The AI workflow could not complete the request.") from exc
        except httpx.RequestError as exc:
            raise InsightServiceError("The AI workflow is currently unavailable.") from exc

        try:
            body = response.json()
        except ValueError as exc:
            raise InsightServiceError("The AI workflow returned an invalid response.") from exc

        data = body.get("data")
        if not isinstance(data, dict):
            raise InsightServiceError("The AI workflow returned an unexpected response shape.")
        if data.get("status") != "succeeded":
            raise InsightServiceError("The AI workflow could not complete the request.")

        outputs = data.get("outputs")
        if not isinstance(outputs, dict):
            raise InsightServiceError("The AI workflow returned an unexpected response shape.")
        try:
            return UserInsightResponse(
                request_id=body.get("workflow_run_id") or body.get("task_id") or str(uuid4()),
                mode="dify",
                context=_parse_object(outputs.get("context"), "context"),
                user_insight=_parse_object(outputs.get("user_insight"), "user_insight")
            )
        except ValidationError as exc:
            raise InsightServiceError("The AI workflow returned an unexpected response shape.") from exc


def build_service(settings: Settings) -> InsightService:
    if settings.app_mode == "dify":
        return DifyInsightService(settings)
    return MockInsightService()
