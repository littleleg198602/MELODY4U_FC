from __future__ import annotations

from pathlib import Path

import requests

from src.config import Config


class FacebookPublisher:
    """Publisher for Facebook Page posts using the official Graph API."""

    def __init__(self, config: Config, timeout_seconds: int = 30) -> None:
        self._config = config
        self._timeout_seconds = timeout_seconds

    @property
    def endpoint(self) -> str:
        return (
            f"https://graph.facebook.com/{self._config.graph_api_version}/"
            f"{self._config.meta_page_id}/photos"
        )

    def publish_photo_post(self, caption: str, image_file: Path) -> str:
        with image_file.open("rb") as binary_image:
            response = requests.post(
                self.endpoint,
                data={
                    "caption": caption,
                    "access_token": self._config.meta_access_token,
                    "published": "true",
                },
                files={"source": binary_image},
                timeout=self._timeout_seconds,
            )

        data = response.json() if response.content else {}
        if response.ok and isinstance(data, dict) and data.get("post_id"):
            return str(data["post_id"])

        error_message = "Unknown Meta API error"
        if isinstance(data, dict):
            error_message = str(data.get("error", {}).get("message", error_message))

        raise RuntimeError(
            f"Meta API request failed ({response.status_code}): {error_message}"
        )
