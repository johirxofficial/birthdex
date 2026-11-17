"""Configuration for BirthDex, loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

PORTAL_BASE = "https://everify.bdris.gov.bd"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)


def _load_dotenv(path: str = ".env") -> None:
    """Load a simple KEY=VALUE .env file without extra dependencies."""
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                if not key or key in os.environ:
                    continue
                os.environ[key] = value.strip().strip('"').strip("'")
    except OSError:
        pass


_load_dotenv()


def _int(name: str, default: int, low: int | None = None, high: int | None = None) -> int:
    raw = os.getenv(name, "").strip()
    try:
        value = int(raw) if raw else default
    except ValueError:
        value = default
    if low is not None:
        value = max(low, value)
    if high is not None:
        value = min(high, value)
    return value


def _bool(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    host: str = "0.0.0.0"
    port: int = 5002
    debug: bool = False
    captcha_ttl: int = 600
    captcha_capacity: int = 200
    connect_timeout: float = 10.0
    read_timeout: float = 30.0
    allow_origin: str = "*"
    portal_base: str = PORTAL_BASE
    user_agent: str = USER_AGENT

    @property
    def portal_timeout(self) -> tuple[float, float]:
        return (self.connect_timeout, self.read_timeout)

    @property
    def public_base(self) -> str | None:
        """Optional public URL used when building absolute captcha links."""
        return os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/") or None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        host=os.getenv("HOST", "0.0.0.0").strip() or "0.0.0.0",
        port=_int("PORT", 5002, 1, 65535),
        debug=_bool("DEBUG"),
        captcha_ttl=_int("CAPTCHA_TTL", 600, 60, 3600),
        captcha_capacity=_int("CAPTCHA_CAPACITY", 200, 10, 5000),
        connect_timeout=float(os.getenv("CONNECT_TIMEOUT", "10") or 10),
        read_timeout=float(os.getenv("READ_TIMEOUT", "30") or 30),
        allow_origin=os.getenv("ALLOW_ORIGIN", "*").strip() or "*",
        portal_base=os.getenv("PORTAL_BASE", PORTAL_BASE).strip().rstrip("/"),
        user_agent=os.getenv("USER_AGENT", USER_AGENT).strip() or USER_AGENT,
    )
