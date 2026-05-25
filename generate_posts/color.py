"""Color normalization helpers for CSS output."""

from __future__ import annotations

import math
import re


HEX_RE = re.compile(r"^#([0-9a-fA-F]{6})$")


def css_color(value: str, hue_hint: float = 260.0) -> str:
    """Return OKLCH for hex colors while leaving gradients/rgba intact."""

    match = HEX_RE.match(value.strip())
    if not match:
        return value

    red = int(match.group(1)[0:2], 16) / 255
    green = int(match.group(1)[2:4], 16) / 255
    blue = int(match.group(1)[4:6], 16) / 255

    lightness, chroma, hue = _srgb_to_oklch(red, green, blue)

    if chroma < 0.004:
        chroma = 0.006
        hue = hue_hint

    if lightness > 0.98:
        lightness = 0.965
    elif lightness < 0.02:
        lightness = 0.13

    return f"oklch({lightness * 100:.2f}% {chroma:.4f} {hue:.2f})"


def normalize_theme(theme: dict) -> dict:
    """Return theme values with direct hex colors converted to OKLCH."""

    hue_hint = _theme_hue_hint(theme)
    normalized = dict(theme)

    for key, value in theme.items():
        if isinstance(value, str):
            normalized[key] = css_color(value, hue_hint)

    return normalized


def _theme_hue_hint(theme: dict) -> float:
    for key in ("dominant_hue", "accent", "highlight_hue"):
        value = theme.get(key)
        if isinstance(value, str) and HEX_RE.match(value):
            _, chroma, hue = _hex_to_oklch(value)
            if chroma >= 0.004:
                return hue
    return 260.0


def _hex_to_oklch(value: str) -> tuple[float, float, float]:
    match = HEX_RE.match(value)
    if not match:
        return 0.5, 0.006, 260.0
    red = int(match.group(1)[0:2], 16) / 255
    green = int(match.group(1)[2:4], 16) / 255
    blue = int(match.group(1)[4:6], 16) / 255
    return _srgb_to_oklch(red, green, blue)


def _srgb_to_oklch(red: float, green: float, blue: float) -> tuple[float, float, float]:
    red = _linearize(red)
    green = _linearize(green)
    blue = _linearize(blue)

    l_val = 0.4122214708 * red + 0.5363325363 * green + 0.0514459929 * blue
    m_val = 0.2119034982 * red + 0.6806995451 * green + 0.1073969566 * blue
    s_val = 0.0883024619 * red + 0.2817188376 * green + 0.6299787005 * blue

    l_root = math.copysign(abs(l_val) ** (1 / 3), l_val)
    m_root = math.copysign(abs(m_val) ** (1 / 3), m_val)
    s_root = math.copysign(abs(s_val) ** (1 / 3), s_val)

    ok_l = 0.2104542553 * l_root + 0.7936177850 * m_root - 0.0040720468 * s_root
    ok_a = 1.9779984951 * l_root - 2.4285922050 * m_root + 0.4505937099 * s_root
    ok_b = 0.0259040371 * l_root + 0.7827717662 * m_root - 0.8086757660 * s_root

    chroma = math.sqrt(ok_a * ok_a + ok_b * ok_b)
    hue = math.degrees(math.atan2(ok_b, ok_a))
    if hue < 0:
        hue += 360

    return ok_l, chroma, hue


def _linearize(channel: float) -> float:
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4
