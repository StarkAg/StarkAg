"""
Shared renderer: ASCII text -> animated SVG with a row-by-row typing reveal.

Used by both gen_reactor_ascii.py (geometry-drawn art) and gen_portrait.py
(photo-derived art), so the animation technique lives in exactly one place.

Technique: each row sits behind a clipPath whose rect grows width 0 -> full
(frozen at the end so it stays revealed), with a small cursor block that
moves across and fades out as that row finishes. Pure SMIL, no JS -- GitHub
strips <script> from README-embedded SVGs, so JS wouldn't run there anyway.
"""


def escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_svg(ascii_art, color="#58a6ff", color_dark=None, bg="#0d1117",
               font_size=9, line_h=11, char_w=6.6, dur=0.05, stagger=0.045):
    """
    ascii_art:  newline-joined rows, monospace, already character-ramped.
    color:      glyph + cursor color (also the color used if color_dark is None).
    color_dark: optional second color for @media(prefers-color-scheme:dark) --
                readable on both GitHub's light and dark viewer themes.
    bg:         background fill.
    dur:        seconds to reveal one row.
    stagger:    gap between successive rows' start times.
    """
    lines = ascii_art.split("\n")
    left_pad, top_pad = 10, 14
    height = len(lines) * line_h + 20
    width = max((len(l) for l in lines), default=0) * char_w + 20

    body = []
    for i, row in enumerate(lines):
        y = top_pad + i * line_h
        row_w = len(row) * char_w
        begin = i * stagger
        clip_id = f"c{i}"
        body.append(
            f'<clipPath id="{clip_id}"><rect x="{left_pad}" y="{y - line_h + 2:.1f}" '
            f'height="{line_h}" width="0"><animate attributeName="width" from="0" '
            f'to="{row_w:.1f}" begin="{begin:.3f}s" dur="{dur}s" fill="freeze"/></rect></clipPath>'
            f'<g clip-path="url(#{clip_id})"><text xml:space="preserve" x="{left_pad}" '
            f'y="{y:.1f}" class="glow" font-size="{font_size}">{escape(row)}</text></g>'
            f'<rect y="{y - line_h + 2:.1f}" width="{char_w:.1f}" height="{line_h}" '
            f'class="cursor" opacity="0">'
            f'<animate attributeName="x" from="{left_pad}" to="{left_pad + row_w:.1f}" '
            f'begin="{begin:.3f}s" dur="{dur}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.8" begin="{begin:.3f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{begin + dur:.3f}s"/>'
            f'</rect>'
        )

    dark_rule = (f"@media(prefers-color-scheme:dark){{.glow,.cursor{{fill:{color_dark}}}}}"
                if color_dark else "")

    return f"""<svg width="{width:.0f}" height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}" xmlns="http://www.w3.org/2000/svg">
  <style>
    .glow {{ font-family: 'JetBrains Mono','SF Mono',Menlo,monospace; fill: {color}; }}
    .cursor {{ fill: {color}; }}
    {dark_rule}
  </style>
  <rect width="100%" height="100%" fill="{bg}"/>
  {''.join(body)}
</svg>
"""
