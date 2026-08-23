import type {
  GrowthBrief,
  InsightResponse,
  ResearchStrategyResponse,
  StrategyResponse
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export async function generateStrategy(brief: GrowthBrief): Promise<StrategyResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v3/strategy`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(brief)
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = typeof body?.detail === "string" ? body.detail : "Unable to generate the strategy.";
    throw new Error(detail);
  }

  return response.json();
}

export async function generateInsight(brief: GrowthBrief): Promise<InsightResponse> {
  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(brief)
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = typeof body?.detail === "string" ? body.detail : "Unable to generate insights.";
    throw new Error(detail);
  }

  return response.json();
}

export async function generateResearchStrategy(
  brief: GrowthBrief
): Promise<ResearchStrategyResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v5/research-strategy`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(brief)
  });

  const body = await response.json().catch(() => null);
  if (!response.ok || typeof body?.detail === "string") {
    const detail = typeof body?.detail === "string"
      ? body.detail
      : "Unable to complete the evidence-backed strategy.";
    throw new Error(detail);
  }

  return body as ResearchStrategyResponse;
}
