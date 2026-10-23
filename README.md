# KL Debate Bootcamp website

Static website for the KL Debate Bootcamp (December 2026, TEDOH, Kuala Lumpur).

- `index.html` – bootcamp landing page
- `international-school-package.html` – International School Package page
- `assets/` – photos and logos

There is no build step: Netlify publishes this folder as it is.
The design is edited on the "KL Debate Bootcamp Landing Page" canvas and re-exported here,
so make changes on the canvas rather than editing these files by hand.

## Re-exporting from the canvas
`_tools/build.py` converts the canvas artboards (`Main.dc.html`, `Schools.dc.html`) into these two pages.
It needs the canvas files and a JSON map of canvas image ids to local image files:
`python3 _tools/build.py <canvas project folder> <assets_map.json> <output folder>`.
