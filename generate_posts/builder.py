"""Build HTML carousel slides from design specs."""

import html
from urllib.parse import urlparse

from jinja2 import Template

from .color import normalize_theme
from .config import WIDTH, HEIGHT
from .svg_elements import (
    gen_barcode,
    gen_circles,
    gen_crosshairs,
    gen_dot_grid,
    gen_geometry,
    gen_hud_lines,
)
from .template import HTML_TEMPLATE
from .themes import DESIGN_SYSTEMS, LAYOUTS
from .typography import get_letter_spacing, get_line_height, get_title_size, wrap_title


def _safe_image_url(value: str) -> str:
    url = str(value or "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return html.escape(url, quote=True)


def build_html(
    design: dict,
    slide: dict | None = None,
    slide_index: int = 1,
    slide_total: int = 1,
    source_image_url: str = "",
) -> str:
    theme  = normalize_theme(DESIGN_SYSTEMS[design["theme"]])
    layout = LAYOUTS[design["layout"]]
    d      = design["density"]
    active_slide = slide or {
        "title": design["title"],
        "subtitle": design["subtitle"],
        "label": design.get("tag1", "SLIDE 01"),
        "microhook": "",
        "badges": [],
    }

    title_length = len(active_slide["title"])
    letter_spacing = get_letter_spacing(theme.get("style", "tech"), title_length)
    line_height = get_line_height(theme.get("style", "tech"))

    return Template(HTML_TEMPLATE).render(
        width=WIDTH,  height=HEIGHT,

        bg=theme["bg"],    bg2=theme["bg2"],
        bg_gradient=theme["bg_gradient"],
        atmosphere=theme["atmosphere"],
        accent=theme["accent"],  accent2=theme["accent2"],  accent3=theme["accent3"],
        text=theme["text"],      subtext=theme["subtext"],  dim=theme["dim"],
        glow=theme["glow"],      glow2=theme["glow2"],      glow3=theme["glow3"],
        grid=theme["grid"],

        font_title=theme["font_title"],
        font_body=theme["font_body"],
        font_url=theme["font_url"],

        top=layout["top"],   left=layout["left"],
        title_width=layout["title_width"],
        subtitle_width=layout["subtitle_width"],
        align=layout["align"],

        title_html=wrap_title(active_slide["title"]),
        subtitle=active_slide["subtitle"],
        microhook=str(active_slide.get("microhook") or ""),
        badges=[str(b) for b in (active_slide.get("badges") or []) if str(b).strip()][:3],
        slide_label=active_slide.get("label", f"SLIDE {slide_index:02d}").upper(),
        slide_index=slide_index,
        slide_total=slide_total,
        slide_variant=(slide_index - 1) % 4,
        source_image_url=_safe_image_url(source_image_url),
        progress_percent=round((slide_index / slide_total) * 100, 2) if slide_total else 100,
        title_size=get_title_size(active_slide["title"]),
        letter_spacing=letter_spacing,
        line_height=line_height,

        tag1=design.get("tag1","SERIES 001"),
        tag2=design.get("tag2","CLASSIFIED"),
        year=design.get("year","2047"),
        code=design.get("code","NX-0000"),
        mood=design.get("mood","cinematic").upper(),
        theme_name=design["theme"].upper(),
        density=d.upper(),
        composition=design.get("composition","").upper(),
        color_story=design.get("color_story","").upper(),

        dot_grid=gen_dot_grid(theme, d),
        circles=gen_circles(theme, design.get("has_circles", True)),
        hud_lines=gen_hud_lines(theme, d),
        crosshairs=gen_crosshairs(theme, d),
        barcode=gen_barcode(theme),
        geometry=gen_geometry(theme, d),
    )

