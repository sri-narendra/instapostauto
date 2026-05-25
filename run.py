import os, sys, subprocess, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def _ensure_playwright_browsers():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch().close()
        print("[run] Playwright browser OK")
    except Exception:
        print("[run] Installing Playwright browsers...")
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium", "--with-deps"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[run] Playwright browsers installed")

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
