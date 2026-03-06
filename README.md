# Zelda Design Co. Workspace

Website concept workspace for Alessandra (Zelda Design Co.), including:
- source photo assets,
- a browser layout editor,
- versioned layout data snapshots,
- render + HTML export tools.

## Folder layout

- `assets/originals/` - original photos/images used in collages.
- `assets/renders/` - generated render outputs.
- `data/layouts/layout.json` - current working layout data.
- `data/layouts/history/` - timestamped layout snapshots (datalog versions).
- `site/layout_editor.html` - browser-based layout editor with drag/resize/rotate and JSON/HTML export.
- `site/index.html` - branded exported homepage generated from the current layout JSON.
- `site/editor_data.js` - embedded asset manifest and starting layout for the browser editor.
- `tools/collage_gui.py` - older Tk editor (kept for reference, not the main path).
- `tools/collage.py` - Pillow compositor (image render output).
- `tools/export_layout_html.py` - compiles layout data to static HTML.
- `site/` - generated web output.
- `prototypes/` - earlier static HTML experiments.

## Python setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Main workflow

Open the browser editor:

```bash
open site/layout_editor.html
```

In the browser editor:
- drag layers directly on the stage
- use the resize and rotate handles on the selected layer
- use arrow keys and mouse wheel against the active parameter
- download JSON or HTML from the toolbar
- save local snapshots in browser storage

The older Tk editor is still present, but it is no longer the recommended workflow.

## CLI commands

Render image from current layout:

```bash
python3 tools/collage.py
```

Compile layout to HTML:

```bash
python3 tools/export_layout_html.py
```

This writes the branded homepage to `site/index.html`.

Optional (Node): regenerate `assets/renders/magazine_render.png` from prototype:

```bash
npm run screenshot:magazine
```

## GitHub Pages

The current shareable static export is prepared in `docs/` for GitHub Pages.

Files:
- `docs/index.html` - latest exported static page
- `docs/assets/` - copied asset bundle for Pages hosting
- `docs/.nojekyll` - disables Jekyll processing

Deploy:

1. Create a GitHub repo and push this project.
2. In GitHub, open `Settings` -> `Pages`.
3. Under `Build and deployment`, choose:
   - `Source`: `Deploy from a branch`
   - `Branch`: `main`
   - `Folder`: `/docs`
4. Save. GitHub will publish the site at:
   - `https://<your-github-username>.github.io/<repo-name>/`

The `docs/` folder is the current best artifact to share with Alessandra for browser review.
