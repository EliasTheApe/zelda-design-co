#!/usr/bin/env python3
"""
Zelda Design Co. - Collage Layout GUI
Run:  python3 tools/collage_gui.py

NOB controller: HID mouse device.
  Click a param label (X / Y / SIZE / ROT / Z) → it glows gold.
  Turn the knob → that param updates. Knob X-axis or Y-axis both work
  (the GUI uses whichever axis is moving more on each tick).
  Right toggle on NOB: switches knob between X and Y mouse axis — both work here.
  Left toggle: not used.

Keyboard shortcuts:
  Arrow keys     — nudge X/Y  (Shift = 10px steps)
  [ ]            — rotate CCW / CW
  = / -          — size up / down
  PgUp / PgDn    — z order up / down
  H              — hide / show toggle
  Ctrl+Z         — undo
  Ctrl+S         — save layout + snapshot
  Ctrl+O         — add image asset layer
  Ctrl+E         — export site/collage_generated.html
  R              — full Pillow render → Preview
"""

import copy
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

ROOT      = Path(__file__).resolve().parent.parent
TOOLS_DIR = ROOT / "tools"
LAYOUT    = ROOT / "data" / "layouts" / "layout.json"
HISTORY   = ROOT / "data" / "layouts" / "history"
ASSET_DIRS = [
    ROOT / "assets" / "originals",
    ROOT / "assets" / "renders",
    ROOT,
]
CANVAS_W = 1440
CANVAS_H = 3900
SCALE    = 0.28

SECTIONS = [
    (0,    880,  "#fdfaf5", "HERO"),
    (880,  1700, "#171410", "ABOUT"),
    (1700, 2320, "#fdfaf5", "SERVICES"),
    (2320, 2900, "#f0ebe0", "PROCESS"),
    (2900, 3320, "#1a1714", "PROJECTS"),
    (3320, 3900, "#fdfaf5", "CONTACT"),
]

G  = "#b89a6e"
BG = "#1e1a14"
DG = "#2a2520"


class CollageGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Zelda Design Co. — Collage Editor")
        self.root.configure(bg="#1a1714")

        self.layers        = []
        self.history       = []
        self.selected      = None   # layer index
        self.focused_param = "size"   # "x" | "y" | "size" | "rot" | "z"

        self._photo_cache  = {}     # filename → PIL Image full-res
        self._thumb_cache  = {}     # (file,size,rot,visible) -> PIL Image preview
        self._tk_photos    = []     # keep PhotoImage refs alive

        self._sensitivity  = tk.DoubleVar(value=1.0)  # global knob multiplier
        self._event_count  = 0
        self._last_pointer = None
        self._motion_remainder = 0.0

        self.load_layout()
        self.build_ui()
        self.render_canvas()
        self.focus_param("size")
        if self.layers:
            self._select(0)

    # ── DATA ────────────────────────────────────────────────────────────────
    def load_layout(self):
        with open(LAYOUT, encoding="utf-8") as f:
            raw = json.load(f)
        self.layers = []
        for L in raw:
            L.setdefault("visible", True)
            L.setdefault("rot", 0.0)
            L.setdefault("z", 25)
            # Migrate w→size, drop h
            if "w" in L and "size" not in L:
                L["size"] = float(L["w"])
            L.pop("h", None)
            L.pop("w", None)
            self.layers.append(L)

    def _layout_serializable(self):
        out = []
        for layer in self.layers:
            d = dict(layer)
            d["w"] = d.pop("size", 200)
            d["h"] = None
            out.append(d)
        return out

    def save_layout(self, _=None):
        out = self._layout_serializable()
        LAYOUT.parent.mkdir(parents=True, exist_ok=True)
        with open(LAYOUT, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)

        HISTORY.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        snapshot_path = HISTORY / f"layout_{stamp}.json"
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
        self.status(f"Saved layout + snapshot ({snapshot_path.name})")

    def _resolve_asset_path(self, file_name):
        candidate = Path(file_name)
        if candidate.is_absolute() and candidate.exists():
            return candidate
        for base in ASSET_DIRS:
            path = base / file_name
            if path.exists():
                return path
        return None

    def push_undo(self):
        self.history.append(copy.deepcopy(self.layers))
        if len(self.history) > 80:
            self.history.pop(0)

    def undo(self, _=None):
        if not self.history:
            return
        self.layers = self.history.pop()
        self.selected = None
        self.render_canvas()
        self.update_panel()
        self.update_list()
        self.status("Undo")

    # ── UI ──────────────────────────────────────────────────────────────────
    def build_ui(self):
        self.left  = tk.Frame(self.root, bg="#1a1714")
        self.right = tk.Frame(self.root, bg=BG, width=300)
        self.left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.right.pack(side=tk.RIGHT, fill=tk.Y)
        self.right.pack_propagate(False)

        # Scrollable canvas
        cw = int(CANVAS_W * SCALE)
        ch = int(CANVAS_H * SCALE)
        self.vbar = tk.Scrollbar(self.left, orient=tk.VERTICAL, bg="#1a1714",
                                  troughcolor="#111")
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas = tk.Canvas(
            self.left, width=cw, height=min(ch, 860),
            bg="#2a2520", yscrollcommand=self.vbar.set,
            cursor="crosshair", highlightthickness=0, takefocus=1,
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH)
        self.canvas.configure(scrollregion=(0, 0, cw, ch))
        self.vbar.configure(command=self.canvas.yview)
        # scroll handled by bind_all in build_ui
        self.canvas.bind("<Button-1>",   self._on_canvas_click)
        self.canvas.bind("<Button-1>", lambda e: self.canvas.focus_set(), add="+")

        # Status bar
        self.status_var = tk.StringVar(value="  Ready")
        tk.Label(self.left, textvariable=self.status_var,
                 font=("Courier", 10), bg="#111", fg=G,
                 anchor="w", padx=8, pady=3).pack(fill=tk.X, side=tk.BOTTOM)
        self.event_var = tk.StringVar(value="  Input: none")
        tk.Label(self.left, textvariable=self.event_var,
                 font=("Courier", 9), bg="#171410", fg="#7e6d56",
                 anchor="w", padx=8, pady=3).pack(fill=tk.X, side=tk.BOTTOM)

        self._build_panel()

        widgets = [self.root, self.canvas, self.layer_list, self.right]
        for w in widgets:
            w.bind("<MouseWheel>", self._on_scroll_knob, add="+")
            w.bind("<Button-4>", self._on_scroll_knob, add="+")
            w.bind("<Button-5>", self._on_scroll_knob, add="+")
            w.bind("<Motion>", self._on_pointer_motion, add="+")
            w.bind("<KeyPress-Up>", self._on_up_key, add="+")
            w.bind("<KeyPress-Down>", self._on_down_key, add="+")
            w.bind("<KeyPress>", self._on_any_key, add="+")

        # Wheel events can be delivered to the widget under the pointer rather than
        # the focused widget, especially on macOS. Bind globally as a fallback.
        self.root.bind_all("<MouseWheel>", self._on_scroll_knob, add="+")
        self.root.bind_all("<Button-4>", self._on_scroll_knob, add="+")
        self.root.bind_all("<Button-5>", self._on_scroll_knob, add="+")

        self.root.bind("<Button-1>", lambda e: self.canvas.focus_set(), add="+")
        self.root.bind("<FocusIn>", lambda e: self.canvas.focus_set(), add="+")
        self.canvas.focus_set()

    def _build_panel(self):
        # Title
        tk.Label(self.right, text="ZELDA  COLLAGE",
                 font=("Courier", 11, "bold"), bg=BG, fg=G,
                 pady=10).pack(fill=tk.X)
        tk.Frame(self.right, bg=DG, height=1).pack(fill=tk.X)

        # Selected image name
        self.sel_label = tk.Label(
            self.right, text="— click an image —",
            font=("Courier", 9, "italic"), bg=BG, fg="#555",
            wraplength=280, justify=tk.LEFT, padx=10, pady=6)
        self.sel_label.pack(fill=tk.X)
        tk.Frame(self.right, bg=DG, height=1).pack(fill=tk.X)

        # ── Parameter rows ──────────────────────────────────
        self.param_rows  = {}   # key → (frame, name_lbl, val_lbl)
        self.param_vars  = {}   # key → StringVar

        pframe = tk.Frame(self.right, bg=BG)
        pframe.pack(fill=tk.X, padx=8, pady=8)

        params = [
            ("X",    "x",    "px"),
            ("Y",    "y",    "px"),
            ("SIZE", "size", "px"),
            ("ROT",  "rot",  "°"),
            ("Z",    "z",    ""),
        ]
        for label, key, unit in params:
            row = tk.Frame(pframe, bg=BG, cursor="hand2")
            row.pack(fill=tk.X, pady=3)

            name_lbl = tk.Label(row, text=f" {label}", width=5,
                                 font=("Courier", 13, "bold"),
                                 bg=BG, fg="#3a3530", anchor="w")
            name_lbl.pack(side=tk.LEFT)

            var = tk.StringVar(value="—")
            val_lbl = tk.Label(row, textvariable=var, width=9,
                                font=("Courier", 13),
                                bg=DG, fg="#555", anchor="e", padx=8)
            val_lbl.pack(side=tk.LEFT, padx=3)

            tk.Label(row, text=unit, font=("Courier", 9),
                     bg=BG, fg="#2a2520", width=2).pack(side=tk.LEFT)

            self.param_rows[key] = (row, name_lbl, val_lbl)
            self.param_vars[key] = var

            for w in (row, name_lbl, val_lbl):
                w.bind("<Button-1>", lambda e, k=key: self._focus_param_and_canvas(k))

        # ── NOB indicator ───────────────────────────────────
        tk.Frame(self.right, bg=DG, height=1).pack(fill=tk.X, pady=6)

        nob_frame = tk.Frame(self.right, bg=BG)
        nob_frame.pack(fill=tk.X, padx=12, pady=2)

        tk.Label(nob_frame, text="NOB", font=("Courier", 9, "bold"),
                 bg=BG, fg="#444").pack(side=tk.LEFT)

        self.nob_dot = tk.Label(nob_frame, text="  ●  ",
                                 font=("Courier", 16), bg=BG, fg="#2a2520")
        self.nob_dot.pack(side=tk.LEFT)

        self.nob_axis_var = tk.StringVar(value="—")
        tk.Label(nob_frame, textvariable=self.nob_axis_var,
                 font=("Courier", 9), bg=BG, fg="#555",
                 width=14, anchor="w").pack(side=tk.LEFT)

        # Sensitivity
        sens_frame = tk.Frame(self.right, bg=BG)
        sens_frame.pack(fill=tk.X, padx=12, pady=4)
        tk.Label(sens_frame, text="SENS", font=("Courier", 9),
                 bg=BG, fg="#444", width=5).pack(side=tk.LEFT)
        self.sens_val_var = tk.StringVar(value="1.0×")
        tk.Label(sens_frame, textvariable=self.sens_val_var,
                 font=("Courier", 9), bg=BG, fg=G, width=5).pack(side=tk.LEFT)
        sens_slider = tk.Scale(
            sens_frame, variable=self._sensitivity,
            from_=0.1, to=5.0, resolution=0.1,
            orient=tk.HORIZONTAL, length=140,
            bg=BG, fg="#555", troughcolor=DG,
            highlightthickness=0, bd=0, showvalue=False,
            command=lambda v: self.sens_val_var.set(f"{float(v):.1f}×"),
        )
        sens_slider.pack(side=tk.LEFT, padx=4)

        # ── Buttons ─────────────────────────────────────────
        tk.Frame(self.right, bg=DG, height=1).pack(fill=tk.X, pady=6)
        btn = dict(font=("Courier", 10), bg=DG, fg=G,
                   relief=tk.FLAT, cursor="hand2", pady=6, padx=8)
        tk.Button(self.right, text="▶  Full Render  (R)",
                  command=self.full_render, **btn).pack(fill=tk.X, padx=8, pady=2)
        tk.Button(self.right, text="💾  Save  (Ctrl+S)",
                  command=self.save_layout, **btn).pack(fill=tk.X, padx=8, pady=2)
        tk.Button(self.right, text="＋  Add Asset  (Ctrl+O)",
                  command=self.add_asset, **btn).pack(fill=tk.X, padx=8, pady=2)
        tk.Button(self.right, text="👁  Hide / Show  (H)",
                  command=self.toggle_visible, **btn).pack(fill=tk.X, padx=8, pady=2)
        tk.Button(self.right, text="🌐  Export HTML  (Ctrl+E)",
                  command=self.export_html, **btn).pack(fill=tk.X, padx=8, pady=2)

        tk.Frame(self.right, bg=DG, height=1).pack(fill=tk.X, pady=4)

        # Layer list
        tk.Label(self.right, text="  LAYERS",
                 font=("Courier", 8), bg=BG, fg="#333").pack(anchor="w", padx=6)
        lf = tk.Frame(self.right, bg=BG)
        lf.pack(fill=tk.BOTH, expand=True, padx=6, pady=2)
        lsb = tk.Scrollbar(lf, bg="#1a1714")
        lsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.layer_list = tk.Listbox(
            lf, yscrollcommand=lsb.set,
            font=("Courier", 8), bg="#111", fg="#555",
            selectbackground=DG, selectforeground=G,
            activestyle="none", relief=tk.FLAT, highlightthickness=0,
        )
        self.layer_list.pack(fill=tk.BOTH, expand=True)
        lsb.configure(command=self.layer_list.yview)
        self.layer_list.bind("<<ListboxSelect>>", self._list_select)
        self.layer_list.bind("<Button-1>", lambda e: self.layer_list.focus_set(), add="+")
        self.update_list()

        tk.Label(self.right,
                 text="  click param → turn knob\n  [ ] rot · = - size · ← → ↑ ↓\n  Ctrl+O add asset · Ctrl+E export HTML",
                 font=("Courier", 8), bg=BG, fg="#2a2520",
                 justify=tk.LEFT, pady=6).pack(anchor="w")

    # ── PARAM FOCUS ─────────────────────────────────────────────────────────
    def focus_param(self, key):
        self.focused_param = key
        self._reset_param_styles()

        # Highlight the focused row
        row, name, val = self.param_rows[key]
        name.config(fg=G, bg="#252010")
        val.config(fg=G, bg="#252010")
        row.config(bg="#252010")

        self.status(f"NOB → {key.upper()}   (click again to release)")

    def _focus_param_and_canvas(self, key):
        self.focus_param(key)
        self.canvas.focus_set()

    def _reset_param_styles(self):
        for k, (row, name, val) in self.param_rows.items():
            name.config(fg="#3a3530", bg=BG)
            val.config(fg="#555",     bg=DG)
            row.config(bg=BG)

    # ── CANVAS ──────────────────────────────────────────────────────────────
    def _orig(self, filename):
        if filename not in self._photo_cache:
            path = self._resolve_asset_path(filename)
            if not path:
                return None
            with Image.open(path) as src:
                self._photo_cache[filename] = src.convert("RGBA")
        return self._photo_cache[filename]

    def _thumb(self, layer):
        file_name = layer["file"]
        size = max(int(layer.get("size", 200)), 4)
        rot = round(float(layer.get("rot", 0.0)), 1)
        visible = bool(layer.get("visible", True))
        cache_key = (file_name, size, rot, visible)

        cached = self._thumb_cache.get(cache_key)
        if cached is None:
            orig = self._orig(file_name)
            if orig is None:
                return None, 0, 0
            th = max(int(size * orig.height / orig.width), 4)
            img = orig.resize((size, th), Image.BILINEAR)
            if rot:
                img = img.rotate(-rot, resample=Image.BILINEAR, expand=True)
            if not visible:
                r, g, b, a = img.split()
                img = Image.merge("RGBA", (r, g, b, a.point(lambda p: p // 5)))
            dw = max(int(img.width * SCALE), 1)
            dh = max(int(img.height * SCALE), 1)
            cached = img.resize((dw, dh), Image.BILINEAR)
            self._thumb_cache[cache_key] = cached

        return ImageTk.PhotoImage(cached), int(layer["x"] * SCALE), int(layer["y"] * SCALE)

    def render_canvas(self):
        self.canvas.delete("all")
        self._tk_photos.clear()

        for y0, y1, color, label in SECTIONS:
            dy0, dy1 = int(y0 * SCALE), int(y1 * SCALE)
            self.canvas.create_rectangle(0, dy0, int(CANVAS_W * SCALE), dy1,
                                          fill=color, outline="")
            tc = "#3a3530" if color in ("#171410", "#1a1714") else "#c8c0b4"
            self.canvas.create_text(6, dy0 + 10, text=label,
                                     font=("Courier", 7), fill=tc, anchor="nw")

        for idx, layer in sorted(enumerate(self.layers),
                                   key=lambda x: x[1].get("z", 20)):
            photo, cx, cy = self._thumb(layer)
            if photo is None:
                continue
            self._tk_photos.append(photo)
            tag = f"L{idx}"
            self.canvas.create_image(cx, cy, image=photo, anchor="nw", tags=(tag,))
            if idx == self.selected:
                pw, ph = photo.width(), photo.height()
                self.canvas.create_rectangle(
                    cx-2, cy-2, cx+pw+2, cy+ph+2,
                    outline=G, width=2, dash=(4,2))
            self.canvas.tag_bind(tag, "<Button-1>",
                                  lambda e, i=idx: self._select(i))

    def _on_canvas_click(self, event):
        items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        if not items:
            self.selected = None
            self.render_canvas()
            self.update_panel()

    def _on_scroll_knob(self, event):
        self._record_event(event)
        num = getattr(event, "num", None)
        delta = getattr(event, "delta", 0)
        if num == 4:
            ticks = 1
        elif num == 5:
            ticks = -1
        else:
            if delta == 0:
                return
            # Trackpads and some mice emit many small deltas on macOS.
            # Normalize to at least one logical tick while preserving direction.
            ticks = delta / 120 if abs(delta) >= 120 else delta
            if ticks > 0:
                ticks = max(1, round(ticks))
            else:
                ticks = min(-1, round(ticks))
        if self.selected is None:
            self.canvas.yview_scroll(-ticks * 2, "units")
            return
        if self.focused_param is None:
            self.focus_param("size")
        self._knob_input(ticks)
        return "break"

    def _on_pointer_motion(self, event):
        x_root = getattr(event, "x_root", None)
        y_root = getattr(event, "y_root", None)
        if x_root is None or y_root is None:
            return None

        current = (x_root, y_root)
        previous = self._last_pointer
        self._last_pointer = current

        if previous is None:
            return None
        if self.selected is None or self.focused_param is None:
            return None

        dx = x_root - previous[0]
        dy = y_root - previous[1]
        dominant = dx if abs(dx) >= abs(dy) else dy
        if dominant == 0:
            return None

        # Some devices show up as pointer motion rather than wheel events.
        # Convert sustained motion into logical knob ticks.
        self._record_event(event, extra=f"motion={dominant}")
        self._motion_remainder += dominant
        threshold = 4.0
        if abs(self._motion_remainder) < threshold:
            return None

        ticks = int(self._motion_remainder / threshold)
        self._motion_remainder -= ticks * threshold
        if ticks:
            self._knob_input(ticks)
            return "break"
        return None

    def _on_up_key(self, _event):
        if self.selected is None:
            return None
        self._knob_input(+1)
        return "break"

    def _on_down_key(self, _event):
        if self.selected is None:
            return None
        self._knob_input(-1)
        return "break"

    def _on_any_key(self, event):
        self._record_event(event)
        key = getattr(event, "keysym", "")
        state = getattr(event, "state", 0)
        if state & 0x4:
            if key.lower() == "z":
                return self.undo(event)
            if key.lower() == "s":
                return self.save_layout(event)
            if key.lower() == "o":
                return self.add_asset()
            if key.lower() == "e":
                return self.export_html()
        if key in ("Up", "KP_Up", "w", "W", "k", "K"):
            return self._on_up_key(event)
        if key in ("Down", "KP_Down", "s", "S", "j", "J"):
            return self._on_down_key(event)
        if key in ("Left", "KP_Left"):
            self._nudge(-1, 0, event)
            return "break"
        if key in ("Right", "KP_Right"):
            self._nudge(1, 0, event)
            return "break"
        if key == "bracketleft":
            self.apply_delta("rot", -1)
            return "break"
        if key == "bracketright":
            self.apply_delta("rot", 1)
            return "break"
        if key == "equal":
            self.apply_delta("size", 10)
            return "break"
        if key == "minus":
            self.apply_delta("size", -10)
            return "break"
        if key == "Prior":
            self.apply_delta("z", 1)
            return "break"
        if key == "Next":
            self.apply_delta("z", -1)
            return "break"
        if key in ("h", "H"):
            self.toggle_visible()
            return "break"
        if key in ("r", "R"):
            self.full_render()
            return "break"
        return None

    def _record_event(self, event, extra=""):
        self._event_count += 1
        name = getattr(event, "keysym", "") or getattr(event, "type", "")
        delta = getattr(event, "delta", "")
        suffix = f" {extra}" if extra else ""
        self.event_var.set(f"  Input {self._event_count}: {name} delta={delta}{suffix}")

    def _knob_input(self, ticks):
        """Single entry point for all knob/arrow/scroll input."""
        if self.selected is None:
            return
        if self.focused_param is None:
            self.focus_param("size")
        sens = self._sensitivity.get()
        step = {
            "x": 20,
            "y": 20,
            "size": 24,
            "rot": 2.0,
            "z": 1,
        }.get(self.focused_param, 1)
        self.apply_delta(self.focused_param, ticks * sens * step)
        self.nob_dot.config(fg=G)
        self.nob_axis_var.set(f"{'▲' if ticks > 0 else '▼'}  {self.focused_param.upper()}")
        self.root.after(150, lambda: self.nob_dot.config(fg="#2a2520"))

    # ── SELECTION ────────────────────────────────────────────────────────────
    def _select(self, idx):
        self.selected = idx
        if self.focused_param is None:
            self.focus_param("size")
        self.render_canvas()
        self.update_panel()
        self.layer_list.selection_clear(0, tk.END)
        self.layer_list.selection_set(idx)
        self.layer_list.see(idx)
        self.canvas.focus_set()

    def _list_select(self, event):
        sel = self.layer_list.curselection()
        if sel:
            self._select(sel[0])

    def update_list(self):
        self.layer_list.delete(0, tk.END)
        for L in self.layers:
            name = os.path.splitext(L["file"])[0][:24]
            vis  = "●" if L.get("visible", True) else "○"
            self.layer_list.insert(tk.END, f"{vis} z{int(L.get('z',0)):>3}  {name}")

    def update_panel(self):
        if self.selected is None or self.selected >= len(self.layers):
            self.sel_label.config(text="— click an image —", fg="#555")
            for var in self.param_vars.values():
                var.set("—")
            return
        L = self.layers[self.selected]
        self.sel_label.config(text=f"  {L['file']}", fg=G)
        self.param_vars["x"].set(f"{L['x']:.0f}")
        self.param_vars["y"].set(f"{L['y']:.0f}")
        self.param_vars["size"].set(f"{L.get('size', 200):.0f}")
        self.param_vars["rot"].set(f"{L.get('rot', 0):.1f}")
        self.param_vars["z"].set(f"{int(L.get('z', 25))}")

    # ── APPLY DELTA ──────────────────────────────────────────────────────────
    def apply_delta(self, key, delta):
        if self.selected is None:
            return
        self.push_undo()
        L = self.layers[self.selected]
        if key == "x":
            L["x"] = L.get("x", 0) + delta
        elif key == "y":
            L["y"] = L.get("y", 0) + delta
        elif key == "size":
            L["size"] = max(10, L.get("size", 200) + delta)
        elif key == "rot":
            L["rot"] = round(L.get("rot", 0) + delta, 1)
        elif key == "z":
            L["z"] = max(1, int(L.get("z", 25) + delta))
        self._thumb_cache.clear()
        self.render_canvas()
        self.update_panel()
        if key == "z":
            self.update_list()

    def _nudge(self, dx, dy, event=None):
        step = 10 if (event and (event.state & 0x1)) else 1
        if dx: self.apply_delta("x", dx * step)
        if dy: self.apply_delta("y", dy * step)

    def toggle_visible(self):
        if self.selected is None:
            return
        self.push_undo()
        L = self.layers[self.selected]
        L["visible"] = not L.get("visible", True)
        self._thumb_cache.clear()
        self.render_canvas()
        self.update_list()

    def add_asset(self):
        file_path = filedialog.askopenfilename(
            title="Select image to add",
            initialdir=str(ROOT / "assets" / "originals"),
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"),
                ("All files", "*.*"),
            ],
        )
        if not file_path:
            return

        source = Path(file_path)
        if not source.exists():
            self.status("Asset not found")
            return

        originals_dir = ROOT / "assets" / "originals"
        originals_dir.mkdir(parents=True, exist_ok=True)
        dest = originals_dir / source.name
        if source.resolve() != dest.resolve():
            stem = dest.stem
            suffix = dest.suffix
            i = 2
            while dest.exists():
                dest = originals_dir / f"{stem}_{i}{suffix}"
                i += 1
            shutil.copy2(source, dest)

        try:
            with Image.open(dest) as src:
                width = max(min(src.width, 420), 120)
        except Exception:
            width = 260

        self.push_undo()
        next_z = max([int(layer.get("z", 20)) for layer in self.layers], default=20) + 1
        self.layers.append({
            "file": dest.name,
            "x": 120,
            "y": 120,
            "size": int(width),
            "rot": 0,
            "z": next_z,
            "visible": True,
        })
        self._photo_cache.pop(dest.name, None)
        self._thumb_cache.clear()
        self.selected = len(self.layers) - 1
        self.render_canvas()
        self.update_list()
        self.update_panel()
        self.layer_list.selection_clear(0, tk.END)
        self.layer_list.selection_set(self.selected)
        self.layer_list.see(self.selected)
        self.status(f"Added asset: {dest.name}")
        self.canvas.focus_set()

    # ── RENDER ───────────────────────────────────────────────────────────────
    def full_render(self):
        self.save_layout()
        self.status("Rendering…  (opens in Preview when done)")
        self.root.update()
        result = subprocess.run(
            [sys.executable, str(TOOLS_DIR / "collage.py")],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        if result.returncode == 0:
            self.status("Done → assets/renders/collage_preview.png")
        else:
            self.status("Render error — check terminal")
            print(result.stdout)
            print(result.stderr)

    def export_html(self):
        self.save_layout()
        self.status("Exporting HTML…")
        self.root.update()
        result = subprocess.run(
            [sys.executable, str(TOOLS_DIR / "export_layout_html.py")],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        if result.returncode == 0:
            self.status("Done → site/collage_generated.html")
        else:
            self.status("HTML export error — check terminal")
            print(result.stdout)
            print(result.stderr)

    def status(self, msg):
        self.status_var.set(f"  {msg}")
        self.root.update_idletasks()


def main():
    root = tk.Tk()
    root.geometry("1120x880")
    CollageGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
