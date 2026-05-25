"""HTML template for rendered carousel slides."""

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="{{ font_url }}" rel="stylesheet">
<style>
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    width: {{ width }}px;
    height: {{ height }}px;
    overflow: hidden;
    background:
        radial-gradient(circle at 80% 20%, {{ glow }}, transparent 30%),
        radial-gradient(circle at 20% 72%, {{ glow2 }}, transparent 40%),
        {{ bg_gradient }};
    font-family: {{ font_body }};
}

.poster {
    position: relative;
    width: 100%;
    height: 100%;
    color: {{ text }};
    padding: 76px 90px 88px;
    display: grid;
    grid-template-rows: 150px 1fr 320px;
    grid-template-columns: 1fr;
    gap: 0;
}

.palette-field {
    position: absolute;
    inset: 0;
    z-index: 1;
    background:
        linear-gradient(90deg, transparent 0 58%, {{ atmosphere }} 58% 100%),
        radial-gradient(circle at 74% 48%, {{ glow3 }}, transparent 36%);
    opacity: 0.85;
}

.art-slab {
    position: absolute;
    z-index: 3;
    width: 360px;
    height: 760px;
    top: 248px;
    right: 104px;
    background: {{ accent }};
    opacity: 0.10;
    transform: skewX(-10deg);
}

.poster.variant-1 .art-slab {
    left: 94px;
    right: auto;
    top: 290px;
    height: 680px;
    transform: skewX(8deg);
}

.poster.variant-2 .art-slab {
    width: 620px;
    height: 420px;
    top: 520px;
    right: -120px;
    transform: skewX(0deg);
}

.poster.variant-3 .art-slab {
    width: 260px;
    height: 980px;
    top: 170px;
    right: 420px;
    transform: rotate(17deg);
}

.source-visual {
    width: 100%;
    max-width: 500px;
    height: 230px;
    margin-top: 28px;
    border: 1px solid {{ grid }};
    overflow: hidden;
    background: rgba(0,0,0,0.18);
    box-shadow: 0 22px 54px rgba(0,0,0,0.28), 0 0 28px {{ glow }};
    opacity: 0.88;
    position: relative;
}

.source-visual:before {
    content: "";
    position: absolute;
    inset: 0;
    z-index: 2;
    background:
        linear-gradient(180deg, rgba(0,0,0,0.06), rgba(0,0,0,0.48)),
        linear-gradient(90deg, {{ atmosphere }}, transparent 68%);
    mix-blend-mode: multiply;
}

.source-visual:after {
    content: "";
    position: absolute;
    inset: 0;
    z-index: 3;
    border: 8px solid rgba(255,255,255,0.035);
    pointer-events: none;
}

.source-visual img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    filter: saturate(0.9) contrast(1.08);
}

.big-index {
    position: absolute;
    right: 58px;
    bottom: 118px;
    z-index: 1;
    color: {{ text }};
    font-family: {{ font_title }};
    font-size: 300px;
    font-weight: 900;
    line-height: 1;
    opacity: 0.045;
}

.grid {
    position: absolute;
    inset: 0;
    background-image:
        linear-gradient({{ grid }} 1px, transparent 1px),
        linear-gradient(90deg, {{ grid }} 1px, transparent 1px);
    background-size: 64px 64px;
    opacity: 0.52;
}

.header {
    position: relative;
    z-index: 10;
    display: grid;
    grid-template-columns: 1fr auto;
    grid-template-rows: auto auto;
    align-items: end;
    row-gap: 16px;
}

.accent-line {
    grid-column: 1 / -1;
    height: 4px;
    width: 100%;
    background: {{ accent }};
    box-shadow: 0 0 25px {{ glow }};
}

.slide-label {
    color: {{ accent }};
    font-family: {{ font_body }};
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 0.22em;
    text-transform: uppercase;
}

.slide-count {
    color: {{ dim }};
    font-family: {{ font_body }};
    font-size: 16px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
}

