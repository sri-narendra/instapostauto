from __future__ import annotations

import json
import os
import re
from typing import Any

import certifi
import requests


def _get_mistral_api_key() -> str | None:
    return os.getenv("MISTRAL_API_KEY")


def pick_instagram_viral(
    stories: list[dict[str, Any]],
    count: int = 1,
) -> list[int]:
    """
    Returns a list of selected story indices (into `stories`).
    Falls back to [0..count-1] if the API is not available.
    """

    api_key = _get_mistral_api_key()
    if not api_key:
        return list(range(min(count, len(stories))))

    payload_stories = []
    for story in stories:
        payload_stories.append(
            {
                "id": story.get("id"),
                "title": story.get("title", ""),
                "url": story.get("url", ""),
                "score": story.get("score", 0),
                "comments": story.get("descendants", 0),
            }
        )

    system = (
        "You are a social media strategist for an Instagram tech page.\n"
        "Goal: pick stories most likely to go viral on Instagram.\n"
        "Prefer: clear novelty, practical tools, strong hook potential, simple narrative, mass appeal.\n"
        "Avoid: niche academic debates, politics, low-context rants.\n"
        "Return STRICT JSON only."
    )

    user = {
        "count": count,
        "stories": payload_stories,
        "task": (
            "Select the best stories for viral Instagram carousel posts. "
            "Return JSON: {\"pick\":[<indices>],\"reasons\":[\"...\"]} "
            "Indices refer to the provided list order."
        ),
    }

    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": "mistral-large-latest",
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(user)}],
        "temperature": 0.3,
        "max_tokens": 600,
        "response_format": {"type": "json_object"},
    }

    try:
        response = requests.post(url, headers=headers, json=body, timeout=60, verify=certifi.where())
        if response.status_code != 200:
            return list(range(min(count, len(stories))))
        raw = response.json()["choices"][0]["message"]["content"]
        raw = re.sub(r"```json|```", "", raw).strip()
        data = json.loads(raw)
        picks = data.get("pick", [])
        if not isinstance(picks, list):
            return list(range(min(count, len(stories))))
        clean: list[int] = []
        for item in picks:
            try:
                idx = int(item)
            except Exception:
                continue
            if 0 <= idx < len(stories) and idx not in clean:
                clean.append(idx)
        if not clean:
            return list(range(min(count, len(stories))))
        return clean[:count]
    except Exception:
        return list(range(min(count, len(stories))))
