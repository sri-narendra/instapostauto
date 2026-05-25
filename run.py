import os, sys, subprocess, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

pw_cache = "/opt/render/.cache/ms-playwright"
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", pw_cache)

def _find_playwright_browser():
    base = os.environ["PLAYWRIGHT_BROWSERS_PATH"]
    for entry in os.listdir(base) if os.path.isdir(base) else []:
        full = os.path.join(base, entry)
        if not os.path.isdir(full):
            continue
        for root, dirs, files in os.walk(full):
            for f in files:
                if f in ("chrome", "chromium", "chrome-headless-shell"):
                    exe = os.path.join(root, f)
                    if os.access(exe, os.X_OK):
                        return exe
    return None

def _ensure_playwright_browsers():
    existing = _find_playwright_browser()
    if existing:
        print(f"[run] Playwright browser at {existing}")
        return
    print("[run] Installing Playwright chromium...")
    subprocess.check_call(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    found = _find_playwright_browser()
    if found:
        print(f"[run] Playwright chromium installed ({found})")
    else:
        print("[run] WARNING: Playwright browser not found after install")

_ensure_playwright_browsers()

try:
    import server as scheduler
    t = threading.Thread(target=scheduler.main, daemon=True)
    t.start()
    print("[run] Scheduler started in background")
except Exception as exc:
    print(f"[run] Scheduler not available: {exc}")

from dashboard import run
run()
