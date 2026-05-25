"""Procedural SVG decoration generators."""

import math
import random

from .config import HEIGHT, WIDTH

def _rnd(lo, hi):   return random.randint(lo, hi)


def _rnd_f(lo, hi): return random.uniform(lo, hi)


def gen_light_blobs(theme, has_light_blobs, density):
    if not has_light_blobs:
        return ""

    n = {"low": 3, "medium": 6, "high": 10}[density]
    out = []

    for i in range(n):
        cx = _rnd(0, WIDTH)
        cy = _rnd(0, HEIGHT)
        r = _rnd(200, 600)
        opacity = round(_rnd_f(0.15, 0.45), 2)

        # Choose color based on theme
        if i % 3 == 0:
            color = theme["light_blob"]
        elif i % 3 == 1:
            color = theme["glow"]
        else:
            color = theme["glow2"]

        # Create layered light effect
        out.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" opacity="{opacity * 0.7}" filter="url(#cinematicBloom)"/>'
        )
        out.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r * 0.7}" fill="{color}" opacity="{opacity * 0.9}" filter="url(#neonGlow)"/>'
        )
        out.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r * 0.4}" fill="{color}" opacity="{opacity}"/>'
        )

    return "\n".join(out)


def gen_cinematic_haze(theme, has_haze, density):
    if not has_haze:
        return ""

    n = {"low": 2, "medium": 4, "high": 6}[density]
    out = []

    for i in range(n):
        x = _rnd(0, WIDTH)
        y = _rnd(0, HEIGHT)
        width = _rnd(400, 1200)
        height = _rnd(300, 800)
        opacity = round(_rnd_f(0.08, 0.25), 2)

        # Choose haze color
        if i % 2 == 0:
            color = theme["haze"]
        else:
            color = theme["atmosphere"]

        out.append(
            f'<ellipse cx="{x}" cy="{y}" rx="{width}" ry="{height}" fill="{color}" opacity="{opacity}" filter="url(#blurHuge)"/>'
        )

    return "\n".join(out)


def gen_vignette(theme, has_vignette):
    if not has_vignette:
        return ""

    return f"""
    <radialGradient id="vignetteGradient" cx="50%" cy="50%" r="50%" fx="50%" fy="50%">
        <stop offset="0%" stop-color="black" stop-opacity="0"/>
        <stop offset="100%" stop-color="black" stop-opacity="0.6"/>
    </radialGradient>
    <rect x="0" y="0" width="1080" height="1350" fill="url(#vignetteGradient)"/>
    """


def gen_glassmorphism(theme, has_glassmorphism, density):
    if not has_glassmorphism:
        return ""

    n = {"low": 1, "medium": 2, "high": 3}[density]
    out = []

    for i in range(n):
        x = _rnd(100, WIDTH - 300)
        y = _rnd(200, HEIGHT - 400)
        width = _rnd(200, 400)
        height = _rnd(150, 300)
        opacity = round(_rnd_f(0.15, 0.35), 2)

        # Create glass effect
        out.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="12" fill="rgba(255,255,255,0.05)" '
            f'stroke="rgba(255,255,255,0.2)" stroke-width="1" opacity="{opacity}" filter="url(#blurMedium)"/>'
        )
        out.append(
            f'<rect x="{x + 10}" y="{y + 10}" width="{width - 20}" height="{height - 20}" rx="8" '
            f'fill="rgba(255,255,255,0.08)" opacity="{opacity * 0.7}"/>'
        )

    return "\n".join(out)


def gen_hud_lines(theme, density):
    n = {"low": 8, "medium": 18, "high": 35}[density]
    out = []
    for _ in range(n):
        x = _rnd(0, WIDTH);  y = _rnd(0, HEIGHT)
        length = _rnd(80, 500)
        op = round(_rnd_f(0.20, 0.42), 2)
        out.append(
            f'<line x1="{x}" y1="{y}" x2="{x + length}" y2="{y}" '
            f'stroke="{theme["accent"]}" stroke-width="1" opacity="{op}"/>'
        )
    return "\n".join(out)


