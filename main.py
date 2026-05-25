import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from get_news.get_news import get_news, mark_generated
from generate_posts.generate_posts import create_posts
from posting.post import post_generated_outputs

DASHBOARD = os.getenv("DASHBOARD", "1") == "1"

if DASHBOARD:
    import threading
    from dashboard import run as start_dashboard
    t = threading.Thread(target=start_dashboard, daemon=True, kwargs={"port": 5001})
    t.start()
    print("[main] Dashboard started at http://localhost:5001")

print("[main] Running pipeline...")
stories = get_news(limit=40, shortlist=15, pick=1, min_score=40, min_comments=8)
outputs = create_posts(stories)
if outputs:
    mark_generated(stories)
    story = stories[0] if stories else {}
    title = story.get("title", "")
    caption = f"New AI and tech stories from Hacker News.\n\n{title}"
    post_generated_outputs(outputs, caption=caption, story_title=title)

if DASHBOARD:
    print("[main] Dashboard available at http://localhost:5001 — keep this process running")
    import time
    while True:
        time.sleep(60)
