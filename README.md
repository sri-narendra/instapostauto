# InstaPostAuto

Automated Instagram carousel generator that turns Hacker News stories into polished, art-directed carousel posts and publishes them to Instagram via direct login.

Pipeline: **HN top stories → viral scoring → Mistral pick → carousel design (Mistral) → HTML rendering → PNG export → Instagram upload**

## Setup

```powershell
pip install -r requirements.txt
playwright install chromium
```

Create `.env`:

```env
MISTRAL_API_KEY=your_key_here
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password
```

`MISTRAL_API_KEY` is required for AI-powered design generation. If missing, the engine uses a local fallback design.

Instagram credentials are optional — only needed for auto-publishing to Instagram.

## Usage

```powershell
python main.py
```

By default this generates carousel PNGs from HN stories and posts them to Instagram if credentials are configured.

To generate carousels without posting, remove the `post_generated_outputs` call from `main.py`.

Each run:
1. Fetches HN top stories (configurable limit)
2. Skips stories already generated in `output/` or `get_news/generated_stories.json`
3. Scores and shortlists likely-viral tech/AI stories using keyword heuristics
4. Uses Mistral (if `MISTRAL_API_KEY` is set) to pick the most Instagram-viral topics
5. Generates a carousel per selected story — Mistral creates the JSON spec, Jinja2 builds HTML slides, Playwright renders high-DPI PNGs
6. Outputs land in `output/<story_title>/slide_01.png` etc.

When no specific colour is mentioned, the engine rotates to a different theme palette each run. The last palette is tracked in `output/.palette_state.json`.

## What The Files Do

### Entry Point

- `main.py` — gets news from HN → creates carousel PNGs → optionally posts to Instagram.

### `generate_posts/` — Carousel Generation Engine

- `posts.py` — controller: builds the Instagram prompt from a story, calls the generation pipeline.
- `ai.py` — calls Mistral API with a system prompt that produces a structured carousel JSON spec (theme, layout, slides, badges, mood, effects toggles). Falls back to static designs if the API fails.
- `builder.py` — combines one slide's design spec, theme colors, layout, typography, SVG decorations, and HTML template into a single slide HTML page.
- `template.py` — Jinja2 HTML/CSS template for a single 1080×1350 slide. The visible carousel composition.
- `themes.py` — 13 theme palettes (cyberpunk, luxury, minimal, streetwear, jade, midnight, etc.) with colors, fonts, layout presets, and color stories.
- `color.py` — converts hex theme values to OKLCH CSS colors; tints pure black/white to avoid flat defaults.
- `svg_elements.py` — procedural SVG generators: dot grids, circles, HUD lines, crosshairs, barcodes, hex grids, waveforms, glitch effects, light blobs, haze, noise/grain filters, scanlines, vignettes.
- `typography.py` — title font sizing, multi-line wrapping with `<wbr>`, line-height per style.
- `renderer.py` — creates output run folders and renders every slide HTML to PNG using Playwright (Chromium, 2x DPI).
- `config.py` — loads `.env`, exposes `WIDTH` (1080), `HEIGHT` (1350), `OUTPUT_DIR`, `MISTRAL_API_KEY`.

### `get_news/` — Hacker News Ingestion

- `get_news.py` — orchestrator: fetches HN top stories, filters candidates, scores virality, shortlists, picks with Mistral, enriches with scraped web details.
- `fetcher.py` — raw HN Firebase API calls (`/v0/topstories.json`, `/v0/item/{id}.json`).
- `filters.py` — keyword-based candidate filter and viral scoring heuristic (score × weight, keyword boosts, domain boosts, recency bonus, engagement velocity).
- `picker.py` — uses Mistral (if configured) to pick the most Instagram-viral stories from the shortlist; fallback to top-N.
- `scraper.py` — fetches and parses the linked article's HTML for OG metadata, images, and excerpt text to enrich carousel content.
- `cache.py` — JSON-persisted caches: HN story score snapshots (for velocity calc) and generated-stories tracker (to avoid duplicates).

### `posting/` — Instagram Publishing

- `post.py` — wrapper: calls `instapost.py` if credentials are present, handles errors gracefully.
- `instapost.py` — Instagram direct login client using instagrapi: logs in with username/password, uploads single photos or carousels.

### Design Docs

- `PRODUCT.md` — brand register, users, design principles, anti-references.
- `DESIGN.md` — visual system notes: color, typography, layout, quality bar.

## File Connection Map

```
main.py ──→  get_news/get_news.py  ──→  get_news/fetcher.py  (HN API)
             │                         ├── get_news/filters.py  (scoring)
             │                         ├── get_news/picker.py  (Mistral selection)
             │                         ├── get_news/scraper.py  (OG metadata)
             │                         └── get_news/cache.py  (JSON persistence)
             │
             ├─→  generate_posts/posts.py  ──→  generate_posts/ai.py  (Mistral spec)
             │                                   ├── generate_posts/builder.py  (HTML assembly)
             │                                   │   ├── generate_posts/template.py  (Jinja2 template)
             │                                   │   ├── generate_posts/themes.py  (palettes)
             │                                   │   ├── generate_posts/color.py  (OKLCH)
             │                                   │   ├── generate_posts/svg_elements.py  (SVG decor)
             │                                   │   └── generate_posts/typography.py  (text sizing)
             │                                   └── generate_posts/renderer.py  (Playwright PNG)
             │
             └─→  posting/post.py  ──→  posting/instapost.py  (instagrapi direct login)
```

## Design

The template follows restrained art-direction: one strong typographic idea per slide, OKLCH-normalized color, no gradient text, no decorative glassmorphism. Each theme provides Google Font pairings and procedural SVG atmosphere (dot grids, circles, HUD lines, barcodes, geometry). 13 themes cycle automatically when no colour is specified.

## Development Checks

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m compileall main.py generate_posts get_news posting
```
