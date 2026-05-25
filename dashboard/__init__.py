from __future__ import annotations

import json
import os
import time
import threading
import mimetypes
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from pathlib import Path
from collections import defaultdict
from typing import Any

from zoneinfo import ZoneInfo
from flask import Flask, jsonify, request, Response, send_file, render_template

app = Flask(__name__)

BASE = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE / "config"
OUTPUT_DIR = BASE / "output"
NEWS_DIR = BASE / "get_news"

TZ = os.getenv("TIMEZONE", "Asia/Kolkata")

_file_cache: dict[str, tuple[float, Any]] = {}
_last_modified: dict[str, float] = {}
_changed_files: set[str] = set()
_sse_clients: list[Any] = []

_pipeline_running = False
_pipeline_progress: dict[str, Any] = {
    "active": False, "stage": None, "stage_start": None,
    "started_at": None, "error": None, "stages_completed": [],
}

SCHEDULE: dict[str, str] = {
    "monday": "19:30", "tuesday": "19:30", "wednesday": "20:00",
    "thursday": "19:30", "friday": "18:30", "saturday": "11:00", "sunday": "18:00",
}


def _now() -> datetime:
    return datetime.now(ZoneInfo(TZ))


def _load_json(path: Path) -> Any:
    key = str(path.resolve())
    try:
        mtime = path.stat().st_mtime
        if key in _file_cache and _file_cache[key][0] == mtime:
            return _file_cache[key][1]
        raw = path.read_text(encoding="utf-8-sig" if path.name == "config.json" else "utf-8")
        data = json.loads(raw)
        _file_cache[key] = (mtime, data)
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {} if path.suffix == ".json" and "log" not in path.name else []


def _save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    key = str(path.resolve())
    _file_cache[key] = (time.time(), data)


def _load_config() -> dict:
    return _load_json(CONFIG_DIR / "config.json") or {}


def _load_logs() -> list:
    return _load_json(CONFIG_DIR / "logs.json") or []


def _load_music() -> list:
    return _load_json(CONFIG_DIR / "music.json") or []


def _load_generated_stories() -> dict:
    return _load_json(NEWS_DIR / "generated_stories.json") or {"stories": {}}


def _load_palette() -> dict:
    return _load_json(OUTPUT_DIR / ".palette_state.json") or {}


def _get_next_schedule() -> dict | None:
    now = _now()
    current_day_index = now.weekday()
    current_time = now.strftime("%H:%M")
    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for offset in range(7):
        check_day_index = (current_day_index + offset) % 7
        day_name = day_names[check_day_index]
        if day_name in SCHEDULE:
            if offset == 0 and SCHEDULE[day_name] <= current_time:
                continue
            future = now + timedelta(days=offset)
            h, m = SCHEDULE[day_name].split(":")
            future = future.replace(hour=int(h), minute=int(m), second=0, microsecond=0)
            return {"day": day_name, "time": future.isoformat(), "seconds_until": int((future - now).total_seconds())}
    return None


