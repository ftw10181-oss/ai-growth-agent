from app.config import Settings
from app.models import GrowthBrief
from app.protection import LiveUsageGuard, brief_cache_key, visitor_key


def test_guard_enforces_per_visitor_daily_limit() -> None:
    guard = LiveUsageGuard(
        Settings(
            live_daily_limit=50,
            live_per_visitor_daily_limit=2,
            live_min_interval_seconds=0,
        )
    )

    first = guard.admit("visitor-a")
    second = guard.admit("visitor-a")
    third = guard.admit("visitor-a")

    assert first.allowed is True
    assert second.allowed is True
    assert third.allowed is False
    assert third.reason == "visitor_daily_limit"


def test_guard_enforces_global_daily_limit() -> None:
    guard = LiveUsageGuard(
        Settings(
            live_daily_limit=2,
            live_per_visitor_daily_limit=10,
            live_min_interval_seconds=0,
        )
    )

    assert guard.admit("visitor-a").allowed is True
    assert guard.admit("visitor-b").allowed is True
    blocked = guard.admit("visitor-c")

    assert blocked.allowed is False
    assert blocked.reason == "global_daily_limit"


def test_guard_returns_retry_after_for_fast_repeat() -> None:
    guard = LiveUsageGuard(
        Settings(
            live_daily_limit=50,
            live_per_visitor_daily_limit=2,
            live_min_interval_seconds=60,
        )
    )

    assert guard.admit("visitor-a").allowed is True
    blocked = guard.admit("visitor-a")

    assert blocked.allowed is False
    assert blocked.reason == "rate_limited"
    assert blocked.retry_after_seconds == 60


def test_cache_key_is_stable_and_visitor_identifier_is_hashed() -> None:
    brief = GrowthBrief(
        product="AI Growth Agent",
        product_description="An AI workflow that turns a growth brief into testable insights.",
        target_market="China",
        target_audience="Early-stage growth operators",
        business_goal="User Acquisition",
    )

    assert brief_cache_key(brief) == brief_cache_key(brief.model_copy())
    assert visitor_key("203.0.113.1") != "203.0.113.1"