def gen_crosshairs(theme, density):
    n = {"low": 4, "medium": 10, "high": 18}[density]
    out = []
    for _ in range(n):
        x = _rnd(100, WIDTH-100);  y = _rnd(100, HEIGHT-100)
        s = _rnd(10, 24)
        out.append(
            f'<g opacity="0.45">'
            f'<line x1="{x-s}" y1="{y}" x2="{x+s}" y2="{y}" stroke="{theme["accent"]}" stroke-width="1"/>'
            f'<line x1="{x}" y1="{y-s}" x2="{x}" y2="{y+s}" stroke="{theme["accent"]}" stroke-width="1"/>'
            f'</g>'
        )
    return "\n".join(out)


def gen_dot_grid(theme, density):
    step = {"low": 36, "medium": 28, "high": 22}[density]
    dots = []
    for x in range(0, WIDTH, step):
        for y in range(0, 450, step):
            dots.append(
                f'<circle cx="{x}" cy="{y}" r="1" fill="{theme["accent"]}" opacity="0.16"/>'
            )
    return "\n".join(dots)


def gen_circles(theme, has_circles):
    if not has_circles:
        return ""
    out = []
    for _ in range(_rnd(1, 3)):
        side = random.choice(["left", "right"])
        cx = 980 if side == "right" else 120
        cy = _rnd(400, 900)
        r = _rnd(180, 420)
        out.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{theme["accent"]}" '
            f'stroke-width="2" fill="none" opacity="0.7"/>'
        )
    return "\n".join(out)


def gen_hex_grid(theme, has_hexgrid, density):
    if not has_hexgrid:
        return ""
    size    = 36
    step_x  = size * 2 * math.cos(math.radians(30))
    step_y  = size * 1.5
    hexes   = []
    for row in range(22):
        for col in range(18):
            cx = col * step_x + (size if row % 2 else 0)
            cy = row * step_y
            pts = []
            for angle in range(0, 360, 60):
                rad = math.radians(angle)
                px  = cx + size * math.cos(rad)
                py  = cy + size * math.sin(rad)
                pts.append(f"{px:.1f},{py:.1f}")
            op = round(_rnd_f(0.08, 0.22), 2)
            hexes.append(
                f'<polygon points="{" ".join(pts)}" '
                f'stroke="{theme["accent"]}" stroke-width="1" '
                f'fill="none" opacity="{op}" filter="url(#neonGlow)"/>'
            )
    return "\n".join(hexes)


def gen_waveform(theme, has_waveform):
    if not has_waveform:
        return ""
    bars = []
    x    = 90
    y0   = 1080
    for i in range(90):
        h  = _rnd(12, 120)
        w  = _rnd(6, 14)
        op = round(_rnd_f(0.4, 0.9), 2)
        bars.append(
            f'<rect x="{x}" y="{y0-h}" width="{w}" height="{h}" '
            f'fill="{theme["accent"]}" opacity="{op}" rx="2" filter="url(#neonGlow)"/>'
        )
        x += w + _rnd(2, 8)
        if x > WIDTH - 90:
            break
    return "\n".join(bars)


def gen_barcode(theme):
    bars = []
    x = 90
    for _ in range(32):
        w = _rnd(2, 6);  h = _rnd(36, 56)
        bars.append(
            f'<rect x="{x}" y="1190" width="{w}" height="{h}" '
            f'fill="{theme["text"]}" opacity="0.7"/>'
        )
        x += w + _rnd(2, 5)
    return "\n".join(bars)


