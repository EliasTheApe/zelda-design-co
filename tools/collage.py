#!/usr/bin/env python3
"""
Zelda Design Co. - Collage compositor
Run:  python3 tools/collage.py
Reads layer positions from data/layouts/layout.json, composites to assets/renders/collage_preview.png.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw

ROOT     = Path(__file__).resolve().parent.parent
LAYOUT   = ROOT / "data" / "layouts" / "layout.json"
RENDERS  = ROOT / "assets" / "renders"
ASSET_DIRS = [
    ROOT / "assets" / "originals",
    RENDERS,
    ROOT,
]
CANVAS_W = 1440
CANVAS_H = 3900
BG_COLOR = (247, 243, 236)

SECTIONS = [
    (0,    880,  (253, 250, 245)),
    (880,  1700, ( 23,  20,  16)),
    (1700, 2320, (253, 250, 245)),
    (2320, 2900, (240, 235, 224)),
    (2900, 3320, ( 26,  23,  20)),
    (3320, 3900, (253, 250, 245)),
]


def drop_shadow(img, offset=(8, 14), blur=24, color=(0, 0, 0, 90)):
    alpha = img.split()[3] if img.mode == "RGBA" else img.convert("RGBA").split()[3]
    shadow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow_layer.paste(Image.new("RGBA", img.size, color), mask=alpha)
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(blur))
    out = Image.new("RGBA", (img.width + abs(offset[0]) + blur,
                              img.height + abs(offset[1]) + blur), (0, 0, 0, 0))
    sx = max(offset[0], 0) + blur // 2
    sy = max(offset[1], 0) + blur // 2
    out.paste(shadow_layer, (sx, sy), shadow_layer)
    ix = max(-offset[0], 0) + blur // 2
    iy = max(-offset[1], 0) + blur // 2
    out.paste(img, (ix, iy), img)
    return out, ix, iy


def open_with_default_app(path):
    path_str = str(path)
    if sys.platform == "darwin":
        subprocess.run(["open", path_str], check=False)
        return
    if os.name == "nt":
        os.startfile(path_str)  # type: ignore[attr-defined]
        return
    xdg_open = shutil.which("xdg-open")
    if xdg_open:
        subprocess.run([xdg_open, path_str], check=False)


def resolve_asset(file_name):
    candidate = Path(file_name)
    if candidate.is_absolute() and candidate.exists():
        return candidate
    for base in ASSET_DIRS:
        path = base / file_name
        if path.exists():
            return path
    return None


def build():
    with open(LAYOUT, encoding="utf-8") as f:
        layers = json.load(f)
    print(f"Building collage with {len(layers)} layers…")

    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (*BG_COLOR, 255))
    for y0, y1, color in SECTIONS:
        canvas.paste(Image.new("RGBA", (CANVAS_W, y1 - y0), (*color, 255)), (0, y0))

    draw = ImageDraw.Draw(canvas)
    for y0, _, _ in SECTIONS[1:]:
        draw.line([(0, y0), (CANVAS_W, y0)], fill=(128, 120, 110, 40), width=1)

    for layer in sorted(layers, key=lambda l: l.get("z", 20)):
        if not layer.get("visible", True):
            continue

        path = resolve_asset(layer["file"])
        if not path:
            print(f"  MISSING: {layer['file']}")
            continue

        with Image.open(path) as src:
            img = src.convert("RGBA")

        tw = int(layer.get("size") or layer.get("w") or 200)
        th = int(img.height * tw / img.width)   # always proportional

        img = img.resize((tw, th), Image.LANCZOS)

        rot = layer.get("rot", 0)
        if rot:
            img = img.rotate(-rot, resample=Image.BICUBIC, expand=True)

        shadowed, ix, iy = drop_shadow(img)

        px = int(layer["x"]) - ix
        py = int(layer["y"]) - iy

        tmp = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        sw, sh = shadowed.size
        cx0 = max(px, 0);   cy0 = max(py, 0)
        cx1 = min(px + sw, CANVAS_W); cy1 = min(py + sh, CANVAS_H)
        if cx0 < cx1 and cy0 < cy1:
            region = shadowed.crop((cx0 - px, cy0 - py, cx1 - px, cy1 - py))
            tmp.paste(region, (cx0, cy0))
        canvas = Image.alpha_composite(canvas, tmp)
        print(f"  ✓  {layer['file']}")

    RENDERS.mkdir(parents=True, exist_ok=True)
    out_path = RENDERS / "collage_preview.png"
    canvas.convert("RGB").save(out_path, "PNG")
    print(f"\nSaved → {out_path}")
    open_with_default_app(out_path)


if __name__ == "__main__":
    build()
