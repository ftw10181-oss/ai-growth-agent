import type { GrowthBrief, InsightResponse } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function generateInsight(brief: GrowthBrief): Promise<InsightResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/insights`, {
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
