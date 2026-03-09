from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from src.config import Config
from src.facebook_publisher import FacebookPublisher
from src.post_loader import PostItem, parse_scheduled_datetime

VALID_STATUSES = {"draft", "scheduled", "published", "failed"}
SUPPORTED_PLATFORMS = {"facebook"}


@dataclass
class RunSummary:
    processed: int = 0
    published: int = 0
    failed: int = 0
    skipped: int = 0


class PostScheduler:
    def __init__(self, config: Config, publisher: FacebookPublisher, logger, dry_run: bool = False):
        self.config = config
        self.publisher = publisher
        self.logger = logger
        self.dry_run = dry_run

    def process(self, posts: list[PostItem]) -> RunSummary:
        summary = RunSummary()
        seen_ids: set[str] = set()

        for post in posts:
            summary.processed += 1

            if post.status != "scheduled":
                duplicate_errors = self._validate_identity(post, seen_ids)
                if duplicate_errors:
                    summary.failed += 1
                    post.status = "failed"
                    post.failure_reason = "; ".join(duplicate_errors)
                    self.logger.error("Post '%s' failed validation: %s", post.id, post.failure_reason)
                    continue

                summary.skipped += 1
                self.logger.info("Skipping post '%s' because status is '%s'.", post.id, post.status)
                continue

            validation_errors = self._validate_scheduled_post(post, seen_ids)
            if validation_errors:
                summary.failed += 1
                post.status = "failed"
                post.failure_reason = "; ".join(validation_errors)
                self.logger.error("Post '%s' failed validation: %s", post.id, post.failure_reason)
                continue

            if not self._is_due(post):
                summary.skipped += 1
                self.logger.info("Skipping post '%s' because scheduled time is not due yet.", post.id)
                continue

            if self.dry_run:
                summary.published += 1
                self.logger.info("[DRY RUN] Post '%s' is due and valid. No publish call was made.", post.id)
                continue

            try:
                image_file = self._resolve_image_file(post.image_path)
                remote_post_id = self.publisher.publish_photo_post(post.caption, image_file)
                post.status = "published"
                post.failure_reason = None
                summary.published += 1
                self.logger.info(
                    "Published post '%s' successfully. Meta post_id=%s", post.id, remote_post_id
                )
            except Exception as exc:  # noqa: BLE001
                post.status = "failed"
                post.failure_reason = str(exc)
                summary.failed += 1
                self.logger.exception("Failed to publish post '%s': %s", post.id, exc)

        return summary

    def _validate_identity(self, post: PostItem, seen_ids: set[str]) -> list[str]:
        errors: list[str] = []
        if not post.id:
            errors.append("missing id")
        elif post.id in seen_ids:
            errors.append(f"duplicate id '{post.id}'")
        else:
            seen_ids.add(post.id)

        if post.status not in VALID_STATUSES:
            errors.append(f"invalid status '{post.status}'")

        return errors

    def _validate_scheduled_post(self, post: PostItem, seen_ids: set[str]) -> list[str]:
        errors = self._validate_identity(post, seen_ids)

        if not post.caption:
            errors.append("missing caption")

        if not isinstance(post.platforms, list) or not post.platforms:
            errors.append("platforms must include at least one platform")
        else:
            invalid_platforms = [p for p in post.platforms if p not in SUPPORTED_PLATFORMS]
            if invalid_platforms:
                errors.append(f"unsupported platform(s): {', '.join(invalid_platforms)}")

        tz_value = post.timezone or self.config.default_timezone
        try:
            ZoneInfo(tz_value)
        except ZoneInfoNotFoundError:
            errors.append(f"invalid timezone '{tz_value}'")

        try:
            parse_scheduled_datetime(post.scheduled_time, tz_value)
        except Exception:  # noqa: BLE001
            errors.append(f"invalid scheduled_time '{post.scheduled_time}' (ISO 8601 required)")

        try:
            self._resolve_image_file(post.image_path)
        except ValueError as exc:
            errors.append(str(exc))

        return errors

    def _resolve_image_file(self, image_path: str) -> Path:
        if not image_path:
            raise ValueError("missing image file ''")

        full_path = (self.config.images_dir / image_path).resolve()
        images_root = self.config.images_dir.resolve()

        if images_root not in full_path.parents and full_path != images_root:
            raise ValueError(f"image_path '{image_path}' points outside images directory")

        if not full_path.exists() or not full_path.is_file():
            raise ValueError(f"missing image file '{image_path}'")

        return full_path

    def _is_due(self, post: PostItem) -> bool:
        tz_name = post.timezone or self.config.default_timezone
        scheduled = parse_scheduled_datetime(post.scheduled_time, tz_name)
        now = datetime.now(timezone.utc)
        return scheduled.astimezone(timezone.utc) <= now
