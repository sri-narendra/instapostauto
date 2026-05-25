from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

CONFIG_DIR = Path(__file__).parent


def _load(name: str) -> dict | list:
    path = CONFIG_DIR / name
    if not path.exists():
        return {} if name == "config.json" else []
    return json.loads(path.read_text(encoding="utf-8"))


def _save(name: str, data: dict | list) -> None:
    path = CONFIG_DIR / name
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_config() -> dict:
    cfg = _load("config.json")
    return cfg if isinstance(cfg, dict) else {}


def get_music() -> list[dict]:
    m = _load("music.json")
    return m if isinstance(m, list) else []


def get_selected_music() -> dict | None:
    for m in get_music():
        if m.get("selected"):
            return m
    return None


def get_logs() -> list[dict]:
    l = _load("logs.json")
    return l if isinstance(l, list) else []


def append_log(entry: dict) -> None:
    logs = get_logs()
    entry["time"] = datetime.now(timezone.utc).isoformat()
    logs.insert(0, entry)
    _save("logs.json", logs[:100])
