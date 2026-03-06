#!/usr/bin/env python3
"""
Export the current layout JSON to a branded static HTML page.
Run: python3 tools/export_layout_html.py
"""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAYOUT = ROOT / "data" / "layouts" / "layout.json"
OUT_HTML = ROOT / "site" / "index.html"

CANVAS_W = 1440
CANVAS_H = 3900
SECTIONS = [
    (0, 880, "#fdfaf5"),
    (880, 1700, "#171410"),
    (1700, 2320, "#fdfaf5"),
    (2320, 2900, "#f0ebe0"),
    (2900, 3320, "#1a1714"),
    (3320, 3900, "#fdfaf5"),
]

ASSET_DIRS = [
    ROOT / "assets" / "originals",
    ROOT / "assets" / "renders",
    ROOT,
]


def resolve_asset_src(file_name: str) -> str:
    for base in ASSET_DIRS:
        path = base / file_name
        if path.exists():
            return os.path.relpath(path, ROOT / "site").replace("\\", "/")
    return file_name


def layer_width(layer: dict) -> int:
    return int(layer.get("size") or layer.get("w") or 200)


def section_divs() -> str:
    blocks = []
    for y0, y1, color in SECTIONS:
        blocks.append(
            f'<div class="section" style="top:{y0}px;height:{y1-y0}px;background:{color};"></div>'
        )
    return "\n            ".join(blocks)


def layer_imgs(layers: list[dict]) -> str:
    html = []
    for layer in sorted(layers, key=lambda l: l.get("z", 20)):
        if not layer.get("visible", True):
            continue
        src = resolve_asset_src(layer["file"])
        w = layer_width(layer)
        x = int(layer.get("x", 0))
        y = int(layer.get("y", 0))
        r = float(layer.get("rot", 0))
        z = int(layer.get("z", 20))
        alt = Path(layer["file"]).stem.replace("_", " ")
        html.append(
            f'<img class="layer" src="{src}" alt="{alt}" '
            f'style="left:{x}px;top:{y}px;width:{w}px;transform:rotate({r}deg);z-index:{z};">'
        )
    return "\n            ".join(html)


