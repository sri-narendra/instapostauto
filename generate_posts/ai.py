"""AI-backed design specification generation."""

import json
import random
import re
import time

import certifi
import requests

from .config import MISTRAL_API_KEY, OUTPUT_DIR
from .themes import DESIGN_SYSTEMS, LAYOUTS

COLOR_KEYWORDS = {
    "red", "blue", "green", "yellow", "orange", "purple", "violet",
    "pink", "black", "white", "gray", "grey", "gold", "silver",
    "brown", "beige", "cream", "cyan", "magenta", "teal", "navy",
    "saffron", "tricolor", "tiranga", "chakra", "monochrome",
    "pastel", "neon", "dark", "light",
}

THEME_POOL = [
    "cyberpunk", "luxury", "minimal", "streetwear", "editorial", "sci-fi",
    "vapor", "brutalist", "neon-noir", "arctic", "inferno", "jade", "midnight",
]

STATE_PATH = f"{OUTPUT_DIR}/.palette_state.json"

SYSTEM_PROMPT = """
You are an elite creative director and poster designer with 20 years of experience
in high-end brand identity, editorial design, and contemporary art direction.

Your task: Given any user prompt, generate a complete high-fidelity Instagram carousel post design specification optimized for saves, shares, and swipe retention.

IMPORTANT: If the user mentions Indian flag, tricolor, saffron, white, green, or chakra,
you MUST use "indian" as the theme and incorporate those colors.

OUTPUT: Respond ONLY with valid JSON. No markdown. No commentary. No backticks.

ALLOWED THEMES (choose the best match for the prompt):
  indian, cyberpunk, luxury, minimal, streetwear, editorial, sci-fi,
  vapor, brutalist, neon-noir, arctic, inferno, jade, midnight

ALLOWED LAYOUTS:
  hero-left, center-stage, editorial-stack, bottom-heavy,
  split-diagonal, full-bleed, centered, top-right

DENSITY: low | medium | high

MOOD EXAMPLES (pick any evocative mood):
  cinematic, surveillance, luxury, dystopian, futuristic, brutalist,
  fashion, techwear, sacred, haunted, ultraviolet, glacial, molten,
  quantum, post-apocalyptic, dreaming, fractured, serene, patriotic

CRITICAL VIRAL RULES:
- Slide 1 must NOT be generic. It needs FOMO, curiosity, shock, or a clear outcome.
- Every tool slide must describe OUTCOMES, not features.
- Add "why people care" signals (time saved, money saved, who uses it) as short badges.
- Use story flow: Hook -> Why it matters -> Tools -> Surprise tool -> Wrap -> CTA.
- Keep each slide skimmable in 1-2 seconds. Short lines, no paragraphs.

SLIDE TITLES should be 2–7 words, punchy, uppercase-friendly.
SLIDE SUBTITLES should be short, outcome-driven, and readable on mobile.
Each slide may include:
- microhook: one short line under the title (adds urgency/value)
- badges: 1-3 tiny labels like "Saves 5+ hrs weekly", "Used by creators", "Trending in startups"

Generate the following JSON schema EXACTLY:

{
  "theme":         "string — one of the allowed themes",
  "layout":        "string — one of the allowed layouts",
  "title":         "string — bold, punchy carousel cover title",
  "subtitle":      "string — short tagline/subtitle",
  "slides": [
    {
      "title": "string — slide headline",
      "subtitle": "string — slide supporting line, under 14 words",
      "label": "string — short section label, e.g. HOOK, WHY, TOOL 01, CTA",
      "microhook": "string — optional 1-line subhook under title (max 8 words)",
      "badges": ["string — up to 3 short badges, max 4 words each"]
    }
  ],
  "mood":          "string — one evocative mood word or short phrase",
  "density":       "string — low | medium | high",
  "tag1":          "string — short metadata tag (e.g. SERIES 001)",
  "tag2":          "string — short metadata tag (e.g. CLASSIFIED)",
  "year":          "string — 4-digit year, can be fictional",
  "code":          "string — short alphanumeric code, e.g. NX-7734",
  "composition":   "string — describe the visual composition style in 10 words",
  "color_story":   "string — describe the intended color feel in 8 words",
  "has_circles":   true | false,
  "has_hexgrid":   true | false,
  "has_waveform":  true | false,
  "has_scanlines": true | false,
  "has_diagonal":  true | false,
  "has_glitch":    true | false,
  "has_light_blobs": true | false,
  "has_haze":      true | false,
  "has_vignette":  true | false,
  "has_glassmorphism": true | false
}

Return 7-9 slides unless the prompt clearly asks for another count.

HOOK (slide 1) should be ONE of these proven formats when relevant:
- "These AI Tools Feel Illegal"
- "AI Tools Replacing Entire Teams"
- "AI Tools That Save 10+ Hours Weekly"
- "X Tools Everyone Will Use in 2026"

CTA (final slide) should be ONE of:
- "Save this before everyone finds out"
- "Which one will you try first?"
- "Follow for daily AI tools"
- "Comment 'AI' for part 2"

Include one "surprise tool" that is less obvious (examples: Perplexity, Cursor, Gamma, ElevenLabs, Claude, HeyGen).
"""


