from __future__ import annotations

import time
from dataclasses import dataclass

KEYWORDS = [
    "ai",
    "agent",
    "gpt",
    "llm",
    "openai",
    "claude",
    "anthropic",
    "mistral",
    "gemini",
    "cursor",
    "copilot",
    "coding",
    "show hn",
    "github",
    "startup",
    "tool",
    "api",
]

VIRAL_WORDS = [
    "replace",
    "faster",
    "cheaper",
    "open-source",
    "opensource",
    "free",
    "launch",
    "released",
    "beats",
    "insane",
    "crazy",
]

TRUSTED_DOMAINS = [
    "github.com",
    "openai.com",
    "anthropic.com",
    "vercel.com",
    "huggingface.co",
]


@dataclass(frozen=True)
class ViralConfig:
    min_score: int = 40
    min_comments: int = 8
    cache_file: str = "get_news/hn_cache.json"
    generated_file: str = "get_news/generated_stories.json"


def _contains_keyword(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def _age_minutes(unix_time: int | float) -> float:
    return (time.time() - float(unix_time)) / 60.0


def _velocity(old: float, new: float, minutes: float) -> float:
    if minutes <= 0:
        return 0.0
    return (new - old) / minutes


def is_candidate(story: dict, config: ViralConfig) -> bool:
    title = str(story.get("title", ""))
    score = int(story.get("score", 0) or 0)
    comments = int(story.get("descendants", 0) or 0)

    if score < config.min_score:
        return False
    if comments < config.min_comments:
        return False
    if not _contains_keyword(title, KEYWORDS):
        return False
    return True


def viral_score(story: dict, cache: dict) -> float:
    title = str(story.get("title", "")).lower()
    score = int(story.get("score", 0) or 0)
    comments = int(story.get("descendants", 0) or 0)
    url = str(story.get("url", "") or "")

    story_id = str(story.get("id", ""))
    age_minutes = _age_minutes(int(story.get("time", 0) or 0))

    total = 0.0

    total += score * 1.5
    total += comments * 3.0

    for keyword in KEYWORDS:
        if keyword in title:
            total += 30.0

    for word in VIRAL_WORDS:
        if word in title:
            total += 20.0

    if "show hn" in title:
        total += 100.0

    if "github.com" in url:
        total += 80.0

    for domain in TRUSTED_DOMAINS:
        if domain in url:
            total += 40.0

    if age_minutes < 60:
        total += 120.0
    elif age_minutes < 180:
        total += 80.0
    elif age_minutes < 360:
        total += 40.0

    if story_id and story_id in cache:
        old = cache[story_id]
        old_score = float(old.get("score", 0) or 0)
        old_comments = float(old.get("comments", 0) or 0)
        old_time = float(old.get("timestamp", time.time()) or time.time())
        elapsed = (time.time() - old_time) / 60.0
        total += _velocity(old_score, score, elapsed) * 25.0
        total += _velocity(old_comments, comments, elapsed) * 40.0

    if story_id:
        cache[story_id] = {"score": score, "comments": comments, "timestamp": time.time()}

    return round(total, 2)
