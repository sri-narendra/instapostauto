"""Post generation controller.

This file is the path through the posts_generator package. The detailed work
stays in ai.py, builder.py, and renderer.py.
"""

from __future__ import annotations

from typing import Any

from .ai import generate_design
from .builder import build_html
from .renderer import render_carousel


def _summarize(story: dict[str, Any]) -> str:
    return f'{story.get("title","")} (score={story.get("score",0)}, comments={story.get("descendants",0)})'


def make_instagram_prompt(story: dict[str, Any]) -> str:
    title = str(story.get("title", "")).strip()
    url = str(story.get("url", "")).strip()
    score = int(story.get("score", 0) or 0)
    comments = int(story.get("descendants", 0) or 0)
    scraped = story.get("scraped_details") if isinstance(story.get("scraped_details"), dict) else {}
    scraped_title = str(scraped.get("title", "")).strip()
    scraped_description = str(scraped.get("description", "")).strip()
    scraped_site = str(scraped.get("site_name", "")).strip()
    scraped_image = str(scraped.get("image_url", "")).strip()
    scraped_excerpt = str(scraped.get("excerpt", "")).strip()
    extra_context = ""
    if scraped:
        extra_context = (
            "Extra source context scraped from the linked page:\n"
            f"Source page title: {scraped_title}\n"
            f"Source site: {scraped_site}\n"
            f"Source description: {scraped_description}\n"
            f"Source image URL: {scraped_image}\n"
            f"Source excerpt: {scraped_excerpt}\n"
            "Use these details to make the carousel more specific and accurate.\n"
        )

    return (
        "Create a 7-slide Instagram carousel about this Hacker News story.\n"
        f"Story title: {title}\n"
        f"Story URL: {url}\n"
        f"HN traction: score {score}, comments {comments}\n"
        f"{extra_context}"
        "Carousel structure:\n"
        "1) Hook (bold claim)\n"
        "2) What happened\n"
        "3) Why it matters\n"
        "4) Key detail / feature\n"
        "5) Use cases\n"
        "6) Risks / limitations\n"
        "7) CTA question\n"
        "Tone: punchy, simple, scroll-stopping. Avoid jargon. No emojis."
    )


def _source_image_url(story: dict[str, Any]) -> str:
    scraped = story.get("scraped_details") if isinstance(story.get("scraped_details"), dict) else {}
    image_url = str(scraped.get("image_url", "")).strip()
    if image_url:
        return image_url
    images = scraped.get("images", [])
    if isinstance(images, list):
        for image in images:
            image_url = str(image).strip()
            if image_url:
                return image_url
    return ""


def create_carousel(prompt: str, content_name: str = "", source_image_url: str = "") -> list[str]:
    design = generate_design(prompt)
    slides = design.get("slides", [])
    print(f"Rendering {len(slides)} slides...")
    html_slides = [
        build_html(
            design,
            slide=slide,
            slide_index=index,
            slide_total=len(slides),
            source_image_url=source_image_url,
        )
        for index, slide in enumerate(slides, start=1)
    ]

    return render_carousel(html_slides, design, content_name=content_name or prompt or design["title"])


def create_post(story: dict[str, Any]) -> list[str]:
    print(f"Generating carousel for: {_summarize(story)}")
    prompt = make_instagram_prompt(story)
    content_name = str(story.get("title", "hn_story"))
    return create_carousel(prompt, content_name=content_name, source_image_url=_source_image_url(story))


def create_posts(stories: list[dict[str, Any]]) -> list[str]:
    if not stories:
        print("No viral stories found with current filters.")
        return []

    outputs: list[str] = []
    for story in stories:
        outputs.extend(create_post(story))

    if outputs:
        print("Generated:")
        for path in outputs:
            print(path)

    return outputs