MODELS = [
    "mistral-large-latest",
    "mistral-medium-latest",
    "mistral-small-latest",
    "open-mixtral-8x7b",
]


FALLBACK = {
    "theme":        "indian",  # Changed to indian as default for flag prompts
    "layout":       "hero-left",
    "title":        "JAI HIND",
    "subtitle":     "SPIRIT OF THE NATION",
    "slides": [
        {
            "title": "JAI HIND",
            "subtitle": "A bold opening for tricolor pride",
            "label": "HOOK",
            "microhook": "Save this for later",
            "badges": ["High share", "Easy skim"],
        },
        {
            "title": "SAFFRON COURAGE",
            "subtitle": "Energy, sacrifice, and forward motion",
            "label": "SLIDE 02",
            "microhook": "Why it matters",
            "badges": ["Fast read", "Swipe next"],
        },
        {
            "title": "WHITE TRUTH",
            "subtitle": "Clarity, peace, and shared purpose",
            "label": "SLIDE 03",
            "microhook": "Worth saving",
            "badges": ["Simple idea"],
        },
        {
            "title": "GREEN GROWTH",
            "subtitle": "Land, progress, and collective hope",
            "label": "SLIDE 04",
            "microhook": "Used daily",
            "badges": ["Creators", "Students"],
        },
        {
            "title": "ONE NATION",
            "subtitle": "Carry the spirit beyond the frame",
            "label": "FINAL",
            "microhook": "Share with a friend",
            "badges": ["CTA"],
        },
    ],
    "mood":         "patriotic",
    "density":      "high",
    "tag1":         "TIRANGA",
    "tag2":         "REPUBLIC",
    "year":         "2024",
    "code":         "IND-1947",
    "composition":  "diagonal tension, layered depth, asymmetric weight",
    "color_story":  "saffron, white, green, navy blue - tricolor harmony",
    "has_circles":  True,  # For Ashoka Chakra
    "has_hexgrid":  False,
    "has_waveform": True,
    "has_scanlines":False,
    "has_diagonal": True,
    "has_glitch":   False,
    "has_light_blobs": True,
    "has_haze":     True,
    "has_vignette": True,
    "has_glassmorphism": False
}


def _normalise_slides(data: dict) -> None:
    slides = data.get("slides")

    if not isinstance(slides, list) or not slides:
        slides = [
            {
                "title": data.get("title", FALLBACK["title"]),
                "subtitle": data.get("subtitle", FALLBACK["subtitle"]),
                "label": "HOOK",
            },
            *FALLBACK["slides"][1:],
        ]

    clean_slides: list[dict] = []
    for index, slide in enumerate(slides[:8], start=1):
        if not isinstance(slide, dict):
            continue
        raw_badges = slide.get("badges", [])
        if not isinstance(raw_badges, list):
            raw_badges = []
        badges: list[str] = []
        for badge in raw_badges[:3]:
            badge_text = str(badge).strip()
            if badge_text:
                badges.append(badge_text)

        clean_slides.append({
            "title": str(slide.get("title") or data.get("title") or FALLBACK["title"]),
            "subtitle": str(slide.get("subtitle") or data.get("subtitle") or FALLBACK["subtitle"]),
            "label": str(slide.get("label") or f"SLIDE {index:02d}"),
            "microhook": str(slide.get("microhook") or ""),
            "badges": badges,
        })

    if not clean_slides:
        clean_slides = FALLBACK["slides"]

    data["slides"] = clean_slides
    data["title"] = clean_slides[0]["title"]
    data["subtitle"] = clean_slides[0]["subtitle"]

    # Ensure slide 1 always has some microhook/badges to boost retention.
    first = data["slides"][0]
    if not str(first.get("microhook", "")).strip():
        first["microhook"] = "Save this before it goes mainstream"
    if not isinstance(first.get("badges"), list) or not first["badges"]:
        first["badges"] = ["FOMO", "High saves", "Swipe fast"]


