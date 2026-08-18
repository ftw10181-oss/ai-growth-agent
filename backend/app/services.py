import json
from abc import ABC, abstractmethod
from typing import Any, Optional
from uuid import uuid4

import httpx
from pydantic import ValidationError

from .config import Settings
from .models import GrowthBrief, UserInsight, UserInsightResponse
from .quality import evaluate_quality


class InsightServiceError(RuntimeError):
    """A safe, client-facing service error."""


class InsightService(ABC):
    @abstractmethod
    async def generate(self, brief: GrowthBrief) -> UserInsightResponse:
        raise NotImplementedError


class MockInsightService(InsightService):
    async def generate(self, brief: GrowthBrief) -> UserInsightResponse:
        contextual_evidence = {
            "basis": "contextual_inference",
            "confidence": "medium",
            "validation_status": "needs_validation",
        }
        behavioral_evidence = {
            "basis": "behavioral_hypothesis",
            "confidence": "low",
            "validation_status": "needs_validation",
        }

        def insight_item(
            insight: str,
            why_it_matters: str,
            relevance: str = "primary",
            evidence: Optional[dict] = None,
        ) -> dict:
            return {
                "insight": insight,
                "why_it_matters": why_it_matters,
                "decision_relevance": relevance,
                "evidence": evidence or contextual_evidence,
            }

        def job_item(
            job: str,
            dimension: str,
            why_it_matters: str,
            relevance: str = "primary",
            evidence: Optional[dict] = None,
        ) -> dict:
            return {
                "job": job,
                "dimension": dimension,
                "why_it_matters": why_it_matters,
                "decision_relevance": relevance,
                "evidence": evidence or contextual_evidence,
            }

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
                job_item("When a business conversation shifts languages, I want to understand and respond without interrupting the flow, so I can keep the meeting productive.", "functional", "Live conversational continuity is the clearest product-value hypothesis."),
                job_item("When I speak with a new international contact, I want confidence that I understood the nuance, so I can avoid an embarrassing mistake.", "emotional", "Reduced anxiety may be more motivating than translation speed alone.", evidence=behavioral_evidence),
                job_item("When colleagues see me operating across languages, I want to appear prepared and respectful, so I can build trust quickly.", "social", "Professional credibility can shape willingness to adopt visible hardware.", "secondary", behavioral_evidence)
            ],
            "pain_points": [
                insight_item("Pausing to type into a phone could break eye contact and conversational rhythm.", "Hands-free interaction can be tested against familiar phone-based workarounds."),
                insight_item("Fast group conversations may move on before a translated response is ready.", "Perceived latency is a candidate activation criterion."),
                insight_item("Travelers may be unsure whether translations preserve business-specific nuance.", "Trust and error recovery should be tested in onboarding and proof points.", "secondary", behavioral_evidence)
            ],
            "purchase_motivations": [
                insight_item("A near-term trip with several multilingual meetings may create urgency.", "Trip planning offers a concrete acquisition moment."),
                insight_item("Reducing dependence on interpreters or phone handoffs may feel operationally efficient.", "Convenience can be tested as a productivity-oriented value proposition."),
                insight_item("A low-risk trial can demonstrate performance in the buyer's own accent and vocabulary.", "Experiential proof may overcome abstract feature comparisons.", "secondary", behavioral_evidence)
            ],
            "adoption_barriers": [
                insight_item("A visible device may feel awkward or impolite in a meeting.", "The product may need a socially acceptable usage ritual.", evidence=behavioral_evidence),
                insight_item("Recording or processing a confidential conversation may create privacy concerns.", "Data handling could block enterprise or executive use."),
                insight_item("Accuracy across accents, jargon, and noisy rooms is not yet established.", "Generic accuracy claims will not answer situational risk.")
            ],
            "typical_scenarios": [
                insight_item("An informal conversation begins after a conference session without an interpreter present.", "Spontaneous networking makes speed and portability testable."),
                insight_item("A traveler visits a supplier site where several participants prefer the local language.", "Multi-party and noisy-environment behavior becomes testable."),
                insight_item("Two attendees clarify a sensitive contract detail during a meal or taxi ride.", "Privacy, nuance, and discreet use converge in a high-stakes moment.", "secondary", behavioral_evidence)
            ],
            "research_questions": [
                "Think about the most recent time language friction changed a business conversation. What happened?",
                "What do you use today when a business conversation shifts languages, and where does it fall short?",
                "What evidence or result would you need before trusting a wearable translator in a meeting?",
                "In which situations would wearing or sharing earbuds feel unacceptable?"
            ],
            "assumptions_to_validate": context["assumptions"],
            "confidence": "medium"
        }
        parsed_insight = UserInsight.model_validate(user_insight)
        return UserInsightResponse(
            request_id=str(uuid4()),
            mode="mock",
            context=context,
            user_insight=parsed_insight,
            quality_review=evaluate_quality(parsed_insight),
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
            parsed_insight = UserInsight.model_validate(
                _parse_object(outputs.get("user_insight"), "user_insight")
            )
            return UserInsightResponse(
                request_id=body.get("workflow_run_id") or body.get("task_id") or str(uuid4()),
                mode="dify",
                context=_parse_object(outputs.get("context"), "context"),
                user_insight=parsed_insight,
                quality_review=evaluate_quality(parsed_insight),
            )
        except ValidationError as exc:
            raise InsightServiceError("The AI workflow returned an unexpected response shape.") from exc


def build_service(settings: Settings) -> InsightService:
    if settings.app_mode == "dify":
        return DifyInsightService(settings)
    return MockInsightService()
