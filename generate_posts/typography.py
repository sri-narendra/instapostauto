"""Typography helpers for carousel layouts."""

import re
import textwrap

def get_title_size(title: str) -> int:
    # Conservative sizing to avoid overlaps in multi-slide carousels.
    clean = re.sub(r"\s+", " ", title.strip())
    n = len(clean)
    max_word = max((len(w) for w in clean.split()), default=0)
    has_colon = ":" in clean

    word_count = len(clean.split())

    # Single long token (tool names) must not overflow the slide.
    if word_count == 1 and max_word >= 9:
        if max_word >= 14:
            return 68
        if max_word >= 12:
            return 78
        return 88

    if max_word >= 14:
        return 68
    if has_colon and n >= 18:
        return 82
    if n <= 10:
        return 118
    if n <= 18:
        return 96
    if n <= 28:
        return 84
    if n <= 40:
        return 74
    return 66


def wrap_title(title: str) -> str:
    clean = re.sub(r"\s+", " ", title.strip())
    # Wrap to 2-3 lines for readability, preferring phrase breaks.
    if len(clean) <= 18:
        return _insert_wbr_for_long_words(clean)

    if ":" in clean:
        head, tail = clean.split(":", 1)
        head = head.strip()
        tail = tail.strip()
        if head and tail:
            # Strong breakpoint for tool labels: "TOOL 04:" / "ELEVENLABS"
            return _insert_wbr_for_long_words(head + ":<br>" + tail)

    width = 14
    if len(clean) >= 38:
        width = 12

    wrapped = textwrap.fill(clean, width=width, break_long_words=False, break_on_hyphens=False)
    return _insert_wbr_for_long_words(wrapped.replace("\n", "<br>"))


def _insert_wbr_for_long_words(text: str) -> str:
    # Prevent ugly mid-word breaks by default; only help extremely long tokens.
    parts = []
    for token in text.split(" "):
        if "<br>" in token:
            parts.append(token)
            continue
        if len(token) >= 14:
            chunk = 10
            rebuilt = ""
            for i in range(0, len(token), chunk):
                rebuilt += token[i : i + chunk]
                if i + chunk < len(token):
                    rebuilt += "<wbr>"
            parts.append(rebuilt)
        elif len(token) >= 8:
            # For common tool names (single tokens), allow a single break opportunity.
            mid = max(4, len(token) // 2)
            parts.append(token[:mid] + "<wbr>" + token[mid:])
        else:
            parts.append(token)
    return " ".join(parts)


def get_letter_spacing(style: str, title_length: int) -> str:
    return "0"


def get_line_height(style: str) -> str:
    if style == "tech": return "0.9"
    if style == "editorial": return "1.0"
    if style == "minimal": return "0.95"
    return "0.88"  # brutal