.sysid {
    grid-column: 2;
    grid-row: 1;
    justify-self: end;
    align-self: start;
    color: {{ accent }};
    font-family: {{ font_body }};
    font-size: 18px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
}

.svg-layer {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    z-index: 2;
    opacity: 0.44;
}

.content {
    position: relative;
    z-index: 10;
    display: grid;
    grid-template-columns: minmax(0, 570px) minmax(0, 290px);
    column-gap: 40px;
    align-items: start;
    align-self: start;
    {% if align == "center" %}
    text-align: left;
    {% elif align == "right" %}
    text-align: left;
    {% endif %}
}

.copy-block {
    min-width: 0;
    max-width: 570px;
}

.title {
    color: {{ text }};
    font-family: {{ font_title }};
    font-size: {{ title_size }}px;
    font-weight: 900;
    line-height: {{ line_height }};
    letter-spacing: {{ letter_spacing }};
    text-transform: uppercase;
    max-width: 570px;
    text-shadow: 0 0 22px {{ glow }};
    {% if align == "center" %}
    margin: 0;
    {% endif %}
    overflow-wrap: anywhere;
    word-break: normal;
    hyphens: manual;
}

.subtitle {
    margin-top: 22px;
    color: {{ subtext }};
    font-family: {{ font_body }};
    font-size: 32px;
    font-weight: 700;
    line-height: 1.28;
    letter-spacing: 0.02em;
    text-transform: none;
    max-width: 530px;
    {% if align == "center" %}
    margin-left: 0;
    margin-right: 0;
    {% endif %}
}

.microhook {
    color: {{ text }};
    font-family: {{ font_body }};
    font-size: 23px;
    font-weight: 700;
    line-height: 1.25;
    letter-spacing: 0.02em;
    max-width: 240px;
    overflow-wrap: anywhere;
}

.signal-panel {
    justify-self: stretch;
    margin-top: 18px;
    min-height: 360px;
    max-width: 290px;
    padding: 24px 0 0 28px;
    border-top: 3px solid {{ accent }};
    border-bottom: 1px solid {{ grid }};
    position: relative;
}

.signal-panel:before {
    content: "";
    position: absolute;
    left: 0;
    top: 24px;
    bottom: 28px;
    width: 7px;
    background: {{ accent }};
    box-shadow: 0 0 28px {{ glow }};
}

.signal-kicker {
    color: {{ accent }};
    font-family: {{ font_body }};
    font-size: 14px;
    font-weight: 800;
    letter-spacing: 0.18em;
    text-transform: uppercase;
}

.signal-number {
    margin-top: 18px;
    color: {{ text }};
    font-family: {{ font_title }};
    font-size: 76px;
    font-weight: 900;
    line-height: 0.86;
    opacity: 0.78;
}

.signal-rule {
    width: 112px;
    height: 2px;
    margin: 22px 0 18px;
    background: {{ accent }};
    opacity: 0.72;
}

.badges {
    margin-top: 24px;
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    {% if align == "center" %}
    justify-content: center;
    {% elif align == "right" %}
    justify-content: flex-end;
    {% else %}
    justify-content: flex-start;
    {% endif %}
}

