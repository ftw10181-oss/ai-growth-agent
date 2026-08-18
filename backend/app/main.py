from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings, get_settings
from .models import GrowthBrief, UserInsightResponse
from .services import InsightServiceError, build_service

settings = get_settings()

app = FastAPI(
    title="AI Growth Agent API",
    version="0.2.1",
    description="A stable product boundary for the AI Growth Agent Dify workflow."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"]
)


@app.get("/health")
async def health(config: Settings = Depends(get_settings)) -> dict[str, str]:
    return {"status": "ok", "mode": config.app_mode, "version": "0.2.1"}


@app.post("/api/analyze", response_model=UserInsightResponse)
@app.post("/api/v2/insights", response_model=UserInsightResponse, include_in_schema=False)
@app.post("/api/v1/insights", response_model=UserInsightResponse, include_in_schema=False)
async def create_insight(
    brief: GrowthBrief, config: Settings = Depends(get_settings)
) -> UserInsightResponse:
    try:
        return await build_service(config).generate(brief)
    except InsightServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
