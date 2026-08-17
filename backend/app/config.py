from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_mode: Literal["mock", "dify"] = "mock"
    dify_base_url: str = "https://api.dify.ai/v1"
    dify_api_key: str = ""
    dify_timeout_seconds: float = Field(default=30, gt=0, le=120)
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @field_validator("dify_api_key")
    @classmethod
    def key_required_in_dify_mode(cls, value: str, info):
        if info.data.get("app_mode") == "dify" and not value.strip():
            raise ValueError("DIFY_API_KEY is required when APP_MODE=dify")
        return value

    @property
    def origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
