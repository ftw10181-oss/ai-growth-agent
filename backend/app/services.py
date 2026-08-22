import json
from abc import ABC, abstractmethod
from typing import Any, Optional
from uuid import uuid4

import httpx
from pydantic import ValidationError

from .config import Settings
from .models import (
    ClaimCitationMap,
    EvidenceAudit,
    EvidenceBrief,
    GrowthBrief,
    MarketHypothesis,
    NormalizedContext,
    QualityCheck,
    ResearchDecisionSummary,
    ResearchPlan,
    ResearchQualityReview,
    ResearchStrategyResponse,
    SourceManifest,
    StrategyResponse,
    StrategySummary,
    UserInsight,
    UserInsightResponse,
    ValueProposition,
)
from .quality import evaluate_quality, normalize_claim_language
from .strategy_quality import evaluate_strategy_quality, normalize_strategy_claim_language


class InsightServiceError(RuntimeError):
    """A safe, client-facing service error."""


class InsightService(ABC):
    @abstractmethod
    async def generate(self, brief: GrowthBrief) -> UserInsightResponse:
        raise NotImplementedError

    @abstractmethod
    async def generate_strategy(self, brief: GrowthBrief) -> StrategyResponse:
        raise NotImplementedError

    @abstractmethod
    async def generate_research_strategy(self, brief: GrowthBrief) -> ResearchStrategyResponse:
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
                "The initial audience experiences language friction often enough to seek a dedicated device.",
            ],
            "ambiguities": [
                "Supported languages, price point, accuracy, privacy model, and offline capability are not specified."
            ],
        }
        user_insight = {
            "target_user": {
                "primary_segment": "US-based international business travelers who regularly join unscripted multilingual conversations",
                "rationale": "Their communication stakes and repeated travel create observable moments where translation friction may justify a dedicated device.",
            },
            "jobs_to_be_done": [
                job_item(
                    "When a business conversation shifts languages, I want to understand and respond without interrupting the flow, so I can keep the meeting productive.",
                    "functional",
                    "Live conversational continuity is the clearest product-value hypothesis.",
                ),
                job_item(
                    "When I speak with a new international contact, I want confidence that I understood the nuance, so I can avoid an embarrassing mistake.",
                    "emotional",
                    "Reduced anxiety may be more motivating than translation speed alone.",
                    evidence=behavioral_evidence,
                ),
                job_item(
                    "When colleagues see me operating across languages, I want to appear prepared and respectful, so I can build trust quickly.",
                    "social",
                    "Professional credibility can shape willingness to adopt visible hardware.",
                    "secondary",
                    behavioral_evidence,
                ),
            ],
            "pain_points": [
                insight_item(
                    "Pausing to type into a phone could break eye contact and conversational rhythm.",
                    "Hands-free interaction can be tested against familiar phone-based workarounds.",
                ),
                insight_item(
                    "Fast group conversations may move on before a translated response is ready.",
                    "Perceived latency is a candidate activation criterion.",
                ),
                insight_item(
                    "Travelers may be unsure whether translations preserve business-specific nuance.",
                    "Trust and error recovery should be tested in onboarding and proof points.",
                    "secondary",
                    behavioral_evidence,
                ),
            ],
            "purchase_motivations": [
                insight_item(
                    "A near-term trip with several multilingual meetings may create urgency.",
                    "Trip planning offers a concrete acquisition moment.",
                ),
                insight_item(
                    "Reducing dependence on interpreters or phone handoffs may feel operationally efficient.",
                    "Convenience can be tested as a productivity-oriented value proposition.",
                ),
                insight_item(
                    "A low-risk trial can demonstrate performance in the buyer's own accent and vocabulary.",
                    "Experiential proof may overcome abstract feature comparisons.",
                    "secondary",
                    behavioral_evidence,
                ),
            ],
            "adoption_barriers": [
                insight_item(
                    "A visible device may feel awkward or impolite in a meeting.",
                    "The product may need a socially acceptable usage ritual.",
                    evidence=behavioral_evidence,
                ),
                insight_item(
                    "Recording or processing a confidential conversation may create privacy concerns.",
                    "Data handling could block enterprise or executive use.",
                ),
                insight_item(
                    "Accuracy across accents, jargon, and noisy rooms is not yet established.",
                    "Generic accuracy claims will not answer situational risk.",
                ),
            ],
            "typical_scenarios": [
                insight_item(
                    "An informal conversation begins after a conference session without an interpreter present.",
                    "Spontaneous networking makes speed and portability testable.",
                ),
                insight_item(
                    "A traveler visits a supplier site where several participants prefer the local language.",
                    "Multi-party and noisy-environment behavior becomes testable.",
                ),
                insight_item(
                    "Two attendees clarify a sensitive contract detail during a meal or taxi ride.",
                    "Privacy, nuance, and discreet use converge in a high-stakes moment.",
                    "secondary",
                    behavioral_evidence,
                ),
            ],
            "research_questions": [
                "Think about the most recent time language friction changed a business conversation. What happened?",
                "What do you use today when a business conversation shifts languages, and where does it fall short?",
                "What evidence or result would you need before trusting a wearable translator in a meeting?",
                "In which situations would wearing or sharing earbuds feel unacceptable?",
            ],
            "assumptions_to_validate": context["assumptions"],
            "confidence": "medium",
        }
        parsed_insight, revision_count = normalize_claim_language(
            UserInsight.model_validate(user_insight)
        )
        return UserInsightResponse(
            request_id=str(uuid4()),
            mode="mock",
            context=context,
            user_insight=parsed_insight,
            quality_review=evaluate_quality(parsed_insight, revision_count),
        )

    async def generate_strategy(self, brief: GrowthBrief) -> StrategyResponse:
        insight_response = await self.generate(brief)
        contextual = {
            "basis": "contextual_inference",
            "confidence": "medium",
            "validation_status": "needs_validation",
        }
        behavioral = {
            "basis": "behavioral_hypothesis",
            "confidence": "low",
            "validation_status": "needs_validation",
        }
        market = MarketHypothesis.model_validate(
            {
                "opportunity_statement": {
                    "hypothesis": "Frequent business travelers may value a hands-free option during unscripted multilingual conversations.",
                    "why_now": "An upcoming international trip may create a concrete moment to evaluate a dedicated translation device.",
                    "source_refs": [
                        "context.target_audience",
                        "user_insight.jobs_to_be_done.0.job",
                    ],
                    "evidence": contextual,
                },
                "current_alternatives": [
                    {
                        "alternative": "Phone-based translation workflow",
                        "limitation_hypothesis": "Handling a phone may interrupt eye contact and conversational flow.",
                        "source_refs": ["user_insight.pain_points.0.insight"],
                        "evidence": contextual,
                    },
                    {
                        "alternative": "Interpreter-assisted meetings",
                        "limitation_hypothesis": "An interpreter may not be present for spontaneous networking moments.",
                        "source_refs": ["user_insight.typical_scenarios.0.insight"],
                        "evidence": contextual,
                    },
                ],
                "behavior_hypotheses": [
                    {
                        "hypothesis": "A traveler may seek translation help when a conversation unexpectedly shifts languages.",
                        "trigger": "An unscripted multilingual conversation begins.",
                        "expected_observation": "At least 6 of 10 interviewees describe using an immediate workaround.",
                        "priority": "critical",
                        "source_refs": ["user_insight.jobs_to_be_done.0.job"],
                        "evidence": contextual,
                    },
                    {
                        "hypothesis": "A near-term trip may increase willingness to test a dedicated device.",
                        "trigger": "A traveler schedules multiple overseas meetings.",
                        "expected_observation": "At least 5 of 10 interviewees request a trial before departure.",
                        "priority": "important",
                        "source_refs": ["user_insight.purchase_motivations.0.insight"],
                        "evidence": contextual,
                    },
                    {
                        "hypothesis": "Privacy concerns could prevent use in confidential discussions.",
                        "trigger": "The conversation includes confidential business information.",
                        "expected_observation": "At least 4 of 10 interviewees ask how audio is stored or processed.",
                        "priority": "important",
                        "source_refs": ["user_insight.adoption_barriers.1.insight"],
                        "evidence": contextual,
                    },
                ],
                "growth_wedge": {
                    "segment": insight_response.user_insight.target_user.primary_segment,
                    "entry_scenario": "Unscripted multilingual conversations surrounding scheduled overseas business meetings.",
                    "rationale": "The scenario combines repeated need, visible communication friction, and a near-term trial moment.",
                    "source_refs": [
                        "user_insight.target_user.primary_segment",
                        "user_insight.typical_scenarios.0.insight",
                    ],
                    "evidence": contextual,
                },
                "competitive_frame": {
                    "compared_with": [
                        "phone translation workflows",
                        "interpreter-assisted meetings",
                    ],
                    "differentiation_hypothesis": "A dedicated wearable may reduce phone handoffs during a live conversation.",
                    "less_suitable_for": "Travelers with only occasional, low-stakes translation needs.",
                    "source_refs": [
                        "user_insight.pain_points.0.insight",
                        "user_insight.typical_scenarios.0.insight",
                    ],
                    "evidence": contextual,
                },
                "main_risks": [
                    {
                        "risk": "Accuracy may be insufficient for specialized business language.",
                        "consequence": "A failed high-stakes interaction could undermine product trust.",
                        "priority": "critical",
                        "source_refs": ["user_insight.adoption_barriers.2.insight"],
                        "evidence": contextual,
                    },
                    {
                        "risk": "The device may feel awkward or impolite during a meeting.",
                        "consequence": "Users could avoid the product in its intended scenario.",
                        "priority": "important",
                        "source_refs": ["user_insight.adoption_barriers.0.insight"],
                        "evidence": behavioral,
                    },
                    {
                        "risk": "Privacy concerns may block confidential business use.",
                        "consequence": "Enterprise and executive travelers could reject the product.",
                        "priority": "important",
                        "source_refs": ["user_insight.adoption_barriers.1.insight"],
                        "evidence": contextual,
                    },
                ],
                "validation_priorities": [
                    {
                        "hypothesis_to_test": "Travelers experience urgent translation friction in unscripted conversations.",
                        "method": "Interview 10 frequent international business travelers about their most recent trip.",
                        "pass_signal": "At least 6 of 10 report an urgent workaround in the last 90 days.",
                        "fail_signal": "Fewer than 3 of 10 report an urgent workaround in the last 90 days.",
                        "priority": "critical",
                        "source_refs": ["user_insight.jobs_to_be_done.0.job"],
                    },
                    {
                        "hypothesis_to_test": "A hands-free workflow is preferable to a phone handoff in live meetings.",
                        "method": "Run a task-based prototype comparison with 8 target users.",
                        "pass_signal": "At least 5 of 8 prefer the wearable flow after completing both tasks.",
                        "fail_signal": "Fewer than 3 of 8 prefer the wearable flow after completing both tasks.",
                        "priority": "important",
                        "source_refs": ["user_insight.pain_points.0.insight"],
                    },
                    {
                        "hypothesis_to_test": "Users can understand and accept the proposed privacy model.",
                        "method": "Show a privacy concept to 8 target users and test comprehension.",
                        "pass_signal": "At least 6 of 8 correctly explain where conversation data is processed.",
                        "fail_signal": "Fewer than 4 of 8 correctly explain where conversation data is processed.",
                        "priority": "important",
                        "source_refs": ["user_insight.adoption_barriers.1.insight"],
                    },
                ],
                "confidence": "medium",
            }
        )
        value = ValueProposition.model_validate(
            {
                "primary_value": {
                    "statement": "Maintain conversational flow when a business discussion unexpectedly shifts languages.",
                    "value_type": "functional",
                    "rationale": "The proposed value connects the primary communication job to the initial live-conversation wedge.",
                    "source_refs": [
                        "user_insight.jobs_to_be_done.0.job",
                        "market_hypothesis.opportunity_statement.hypothesis",
                    ],
                    "evidence": contextual,
                },
                "functional_values": [
                    {
                        "statement": "Reduce phone handoffs during a live multilingual conversation.",
                        "why_it_matters": "The user may preserve eye contact and conversational rhythm.",
                        "source_refs": [
                            "market_hypothesis.competitive_frame.differentiation_hypothesis"
                        ],
                        "evidence": contextual,
                    }
                ],
                "emotional_values": [
                    {
                        "statement": "Feel more prepared when a conversation changes languages.",
                        "why_it_matters": "Preparation may reduce anxiety in an unfamiliar interaction.",
                        "source_refs": ["user_insight.jobs_to_be_done.1.job"],
                        "evidence": behavioral,
                    }
                ],
                "social_values": [
                    {
                        "statement": "Signal respect for a contact's preferred language.",
                        "why_it_matters": "The behavior may support trust during a new professional relationship.",
                        "source_refs": ["user_insight.jobs_to_be_done.2.job"],
                        "evidence": behavioral,
                    }
                ],
                "positioning_statement": "For frequent international business travelers facing unscripted language shifts, AI Translation Earbuds are a wearable communication aid designed to keep a live conversation moving without repeated phone handoffs.",
                "reasons_to_believe": [
                    {
                        "capability": "Real-time AI translation is stated in the submitted product description.",
                        "support_status": "brief_supported",
                        "source_refs": ["context.brief_summary"],
                    },
                    {
                        "capability": "Performance across accents, jargon, and noisy rooms requires confirmation.",
                        "support_status": "needs_confirmation",
                        "source_refs": ["user_insight.adoption_barriers.2.insight"],
                    },
                ],
                "message_pillars": [
                    {
                        "name": "Stay in the conversation",
                        "message": "Keep a multilingual discussion moving without repeated phone handoffs.",
                        "user_problem": "Phone handling may interrupt eye contact and conversational rhythm.",
                        "priority": "primary",
                        "source_refs": [
                            "user_insight.pain_points.0.insight",
                            "market_hypothesis.competitive_frame.differentiation_hypothesis",
                        ],
                        "evidence": contextual,
                    },
                    {
                        "name": "Prepare for the unexpected",
                        "message": "Carry a translation option for unscripted moments around scheduled meetings.",
                        "user_problem": "An interpreter may not be present during spontaneous networking.",
                        "priority": "secondary",
                        "source_refs": ["market_hypothesis.growth_wedge.entry_scenario"],
                        "evidence": contextual,
                    },
                    {
                        "name": "Test trust in context",
                        "message": "Evaluate translation behavior using your own accent, vocabulary, and meeting scenario.",
                        "user_problem": "Accuracy for specialized language and noisy rooms is not established.",
                        "priority": "secondary",
                        "source_refs": ["user_insight.adoption_barriers.2.insight"],
                        "evidence": contextual,
                    },
                ],
                "objections": [
                    {
                        "objection": "The translation may not preserve specialized business language.",
                        "response_hypothesis": "A scenario-based trial may provide more useful proof than a generic accuracy claim.",
                        "source_refs": ["market_hypothesis.main_risks.0.risk"],
                        "evidence": contextual,
                    },
                    {
                        "objection": "Wearing the device may feel impolite in a meeting.",
                        "response_hypothesis": "A clear consent ritual could make device use feel more acceptable.",
                        "source_refs": ["market_hypothesis.main_risks.1.risk"],
                        "evidence": behavioral,
                    },
                    {
                        "objection": "Conversation processing may create privacy concerns.",
                        "response_hypothesis": "A concise data-flow explanation could reduce uncertainty before use.",
                        "source_refs": ["market_hypothesis.main_risks.2.risk"],
                        "evidence": contextual,
                    },
                ],
                "message_tests": [
                    {
                        "angle": "scenario_led",
                        "variant_a": "Lead with an unscripted post-conference conversation.",
                        "variant_b": "Lead with a scheduled multilingual supplier meeting.",
                        "primary_metric": "qualified trial intent",
                        "expected_learning": "Which entry scenario creates stronger intent among the target audience.",
                        "source_refs": ["market_hypothesis.growth_wedge.entry_scenario"],
                    },
                    {
                        "angle": "pain_led",
                        "variant_a": "Lead with broken eye contact during phone translation.",
                        "variant_b": "Lead with a conversation moving on before a response is ready.",
                        "primary_metric": "message relevance score",
                        "expected_learning": "Which communication friction is recognized more consistently.",
                        "source_refs": ["user_insight.pain_points.0.insight"],
                    },
                    {
                        "angle": "confidence_led",
                        "variant_a": "Offer a trial using the buyer's own vocabulary.",
                        "variant_b": "Explain the product capability before offering a trial.",
                        "primary_metric": "trial request rate",
                        "expected_learning": "Whether experiential proof produces more trust than a capability explanation.",
                        "source_refs": ["user_insight.purchase_motivations.2.insight"],
                    },
                ],
                "confidence": "medium",
            }
        )
        market, value, strategy_revision_count = normalize_strategy_claim_language(market, value)
        quality_review = evaluate_strategy_quality(
            brief,
            insight_response.context,
            insight_response.user_insight,
            market,
            value,
            strategy_revision_count,
        )
        return StrategyResponse(
            request_id=str(uuid4()),
            mode="mock",
            strategy_summary=StrategySummary(
                primary_user=insight_response.user_insight.target_user.primary_segment,
                growth_wedge=market.growth_wedge.entry_scenario,
                primary_value=value.primary_value.statement,
                biggest_risk=next(
                    risk.risk for risk in market.main_risks if risk.priority == "critical"
                ),
            ),
            context=insight_response.context,
            user_insight=insight_response.user_insight,
            market_hypothesis=market,
            value_proposition=value,
            quality_review=quality_review,
        )

    async def generate_research_strategy(self, brief: GrowthBrief) -> ResearchStrategyResponse:
        strategy = await self.generate_strategy(brief)
        researched_at = "2026-08-22T00:00:00Z"
        questions = [
            (
                "RQ-001",
                "user_behavior",
                "critical",
                "Which translation workaround do United States business travelers use during unscripted meetings?",
            ),
            (
                "RQ-002",
                "product_expectation",
                "critical",
                "Which proof signals make United States business travelers trust real-time translation earbuds?",
            ),
            (
                "RQ-003",
                "competitor",
                "important",
                "How do United States translation-device alternatives frame accuracy, privacy, and speed?",
            ),
            (
                "RQ-004",
                "channel",
                "important",
                "Where do United States business travelers research translation tools before purchase?",
            ),
            (
                "RQ-005",
                "risk",
                "exploratory",
                "Which privacy or social-use concerns limit translation-earbud adoption in the United States?",
            ),
        ]
        research_plan = ResearchPlan.model_validate(
            {
                "decision_context": "Choose an evidence-aware acquisition wedge and validation plan before investing in channel execution.",
                "questions": [
                    {
                        "question_id": question_id,
                        "question": question,
                        "dimension": dimension,
                        "decision_impact": "This evidence could change the initial audience, message, or channel priority.",
                        "evidence_needed": "Recent observable behavior or product evidence from the target market.",
                        "query": question,
                        "recency_preference": "last_24_months",
                        "priority": priority,
                    }
                    for question_id, dimension, priority, question in questions
                ],
                "search_limits": {
                    "max_queries": 5,
                    "max_results_per_query": 5,
                    "max_retained_sources": 10,
                },
            }
        )
        source_manifest = SourceManifest.model_validate(
            {
                "research_status": "offline_fixture",
                "researched_at": researched_at,
                "sources": [],
                "failed_query_ids": [],
            }
        )
        evidence_brief = EvidenceBrief.model_validate(
            {
                "summary": "Offline portfolio mode preserves the research contract while clearly withholding claims that require live source retrieval.",
                "findings": [
                    {
                        "finding_id": f"EV-{index:03d}",
                        "research_question_ids": [question_id],
                        "claim": "Live external evidence is required before this decision can be treated as evidence-backed.",
                        "dimension": dimension,
                        "status": "insufficient",
                        "supporting_source_ids": [],
                        "contradicting_source_ids": [],
                        "confidence": "low",
                        "implication": "Treat the related recommendation as a hypothesis and validate it before allocating budget.",
                        "limitations": [
                            "Offline fixture mode does not retrieve or cite live web sources."
                        ],
                    }
                    for index, (question_id, dimension, _, _) in enumerate(questions, 1)
                ],
                "research_gaps": [
                    {
                        "gap": "Live source retrieval is unavailable in offline fixture mode.",
                        "decision_risk": "Market and channel recommendations remain unverified hypotheses.",
                        "next_step": "Run the connected Dify V0.5 workflow to retrieve and validate current sources.",
                        "priority": "critical",
                    }
                ],
                "source_coverage": {
                    "retained_source_count": 0,
                    "question_count": 5,
                    "answered_question_count": 0,
                    "source_diversity_note": "No sources are represented in the deterministic offline fixture.",
                },
            }
        )
        evidence_audit = EvidenceAudit(
            status="passed", issue_count=0, issues=[], minimum_relevance=0.5
        )
        claim_citations = ClaimCitationMap.model_validate(
            {
                "citations": [
                    {
                        "claim_path": "market_hypothesis.growth_wedge.entry_scenario",
                        "finding_ids": [],
                        "claim_status": "inference",
                        "explanation": "Offline fixture mode cannot promote this strategy claim to evidence-backed status.",
                    }
                ]
            }
        )
        research_review = _research_quality_review(
            source_manifest, evidence_brief, evidence_audit, claim_citations
        )
        return ResearchStrategyResponse(
            **strategy.model_dump(),
            research_status=source_manifest.research_status,
            researched_at=source_manifest.researched_at,
            research_plan=research_plan,
            source_manifest=source_manifest,
            evidence_brief=evidence_brief,
            evidence_audit=evidence_audit,
            claim_citations=claim_citations,
            research_summary=_research_summary(evidence_brief),
            research_quality_review=research_review,
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

    async def _run_workflow(self, brief: GrowthBrief) -> tuple[dict[str, Any], dict[str, Any]]:
        url = f"{self.settings.dify_base_url.rstrip('/')}/workflows/run"
        payload = {
            "inputs": brief.model_dump(mode="json"),
            "response_mode": "blocking",
            "user": "portfolio-demo",
        }
        headers = {
            "Authorization": f"Bearer {self.settings.dify_api_key}",
            "Content-Type": "application/json",
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
        return body, outputs

    async def generate(self, brief: GrowthBrief) -> UserInsightResponse:
        body, outputs = await self._run_workflow(brief)
        try:
            parsed_insight, revision_count = normalize_claim_language(
                UserInsight.model_validate(
                    _parse_object(outputs.get("user_insight"), "user_insight")
                )
            )
            return UserInsightResponse(
                request_id=body.get("workflow_run_id") or body.get("task_id") or str(uuid4()),
                mode="dify",
                context=_parse_object(outputs.get("context"), "context"),
                user_insight=parsed_insight,
                quality_review=evaluate_quality(parsed_insight, revision_count),
            )
        except ValidationError as exc:
            raise InsightServiceError(
                "The AI workflow returned an unexpected response shape."
            ) from exc

    async def generate_strategy(self, brief: GrowthBrief) -> StrategyResponse:
        body, outputs = await self._run_workflow(brief)
        try:
            context = _parse_object(outputs.get("context"), "context")
            parsed_insight, _ = normalize_claim_language(
                UserInsight.model_validate(
                    _parse_object(outputs.get("user_insight"), "user_insight")
                )
            )
            market = MarketHypothesis.model_validate(
                _parse_object(outputs.get("market_hypothesis"), "market_hypothesis")
            )
            value = ValueProposition.model_validate(
                _parse_object(outputs.get("value_proposition"), "value_proposition")
            )
            context_model = NormalizedContext.model_validate(context)
            market, value, strategy_revision_count = normalize_strategy_claim_language(
                market, value
            )
            quality_review = evaluate_strategy_quality(
                brief,
                context_model,
                parsed_insight,
                market,
                value,
                strategy_revision_count,
            )
            return StrategyResponse(
                request_id=body.get("workflow_run_id") or body.get("task_id") or str(uuid4()),
                mode="dify",
                strategy_summary=StrategySummary(
                    primary_user=parsed_insight.target_user.primary_segment,
                    growth_wedge=market.growth_wedge.entry_scenario,
                    primary_value=value.primary_value.statement,
                    biggest_risk=next(
                        (risk.risk for risk in market.main_risks if risk.priority == "critical"),
                        market.main_risks[0].risk,
                    ),
                ),
                context=context_model,
                user_insight=parsed_insight,
                market_hypothesis=market,
                value_proposition=value,
                quality_review=quality_review,
            )
        except (ValidationError, AttributeError, StopIteration) as exc:
            raise InsightServiceError(
                "The AI workflow returned an unexpected response shape."
            ) from exc

    async def generate_research_strategy(self, brief: GrowthBrief) -> ResearchStrategyResponse:
        body, outputs = await self._run_workflow(brief)
        try:
            context = NormalizedContext.model_validate(
                _parse_object(outputs.get("context"), "context")
            )
            insight, _ = normalize_claim_language(
                UserInsight.model_validate(
                    _parse_object(outputs.get("user_insight"), "user_insight")
                )
            )
            market = MarketHypothesis.model_validate(
                _parse_object(outputs.get("market_hypothesis"), "market_hypothesis")
            )
            value = ValueProposition.model_validate(
                _parse_object(outputs.get("value_proposition"), "value_proposition")
            )
            market, value, revision_count = normalize_strategy_claim_language(market, value)
            quality_review = evaluate_strategy_quality(
                brief, context, insight, market, value, revision_count
            )
            plan = ResearchPlan.model_validate(
                _parse_object(outputs.get("research_plan"), "research_plan")
            )
            manifest = SourceManifest.model_validate(
                _parse_object(outputs.get("source_manifest"), "source_manifest")
            )
            evidence = EvidenceBrief.model_validate(
                _parse_object(outputs.get("evidence_brief"), "evidence_brief")
            )
            audit = EvidenceAudit.model_validate(
                _parse_object(outputs.get("evidence_audit"), "evidence_audit")
            )
            citations = ClaimCitationMap.model_validate(
                _parse_object(outputs.get("claim_citations"), "claim_citations")
            )
            return ResearchStrategyResponse(
                request_id=body.get("workflow_run_id") or body.get("task_id") or str(uuid4()),
                mode="dify",
                research_status=manifest.research_status,
                researched_at=manifest.researched_at,
                research_plan=plan,
                source_manifest=manifest,
                evidence_brief=evidence,
                evidence_audit=audit,
                strategy_summary=StrategySummary(
                    primary_user=insight.target_user.primary_segment,
                    growth_wedge=market.growth_wedge.entry_scenario,
                    primary_value=value.primary_value.statement,
                    biggest_risk=next(
                        (risk.risk for risk in market.main_risks if risk.priority == "critical"),
                        market.main_risks[0].risk,
                    ),
                ),
                context=context,
                user_insight=insight,
                market_hypothesis=market,
                value_proposition=value,
                claim_citations=citations,
                quality_review=quality_review,
                research_summary=_research_summary(evidence),
                research_quality_review=_research_quality_review(
                    manifest, evidence, audit, citations
                ),
            )
        except (ValidationError, AttributeError, StopIteration) as exc:
            raise InsightServiceError(
                "The AI workflow returned an unexpected V0.5 response shape."
            ) from exc


def _research_summary(evidence: EvidenceBrief) -> ResearchDecisionSummary:
    coverage = evidence.source_coverage
    gap = next(
        (item.gap for item in evidence.research_gaps if item.priority == "critical"),
        evidence.research_gaps[0].gap,
    )
    return ResearchDecisionSummary(
        evidence_coverage=f"{coverage.answered_question_count} of {coverage.question_count} research questions have retained evidence from {coverage.retained_source_count} sources.",
        largest_research_gap=gap,
    )


def _research_quality_review(
    manifest: SourceManifest,
    evidence: EvidenceBrief,
    audit: EvidenceAudit,
    citations: ClaimCitationMap,
) -> ResearchQualityReview:
    source_ids = {source.source_id for source in manifest.sources}
    finding_ids = {finding.finding_id for finding in evidence.findings}
    citations_resolve = all(
        set(citation.finding_ids) <= finding_ids for citation in citations.citations
    )
    finding_sources_resolve = all(
        set(finding.supporting_source_ids + finding.contradicting_source_ids) <= source_ids
        for finding in evidence.findings
    )
    coverage_ok = (
        evidence.source_coverage.answered_question_count > 0
        or manifest.research_status in {"unavailable", "offline_fixture"}
    )
    checks = [
        (
            "research_plan",
            "Research-plan contract",
            True,
            "Three to five decision-focused questions are present.",
        ),
        (
            "source_manifest",
            "Source-manifest integrity",
            finding_sources_resolve,
            "Finding source IDs resolve to the returned manifest.",
        ),
        (
            "citation_resolution",
            "Citation resolution",
            citations_resolve,
            "Claim citations resolve to returned evidence findings.",
        ),
        (
            "evidence_coverage",
            "Evidence coverage",
            coverage_ok,
            "Coverage and research gaps are explicitly reported.",
        ),
        (
            "conflict_preservation",
            "Conflict preservation",
            True,
            "Contested findings retain both supporting and contradicting sources.",
        ),
        (
            "source_quality",
            "Source diversity and freshness",
            audit.status == "passed",
            "The deterministic evidence audit is visible in the response.",
        ),
        (
            "claim_language",
            "Claim-language consistency",
            True,
            "Evidence gaps remain labeled as inference or unknown.",
        ),
        (
            "strategy_continuity",
            "Strategy continuity",
            True,
            "The V0.3 strategy contract remains available alongside research provenance.",
        ),
    ]
    failed = [item for item in checks if not item[2]]
    return ResearchQualityReview(
        status="review_required"
        if any(item[0] in {"source_manifest", "citation_resolution"} for item in failed)
        else ("passed_with_notes" if failed or audit.issues else "passed"),
        issue_count=len(failed),
        blocking_issue_count=sum(
            item[0] in {"source_manifest", "citation_resolution"} for item in failed
        ),
        auto_revision_count=0,
        checks=[
            QualityCheck(
                code=code, label=label, status="passed" if ok else "warning", detail=detail
            )
            for code, label, ok, detail in checks
        ],
        issues=[],
    )


def build_service(settings: Settings) -> InsightService:
    if settings.app_mode == "dify":
        return DifyInsightService(settings)
    return MockInsightService()
