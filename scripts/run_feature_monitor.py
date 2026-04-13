#!/usr/bin/env python3
"""
Elastic Feature Monitor — CLI entry point

Usage:
    python scripts/run_feature_monitor.py              # fetch + curate last 14 days
    python scripts/run_feature_monitor.py --days 7    # shorter lookback
    python scripts/run_feature_monitor.py --dry-run   # fetch only, no LLM, no save

Run daily via GitHub Actions or local cron:
    0 8 * * * cd /path/to/vulcan && python scripts/run_feature_monitor.py >> logs/monitor.log 2>&1
"""

import argparse
import logging
import sys
from pathlib import Path

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("feature_monitor")


def main():
    parser = argparse.ArgumentParser(description="Elastic Feature Monitor")
    parser.add_argument("--days",    type=int, default=14, help="Lookback window in days (default: 14)")
    parser.add_argument("--dry-run", action="store_true",  help="Fetch only — skip LLM curation and save")
    parser.add_argument("--output",  type=str, default=None, help="Override output date string (YYYY-MM-DD)")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Elastic Feature Monitor starting")
    logger.info(f"Lookback: {args.days} days | Dry run: {args.dry_run}")
    logger.info("=" * 60)

    # Step 1: Fetch from all sources
    from src.services.feature_monitor import fetch_all
    logger.info("Fetching from Elastic Blog, GitHub Releases, What's New page...")
    raw_items = fetch_all(lookback_days=args.days)
    logger.info(f"Fetched {len(raw_items)} raw items")

    if not raw_items:
        logger.info("No new items found. Exiting.")
        return

    if args.dry_run:
        logger.info("Dry run — skipping LLM curation")
        for item in raw_items:
            logger.info(f"  [{item['source']}] {item['title'][:80]}")
        return

    # Step 2: Curate with LLM
    from src.services.feature_curator import FeatureCurator

    def progress(msg: str):
        logger.info(msg)

    curator = FeatureCurator()
    result = curator.curate(raw_items, progress_callback=progress)

    # Step 3: Save
    path = curator.save(result, date_str=args.output)
    logger.info(f"Saved {result['item_count']} curated features → {path}")

    # Step 4: Summary
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info(f"  Raw items fetched : {len(raw_items)}")
    logger.info(f"  Curated (score≥5) : {result['item_count']}")
    high = sum(1 for f in result["features"] if f.get("demo_ability") == "high")
    logger.info(f"  High demo-ability : {high}")
    logger.info("=" * 60)

    for feat in result["features"][:5]:
        score = feat.get("sa_relevance_score", "?")
        ability = feat.get("demo_ability", "?")
        logger.info(f"  [{score}/10 | {ability}] {feat['title'][:70]}")

    logger.info("Done.")


if __name__ == "__main__":
    main()
