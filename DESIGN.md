# Design

## Overview

TextToPost produces prompt-driven 1080 by 1350 carousel slides for social feeds. The visual system is brand-register first: the carousel itself is the product.

## Color

Colors are stored per theme in `posts_generator/themes.py` and normalized through `posts_generator/color.py` before rendering. Hex theme values are converted to OKLCH CSS colors; pure black and pure white are tinted so the output avoids flat defaults.

## Typography

Each theme supplies its own Google Font pairing. The slide template uses oversized display type, short uppercase labels, compact metadata, and a slide counter. Each slide title is the dominant object.

## Layout

Layouts live in `posts_generator/themes.py`. The active template uses a disciplined poster grid: top accent rule, label/counter row, strong title block, restrained procedural geometry, data panel, and bottom production metadata.

## Components

- Header metadata: slide label, slide count, prompt-derived code, and footer metadata.
- Main content: slide title and slide subtitle.
- Atmosphere layer: SVG-generated dots, circles, lines, barcode, and simple geometry.
- Footer metadata: composition, signal, and engine label.

## Motion

The current renderer outputs static PNGs. Animation is intentionally avoided in the image path.

## Quality Bar

Outputs should look art-directed at first glance: clear hierarchy, readable text, enough procedural detail to feel premium, and consistent slide-to-slide rhythm.