def brand_components() -> str:
    return f"""
          <div class="component-stack" aria-label="ZELDA design co.">
            <svg class="component-svg" viewBox="0 0 760 222" xmlns="http://www.w3.org/2000/svg" aria-label="ZEL">
              <defs>
                <clipPath id="mask-zel">
                  <text x="8" y="190" font-family="'Fraunces', Georgia, serif" font-size="218" font-weight="800" letter-spacing="-4">ZEL</text>
                </clipPath>
                <linearGradient id="glow-zel" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stop-color="#f5e8ce"/>
                  <stop offset="100%" stop-color="#8b5f3d"/>
                </linearGradient>
              </defs>
              <image href="{resolve_asset_src('hollywood_hills_home.png')}" x="-40" y="-24" width="860" height="280" preserveAspectRatio="xMidYMid slice" clip-path="url(#mask-zel)"/>
              <rect x="0" y="0" width="760" height="222" fill="url(#glow-zel)" opacity="0.2" clip-path="url(#mask-zel)"/>
              <text x="8" y="190" font-family="'Fraunces', Georgia, serif" font-size="218" font-weight="800" letter-spacing="-4" fill="none" stroke="#fff2df" stroke-width="8" opacity="0.12">ZEL</text>
            </svg>
            <svg class="component-svg" viewBox="0 0 760 222" xmlns="http://www.w3.org/2000/svg" aria-label="DA">
              <defs>
                <clipPath id="mask-da">
                  <text x="8" y="190" font-family="'Fraunces', Georgia, serif" font-size="218" font-weight="800" letter-spacing="-4">DA</text>
                </clipPath>
                <linearGradient id="glow-da" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stop-color="#f7ead1"/>
                  <stop offset="100%" stop-color="#9b6f51"/>
                </linearGradient>
              </defs>
              <image href="{resolve_asset_src('flower_wall.jpg')}" x="-20" y="-30" width="820" height="300" preserveAspectRatio="xMidYMid slice" clip-path="url(#mask-da)"/>
              <rect x="0" y="0" width="760" height="222" fill="url(#glow-da)" opacity="0.22" clip-path="url(#mask-da)"/>
              <text x="8" y="190" font-family="'Fraunces', Georgia, serif" font-size="218" font-weight="800" letter-spacing="-4" fill="none" stroke="#fff2df" stroke-width="8" opacity="0.12">DA</text>
            </svg>
            <svg class="component-svg" viewBox="0 0 760 168" xmlns="http://www.w3.org/2000/svg" aria-label="des">
              <defs>
                <clipPath id="mask-des">
                  <text x="10" y="142" font-family="'Fraunces', Georgia, serif" font-size="164" font-weight="800" letter-spacing="-5">des</text>
                </clipPath>
                <linearGradient id="glow-des" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stop-color="#f5e6cb"/>
                  <stop offset="100%" stop-color="#7b5638"/>
                </linearGradient>
              </defs>
              <image href="{resolve_asset_src('shelves.jpg')}" x="-10" y="-18" width="780" height="210" preserveAspectRatio="xMidYMid slice" clip-path="url(#mask-des)"/>
              <rect x="0" y="0" width="760" height="168" fill="url(#glow-des)" opacity="0.22" clip-path="url(#mask-des)"/>
              <text x="10" y="142" font-family="'Fraunces', Georgia, serif" font-size="164" font-weight="800" letter-spacing="-5" fill="none" stroke="#fff2df" stroke-width="7" opacity="0.12">des</text>
            </svg>
            <svg class="component-svg" viewBox="0 0 760 168" xmlns="http://www.w3.org/2000/svg" aria-label="ign">
              <defs>
                <clipPath id="mask-ign">
                  <text x="10" y="142" font-family="'Fraunces', Georgia, serif" font-size="164" font-weight="800" letter-spacing="-5">ign</text>
                </clipPath>
                <linearGradient id="glow-ign" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stop-color="#f5e2c8"/>
                  <stop offset="100%" stop-color="#8d6647"/>
                </linearGradient>
              </defs>
              <image href="{resolve_asset_src('mediterranean.jpg')}" x="-12" y="-18" width="790" height="220" preserveAspectRatio="xMidYMid slice" clip-path="url(#mask-ign)"/>
              <rect x="0" y="0" width="760" height="168" fill="url(#glow-ign)" opacity="0.22" clip-path="url(#mask-ign)"/>
              <text x="10" y="142" font-family="'Fraunces', Georgia, serif" font-size="164" font-weight="800" letter-spacing="-5" fill="none" stroke="#fff2df" stroke-width="7" opacity="0.12">ign</text>
            </svg>
            <svg class="component-svg" viewBox="0 0 760 126" xmlns="http://www.w3.org/2000/svg" aria-label="co.">
              <defs>
                <clipPath id="mask-co">
                  <text x="12" y="104" font-family="'Fraunces', Georgia, serif" font-size="120" font-weight="800" letter-spacing="-2">co.</text>
                </clipPath>
                <linearGradient id="glow-co" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stop-color="#f8ecd6"/>
                  <stop offset="100%" stop-color="#93613a"/>
                </linearGradient>
              </defs>
              <image href="{resolve_asset_src('perrier.jpg')}" x="-14" y="-16" width="520" height="168" preserveAspectRatio="xMidYMid slice" clip-path="url(#mask-co)"/>
              <rect x="0" y="0" width="760" height="126" fill="url(#glow-co)" opacity="0.22" clip-path="url(#mask-co)"/>
              <text x="12" y="104" font-family="'Fraunces', Georgia, serif" font-size="120" font-weight="800" letter-spacing="-2" fill="none" stroke="#fff2df" stroke-width="6" opacity="0.12">co.</text>
            </svg>
          </div>
"""


