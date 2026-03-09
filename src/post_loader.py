from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


@dataclass
class PostItem:
    id: str
    title: str
    caption: str
    image_path: str
    scheduled_time: str
    timezone: str
    language: str
    status: str
    platforms: list[str]
    failure_reason: str | None = None


def load_posts(posts_file: Path) -> list[PostItem]:
    if not posts_file.exists():
        raise FileNotFoundError(f"Posts file not found: {posts_file}")

    with posts_file.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, list):
        raise ValueError("posts.json must contain a JSON array of post objects")

    posts: list[PostItem] = []
    for idx, raw_post in enumerate(payload, start=1):
        if not isinstance(raw_post, dict):
            raise ValueError(f"Entry #{idx} is invalid: expected object")

        post = PostItem(
            id=str(raw_post.get("id", "")).strip(),
            title=str(raw_post.get("title", "")).strip(),
            caption=str(raw_post.get("caption", "")).strip(),
            image_path=str(raw_post.get("image_path", "")).strip(),
            scheduled_time=str(raw_post.get("scheduled_time", "")).strip(),
            timezone=str(raw_post.get("timezone", "")).strip(),
            language=str(raw_post.get("language", "en")).strip() or "en",
            status=str(raw_post.get("status", "draft")).strip(),
            platforms=list(raw_post.get("platforms", [])),
            failure_reason=(
                str(raw_post.get("failure_reason")).strip()
                if raw_post.get("failure_reason") is not None
                else None
            ),
        )
        posts.append(post)

    return posts


def save_posts(posts_file: Path, posts: list[PostItem]) -> None:
    serialized: list[dict] = []
    for post in posts:
        payload = {
            "id": post.id,
            "title": post.title,
            "caption": post.caption,
            "image_path": post.image_path,
            "scheduled_time": post.scheduled_time,
            "timezone": post.timezone,
            "language": post.language,
            "status": post.status,
            "platforms": post.platforms,
        }
        if post.failure_reason:
            payload["failure_reason"] = post.failure_reason
        serialized.append(payload)

    with posts_file.open("w", encoding="utf-8") as handle:
        json.dump(serialized, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def parse_scheduled_datetime(raw_time: str, timezone: str) -> datetime:
    dt = datetime.fromisoformat(raw_time)
    if dt.tzinfo is not None:
        return dt

    return dt.replace(tzinfo=ZoneInfo(timezone))
