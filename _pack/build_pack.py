"""Build the downloadable camp pack PDF.

    camp brief (out/brief.pdf, page 1)
  + Luqman's schedule pages (schedule-source.pdf, with the fixes below)
  + fees, school package and FAQs (out/brief.pdf, page 2)
  = assets/KL-Debate-Orators-Camp-2026-Camp-Pack.pdf

Fixes applied to the schedule pages when the old wording is found
(if the source PDF is already correct, nothing is changed):
  * "KL DEBATE CAMP" -> "KL DEBATE ORATORS CAMP" in the letter-spaced headers
  * ages "7 to 20" / "16-20" -> "7 to 19" / "16-19"

Run `node render.js` first to produce out/brief.pdf.
"""
import os
import re
import sys

import pymupdf
from pypdf import PdfReader, PdfWriter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SOURCE = os.path.join(HERE, "schedule-source.pdf")
BRIEF = os.path.join(HERE, "out", "brief.pdf")
PATCHED = os.path.join(HERE, "out", "schedule-patched.pdf")
OUTPUT = os.path.join(ROOT, "assets", "KL-Debate-Orators-Camp-2026-Camp-Pack.pdf")

FONT_DIRS = [os.path.join(HERE, "fonts"), "/usr/share/fonts"]


def find_font(names):
    for d in FONT_DIRS:
        for dirpath, _, files in os.walk(d):
            for f in files:
                if f in names:
                    return os.path.join(dirpath, f)
    sys.exit("Font not found: %s" % names)


def font_for(span_font):
    if "Mono" in span_font:
        return find_font({"DejaVuSansMono.ttf"})
    if "Poppins" in span_font:
        return find_font({"Poppins-Medium.ttf"})
    return find_font({"Inter-Regular.otf", "Inter-Regular.ttf"})


def rgb(c):
    return ((c >> 16) & 255) / 255, ((c >> 8) & 255) / 255, (c & 255) / 255


def background(pix, rect):
    pts = [(rect.x0 - 3, rect.y0 + 2), (rect.x1 + 3, rect.y0 + 2), (rect.x0 + 1, rect.y0 - 1.2),
           (rect.x1 - 1, rect.y0 - 1.2), (rect.x0 + 1, rect.y1 + 1.0)]
    vals = []
    for x, y in pts:
        x, y = int(x * 2), int(y * 2)
        if 0 <= x < pix.width and 0 <= y < pix.height:
            vals.append(pix.pixel(x, y))
    return tuple(v / 255 for v in max(vals, key=sum))


def spaced_text(letters):
    """Rebuild a letter-spaced string (mono header) and return (text, pitch)."""
    xs = [c["origin"][0] for c in letters]
    pitch = min(b - a for a, b in zip(xs, xs[1:]) if b - a > 0.5)
    out = letters[0]["c"]
    for prev, cur in zip(letters, letters[1:]):
        gap = round((cur["origin"][0] - prev["origin"][0]) / pitch)
        out += " " * (gap - 1) + cur["c"]
    return out, pitch


def patch(doc):
    changes = 0
    for page in doc:
        pix = page.get_pixmap(dpi=144)
        jobs = []
        for block in page.get_text("rawdict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    chars = span["chars"]
                    letters = [c for c in chars if c["c"] != " "]
                    if not letters:
                        continue
                    flat = "".join(c["c"] for c in letters)
                    rect = pymupdf.Rect(span["bbox"])
                    # 1) camp name in the letter-spaced mono headers
                    if "KLDEBATECAMP" in flat and "Mono" in span["font"]:
                        text, pitch = spaced_text(letters)
                        new = text.replace("KL DEBATE CAMP", "KL DEBATE ORATORS CAMP")
                        x_first, x_last = letters[0]["origin"][0], letters[-1]["origin"][0]
                        right_aligned = rect.x1 > page.rect.width * 0.85 and rect.y0 < 40
                        start = x_last - pitch * (len(new) - 1) if right_aligned else x_first
                        jobs.append(("chars", rect, new, start, pitch, letters[0]["origin"][1], span))
                        continue
                    # 2) ages 20 -> 19
                    for key in ("ages7to20", "Ages16–20", "AGES16–20"):
                        k = flat.find(key)
                        if k < 0:
                            continue
                        c2, c0 = letters[k + len(key) - 2], letters[k + len(key) - 1]
                        r = pymupdf.Rect(c2["bbox"]) | pymupdf.Rect(c0["bbox"])
                        if "Mono" in span["font"]:
                            pitch = c0["origin"][0] - c2["origin"][0]
                            jobs.append(("chars", r, "19", c2["origin"][0], pitch, c2["origin"][1], span))
                        else:
                            jobs.append(("word", r, "19", c2["origin"][0], 0, c2["origin"][1], span))
        if not jobs:
            continue
        for _, r, *_rest in jobs:
            page.add_redact_annot(r, fill=background(pix, r))
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)
        fonts = {}
        for kind, r, text, x, pitch, y, span in jobs:
            path = font_for(span["font"])
            if path not in fonts:
                fonts[path] = "F%d" % len(fonts)
                page.insert_font(fontname=fonts[path], fontfile=path)
            fn = fonts[path]
            if kind == "chars":
                for i, ch in enumerate(text):
                    if ch != " ":
                        page.insert_text((x + i * pitch, y), ch, fontname=fn, fontsize=span["size"], color=rgb(span["color"]))
            else:
                page.insert_text((x, y), text, fontname=fn, fontsize=span["size"], color=rgb(span["color"]))
            changes += 1
    return changes


def main():
    if not os.path.exists(BRIEF):
        sys.exit("Run `node render.js` first (out/brief.pdf is missing).")
    doc = pymupdf.open(SOURCE)
    n = patch(doc)
    doc.save(PATCHED, garbage=3, deflate=True)
    print("Schedule pages: %d page(s), %d fix(es) applied" % (doc.page_count, n))

    brief = PdfReader(BRIEF)
    sched = PdfReader(PATCHED)
    out = PdfWriter()
    out.add_page(brief.pages[0])
    for p in sched.pages:
        out.add_page(p)
    out.add_page(brief.pages[1])
    out.add_metadata({"/Title": "Kuala Lumpur Debate Orators Camp 2026 — Camp brief, schedule, fees and FAQs"})
    with open(OUTPUT, "wb") as f:
        out.write(f)
    print("Wrote", os.path.relpath(OUTPUT, ROOT), "(%d pages)" % (len(brief.pages) + len(sched.pages)))


if __name__ == "__main__":
    main()
