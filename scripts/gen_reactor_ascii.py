#!/usr/bin/env python3
"""
Generate reactor.svg — an original ASCII arc-reactor glow, drawn from
geometry (concentric rings, radial spokes, a bright core), not traced from
any photo or copyrighted artwork. Matches the arc-reactor banner already in
this profile.

Run:
    python3 scripts/gen_reactor_ascii.py

Deterministic: same output every run, so a scheduled workflow run only
commits when this script itself changes.
"""
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

RAMP = " .:-=+*#%@"          # quiet -> loud, same idea as a photo character-ramp
W, H = 88, 40                 # character grid
CX, CY = W / 2, H / 2
ASPECT = 2.0                  # terminal cells are ~2x taller than wide


def field(x, y):
    """Brightness at a grid cell: concentric rings + spokes + core glow."""
    dx = (x - CX) / ASPECT
    dy = y - CY
    r = math.hypot(dx, dy)
    angle = math.atan2(dy, dx)

    core = max(0.0, 1.0 - r / 3.0) ** 1.5

    ring_val = 0.0
    for radius, width, strength in ((8, 0.9, 1.0), (13, 0.7, 0.8), (17.5, 0.55, 0.6)):
        ring_val = max(ring_val, strength * max(0.0, 1.0 - abs(r - radius) / width))

    spokes = 0.0
    n_spokes = 12
    for i in range(n_spokes):
        a = 2 * math.pi * i / n_spokes
        d = abs(((angle - a + math.pi) % (2 * math.pi)) - math.pi)
        spokes = max(spokes, 0.35 * max(0.0, 1.0 - d * 9) * max(0.0, 1.0 - abs(r - 15) / 6))

    outer_fade = max(0.0, 1.0 - max(0.0, r - 19) / 3)

    return min(1.0, max(core, ring_val, spokes)) * outer_fade


def render_ascii():
    rows = []
    for y in range(H):
        row = []
        for x in range(W):
            v = field(x, y)
            idx = min(len(RAMP) - 1, int(v * len(RAMP)))
            row.append(RAMP[idx])
        rows.append("".join(row).rstrip() or " ")
    return "\n".join(rows)


def render_svg(ascii_art):
    """Row-by-row typing reveal, same SMIL technique as the reference profile:
    each row sits behind a clipPath whose rect grows width 0 -> full (frozen
    at the end so it stays revealed), with a small cursor block that moves
    across and fades out as that row finishes. Pure SMIL, no JS -- GitHub
    strips <script> from README-embedded SVGs, so JS wouldn't run there
    anyway."""
    lines = ascii_art.split("\n")
    line_h = 11
    char_w = 6.6
    left_pad = 10
    top_pad = 14
    height = len(lines) * line_h + 20
    width = max(len(l) for l in lines) * char_w + 20

    dur = 0.05          # seconds to reveal one row
    stagger = 0.045      # gap between successive rows' start times

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
            f'y="{y:.1f}" class="glow" font-size="9">{escape(row)}</text></g>'
            f'<rect y="{y - line_h + 2:.1f}" width="{char_w:.1f}" height="{line_h}" '
            f'class="cursor" opacity="0">'
            f'<animate attributeName="x" from="{left_pad}" to="{left_pad + row_w:.1f}" '
            f'begin="{begin:.3f}s" dur="{dur}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.8" begin="{begin:.3f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{begin + dur:.3f}s"/>'
            f'</rect>'
        )

    return f"""<svg width="{width:.0f}" height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}" xmlns="http://www.w3.org/2000/svg">
  <style>
    .glow {{ font-family: 'JetBrains Mono','SF Mono',Menlo,monospace; fill: #58a6ff; }}
    .cursor {{ fill: #58a6ff; }}
  </style>
  <rect width="100%" height="100%" fill="#0d1117"/>
  {''.join(body)}
</svg>
"""


def escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    art = render_ascii()
    svg = render_svg(art)
    out = ROOT / "reactor.svg"
    changed = not out.exists() or out.read_text() != svg
    out.write_text(svg)
    print(art)
    print(f"\n{'wrote' if changed else 'unchanged'}: {out}")
