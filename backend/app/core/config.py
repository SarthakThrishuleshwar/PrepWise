from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_ROOT / ".env", extra="ignore")
    database_url: str = "sqlite:///./data/learnnova.db"
    model_base_url: str = "http://127.0.0.1:11434"
    reasoning_model: str = ""
    embedding_model: str = ""
    embedding_fingerprint: str = ""
    frontend_origin: str = "http://127.0.0.1:5173"
    model_timeout_seconds: float = Field(default=20, gt=0, le=120)
    max_active_jobs: int = Field(default=4, ge=1, le=16)
    app_timezone: str = "Asia/Kolkata"
    log_level: str = "INFO"

    @field_validator("app_timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Use a valid IANA timezone") from exc
        return value

    @field_validator("model_base_url")
    @classmethod
    def valid_model_url(cls, value: str) -> str:
        from urllib.parse import urlparse
        url = urlparse(value)
        if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password:
            raise ValueError("MODEL_BASE_URL must be an HTTP URL without credentials")
        return value.rstrip("/")

    @property
    def resolved_database_url(self) -> str:
        if self.database_url.startswith("sqlite:///./"):
            path = (BACKEND_ROOT / self.database_url.removeprefix("sqlite:///./")).resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            return "sqlite:///" + path.as_posix()
        return self.database_url
