"""24/7 HTTP server with schedule-based posting."""

import json
import os
import threading
import time
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from zoneinfo import ZoneInfo
from typing import Optional

from get_news.get_news import get_news, mark_generated
from generate_posts.generate_posts import create_posts
from posting.post import post_generated_outputs

SCHEDULE: dict[str, str] = {
    "monday":    "19:30",
    "tuesday":   "19:30",
    "wednesday": "20:00",
    "thursday":  "19:30",
    "friday":    "18:30",
    "saturday":  "11:00",
    "sunday":    "18:00",
}

PORT = int(os.getenv("PORT", "8000"))
TZ = os.getenv("TIMEZONE", "Asia/Kolkata")

_last_run_day: Optional[str] = None
_running = False


def _now() -> datetime:
    return datetime.now(ZoneInfo(TZ))


def _current_day_time() -> tuple[str, str]:
    dt = _now()
    return dt.strftime("%A").lower(), dt.strftime("%H:%M")


def _next_schedule() -> Optional[tuple[str, str]]:
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
            hour, minute = SCHEDULE[day_name].split(":")
            future = future.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
            return day_name, future.isoformat()

    return None


def _should_run() -> bool:
    global _last_run_day
    today, now_time = _current_day_time()
    target = SCHEDULE.get(today)
    if target is None:
        return False
    if now_time == target and _last_run_day != today:
        return True
    return False


def _run_pipeline() -> None:
    global _last_run_day, _running
    today = _now().strftime("%A")
    print(f"[{_now().isoformat()}] --- Scheduled run for {today} ---")

    try:
        stories = get_news(limit=120, shortlist=15, pick=1, min_score=40, min_comments=8)
        outputs = create_posts(stories)
        if outputs:
            mark_generated(stories)
            post_generated_outputs(outputs, caption="Top AI and tech stories from Hacker News.")
        _last_run_day = _now().strftime("%Y-%m-%d")
        print(f"[{_now().isoformat()}] Pipeline complete")
    except Exception as exc:
        print(f"[{_now().isoformat()}] Pipeline failed: {exc}")
    finally:
        _running = False


def _scheduler_loop() -> None:
    while True:
        try:
            if not _running and _should_run():
                _running = True
                t = threading.Thread(target=_run_pipeline, daemon=True)
                t.start()
        except Exception as exc:
            print(f"[{_now().isoformat()}] Scheduler error: {exc}")
        time.sleep(30)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            next_run = _next_schedule()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "time": _now().isoformat(),
                "timezone": TZ,
                "last_run": _last_run_day,
                "next_schedule": next_run,
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args) -> None:
        pass


def main() -> None:
    print(f"[{_now().isoformat()}] Starting InstaPostAuto on port {PORT}")
    print(f"[{_now().isoformat()}] Timezone: {TZ}")
    print(f"[{_now().isoformat()}] Schedule: {json.dumps(SCHEDULE, indent=2)}")

    threading.Thread(target=_scheduler_loop, daemon=True).start()

    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
