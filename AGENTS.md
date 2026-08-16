# AGENTS.md

## Cursor Cloud specific instructions

This repo is a **static-website monorepo** with two independent products and **no backend, database, or package manager**:

- **UNO: Guardians of the Deep** — served from the repo root (`index.html`), a WebGL + GSAP interactive landing page. `uno-guardians-of-the-deep.html` is the self-contained offline deliverable (images base64-inlined).
- **Omniscience** — served from `/omniscience/`, a vanilla multi-page marketing site (`css/site.css`, `js/site.js`).

### Running (dev)

There is no dev-server command defined in the repo. Serve the static files from the repo root with any static server, e.g.:

```bash
python3 -m http.server 8000
# UNO:         http://localhost:8000/
# Omniscience: http://localhost:8000/omniscience/
```

Serve from the repo root (not `/omniscience/`) so UNO's `/assets/*` and the `/omniscience/` sub-site both resolve.

### Build

`python3 rebuild.py` regenerates `index.html` (web, references `/assets/*.webp`) and `uno-guardians-of-the-deep.html` (offline, base64-inlined) from `src/template.html` + `assets/*.webp`. It uses only the Python stdlib. Output is deterministic — re-running on an unchanged tree leaves git clean. Run it after editing `src/template.html` or swapping assets.

### Notes / gotchas

- No lint config and no test runner exist. The `README.md` references `src/app.js` and `python test.py`, but **neither file exists** in the repo (the WebGL engine is inlined in the HTML; there is no Playwright test).
- `src/process.py` (image optimization) needs `opencv-python`, `numpy`, `Pillow` (undeclared) and has hard-coded absolute paths, so it will not run as-is. It is not part of the normal dev/test flow.
- Fonts (Google Fonts) and the YouTube trailer embed load from the internet and degrade gracefully offline.