.badge {
    display: inline-flex;
    align-items: center;
    min-height: 34px;
    padding: 0 12px;
    border: 1px solid {{ grid }};
    color: {{ subtext }};
    font-family: {{ font_body }};
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    background: rgba(0,0,0,0.08);
    max-width: 240px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.footer {
    position: relative;
    z-index: 10;
    display: grid;
    grid-template-rows: auto 1fr auto;
    row-gap: 22px;
    align-content: end;
}

.data-panel {
    color: {{ text }};
    font-family: {{ font_body }};
    font-size: 18px;
    line-height: 1.65;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    max-width: 720px;
}

.panel-title {
    color: {{ accent }};
    font-weight: 700;
    margin-bottom: 10px;
}

.panel-line {
    color: {{ subtext }};
}

.slashes {
    color: {{ accent }};
    margin-top: 12px;
    letter-spacing: 0.28em;
}

.footer-meta {
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: end;
    column-gap: 24px;
}

.footer-left {
    color: {{ dim }};
    font-family: {{ font_body }};
    font-size: 16px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
}

.footer-right {
    color: {{ accent }};
    font-family: {{ font_body }};
    font-size: 18px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    text-align: right;
}

.progress-rail {
    height: 2px;
    width: 100%;
    background: {{ grid }};
}

.progress-fill {
    height: 100%;
    width: {{ progress_percent }}%;
    background: {{ accent }};
}

.corner-mark {
    position: absolute;
    z-index: 8;
    width: 68px;
    height: 1px;
    background: {{ accent }};
    opacity: 0.68;
}

.corner-mark.top-left { top: 82px; left: 90px; }
.corner-mark.top-right { top: 82px; right: 90px; }
.corner-mark.bottom-left { bottom: 82px; left: 90px; }
.corner-mark.bottom-right { bottom: 82px; right: 90px; }
</style>
</head>
<body>
<div class="poster variant-{{ slide_variant }}">
    <div class="palette-field"></div>
    <div class="art-slab"></div>
    <div class="big-index">{{ "%02d"|format(slide_index) }}</div>
    <div class="grid"></div>

    <div class="corner-mark top-left"></div>
    <div class="corner-mark top-right"></div>
    <div class="corner-mark bottom-left"></div>
    <div class="corner-mark bottom-right"></div>

    <header class="header">
        <div class="sysid">{{ code }}</div>
        <div class="slide-label">{{ slide_label }}</div>
        <div class="slide-count">{{ "%02d"|format(slide_index) }} / {{ "%02d"|format(slide_total) }}</div>
        <div class="accent-line"></div>
    </header>

    <svg class="svg-layer" viewBox="0 0 {{ width }} {{ height }}" xmlns="http://www.w3.org/2000/svg">
        {{ dot_grid }}
        {{ hud_lines }}
        {{ crosshairs }}
        {{ circles }}
        {{ barcode }}
        {{ geometry }}
    </svg>

    <main class="content">
        <div class="copy-block">
        <div class="title">{{ title_html }}</div>
        <div class="subtitle">{{ subtitle }}</div>
        {% if source_image_url %}
        <figure class="source-visual">
            <img src="{{ source_image_url }}" alt="" referrerpolicy="no-referrer" crossorigin="anonymous" onerror="this.closest('.source-visual').style.display='none'">
        </figure>
        {% endif %}
        </div>
        <aside class="signal-panel">
            <div class="signal-kicker">{{ slide_label }}</div>
            <div class="signal-number">{{ "%02d"|format(slide_index) }}</div>
            <div class="signal-rule"></div>
            {% if microhook %}
            <div class="microhook">{{ microhook }}</div>
            {% else %}
            <div class="microhook">Swipe for the useful part</div>
            {% endif %}
        {% if badges and badges|length > 0 %}
        <div class="badges">
            {% for b in badges %}
            <div class="badge">{{ b }}</div>
            {% endfor %}
        </div>
        {% endif %}
        </aside>
    </main>

    <footer class="footer">
        <section class="data-panel">
            <div class="panel-title">Status: {{ mood }}</div>
            <div class="panel-line">Theme: {{ theme_name }}</div>
            <div class="panel-line">Swipe: next frame</div>
            <div class="slashes">/ / / / / /</div>
        </section>

        <div class="progress-rail"><div class="progress-fill"></div></div>

        <div class="footer-meta">
            <div class="footer-left">NCN · {{ year }} · {{ tag1 }}</div>
            <div class="footer-right">AI Poster Engine · v{{ year }}</div>
        </div>
    </footer>
</div>
</body>
</html>
"""
