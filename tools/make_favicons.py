"""Make the site icons from the author's logo.

Source: assets/logo/logo.png (supplied by the author, 2026-11-17). Writes, at the site root:
  favicon.png           64 x 64, linked from every Quarto page (_quarto.yml: website.favicon)
  favicon.ico           16, 32 and 48 px, for browsers and pages that ask for /favicon.ico
  apple-touch-icon.png  180 x 180, for phone home screens

The logo is cropped to a square around its drawing, placed on a white rounded tile so it stays visible
on dark browser tabs, and resized with Lanczos filtering.

Run: python tools/make_favicons.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "logo" / "logo.png"


def square_crop(im, margin=0.05, white_cut=235):
    """Square crop centred on the non-white drawing, with a margin as a fraction of the side."""
    a = np.asarray(im.convert("RGB"))
    ys, xs = np.where(a.min(axis=2) < white_cut)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    side = int(round(max(x1 - x0, y1 - y0) * (1 + 2 * margin)))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    left, top = int(round(cx - side / 2)), int(round(cy - side / 2))
    canvas = Image.new("RGB", (side, side), "white")
    canvas.paste(im.convert("RGB"), (-left, -top))
    return canvas


def thicken(square, size):
    """Widen the strokes before a small resize, so lines stay about a pixel wide in the icon."""
    stroke = 5.5 * square.size[0] / 393  # stroke width of the 512-px source logo, in crop pixels
    target = max(1.0, 0.9 * square.size[0] / size)  # crop pixels per icon pixel
    k = int(round(max(0.0, target - stroke)))
    k += 1 - k % 2  # MinFilter needs an odd size
    return square.filter(ImageFilter.MinFilter(k)) if k >= 3 else square


def tile(square, size, radius=0.18):
    """The square logo on a white rounded tile, transparent outside the corners."""
    art = thicken(square, size).resize((size, size), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size * 4 - 1, size * 4 - 1], radius=int(radius * size * 4), fill=255)
    art.putalpha(mask.resize((size, size), Image.LANCZOS))
    return art


def main():
    square = square_crop(Image.open(SOURCE))
    tile(square, 64).save(ROOT / "favicon.png", optimize=True)
    tile(square, 180).convert("RGB").save(ROOT / "apple-touch-icon.png", optimize=True)  # iOS fills corners itself
    frames = [tile(square, s) for s in (16, 32, 48)]  # each size drawn on its own, not scaled from one
    frames[-1].save(ROOT / "favicon.ico", sizes=[f.size for f in frames], append_images=frames[:-1])
    for name in ("favicon.png", "apple-touch-icon.png", "favicon.ico"):
        print(name, (ROOT / name).stat().st_size, "bytes")


if __name__ == "__main__":
    main()
