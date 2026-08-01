#!/usr/bin/env python3
"""
Photo -> animated ASCII SVG, in the same style and typing-reveal animation as
reactor.svg. Use it on a photo you have the rights to use — your own portrait,
something you shot, something properly licensed. It's a generic converter; it
carries no opinion about what you feed it, but you do.

Usage:
    python3 scripts/gen_portrait.py path/to/photo.jpg
    python3 scripts/gen_portrait.py path/to/photo.jpg --width 100 --out portrait.svg
    python3 scripts/gen_portrait.py path/to/photo.jpg --invert   # for a light background
    python3 scripts/gen_portrait.py path/to/photo.jpg --crop left,top,right,bottom
    python3 scripts/gen_portrait.py path/to/photo.jpg --curve 1.7

Requires Pillow only:  pip install pillow

Two things decide whether the output is any good, same as any photo-to-ASCII
conversion — neither is a flag:
  * The photo. ASCII draws with shadow, not detail. Side light (a window at
    ~45 degrees), a tight crop to the head, real resolution. Flat frontal
    light renders a face as a hole; a small/blurry source loses fine features
    on downscale.
  * --curve. Left at 1.0 most photos come out washed out — faces read as flat
    mid-grey. Raising it (try 1.5-2.0) darkens midtones and pulls shadow
    detail back in. This one parameter matters more than any other here.

Not included, to keep this dependency-light (just Pillow): background removal
and exact monospace-width font embedding. If you want either:
  * Background removal: run `pip install rembg onnxruntime`, cut the subject
    out and composite it onto a flat background yourself before passing the
    image in here — simplest way to add it without new required deps.
  * Font embedding: this SVG relies on the viewer's own monospace font, so
    character width varies slightly by viewer. Fine for a rough grid; if you
    want pixel-exact alignment, subset and inline a font as a base64 @font-face
    and fix CHAR_W in _ascii_svg.py to that font's real advance width.
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _ascii_svg import render_svg  # noqa: E402

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Requires Pillow. Run:  pip install pillow")

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_RAMP = " .:-=+*#%@"   # quiet -> loud; index 0 renders as blank


def image_to_ascii(path, width, ramp, invert, crop=None, curve=1.0,
                   char_aspect=2.0, autocontrast=True):
    img = Image.open(path).convert("L")           # grayscale
    if crop:
        img = img.crop(crop)
    if autocontrast:
        img = ImageOps.autocontrast(img, cutoff=1)

    src_w, src_h = img.size
    height = max(1, round((src_h / src_w) * width / char_aspect))
    img = img.resize((width, height), Image.LANCZOS)

    pixels = img.load()
    ramp_len = len(ramp)
    rows = []
    for y in range(height):
        row_chars = []
        for x in range(width):
            v = pixels[x, y] / 255.0               # 0 = black, 1 = white
            if curve != 1.0:
                v = v ** curve                      # >1 darkens midtones
            if invert:
                v = 1.0 - v
            idx = min(ramp_len - 1, int(v * ramp_len))
            row_chars.append(ramp[idx])
        rows.append("".join(row_chars).rstrip())

    while rows and not rows[0].strip():
        rows.pop(0)
    while rows and not rows[-1].strip():
        rows.pop()
    return "\n".join(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image", type=pathlib.Path, help="source photo")
    ap.add_argument("--width", type=int, default=90, help="output columns (default 90)")
    ap.add_argument("--out", type=pathlib.Path, default=None,
                    help="output SVG path (default: <image-stem>.svg in repo root)")
    ap.add_argument("--ramp", default=DEFAULT_RAMP,
                    help="character ramp, quiet to loud (default: %(default)r)")
    ap.add_argument("--invert", action="store_true",
                    help="use for photos meant to sit on a LIGHT background "
                         "(default assumes a dark background, like reactor.svg)")
    ap.add_argument("--crop", help="left,top,right,bottom, applied first — crop "
                                   "tight to the head so the whole grid goes to it")
    ap.add_argument("--curve", type=float, default=1.0,
                    help="darkening exponent; try 1.5-2.0 if faces come out "
                         "washed out (default 1.0 = no change)")
    ap.add_argument("--color", default="#58a6ff", help="glyph/cursor color")
    ap.add_argument("--bg", default="#0d1117", help="background fill")
    ap.add_argument("--no-print", action="store_true", help="skip the terminal preview")
    args = ap.parse_args()

    if not args.image.exists():
        sys.exit(f"not found: {args.image}")

    crop = None
    if args.crop:
        parts = [int(v) for v in args.crop.split(",")]
        if len(parts) != 4:
            sys.exit("--crop needs four numbers: left,top,right,bottom")
        crop = tuple(parts)

    art = image_to_ascii(args.image, args.width, args.ramp, args.invert,
                         crop=crop, curve=args.curve)
    svg = render_svg(art, color=args.color, bg=args.bg)

    out = args.out or (ROOT / f"{args.image.stem}.svg")
    out.write_text(svg)

    if not args.no_print:
        print(art)
    print(f"\nwrote: {out}  ({len(art.splitlines())} rows x {args.width} cols)")


if __name__ == "__main__":
    main()
