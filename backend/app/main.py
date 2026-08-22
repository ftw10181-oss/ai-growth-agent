from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings, get_settings
from .models import GrowthBrief, StrategyResponse, UserInsightResponse
from .protection import LiveUsageGuard, brief_cache_key, visitor_key
from .services import InsightServiceError, build_service

settings = get_settings()
usage_guard = LiveUsageGuard(settings)

app = FastAPI(
    title="AI Growth Agent API",
    version="0.3.0",
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
    return {"status": "ok", "mode": config.app_mode, "version": "0.3.0"}


@app.post("/api/analyze", response_model=UserInsightResponse)
@app.post("/api/v2/insights", response_model=UserInsightResponse, include_in_schema=False)
@app.post("/api/v1/insights", response_model=UserInsightResponse, include_in_schema=False)
async def create_insight(
    brief: GrowthBrief,
    request: Request,
    response: Response,
    config: Settings = Depends(get_settings),
) -> UserInsightResponse:
    if config.app_mode == "mock":
        return await build_service(config).generate(brief)

    key = brief_cache_key(brief)
    cached = usage_guard.cached(key)
    if cached is not None:
        response.headers["X-AI-Cache"] = "HIT"
        return cached

    raw_visitor = (
        request.headers.get("cf-connecting-ip")
        or request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
        or (request.client.host if request.client else "anonymous")
    )
    admission = usage_guard.admit(visitor_key(raw_visitor))
    if not admission.allowed:
        if admission.reason == "rate_limited":
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please wait before trying again.",
                headers={"Retry-After": str(admission.retry_after_seconds or 60)},
            )
        response.headers["X-AI-Fallback"] = admission.reason or "quota_limit"
        mock_config = config.model_copy(update={"app_mode": "mock"})
        return await build_service(mock_config).generate(brief)

    try:
        result = await build_service(config).generate(brief)
        usage_guard.remember(key, result)
        response.headers["X-AI-Cache"] = "MISS"
        return result
    except InsightServiceError as exc:
        if config.live_fallback_to_mock:
            response.headers["X-AI-Fallback"] = "upstream_error"
            mock_config = config.model_copy(update={"app_mode": "mock"})
            return await build_service(mock_config).generate(brief)
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/v3/strategy", response_model=StrategyResponse)
async def create_strategy(
    brief: GrowthBrief,
    request: Request,
    response: Response,
    config: Settings = Depends(get_settings),
) -> StrategyResponse:
    if config.app_mode == "mock":
        return await build_service(config).generate_strategy(brief)

    key = f"strategy:{brief_cache_key(brief)}"
    cached = usage_guard.cached(key)
    if isinstance(cached, StrategyResponse):
        response.headers["X-AI-Cache"] = "HIT"
        return cached

    raw_visitor = (
        request.headers.get("cf-connecting-ip")
        or request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
        or (request.client.host if request.client else "anonymous")
    )
    admission = usage_guard.admit(visitor_key(raw_visitor))
    if not admission.allowed:
        if admission.reason == "rate_limited":
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please wait before trying again.",
                headers={"Retry-After": str(admission.retry_after_seconds or 60)},
            )
        response.headers["X-AI-Fallback"] = admission.reason or "quota_limit"
        mock_config = config.model_copy(update={"app_mode": "mock"})
        return await build_service(mock_config).generate_strategy(brief)

    try:
        result = await build_service(config).generate_strategy(brief)
        usage_guard.remember(key, result)
        response.headers["X-AI-Cache"] = "MISS"
        return result
    except InsightServiceError as exc:
        if config.live_fallback_to_mock:
            response.headers["X-AI-Fallback"] = "upstream_error"
            mock_config = config.model_copy(update={"app_mode": "mock"})
            return await build_service(mock_config).generate_strategy(brief)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
