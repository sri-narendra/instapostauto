from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlparse

import certifi
import requests

MAX_HTML_BYTES = 1_500_000
MAX_EXCERPT_CHARS = 900
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0 Safari/537.36"
)


class _PageDetailsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.meta: dict[str, str] = {}
        self.images: list[str] = []
        self._in_title = False
        self._skip_depth = 0
        self._text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {name.lower(): value or "" for name, value in attrs}
        tag = tag.lower()

        if tag == "title":
            self._in_title = True
            return

        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
            return

        if tag == "meta":
            key = (attrs_dict.get("property") or attrs_dict.get("name") or "").strip().lower()
            content = attrs_dict.get("content", "").strip()
            if key and content:
                self.meta[key] = html.unescape(content)
            return

        if tag == "img":
            src = attrs_dict.get("src") or attrs_dict.get("data-src") or attrs_dict.get("data-original")
            if src:
                self.images.append(src.strip())

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self._in_title = False
        elif tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        if self._in_title:
            self.title += text + " "
            return
        if self._skip_depth:
            return
        if len(text) >= 35:
            self._text_parts.append(text)

    @property
    def text_excerpt(self) -> str:
        text = " ".join(self._text_parts)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:MAX_EXCERPT_CHARS].strip()


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()


def _best_meta(meta: dict[str, str], keys: list[str]) -> str:
    for key in keys:
        value = _clean(meta.get(key, ""))
        if value:
            return value
    return ""


def _absolute_url(base_url: str, value: str) -> str:
    if not value:
        return ""
    return urljoin(base_url, value)


def _is_probable_image_url(value: str) -> bool:
    path = urlparse(value).path.lower()
    return path.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"))


def scrape_story_details(url: str, timeout: int = 12) -> dict[str, Any]:
    if not url:
        return {}

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "User-Agent": USER_AGENT,
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout, verify=certifi.where(), allow_redirects=True)
        response.raise_for_status()
    except requests.RequestException:
        return {}

    content_type = response.headers.get("content-type", "").lower()
    if "text/html" not in content_type and "application/xhtml" not in content_type:
        image_url = response.url if content_type.startswith("image/") else ""
        return {
            "source_url": response.url,
            "content_type": content_type,
            "image_url": image_url,
            "images": [image_url] if image_url else [],
        }

    parser = _PageDetailsParser()
    try:
        html_text = response.content[:MAX_HTML_BYTES].decode(response.encoding or "utf-8", errors="replace")
        parser.feed(html_text)
    except Exception:
        return {}

    title = _best_meta(parser.meta, ["og:title", "twitter:title"]) or _clean(parser.title)
    description = _best_meta(
        parser.meta,
        ["og:description", "twitter:description", "description"],
    )
    site_name = _best_meta(parser.meta, ["og:site_name", "application-name"])
    image_url = _best_meta(
        parser.meta,
        ["og:image:secure_url", "og:image", "twitter:image", "twitter:image:src"],
    )

    images = []
    if image_url:
        images.append(_absolute_url(response.url, image_url))
    for src in parser.images:
        absolute = _absolute_url(response.url, src)
        if absolute and absolute not in images and _is_probable_image_url(absolute):
            images.append(absolute)
        if len(images) >= 5:
            break

    return {
        "source_url": response.url,
        "title": title,
        "description": description,
        "site_name": site_name,
        "image_url": images[0] if images else "",
        "images": images,
        "excerpt": parser.text_excerpt,
        "content_type": content_type,
    }


def enrich_story(story: dict[str, Any]) -> dict[str, Any]:
    url = str(story.get("url", "") or "").strip()
    if not url:
        return story
    details = scrape_story_details(url)
    if details:
        story["scraped_details"] = details
    return story


def enrich_stories(stories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for story in stories:
        enrich_story(story)
    return stories