def gen_geometry(theme, density):
    n = {"low": 3, "medium": 8, "high": 15}[density]
    out = []
    for _ in range(n):
        x = _rnd(0, WIDTH)
        y = _rnd(0, HEIGHT)
        w = _rnd(20, 140)
        h = _rnd(2, 12)
        out.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
            f'fill="{theme["accent"]}" opacity="0.14"/>'
        )
    return "\n".join(out)


def gen_diagonal(theme, has_diagonal):
    if not has_diagonal:
        return ""
    y_start = _rnd(200, 600)
    return (
        f'<line x1="0" y1="{y_start}" x2="{WIDTH}" y2="{y_start+350}" '
        f'stroke="{theme["accent2"]}" stroke-width="2" opacity="0.25" filter="url(#blurMedium)"/>'
        f'<line x1="0" y1="{y_start+12}" x2="{WIDTH}" y2="{y_start+362}" '
        f'stroke="{theme["accent"]}" stroke-width="1" opacity="0.18" filter="url(#neonGlow)"/>'
    )


def gen_glitch(theme, has_glitch, density):
    if not has_glitch:
        return ""
    n = {"low": 3, "medium": 8, "high": 15}[density]
    out = []
    for _ in range(n):
        y  = _rnd(0, HEIGHT);  h = _rnd(2, 8)
        x  = _rnd(0, 250);     w = _rnd(120, WIDTH - x)
        op = round(_rnd_f(0.12, 0.35), 2)
        dx = _rnd(-40, 40)
        color = random.choice([theme["accent"], theme["accent2"], theme["accent3"]])
        out.append(
            f'<rect x="{x+dx}" y="{y}" width="{w}" height="{h}" '
            f'fill="{color}" opacity="{op}" filter="url(#neonGlow)"/>'
        )
    return "\n".join(out)


def gen_noise_filter(theme):
    return """
    <defs>
      <!-- Cinematic Filters -->
      <filter id="blurHuge" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="20" result="blur"/>
      </filter>

      <filter id="blurMedium" x="-30%" y="-30%" width="160%" height="160%">
        <feGaussianBlur stdDeviation="8" result="blur"/>
      </filter>

      <filter id="blurSmall" x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur stdDeviation="3" result="blur"/>
      </filter>

      <filter id="neonGlow" x="-30%" y="-30%" width="160%" height="160%">
        <feGaussianBlur stdDeviation="4" result="blur"/>
        <feMerge>
          <feMergeNode in="blur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>

      <filter id="cinematicBloom" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="12" result="blur"/>
        <feMerge>
          <feMergeNode in="blur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>

      <filter id="noiseFilm" x="0%" y="0%" width="100%" height="100%">
        <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch" result="noise"/>
        <feColorMatrix type="saturate" values="0" in="noise" result="grayNoise"/>
        <feBlend in="SourceGraphic" in2="grayNoise" mode="overlay" result="blend"/>
        <feComposite in="blend" in2="SourceGraphic" operator="in"/>
      </filter>

      <filter id="grainTexture" x="0%" y="0%" width="100%" height="100%">
        <feTurbulence type="fractalNoise" baseFrequency="0.55" numOctaves="4" stitchTiles="stitch" result="noise"/>
        <feColorMatrix type="saturate" values="0" in="noise" result="grayNoise"/>
        <feBlend in="SourceGraphic" in2="grayNoise" mode="overlay" opacity="0.08"/>
      </filter>

      <!-- Chromatic Aberration -->
      <filter id="chromaticAberration" x="-20%" y="-20%" width="140%" height="140%">
        <feOffset in="SourceGraphic" dx="1.5" dy="0" result="red"/>
        <feOffset in="SourceGraphic" dx="-1.5" dy="0" result="blue"/>
        <feMerge>
          <feMergeNode in="blue"/>
          <feMergeNode in="SourceGraphic"/>
          <feMergeNode in="red"/>
        </feMerge>
      </filter>

      <!-- Vignette -->
      <radialGradient id="vignetteGrad" cx="50%" cy="50%" r="50%" fx="50%" fy="50%">
        <stop offset="0%" stop-color="black" stop-opacity="0"/>
        <stop offset="100%" stop-color="black" stop-opacity="0.4"/>
      </radialGradient>
    </defs>
    <rect x="0" y="0" width="1080" height="1350" fill="transparent" filter="url(#grainTexture)" opacity="0.12"/>
    """


