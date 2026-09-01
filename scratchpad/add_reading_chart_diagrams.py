"""Add a small labelled chart diagram to each 'Reading a Chart' explainer PDF
(moving-averages, trend-lines, support-resistance, volume) — mirrors what
add_candlestick_diagram.py did for candlesticks-explainer.pdf, dropped into the
existing blank space on page 1 above the footer.
"""
import io

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas as rl_canvas

PURPLE = (0.486, 0.227, 0.929)
GREEN = (0.0, 0.62, 0.42)
RED = (0.83, 0.18, 0.18)
GRAY = (0.35, 0.38, 0.5)
DARK = (0.1, 0.11, 0.18)
BLUE = (0.23, 0.51, 0.96)

LEFT = 62.69
FOOTER_TOP = 822  # pdfplumber 'top' of footer line, constant across these templates
PAGE_H = 841.8898
PAGE_W = 595.2756


def label(c, x, y, text, align="left", size=8, color=GRAY, font="Helvetica"):
    c.setFillColorRGB(*color)
    c.setFont(font, size)
    if align == "left":
        c.drawString(x, y, text)
    elif align == "right":
        c.drawRightString(x, y, text)
    else:
        c.drawCentredString(x, y, text)


def heading_y(last_text_bottom):
    """Bottom-up y for the section heading, just under the last existing line."""
    gap_top = PAGE_H - last_text_bottom
    return gap_top - 22


# ── Moving Averages ─────────────────────────────────────────────────────────

def draw_moving_averages(c, base_y):
    x0 = LEFT + 10
    w = 430
    h = 110
    # price zigzag (raw, noisy)
    pts_price = [(0, 40), (40, 75), (80, 50), (120, 95), (160, 60), (200, 100),
                 (240, 70), (280, 40), (320, 55), (360, 20), (400, 30), (430, 15)]
    c.setStrokeColorRGB(*GRAY)
    c.setLineWidth(1.0)
    p = c.beginPath()
    p.moveTo(x0 + pts_price[0][0], base_y + pts_price[0][1])
    for px, py in pts_price[1:]:
        p.lineTo(x0 + px, base_y + py)
    c.drawPath(p, stroke=1, fill=0)

    # smoothed MA line
    pts_ma = [(0, 60), (60, 65), (120, 68), (180, 65), (240, 58), (300, 45),
              (360, 32), (430, 22)]
    c.setStrokeColorRGB(*BLUE)
    c.setLineWidth(2.2)
    p2 = c.beginPath()
    p2.moveTo(x0 + pts_ma[0][0], base_y + pts_ma[0][1])
    for px, py in pts_ma[1:]:
        p2.lineTo(x0 + px, base_y + py)
    c.drawPath(p2, stroke=1, fill=0)

    # death cross marker (MA crossing down through price early on) and golden cross later
    c.setFillColorRGB(*RED)
    c.circle(x0 + 120, base_y + 68, 3, fill=1, stroke=0)
    label(c, x0 + 120, base_y + 78, "Death cross", align="center", size=7, color=RED, font="Helvetica-Bold")

    c.setFillColorRGB(*GREEN)
    c.circle(x0 + 300, base_y + 45, 3, fill=1, stroke=0)
    label(c, x0 + 300, base_y - 12, "Golden cross", align="center", size=7, color=GREEN, font="Helvetica-Bold")

    # legend
    label(c, x0, base_y + h - 6, "— Price", size=7.5, color=GRAY)
    c.setStrokeColorRGB(*BLUE)
    c.setLineWidth(2.2)
    c.line(x0 + 55, base_y + h - 4, x0 + 75, base_y + h - 4)
    label(c, x0 + 80, base_y + h - 6, "50-day moving average", size=7.5, color=BLUE)


# ── Trend Lines ──────────────────────────────────────────────────────────────

def draw_trend_lines(c, base_y):
    x0 = LEFT + 10
    h = 100
    # uptrend: higher highs, higher lows
    pts = [(0, 20), (50, 55), (100, 35), (150, 70), (200, 50), (250, 85),
           (300, 62), (350, 95), (400, 80)]
    c.setStrokeColorRGB(*GRAY)
    c.setLineWidth(1.0)
    p = c.beginPath()
    p.moveTo(x0 + pts[0][0], base_y + pts[0][1])
    for px, py in pts[1:]:
        p.lineTo(x0 + px, base_y + py)
    c.drawPath(p, stroke=1, fill=0)

    # swing lows: (0,20) (100,35) (200,50) -> trend line through them, extended
    c.setStrokeColorRGB(*GREEN)
    c.setLineWidth(1.8)
    c.setDash(1, 0)
    c.line(x0 + 0, base_y + 20, x0 + 400, base_y + 20 + (400 / 200) * 30)

    for px, py in [(0, 20), (100, 35), (200, 50)]:
        c.setFillColorRGB(*GREEN)
        c.circle(x0 + px, base_y + py, 2.6, fill=1, stroke=0)

    label(c, x0 + 90, base_y - 14, "Uptrend line — connects the swing lows", size=7.5, color=GREEN, font="Helvetica-Bold")
    label(c, x0, base_y + h - 6, "Higher highs, higher lows = uptrend", size=7.5, color=GRAY)


