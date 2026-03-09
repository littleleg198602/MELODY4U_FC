from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    """Application settings loaded from environment variables."""

    meta_page_id: str
    meta_access_token: str
    default_timezone: str
    posts_file: Path
    images_dir: Path
    graph_api_version: str = "v19.0"


class ConfigError(ValueError):
    """Raised when required configuration is missing."""


def load_config() -> Config:
    load_dotenv()

    root = Path(__file__).resolve().parents[1]
    meta_page_id = os.getenv("META_PAGE_ID", "").strip()
    meta_access_token = os.getenv("META_ACCESS_TOKEN", "").strip()
    default_timezone = os.getenv("DEFAULT_TIMEZONE", "UTC").strip() or "UTC"

    missing: list[str] = []
    if not meta_page_id:
        missing.append("META_PAGE_ID")
    if not meta_access_token:
        missing.append("META_ACCESS_TOKEN")

    if missing:
        missing_list = ", ".join(missing)
        raise ConfigError(
            f"Missing required environment variables: {missing_list}. "
            "Set them in GitHub Secrets or your local .env file."
        )

    return Config(
        meta_page_id=meta_page_id,
        meta_access_token=meta_access_token,
        default_timezone=default_timezone,
        posts_file=root / "data" / "posts.json",
        images_dir=root / "images",
    )