def main() -> None:
    layers = json.loads(LAYOUT.read_text(encoding="utf-8"))
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)

    content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Zelda Design Co.</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,500;1,600&family=Fraunces:opsz,wght,SOFT,WONK@9..144,800,0,0&display=swap" rel="stylesheet">
  <style>
    :root {{
      --ink: #16110d;
      --paper: #efe5d6;
      --sand: #d5b58a;
      --taupe: #9f8667;
      --line: rgba(255, 244, 230, 0.14);
      --canvas-w: {CANVAS_W}px;
      --canvas-h: {CANVAS_H}px;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      color: var(--paper);
      background:
        radial-gradient(circle at 12% 12%, rgba(213, 181, 138, 0.18), transparent 28%),
        radial-gradient(circle at 88% 20%, rgba(213, 181, 138, 0.08), transparent 24%),
        linear-gradient(180deg, #17110d 0%, #0f0b08 100%);
      font-family: "Cormorant Garamond", Georgia, serif;
    }}
    .page {{
      width: min(1280px, calc(100vw - 36px));
      margin: 0 auto;
      padding: 24px 0 28px;
    }}
    .frame {{
      border: 1px solid var(--line);
      background:
        linear-gradient(180deg, rgba(255, 244, 230, 0.035), rgba(255, 244, 230, 0.01)),
        rgba(14, 11, 9, 0.82);
      box-shadow: 0 28px 90px rgba(0, 0, 0, 0.36);
      backdrop-filter: blur(10px);
      overflow: hidden;
    }}
    .hero {{
      display: grid;
      grid-template-columns: minmax(0, 1.05fr) minmax(280px, 0.72fr);
      min-height: 860px;
    }}
    .mark-panel {{
      padding: 56px 56px 34px;
      border-right: 1px solid var(--line);
      display: flex;
      flex-direction: column;
      justify-content: center;
    }}
    .notes-panel {{
      padding: 56px 44px 34px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .eyebrow {{
      margin: 0 0 18px;
      font-size: 12px;
      letter-spacing: 0.28em;
      text-transform: uppercase;
      color: var(--taupe);
    }}
    .component-stack, .component-svg, .subtitle-svg, .descriptor-svg {{
      display: block;
      width: 100%;
    }}
    .component-stack {{
      max-width: 660px;
      margin-bottom: 14px;
      display: grid;
      gap: 8px;
    }}
    .component-svg {{ overflow: visible; }}
    .subtitle-svg {{ max-width: 580px; margin: 6px 0 2px; }}
    .descriptor-svg {{ max-width: 600px; opacity: 0.94; }}
    .brand-copy {{
      margin: 0 0 26px;
      color: #d4c2a8;
      font-size: 20px;
      line-height: 1.35;
    }}
    .divider {{
      height: 1px;
      background: linear-gradient(90deg, transparent, var(--line), transparent);
      margin: 24px 0 28px;
    }}
    .instagram {{
      display: inline-block;
      color: var(--paper);
      text-decoration: none;
      font-size: 14px;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      border-bottom: 1px solid rgba(239, 229, 214, 0.45);
      padding-bottom: 5px;
      width: fit-content;
    }}
    .contact-block {{
      margin-top: 24px;
      color: #e9dcc8;
    }}
    .contact-block h2 {{
      margin: 0 0 16px;
      font-size: 38px;
      line-height: 0.96;
      font-weight: 600;
    }}
    .contact-block p {{
      margin: 0;
      font-size: 23px;
      line-height: 1.28;
    }}
    .contact-block a {{
      color: inherit;
      text-decoration: none;
      border-bottom: 1px solid rgba(239, 229, 214, 0.35);
    }}
    .microcopy {{
      margin-top: 28px;
      color: var(--taupe);
      font-size: 14px;
      line-height: 1.55;
    }}
    .collage-shell {{
      padding: 28px;
      border-top: 1px solid var(--line);
      background:
        linear-gradient(180deg, rgba(255, 244, 230, 0.02), rgba(255, 244, 230, 0)),
        rgba(9, 8, 7, 0.34);
    }}
    .collage-title {{
      margin: 0 0 18px;
      font-size: 12px;
      letter-spacing: 0.24em;
      text-transform: uppercase;
      color: var(--taupe);
    }}
    .canvas-wrap {{
      overflow: auto;
      padding-bottom: 6px;
    }}
    .canvas {{
      position: relative;
      width: var(--canvas-w);
      height: var(--canvas-h);
      overflow: hidden;
      background: #f7f3ec;
      box-shadow: 0 24px 70px rgba(0,0,0,.35);
    }}
    .section {{
      position: absolute;
      left: 0;
      width: var(--canvas-w);
    }}
    .layer {{
      position: absolute;
      height: auto;
      box-shadow: 8px 14px 24px rgba(0,0,0,.35);
      transform-origin: center center;
      user-select: none;
      -webkit-user-drag: none;
    }}
    footer {{
      display: flex;
      justify-content: space-between;
      gap: 24px;
      padding: 18px 24px 0;
      margin-top: 12px;
      border-top: 1px solid var(--line);
      color: var(--taupe);
      font-size: 12px;
      letter-spacing: 0.16em;
      text-transform: uppercase;
    }}
    footer span:last-child {{
      text-align: right;
    }}
    @media (max-width: 1500px) {{
      .canvas {{
        width: min(96vw, var(--canvas-w));
        height: auto;
        aspect-ratio: {CANVAS_W}/{CANVAS_H};
      }}
    }}
    @media (max-width: 980px) {{
      .hero {{
        grid-template-columns: 1fr;
      }}
      .mark-panel {{
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }}
      footer {{
        flex-direction: column;
      }}
      footer span:last-child {{
        text-align: left;
      }}
      .collage-shell {{
        padding: 18px;
      }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <div class="frame">
      <section class="hero">
        <div class="mark-panel">
          <p class="eyebrow">Residential Design Studio</p>
          {brand_components()}
          <svg class="subtitle-svg" viewBox="0 0 920 120" xmlns="http://www.w3.org/2000/svg" aria-label="Residential Design Studio">
            <text x="8" y="86"
                  font-family="'Cormorant Garamond', Georgia, serif"
                  font-size="74"
                  font-style="italic"
                  font-weight="600"
                  letter-spacing="1"
                  fill="#efe5d6">Residential Design Studio</text>
          </svg>
          <svg class="descriptor-svg" viewBox="0 0 1120 72" xmlns="http://www.w3.org/2000/svg" aria-label="historic rehabilitation. new construction. eclectic interiors">
            <text x="8" y="44"
                  font-family="'Cormorant Garamond', Georgia, serif"
                  font-size="34"
                  font-weight="600"
                  letter-spacing="1.1"
                  fill="#bfa488">historic rehabilitation. new construction. eclectic interiors</text>
          </svg>
        </div>
        <div class="notes-panel">
          <div>
            <p class="brand-copy">A heavier window-mark designed to let photography live inside the name while keeping the rest of the page atmospheric and editorial.</p>
            <div class="divider"></div>
            <a class="instagram" href="https://www.instagram.com/zeldadesignco/" target="_blank" rel="noreferrer">Instagram</a>
          </div>
          <div class="contact-block">
            <h2>Reach out for your upcoming project!</h2>
            <p>
              Zelda Design Co.<br>
              440 E Rte 66, Suite 115<br>
              Glendora, CA 91741<br>
              <a href="mailto:hello@zeldadesignco.com">hello@zeldadesignco.com</a>
            </p>
            <p class="microcopy">The collage section below is generated from the current layout data and can continue evolving independently of this brand shell.</p>
          </div>
        </div>
      </section>

      <section class="collage-shell">
        <p class="collage-title">Current Layout</p>
        <div class="canvas-wrap">
          <main class="canvas">
            {section_divs()}
            {layer_imgs(layers)}
          </main>
        </div>
      </section>
    </div>

    <footer>
      <span>ZELDA DESIGN CO.</span>
      <span>©2026 by Zelda Design Co. | Full Service Interior Design | Glendora, CA</span>
    </footer>
  </div>
</body>
</html>
"""

    OUT_HTML.write_text(content, encoding="utf-8")
    print(f"Wrote {OUT_HTML}")


if __name__ == "__main__":
    main()
