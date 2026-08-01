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
    lines = ascii_art.split("\n")
    line_h = 11
    char_w = 6.6
    height = len(lines) * line_h + 20
    width = max(len(l) for l in lines) * char_w + 20

    tspans = "".join(
        f'<tspan x="10" dy="{line_h if i else 0}">{escape(l)}</tspan>'
        for i, l in enumerate(lines)
    )
    return f"""<svg width="{width:.0f}" height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="#0d1117"/>
  <text x="10" y="14" font-family="'JetBrains Mono','SF Mono',Menlo,monospace" font-size="9" fill="#58a6ff" xml:space="preserve">{tspans}</text>
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