def gen_scanlines(has_scanlines):
    if not has_scanlines:
        return ""
    return (
        '<defs><pattern id="scanpat" x="0" y="0" width="1" height="3" patternUnits="userSpaceOnUse">'
        '<rect x="0" y="0" width="1" height="1.5" fill="black" opacity="0.12"/>'
        '</pattern></defs>'
        '<rect x="0" y="0" width="1080" height="1350" fill="url(#scanpat)"/>'
    )


def gen_corners(theme):
    s  = 50
    sw = "2"
    c  = theme["accent"]
    op = "0.8"
    pairs = [
        (30, 30, s, 0, 0, s),
        (WIDTH-30, 30, -s, 0, 0, s),
        (30, HEIGHT-30, s, 0, 0, -s),
        (WIDTH-30, HEIGHT-30, -s, 0, 0, -s),
    ]
    out = []
    for (x, y, dx1, dy1, dx2, dy2) in pairs:
        out.append(
            f'<g stroke="{c}" stroke-width="{sw}" opacity="{op}" filter="url(#neonGlow)">'
            f'<line x1="{x}" y1="{y}" x2="{x+dx1}" y2="{y+dy1}"/>'
            f'<line x1="{x}" y1="{y}" x2="{x+dx2}" y2="{y+dy2}"/>'
            f'</g>'
        )
    return "\n".join(out)


def gen_metadata_blocks(theme, density):
    n = {"low": 2, "medium": 4, "high": 6}[density]
    out = []

    for i in range(n):
        x = _rnd(100, WIDTH - 250)
        y = _rnd(150, HEIGHT - 150)
        width = _rnd(180, 280)
        height = _rnd(60, 120)
        opacity = round(_rnd_f(0.15, 0.40), 2)

        # Create glassmorphic effect
        out.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" '
            f'fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.2)" stroke-width="1" '
            f'opacity="{opacity}" filter="url(#blurSmall)"/>'
        )
        out.append(
            f'<rect x="{x + 5}" y="{y + 5}" width="{width - 10}" height="{height - 10}" rx="4" '
            f'fill="rgba(255,255,255,0.05)" opacity="{opacity * 0.7}"/>'
        )

    return "\n".join(out)


def gen_ambient_particles(theme, density):
    n = {"low": 50, "medium": 120, "high": 200}[density]
    out = []

    for _ in range(n):
        x = _rnd(0, WIDTH)
        y = _rnd(0, HEIGHT)
        r = _rnd(1, 4)
        op = round(_rnd_f(0.1, 0.4), 2)
        color = random.choice([theme["accent"], theme["accent2"], theme["atmosphere"]])

        out.append(
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}" opacity="{op}" filter="url(#neonGlow)"/>'
        )

    return "\n".join(out)


def gen_energy_rings(theme, density):
    n = {"low": 2, "medium": 4, "high": 6}[density]
    out = []

    for i in range(n):
        cx = _rnd(100, WIDTH - 100)
        cy = _rnd(200, HEIGHT - 200)
        r = _rnd(80, 200)
        op = round(_rnd_f(0.15, 0.45), 2)
        color = random.choice([theme["accent"], theme["accent2"], theme["accent3"]])

        out.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{color}" '
            f'stroke-width="1.5" fill="none" opacity="{op}" filter="url(#cinematicBloom)"/>'
        )
        out.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r * 0.8}" stroke="{color}" '
            f'stroke-width="1" fill="none" opacity="{op * 0.7}" filter="url(#neonGlow)"/>'
        )

    return "\n".join(out)