def _mentions_specific_colour(user_prompt: str) -> bool:
    words = set(re.findall(r"[a-z]+", user_prompt.lower()))
    return bool(words & COLOR_KEYWORDS)


def _mentions_theme(user_prompt: str) -> bool:
    words = set(re.findall(r"[a-z0-9\\-]+", user_prompt.lower()))
    theme_words = set(DESIGN_SYSTEMS.keys())
    return bool(words & theme_words)


def _is_indian_flag_prompt(user_prompt: str) -> bool:
    prompt = user_prompt.lower()
    flag_terms = ["indian flag", "india flag", "tiranga", "ashoka chakra", "tricolor", "tricolour"]
    return any(term in prompt for term in flag_terms)


def _read_palette_state() -> dict:
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}


def _write_palette_state(theme: str) -> None:
    try:
        import os

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(STATE_PATH, "w", encoding="utf-8") as handle:
            json.dump({"last_theme": theme}, handle)
    except OSError:
        pass


def _rotate_palette(data: dict, user_prompt: str) -> None:
    if _mentions_specific_colour(user_prompt):
        _write_palette_state(data["theme"])
        return
    if _mentions_theme(user_prompt):
        _write_palette_state(data["theme"])
        return

    state = _read_palette_state()
    last_theme = state.get("last_theme")
    candidates = [theme for theme in THEME_POOL if theme != last_theme]

    chosen = random.choice(candidates)
    data["theme"] = chosen
    data["color_story"] = DESIGN_SYSTEMS[chosen].get("color_story", data.get("color_story", "fresh rotating palette"))
    print(f"  [✓] No specific colour requested - rotating palette to '{chosen}'")
    _write_palette_state(chosen)


def generate_design(user_prompt: str = "") -> dict:
    # Check for Indian flag related keywords
    if _is_indian_flag_prompt(user_prompt):
        print("  [✓] Indian flag colors detected - using 'indian' theme")
        indian_fallback = FALLBACK.copy()
        indian_fallback["theme"] = "indian"
        indian_fallback["title"] = "JAI HIND"
        indian_fallback["subtitle"] = "TRICOLOR SPIRIT"
        _normalise_slides(indian_fallback)
        _write_palette_state("indian")
        return indian_fallback

    if not MISTRAL_API_KEY:
        print("[!] No MISTRAL_API_KEY — using fallback design")
        fallback = FALLBACK.copy()
        fallback["slides"] = [slide.copy() for slide in FALLBACK["slides"]]
        _rotate_palette(fallback, user_prompt)
        return fallback

    url     = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type":  "application/json",
    }

    user_message = user_prompt if user_prompt else \
        "Create a random visually striking carousel with a compelling concept."

    for model in MODELS:
        try:
            payload = {
                "model":    model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_message},
                ],
                "temperature":    0.95,
                "max_tokens":     1500,
                "response_format": {"type": "json_object"},
            }
            r = requests.post(
                url, headers=headers, json=payload,
                timeout=60, verify=certifi.where()
            )
            if r.status_code != 200:
                print(f"  [{model}] HTTP {r.status_code}: {r.text[:200]}")
                continue

            raw = r.json()["choices"][0]["message"]["content"]
            raw = re.sub(r"```json|```", "", raw).strip()
            data = json.loads(raw)

            # Validate and sanitise
            if data.get("theme")  not in DESIGN_SYSTEMS: data["theme"]  = FALLBACK["theme"]
            if data.get("layout") not in LAYOUTS:         data["layout"] = FALLBACK["layout"]
            _normalise_slides(data)
            for key in ["tag1","tag2","year","code","composition","color_story",
                        "has_circles","has_hexgrid","has_waveform","has_scanlines",
                        "has_diagonal","has_glitch","has_light_blobs","has_haze",
                        "has_vignette","has_glassmorphism"]:
                if key not in data:
                    data[key] = FALLBACK[key]

            _rotate_palette(data, user_prompt)

            print(f"  [✓] Generated with {model}")
            return data

        except Exception as exc:
            print(f"  [{model}] Error: {exc}")

    print("[!] All models failed — using fallback")
    return FALLBACK

