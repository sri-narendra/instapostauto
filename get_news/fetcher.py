from __future__ import annotations

import time
from typing import Any

import requests

HN_BASE_URL = "https://hacker-news.firebaseio.com/v0"


def get_top_story_ids(limit: int = 100) -> list[int]:
    response = requests.get(f"{HN_BASE_URL}/topstories.json", timeout=15)
    response.raise_for_status()
    ids = response.json()
    return [int(story_id) for story_id in ids[:limit]]


def get_item(item_id: int) -> dict[str, Any] | None:
    response = requests.get(f"{HN_BASE_URL}/item/{item_id}.json", timeout=15)
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, dict) else None


def safe_sleep(seconds: float) -> None:
    # Avoids hammering Firebase if a user asks for high limits.
    time.sleep(max(0.0, min(seconds, 0.25)))