def _get_reel_info() -> dict:
    reel_path = OUTPUT_DIR / "reels" / "reel.mp4"
    if reel_path.exists():
        stat = reel_path.stat()
        return {"exists": True, "size_bytes": stat.st_size, "size_mb": round(stat.st_size / 1024 / 1024, 2),
                "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(), "path": str(reel_path)}
    return {"exists": False}


def _scan_assets() -> list[dict]:
    assets = []
    if OUTPUT_DIR.exists():
        for entry in sorted(OUTPUT_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if entry.name.startswith("."):
                continue
            if entry.is_dir():
                files = list(entry.iterdir()) if entry.exists() else []
                assets.append({"name": entry.name, "type": "dir", "count": len(files), "path": str(entry)})
            elif entry.suffix in (".mp4", ".png", ".jpg", ".wav", ".json"):
                assets.append({"name": entry.name, "type": "file", "ext": entry.suffix,
                               "size_kb": round(entry.stat().st_size / 1024, 1), "path": str(entry)})
    return assets


def _compute_metrics() -> dict:
    logs = _load_logs()
    total_posts = len(logs)
    successful = sum(1 for l in logs if l.get("status") in ("posted", "published", "publishing"))
    failed = sum(1 for l in logs if l.get("status") in ("failed", "error"))
    config = _load_config()
    next_sched = _get_next_schedule()
    return {
        "total_reels": total_posts, "total_published": successful, "failed_posts": failed,
        "success_rate": round(successful / total_posts * 100, 1) if total_posts else 100,
        "queue_size": 0, "avg_render_time": None, "avg_post_time": None, "viral_score_avg": None,
        "next_schedule": next_sched, "schedule_enabled": config.get("schedule_enabled", True),
        "uptime_seconds": None, "last_run": None,
        "post_as_reel": config.get("post_as_reel", True),
        "current_theme": config.get("theme_override") or _load_palette().get("last_theme", "auto"),
        "selected_music": config.get("selected_music", "none"),
    }


def _get_stories() -> list[dict]:
    gen = _load_generated_stories()
    return sorted(
        [{"id": sid, "title": s.get("title", ""), "url": s.get("url", ""),
          "generated_at": s.get("generated_at"), "status": "generated"}
         for sid, s in gen.get("stories", {}).items()],
        key=lambda x: x.get("generated_at", 0), reverse=True,
    )


def _get_error_logs() -> list[dict]:
    return [{"title": l.get("title", ""), "status": l.get("status"),
             "time": l.get("time"), "post_id": l.get("post_id")}
            for l in _load_logs() if l.get("status") in ("failed", "error")]


def _run_pipeline_now():
    global _pipeline_running, _pipeline_progress
    if _pipeline_running:
        return {"ok": False, "error": "Pipeline already running"}
    _pipeline_running = True
    _pipeline_progress = {
        "active": True, "stage": "fetch", "stage_start": time.time(),
        "started_at": datetime.now(timezone.utc).isoformat(), "error": None, "stages_completed": [],
    }

    def _run():
        global _pipeline_running, _pipeline_progress
        try:
            from get_news.get_news import get_news, mark_generated
            from generate_posts.generate_posts import create_posts
            from posting.post import post_generated_outputs
            _pipeline_progress["stage"] = "fetch"
            stories = get_news(limit=120, shortlist=15, pick=1, min_score=40, min_comments=8)
            _pipeline_progress["stages_completed"].append("fetch")
            _pipeline_progress["stage"] = "generate"
            _pipeline_progress["stages_completed"].append("generate")
            _pipeline_progress["stage"] = "render"
            outputs = create_posts(stories)
            _pipeline_progress["stages_completed"].append("render")
            if outputs:
                _pipeline_progress["stage"] = "upload"
                result = post_generated_outputs(outputs, caption="Top AI and tech stories from Hacker News.")
                if result:
                    _pipeline_progress["stages_completed"].append("upload")
                else:
                    _pipeline_progress["stage"] = "failed"
                    _pipeline_progress["error"] = "Upload returned no result (see logs)"
                    return
            _pipeline_progress["stage"] = "complete"
        except Exception as exc:
            _pipeline_progress["error"] = str(exc)
            _pipeline_progress["stage"] = "failed"
        finally:
            _pipeline_running = False
            _pipeline_progress["active"] = False

    threading.Thread(target=_run, daemon=True).start()
    return {"ok": True, "message": "Pipeline started"}


def _file_watcher():
    watched = [
        CONFIG_DIR / "config.json", CONFIG_DIR / "logs.json", CONFIG_DIR / "music.json",
        NEWS_DIR / "generated_stories.json", OUTPUT_DIR / ".palette_state.json",
        OUTPUT_DIR / "reels" / "reel.mp4",
    ]
    while True:
        for path in watched:
            if path.exists():
                mtime = path.stat().st_mtime
                key = str(path.resolve())
                if key in _last_modified and _last_modified[key] != mtime:
                    _changed_files.add(key)
                    _file_cache.pop(key, None)
                _last_modified[key] = mtime
        time.sleep(2)


def _sse_broadcast():
    while True:
        data = _collect_all_data()
        data["changed_files"] = list(_changed_files)
        _changed_files.clear()
        payload = f"data: {json.dumps(data)}\n\n"
        dead = []
        for client in _sse_clients:
            try:
                client(payload)
            except Exception:
                dead.append(client)
        for d in dead:
            _sse_clients.remove(d)
        time.sleep(5)


def _collect_all_data() -> dict:
    return {
        "metrics": _compute_metrics(),
        "pipeline": {"stages": ["fetch", "filter", "score", "generate", "render", "upload"], **_pipeline_progress},
        "schedule": {"current_time": _now().isoformat(), "timezone": TZ, "schedule": SCHEDULE, "next": _get_next_schedule()},
        "stories": _get_stories(), "reel": _get_reel_info(), "posts": _load_logs(),
        "errors": _get_error_logs(), "assets": _scan_assets(),
        "config": _load_config(), "music": _load_music(), "palette": _load_palette(),
    }


threading.Thread(target=_file_watcher, daemon=True).start()
threading.Thread(target=_sse_broadcast, daemon=True).start()


@app.route("/")
def index():
    themes = ["indian", "cyberpunk", "luxury", "minimal", "streetwear", "editorial",
              "sci-fi", "vapor", "brutalist", "neon-noir", "arctic", "inferno", "jade", "midnight"]
    layouts = ["hero-left", "center-stage", "editorial-stack", "bottom-heavy",
               "split-diagonal", "full-bleed", "centered", "top-right"]
    return render_template("dashboard.html", themes=themes, layouts=layouts, music=_load_music(),
                           config=_load_config(), tz=TZ, SCHEDULE=SCHEDULE)


@app.route("/api/health")
def api_health():
    return jsonify(_compute_metrics())


@app.route("/api/metrics")
def api_metrics():
    return jsonify(_compute_metrics())


@app.route("/api/pipeline/status")
def api_pipeline_status():
    return jsonify({"stages": ["fetch", "filter", "score", "generate", "render", "upload"], **_pipeline_progress})


@app.route("/api/pipeline/logs")
def api_pipeline_logs():
    return jsonify(_load_logs()[:50])


@app.route("/api/stories")
def api_stories():
    return jsonify(_get_stories())


@app.route("/api/reels")
def api_reels():
    return jsonify(_get_reel_info())


@app.route("/api/posts")
def api_posts():
    return jsonify(_load_logs())


@app.route("/api/schedule")
def api_schedule():
    return jsonify({"current_time": _now().isoformat(), "timezone": TZ, "schedule": SCHEDULE,
                    "next": _get_next_schedule(), "config": _load_config()})


@app.route("/api/errors")
def api_errors():
    return jsonify(_get_error_logs())


@app.route("/api/analytics")
def api_analytics():
    logs = _load_logs()
    posts_by_day: dict[str, int] = defaultdict(int)
    for l in logs:
        d = l.get("time", "")[:10]
        if d:
            posts_by_day[d] += 1
    return jsonify({"posts_per_day": [{"date": k, "count": v} for k, v in sorted(posts_by_day.items())],
                    "total_posts": len(logs)})


@app.route("/api/assets")
def api_assets():
    return jsonify(_scan_assets())


@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    if request.method == "POST":
        data = request.get_json(force=True)
        config = _load_config()
        if isinstance(config, dict):
            for k, v in data.items():
                if k != "_run_now":
                    config[k] = v
            _save_json(CONFIG_DIR / "config.json", config)
        trigger = data.get("_run_now", False)
        return jsonify({"ok": True, "triggered": trigger})
    return jsonify(_load_config())


@app.route("/api/music", methods=["GET", "POST"])
def api_music():
    if request.method == "POST":
        data = request.get_json(force=True)
        music = _load_music()
        if isinstance(music, list) and "id" in data:
            for m in music:
                m["selected"] = m["id"] == data["id"]
            _save_json(CONFIG_DIR / "music.json", music)
            config = _load_config()
            if isinstance(config, dict):
                config["selected_music"] = data["id"]
                _save_json(CONFIG_DIR / "config.json", config)
        return jsonify({"ok": True})
    return jsonify(_load_music())


@app.route("/api/trigger", methods=["POST"])
def api_trigger():
    return jsonify(_run_pipeline_now())


@app.route("/api/pause", methods=["POST"])
def api_pause():
    config = _load_config()
    if isinstance(config, dict):
        config["schedule_enabled"] = False
        _save_json(CONFIG_DIR / "config.json", config)
    return jsonify({"ok": True, "paused": True})


@app.route("/api/resume", methods=["POST"])
def api_resume():
    config = _load_config()
    if isinstance(config, dict):
        config["schedule_enabled"] = True
        _save_json(CONFIG_DIR / "config.json", config)
    return jsonify({"ok": True, "paused": False})


@app.route("/api/reel/preview")
def api_reel_preview():
    reel_path = OUTPUT_DIR / "reels" / "reel.mp4"
    if reel_path.exists():
        return send_file(str(reel_path), mimetype="video/mp4")
    return jsonify({"error": "No reel found"}), 404


@app.route("/api/assets/download")
def api_asset_download():
    asset_path = request.args.get("path", "")
    full_path = (BASE / asset_path).resolve()
    if not str(full_path).startswith(str(BASE.resolve())):
        return jsonify({"error": "Invalid path"}), 403
    if full_path.exists() and full_path.is_file():
        mime, _ = mimetypes.guess_type(str(full_path))
        return send_file(str(full_path), mimetype=mime or "application/octet-stream")
    return jsonify({"error": "Not found"}), 404


@app.route("/api/events")
def api_events():
    def stream():
        queue: list[str] = []

        def send(data: str):
            queue.append(data)

        _sse_clients.append(send)
        try:
            while True:
                if queue:
                    yield queue.pop(0)
                else:
                    yield ": heartbeat\n\n"
                time.sleep(3)
        except GeneratorExit:
            if send in _sse_clients:
                _sse_clients.remove(send)

    return Response(stream(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache", "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*", "X-Accel-Buffering": "no",
    })


def run(host="0.0.0.0", port=None, debug=False):
    if port is None:
        port = int(os.getenv("PORT", "5001"))
    app.run(host=host, port=port, debug=debug, threaded=True)
