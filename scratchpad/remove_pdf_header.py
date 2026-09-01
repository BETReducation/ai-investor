"""Remove the top-of-page 'GROWTH CAPITAL GROUP' header (logo icon + text) from
every lesson PDF's cover page — it sat right under the coloured top stripe
with barely any margin, and the identical branding already appears in the
footer.

The header/footer logo instances are identified by their actual cumulative
Y position on the page (tracked through the q/Q graphics-state stack and
each cm's translation), not by their order in the content stream — that
order isn't consistent across the ~4 template variants these 45 PDFs were
built from, and assuming otherwise silently removed the wrong instance on
one template family. Whichever image Do call sits higher up the page (top
half) is the header and gets removed; the lower one (footer) is left alone.
"""
import glob
import sys

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream


def find_top_image_do_index(ops, page_h):
    """Return the index into `ops` of the image Do call with the highest
    cumulative Y position, if that position is in the top half of the page
    (i.e. it's a header, not a footer) — else None."""
    y_stack = [0.0]
    candidates = []  # (cumulative_y, index)
    for i, (operands, operator) in enumerate(ops):
        if operator == b"q":
            y_stack.append(y_stack[-1])
        elif operator == b"Q":
            if len(y_stack) > 1:
                y_stack.pop()
        elif operator == b"cm":
            # operands: [a, b, c, d, e, f] — approximate by just adding the
            # translation component; every cm seen in these files is either
            # a pure translate or a pure scale, so this ranks correctly.
            y_stack[-1] += float(operands[5])
        elif operator == b"Do" and str(operands[0]).startswith("/FormXob"):
            candidates.append((y_stack[-1], i))

    if not candidates:
        return None
    candidates.sort(key=lambda t: t[0], reverse=True)
    top_y, top_idx = candidates[0]
    if top_y <= page_h / 2:
        return None  # the topmost instance isn't actually in the top half — don't touch it
    return top_idx


def process(path):
    reader = PdfReader(path)
    writer = PdfWriter()

    for pnum, page in enumerate(reader.pages):
        writer.add_page(page)
        wpage = writer.pages[-1]

        # Only the cover page carries the standalone "GROWTH CAPITAL GROUP"
        # brand header — continuation pages show a running header (lesson
        # title + tag) instead, which is useful and stays untouched.
        if pnum != 0:
            continue

        page_h = float(wpage.mediabox.height)
        cs = ContentStream(wpage.get_contents(), writer)
        ops = cs.operations

        header_do_idx = find_top_image_do_index(ops, page_h)

        new_ops = []
        removed_logo = removed_text = False
        for i, (operands, operator) in enumerate(ops):
            if i == header_do_idx:
                removed_logo = True
                continue
            if operator == b"Tj" and str(operands[0]) == "GROWTH CAPITAL GROUP":
                removed_text = True
                continue
            new_ops.append((operands, operator))

        cs.operations = new_ops
        wpage.replace_contents(cs)
        if not removed_logo:
            print("  WARNING:", path, "no header-position logo found (left untouched)")

    with open(path, "wb") as f:
        writer.write(f)


if __name__ == "__main__":
    targets = sys.argv[1:] or sorted(glob.glob("static/downloads/*.pdf"))
    for path in targets:
        process(path)
        print("done:", path)
