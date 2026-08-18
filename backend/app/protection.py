import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from time import monotonic
from threading import Lock
from typing import Optional

from .config import Settings
from .models import GrowthBrief, UserInsightResponse


@dataclass(frozen=True)
class Admission:
    allowed: bool
    reason: Optional[str] = None
    retry_after_seconds: Optional[int] = None


@dataclass
class VisitorUsage:
    count: int = 0
    last_request_at: Optional[float] = None


@dataclass
class CachedInsight:
    expires_at: float
    response: UserInsightResponse


class LiveUsageGuard:
    """Best-effort quota protection for a single API process."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._lock = Lock()
        self._day = self._today()
        self._global_count = 0
        self._visitors: dict[str, VisitorUsage] = {}
        self._cache: dict[str, CachedInsight] = {}

    @staticmethod
    def _today() -> str:
        return datetime.now(timezone.utc).date().isoformat()

    def _reset_if_new_day(self) -> None:
        today = self._today()
        if today != self._day:
            self._day = today
            self._global_count = 0
            self._visitors.clear()
            self._cache.clear()

    def cached(self, key: str) -> Optional[UserInsightResponse]:
        now = monotonic()
        with self._lock:
            item = self._cache.get(key)
            if item is None:
                return None
            if item.expires_at <= now:
                self._cache.pop(key, None)
                return None
            return item.response.model_copy(deep=True)

    def remember(self, key: str, response: UserInsightResponse) -> None:
        if self.settings.live_cache_ttl_seconds <= 0:
            return
        with self._lock:
            self._cache[key] = CachedInsight(
                expires_at=monotonic() + self.settings.live_cache_ttl_seconds,
                response=response.model_copy(deep=True),
            )

    def admit(self, visitor_id: str) -> Admission:
        now = monotonic()
        with self._lock:
            self._reset_if_new_day()
            usage = self._visitors.setdefault(visitor_id, VisitorUsage())

            minimum_interval = self.settings.live_min_interval_seconds
            if minimum_interval > 0 and usage.last_request_at is not None:
                elapsed = now - usage.last_request_at
                if elapsed < minimum_interval:
                    retry_after = max(1, int(minimum_interval - elapsed + 0.999))
                    return Admission(False, "rate_limited", retry_after)

            per_visitor_limit = self.settings.live_per_visitor_daily_limit
            if per_visitor_limit > 0 and usage.count >= per_visitor_limit:
                return Admission(False, "visitor_daily_limit")

            daily_limit = self.settings.live_daily_limit
            if daily_limit > 0 and self._global_count >= daily_limit:
                return Admission(False, "global_daily_limit")

            usage.count += 1
            usage.last_request_at = now
            self._global_count += 1
            return Admission(True)


def brief_cache_key(brief: GrowthBrief) -> str:
    normalized = json.dumps(
        brief.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def visitor_key(raw_identifier: str) -> str:
    return hashlib.sha256(raw_identifier.encode("utf-8")).hexdigest()
