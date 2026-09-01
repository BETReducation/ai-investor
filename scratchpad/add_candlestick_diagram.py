"""Add a labelled candlestick anatomy diagram to candlesticks-explainer.pdf's
first page — the lesson describes bodies/wicks/colour in detail but never
actually shows one, so a reader with no prior chart exposure has nothing to
look at.
"""
import io

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas as rl_canvas

PATH = "static/downloads/candlesticks-explainer.pdf"

PURPLE = (0.486, 0.227, 0.929)
GREEN = (0.0, 0.62, 0.42)
RED = (0.83, 0.18, 0.18)
GRAY = (0.35, 0.38, 0.5)
DARK = (0.1, 0.11, 0.18)


def draw_candle(c, x, open_y, close_y, low_y, high_y, width, bullish):
    color = GREEN if bullish else RED
    # wick
    c.setStrokeColorRGB(*GRAY)
    c.setLineWidth(1.3)
    c.line(x, low_y, x, high_y)
    # body
    body_bottom = min(open_y, close_y)
    body_top = max(open_y, close_y)
    if bullish:
        c.setStrokeColorRGB(*color)
        c.setFillColorRGB(1, 1, 1)
        c.setLineWidth(1.6)
        c.rect(x - width / 2, body_bottom, width, body_top - body_bottom, fill=1, stroke=1)
    else:
        c.setFillColorRGB(*color)
        c.setStrokeColorRGB(*color)
        c.rect(x - width / 2, body_bottom, width, body_top - body_bottom, fill=1, stroke=1)


def label(c, x, y, text, align="left", size=8, color=GRAY, font="Helvetica"):
    c.setFillColorRGB(*color)
    c.setFont(font, size)
    if align == "left":
        c.drawString(x, y, text)
    elif align == "right":
        c.drawRightString(x, y, text)
    else:
        c.drawCentredString(x, y, text)


def build_overlay(page_w, page_h):
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(page_w, page_h))

    left = 62.69
    top_y = 300  # bottom-up y where the section starts (below existing body text)

    # Section heading, matching the doc's existing h2 style.
    c.setFillColorRGB(*PURPLE)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(left, top_y, "What a Candlestick Actually Looks Like")

    # ── Labelled anatomy candle (bullish) ───────────────────────────────
    anat_x = left + 70
    low_y, high_y = 130, 260
    open_y, close_y = 155, 235
    body_w = 26
    draw_candle(c, anat_x, open_y, close_y, low_y, high_y, body_w, bullish=True)

    def leader(y, text, label_x):
        c.setStrokeColorRGB(*GRAY)
        c.setLineWidth(0.6)
        c.line(anat_x + body_w / 2 + 4, y, label_x - 4, y)
        label(c, label_x, y - 3, text, size=8.5, color=DARK, font="Helvetica-Bold")

    label_x = anat_x + 55
    leader(high_y, "High — the peak price", label_x)
    leader(close_y, "Close — price at the end", label_x)
    leader(open_y, "Open — price at the start", label_x)
    leader(low_y, "Low — the trough price", label_x)

    # Wick / body braces on the left of the candle
    c.setStrokeColorRGB(*GRAY)
    c.setLineWidth(0.6)
    wick_label_x = anat_x - 14
    c.line(wick_label_x, close_y, wick_label_x, high_y)
    c.line(wick_label_x, low_y, wick_label_x, open_y)
    label(c, wick_label_x - 4, (close_y + high_y) / 2 - 3, "wick", align="right", size=7.5, color=GRAY)
    label(c, wick_label_x - 4, (low_y + open_y) / 2 - 3, "wick", align="right", size=7.5, color=GRAY)
    body_label_x = anat_x - 14
    label(c, body_label_x - 4, (open_y + close_y) / 2 - 3, "body", align="right", size=7.5, color=GRAY)
    c.line(body_label_x, open_y, body_label_x, close_y)

    label(c, anat_x, low_y - 22, "BULLISH", align="center", size=9, color=GREEN, font="Helvetica-Bold")
    label(c, anat_x, low_y - 33, "close above open", align="center", size=7.5, color=GRAY)

    # ── Small bearish candle beside it, for direct colour contrast ─────
    bear_x = anat_x + 235
    draw_candle(c, bear_x, close_y, open_y, low_y, high_y, body_w, bullish=False)
    label(c, bear_x, low_y - 22, "BEARISH", align="center", size=9, color=RED, font="Helvetica-Bold")
    label(c, bear_x, low_y - 33, "close below open", align="center", size=7.5, color=GRAY)

    c.save()
    buf.seek(0)
    return buf


def main():
    reader = PdfReader(PATH)
    writer = PdfWriter()
    for pnum, page in enumerate(reader.pages):
        writer.add_page(page)
        if pnum == 0:
            wpage = writer.pages[-1]
            pw, ph = float(wpage.mediabox.width), float(wpage.mediabox.height)
            overlay = build_overlay(pw, ph)
            overlay_reader = PdfReader(overlay)
            wpage.merge_page(overlay_reader.pages[0])
    with open(PATH, "wb") as f:
        writer.write(f)
    print("done:", PATH)


if __name__ == "__main__":
    main()
