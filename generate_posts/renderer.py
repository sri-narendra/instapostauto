"""Playwright carousel rendering."""

import os
import re

from .config import HEIGHT, OUTPUT_DIR, WIDTH

def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug[:48] or "carousel"


def create_run_dir(content_name: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    base_slug = _slug(content_name)
    run_dir = os.path.join(OUTPUT_DIR, base_slug)
    if not os.path.exists(run_dir):
        os.makedirs(run_dir)
        return run_dir

    index = 2
    while True:
        candidate = os.path.join(OUTPUT_DIR, f"{base_slug}_{index:02d}")
        if not os.path.exists(candidate):
            os.makedirs(candidate)
            return candidate
        index += 1


def render(html: str, design: dict, suffix: str = "", output_dir: str | None = None) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "Playwright is not available in this Python environment. "
            "Install it for the Python you are running: "
            "`python -m pip install playwright` then "
            "`python -m playwright install chromium`."
        ) from exc

    target_dir = output_dir or create_run_dir(design["title"])

    filename  = f"slide{suffix}.png"
    path      = os.path.join(target_dir, filename)
    html_path = os.path.join(target_dir, f"_preview{suffix}.html")

    # Save HTML for debug
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": WIDTH, "height": HEIGHT},
            device_scale_factor=2  # Higher DPI for sharper output
        )
        page = context.new_page()
        page.goto(f"file://{os.path.abspath(html_path)}")

        # Wait for fonts and effects to load
        page.wait_for_timeout(3500)

        # Set higher quality rendering
        page.evaluate('''() => {
            document.body.style.imageRendering = "pixelated";
        }''')

        # Take screenshot with GPU acceleration
        page.screenshot(
            path=path,
            full_page=False,
            type="png",
            animations="disabled"
        )

        browser.close()

    # Clean up tmp html
    try: os.remove(html_path)
    except: pass

    return path


def render_carousel(html_slides: list[str], design: dict, content_name: str = "") -> list[str]:
    run_dir = create_run_dir(content_name or design["title"])
    return [
        render(html, design, suffix=f"_{index:02d}", output_dir=run_dir)
        for index, html in enumerate(html_slides, start=1)
    ]

