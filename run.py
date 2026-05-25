import os, sys, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import server as scheduler
    t = threading.Thread(target=scheduler.main, daemon=True)
    t.start()
    print("[run] Scheduler started in background")
except Exception as exc:
    print(f"[run] Scheduler not available: {exc}")

from dashboard import run
run()
