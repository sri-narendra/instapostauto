from __future__ import annotations

import json
import os
import re
import time
from typing import Any


def load_cache(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}


def save_cache(path: str, cache: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(cache, handle, indent=2)


def load_generated(path: str) -> dict:
    if not os.path.exists(path):
        return {"stories": {}}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {"stories": {}}
    if not isinstance(data, dict):
        return {"stories": {}}
    stories = data.get("stories")
    if not isinstance(stories, dict):
        data["stories"] = {}
    return data


def save_generated(path: str, generated: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(generated, handle, indent=2)


def is_generated(story: dict, generated: dict) -> bool:
    story_id = str(story.get("id", ""))
    return bool(story_id and story_id in generated.get("stories", {}))


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug[:48] or "carousel"


def has_existing_output(story: dict, output_dir: str = "output") -> bool:
    title = str(story.get("title", ""))
    base_slug = _slug(title)
    if not base_slug or not os.path.isdir(output_dir):
        return False

    try:
        names = os.listdir(output_dir)
    except OSError:
        return False

    return any(name == base_slug or name.startswith(f"{base_slug}_") for name in names)


def mark_generated(stories: list[dict[str, Any]], path: str = "get_news/generated_stories.json") -> None:
    generated = load_generated(path)
    generated_stories = generated["stories"]
    for story in stories:
        story_id = str(story.get("id", ""))
        if not story_id:
            continue
        generated_stories[story_id] = {
            "title": story.get("title", ""),
            "url": story.get("url", ""),
            "generated_at": time.time(),
        }
    save_generated(path, generated)
