from __future__ import annotations

import time
from typing import Any

from .cache import (
    has_existing_output,
    is_generated,
    load_cache,
    load_generated,
    mark_generated,
    save_cache,
    save_generated,
)
from .fetcher import get_item, get_top_story_ids, safe_sleep
from .filters import ViralConfig, is_candidate, viral_score
from .picker import pick_instagram_viral
from .scraper import enrich_stories


def get_news(
    limit: int,
    shortlist: int,
    pick: int,
    min_score: int,
    min_comments: int,
    skip_generated: bool = True,
    scrape_details: bool = True,
) -> list[dict[str, Any]]:
    start_time = time.time()
    config = ViralConfig(min_score=min_score, min_comments=min_comments)
    cache = load_cache(config.cache_file)
    generated = load_generated(config.generated_file)

    print(f"Fetching HN top stories (limit={limit})...")
    ids = get_top_story_ids(limit=limit)
    scored: list[dict[str, Any]] = []
    checked = 0
    candidates = 0
    skipped_generated = 0
    errors = 0

    def status_line(final: bool = False) -> None:
        elapsed = int(time.time() - start_time)
        line = (
            f"Scanning HN: {checked}/{len(ids)} checked | "
            f"{candidates} candidates | {len(scored)} scored | "
            f"{skipped_generated} already used | "
            f"{errors} errors | {elapsed}s elapsed"
        )
        if final:
            print(line)
        else:
            print("\r" + line.ljust(110), end="", flush=True)

    for index, story_id in enumerate(ids, start=1):
        checked = index
        story = get_item(story_id)
        if not story:
            errors += 1
            if index % 10 == 0 or index == 1:
                status_line()
            continue
        if story.get("type") != "story":
            if index % 10 == 0 or index == 1:
                status_line()
            continue
        if not story.get("title"):
            if index % 10 == 0 or index == 1:
                status_line()
            continue
        if skip_generated and (is_generated(story, generated) or has_existing_output(story)):
            skipped_generated += 1
            if index % 10 == 0 or index == 1:
                status_line()
            continue
        if not is_candidate(story, config):
            if index % 10 == 0 or index == 1:
                status_line()
            continue

        candidates += 1
        story["viral_score"] = viral_score(story, cache)
        scored.append(story)
        safe_sleep(0.05)
        if index % 10 == 0 or index == 1:
            status_line()

    save_cache(config.cache_file, cache)
    print()  # newline after the carriage-return status line

    scored.sort(key=lambda item: float(item.get("viral_score", 0) or 0), reverse=True)
    shortlist_items = scored[: max(1, shortlist)]

    if not shortlist_items:
        return []

    status_line(final=True)
    print(f"Shortlist: taking top {min(shortlist, len(scored))} by heuristic viral score...")
    picks = pick_instagram_viral(shortlist_items, count=pick)
    selected = [shortlist_items[idx] for idx in picks if 0 <= idx < len(shortlist_items)]
    if scrape_details:
        print(f"Scraping extra web details for {len(selected)} selected stories...")
        enrich_stories(selected)
    return selected