# ── Support & Resistance ──────────────────────────────────────────────────────

def draw_support_resistance(c, base_y):
    x0 = LEFT + 10
    level_y = base_y + 38
    # dashed level line
    c.setStrokeColorRGB(*PURPLE)
    c.setLineWidth(1.3)
    c.setDash(3, 2)
    c.line(x0, level_y, x0 + 430, level_y)
    c.setDash(1, 0)

    # price bounces off level twice, then breaks through and retests as support
    pts = [(0, 15), (40, 33), (60, 38), (90, 15), (130, 30), (150, 38), (180, 10),
           (220, 38), (260, 55), (300, 38), (340, 60), (380, 45), (420, 60)]
    c.setStrokeColorRGB(*DARK)
    c.setLineWidth(1.1)
    p = c.beginPath()
    p.moveTo(x0 + pts[0][0], base_y + pts[0][1])
    for px, py in pts[1:]:
        p.lineTo(x0 + px, base_y + py)
    c.drawPath(p, stroke=1, fill=0)

    label(c, x0 + 60, level_y + 10, "resistance holds", align="center", size=6.5, color=GRAY)
    label(c, x0 + 260, level_y - 14, "breakout", align="center", size=6.5, color=GREEN, font="Helvetica-Bold")
    label(c, x0 + 400, level_y + 18, "old resistance =", align="center", size=6.5, color=PURPLE, font="Helvetica-Bold")
    label(c, x0 + 400, level_y + 10, "new support", align="center", size=6.5, color=PURPLE, font="Helvetica-Bold")


# ── Volume ──────────────────────────────────────────────────────────────────

def draw_volume(c, base_y):
    x0 = LEFT + 10
    price_base = base_y + 55
    # small price line up top
    pts = [(0, 8), (60, 14), (120, 10), (180, 20), (240, 16), (300, 40), (360, 35), (420, 44)]
    c.setStrokeColorRGB(*DARK)
    c.setLineWidth(1.1)
    p = c.beginPath()
    p.moveTo(x0 + pts[0][0], price_base + pts[0][1])
    for px, py in pts[1:]:
        p.lineTo(x0 + px, price_base + py)
    c.drawPath(p, stroke=1, fill=0)
    label(c, x0, price_base + 48, "Price", size=7, color=GRAY)

    # volume bars beneath, one bar spikes on the big move (last one)
    bar_heights = [6, 8, 5, 10, 7, 26, 9, 34]
    bar_xs = [px for px, _ in pts]
    c.setFillColorRGB(*GRAY)
    for i, (bx, bh) in enumerate(zip(bar_xs, bar_heights)):
        color = RED if i == len(bar_heights) - 1 else GRAY
        c.setFillColorRGB(*color)
        c.rect(x0 + bx - 8, base_y, 16, bh, fill=1, stroke=0)
    label(c, x0, base_y - 12, "Volume", size=7, color=GRAY)
    label(c, x0 + bar_xs[-1], base_y + bar_heights[-1] + 14, "high volume =",
          align="center", size=6.5, color=RED, font="Helvetica-Bold")
    label(c, x0 + bar_xs[-1], base_y + bar_heights[-1] + 6, "high conviction",
          align="center", size=6.5, color=RED, font="Helvetica-Bold")


JOBS = [
    ("static/downloads/moving-averages-explainer.pdf", "How It Looks on a Chart", 595, draw_moving_averages, 150),
    ("static/downloads/trend-lines-explainer.pdf", "How It Looks on a Chart", 657, draw_trend_lines, 130),
    ("static/downloads/support-resistance-explainer.pdf", "How It Looks on a Chart", 707, draw_support_resistance, 80),
    ("static/downloads/volume-explainer.pdf", "How It Looks on a Chart", 653, draw_volume, 130),
]


def build_overlay(page_w, page_h, heading, last_bottom, draw_fn, diagram_h):
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(page_w, page_h))
    hy = heading_y(last_bottom)
    c.setFillColorRGB(*PURPLE)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(LEFT, hy, heading)
    base_y = hy - diagram_h - 8
    draw_fn(c, base_y)
    c.save()
    buf.seek(0)
    return buf


def main():
    for path, heading, last_bottom, draw_fn, diagram_h in JOBS:
        reader = PdfReader(path)
        writer = PdfWriter()
        for pnum, page in enumerate(reader.pages):
            writer.add_page(page)
            if pnum == 0:
                wpage = writer.pages[-1]
                pw, ph = float(wpage.mediabox.width), float(wpage.mediabox.height)
                overlay = build_overlay(pw, ph, heading, last_bottom, draw_fn, diagram_h)
                overlay_reader = PdfReader(overlay)
                wpage.merge_page(overlay_reader.pages[0])
        with open(path, "wb") as f:
            writer.write(f)
        print("done:", path)


if __name__ == "__main__":
    main()
