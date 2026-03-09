from __future__ import annotations

import argparse
import sys

from src.config import ConfigError, load_config
from src.facebook_publisher import FacebookPublisher
from src.logger import setup_logger
from src.post_loader import load_posts, save_posts
from src.scheduler import PostScheduler


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Melody4U Facebook autopost scheduler")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and process due posts without calling the Meta API.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logger = setup_logger()

    try:
        config = load_config()
    except ConfigError as exc:
        logger.error(str(exc))
        return 1

    try:
        posts = load_posts(config.posts_file)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unable to load posts: %s", exc)
        return 1

    scheduler = PostScheduler(
        config=config,
        publisher=FacebookPublisher(config),
        logger=logger,
        dry_run=args.dry_run,
    )

    summary = scheduler.process(posts)
    save_posts(config.posts_file, posts)

    logger.info(
        "Run complete | processed=%s published=%s failed=%s skipped=%s dry_run=%s",
        summary.processed,
        summary.published,
        summary.failed,
        summary.skipped,
        args.dry_run,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
