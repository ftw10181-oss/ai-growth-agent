"""Run the fixed V0.1 evaluation set against a published Dify workflow."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.models import GrowthBrief, UserInsightResponse  # noqa: E402


BASE_URL = os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1").rstrip("/")
API_KEY = os.getenv("DIFY_API_KEY", "").strip()
OUTPUT_DIR = ROOT / "evals" / "results" / "baseline-v0.1"
CONCURRENCY = 2


def parse_object(value: Any) -> Any:
    return json.loads(value) if isinstance(value, str) else value


async def run_case(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    case: dict[str, Any],
    position: int,
    total: int,
) -> dict[str, Any]:
    brief = GrowthBrief.model_validate(case["input"])
    payload = {
        "inputs": brief.model_dump(mode="json"),
        "response_mode": "blocking",
        "user": f"portfolio-eval-{case['id']}",
    }
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    async with semaphore:
        started = time.perf_counter()
        response = None
        for attempt in range(2):
            response = await client.post(f"{BASE_URL}/workflows/run", json=payload, headers=headers)
            if response.status_code != 429 and response.status_code < 500:
                break
            await asyncio.sleep(2 * (attempt + 1))

        elapsed = round(time.perf_counter() - started, 3)
        assert response is not None
        response.raise_for_status()
        body = response.json()
        data = body.get("data") or {}
        if data.get("status") != "succeeded":
            raise RuntimeError(f"{case['id']}: workflow status {data.get('status')}")
        outputs = data.get("outputs") or {}

        public_response = UserInsightResponse(
            request_id=body.get("workflow_run_id") or body.get("task_id"),
            mode="dify",
            context=parse_object(outputs.get("context")),
            user_insight=parse_object(outputs.get("user_insight")),
        )
        output_path = OUTPUT_DIR / f"{case['id']}.json"
        output_path.write_text(
            json.dumps(public_response.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"[{position}/{total}] {case['id']} succeeded in {elapsed:.1f}s", flush=True)
        return {
            "case_id": case["id"],
            "status": "succeeded",
            "elapsed_seconds": elapsed,
            "workflow_elapsed_seconds": data.get("elapsed_time"),
            "total_tokens": data.get("total_tokens"),
            "total_steps": data.get("total_steps"),
            "request_id": public_response.request_id,
        }


async def main() -> int:
    if not API_KEY.startswith("app-"):
        raise SystemExit("DIFY_API_KEY is missing or invalid")

    case_set = json.loads((ROOT / "evals" / "cases.json").read_text(encoding="utf-8"))
    cases = case_set["cases"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async with httpx.AsyncClient(timeout=120) as client:
        tasks = [
            run_case(client, semaphore, case, index, len(cases))
            for index, case in enumerate(cases, start=1)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    summary_cases = []
    failures = 0
    for case, result in zip(cases, results):
        if isinstance(result, Exception):
            failures += 1
            summary_cases.append({"case_id": case["id"], "status": "failed", "error": str(result)})
            print(f"[failed] {case['id']}: {result}", flush=True)
        else:
            summary_cases.append(result)

    summary = {
        "evaluation_version": case_set["version"],
        "prompt_version": "v0.1",
        "run_at": datetime.now(timezone.utc).isoformat(),
        "case_count": len(cases),
        "success_count": len(cases) - failures,
        "failure_count": failures,
        "concurrency": CONCURRENCY,
        "cases": summary_cases,
    }
    (OUTPUT_DIR / "run-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
