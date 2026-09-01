"""Rebrand the lesson PDFs: swap the embedded GCA logo for GCE Square.png,
and rewrite the branding text directly in each page's content stream (true
replacement, not a visual-only redaction — old text would otherwise still
be present underneath and show up in copy-paste/search/screen readers).
"""
import glob
import sys

from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, TextStringObject

NEW_LOGO = Image.open("static/logos/GCE Square.png")

TEXT_REPLACEMENTS = [
    ("GROWTH CAPITAL ACADEMY", "GROWTH CAPITAL GROUP"),
    ("Growth Capital Academy", "Growth Capital Group"),
    ("growthcapitalacademy.com", "growthcapitalgroup.org"),
]


def process(path):
    reader = PdfReader(path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)
        wpage = writer.pages[-1]

        # 1. Swap the embedded logo image(s) on this page.
        for img in wpage.images:
            if img.image.size == (914, 920):
                img.replace(NEW_LOGO)

        # 2. Rewrite the branding text directly in the content stream.
        cs = ContentStream(wpage.get_contents(), wpage.pdf if hasattr(wpage, "pdf") else writer)
        changed = False
        for operands, operator in cs.operations:
            if operator not in (b"Tj",):
                continue
            s = operands[0]
            text = str(s)
            new_text = text
            for old, new in TEXT_REPLACEMENTS:
                if old in new_text:
                    new_text = new_text.replace(old, new)
            if new_text != text:
                operands[0] = TextStringObject(new_text)
                changed = True
        if changed:
            wpage.replace_contents(cs)

    with open(path, "wb") as f:
        writer.write(f)


if __name__ == "__main__":
    targets = sys.argv[1:] or sorted(glob.glob("static/downloads/*.pdf"))
    for path in targets:
        process(path)
        print("done:", path)
