# Kuala Lumpur Debate Orators Camp website

Static website for the Kuala Lumpur Debate Orators Camp (December 2026, TEDOH, Kuala Lumpur),
published at https://bootcamp.kualalumpurdebate.com with GitHub Pages.

- `index.html` – camp landing page
- `international-school-package.html` – International School Package page
- `assets/` – photos, logos and the downloadable camp pack PDF
- `_pack/` – sources for the camp pack PDF (see below)
- `.github/workflows/publish.yml` – rebuilds the camp pack and publishes the site on every change

The design is edited on the "Kuala Lumpur Debate Orators Camp Landing Page" canvas and re-exported here,
so make changes on the canvas rather than editing the HTML by hand.

## Camp pack PDF (the "Download the full schedule (PDF)" button)

`assets/KL-Debate-Orators-Camp-2026-Camp-Pack.pdf` is built automatically from:

1. `_pack/brief.html` – the camp brief (front page) and the fees, school package and FAQs page (page 5)
2. `_pack/schedule-source.pdf` – the four schedule pages, exactly as designed

When the schedule changes, replace `_pack/schedule-source.pdf` with the new PDF (same file name;
on GitHub: open the `_pack` folder → Add file → Upload files → commit). The workflow then rebuilds the
pack and republishes the site within a few minutes. If the uploaded schedule still says "KL DEBATE CAMP"
or ages "7 to 20" / "16–20", the build fixes those to "KL DEBATE ORATORS CAMP" and 19 automatically.

To build it locally: `cd _pack && npm ci && node render.js && python3 build_pack.py`
(needs Python with `pymupdf` and `pypdf`).

## Re-exporting from the canvas
`_tools/build.py` converts the canvas artboards (`Main.dc.html`, `Schools.dc.html`) into the two pages.
It needs the canvas files and a JSON map of canvas file ids to local files:
`python3 _tools/build.py <canvas project folder> <assets_map.json> <output folder>`.
