"""Generate the 3 downloadable PDFs for the new Intermediate 'Chart Patterns' lesson:
chart-patterns-explainer.pdf, -worksheet.pdf, -further-reading.pdf.

Matches the established GCG PDF branding (4-color top/bottom ribbon, rotating
section-heading accent colors, Helvetica type) reverse-engineered from
support-resistance-explainer.pdf, but with WIDER gaps between sections per
Gary's 2026-09-01 instruction: from Intermediate onward, PDFs should feel less
cramped than the Beginner-track ones (which are left as-is).
"""
import textwrap

from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.colors import Color

PAGE_W, PAGE_H = 595.2756, 841.8898
LEFT = 62.69291
RIGHT = PAGE_W - LEFT
CONTENT_W = RIGHT - LEFT

PURPLE = Color(0.486275, 0.227451, 0.929412)
TEAL = Color(0.0, 0.831373, 0.666667)
GREEN = Color(0.290196, 0.870588, 0.501961)
GOLD = Color(0.960784, 0.72549, 0.258824)
DARK = Color(0.078431, 0.094118, 0.14902)
GRAY = Color(0.356863, 0.392157, 0.470588)
RIBBON = [PURPLE, TEAL, GREEN, GOLD]

# Wider spacing for Intermediate onward (Beginner used tighter values, left alone).
SECTION_GAP = 40
PARA_GAP = 17
LINE_H = 14.5
BODY_SIZE = 9.5
FOOTER_Y = 24


def ribbon(c):
    seg = PAGE_W / 4
    for i, col in enumerate(RIBBON):
        c.setFillColor(col)
        c.rect(i * seg, PAGE_H - 6, seg, 6, fill=1, stroke=0)
        c.rect(i * seg, 0, seg, 6, fill=1, stroke=0)


def footer(c, title, page_num):
    c.setFont("Helvetica", 8)
    c.setFillColor(GRAY)
    c.drawString(LEFT, FOOTER_Y, f"{title} Growth Capital Group")
    c.drawRightString(RIGHT, FOOTER_Y, f"growthcapitalgroup.org   Page {page_num}")


def running_header(c, title):
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(GRAY)
    c.drawString(LEFT, PAGE_H - 22, title.upper())


def wrap(text, width_chars):
    return textwrap.wrap(text, width_chars)


def draw_body(c, y, text, size=BODY_SIZE, color=DARK, bold_lead=None, width_chars=98):
    """Very simple wrapper: draws left-aligned paragraph, returns new y."""
    c.setFont("Helvetica", size)
    c.setFillColor(color)
    lines = wrap(text, width_chars)
    for line in lines:
        c.drawString(LEFT, y, line)
        y -= LINE_H
    return y


def draw_heading(c, y, text, color, size=13):
    c.setFont("Helvetica-Bold", size)
    c.setFillColor(color)
    c.drawString(LEFT, y, text)
    return y - (size + 6)


def new_page(c, title_tag, page_num, running=True):
    ribbon(c)
    if running:
        running_header(c, title_tag)
    footer(c, title_tag, page_num)


# ── Pattern diagrams (vector) ────────────────────────────────────────────────

def draw_head_shoulders(c, x0, y0, w, h):
    pts = [(0, 0.15), (0.14, 0.55), (0.29, 0.15), (0.43, 0.95), (0.57, 0.15),
           (0.71, 0.6), (0.86, 0.2), (1.0, 0.02)]
    c.setStrokeColor(GRAY)
    c.setLineWidth(0.6)
    c.setDash(3, 2)
    c.line(x0, y0 + 0.15 * h, x0 + w, y0 + 0.11 * h)
    c.setDash(1, 0)
    c.setStrokeColor(DARK)
    c.setLineWidth(1.6)
    p = c.beginPath()
    p.moveTo(x0 + pts[0][0] * w, y0 + pts[0][1] * h)
    for px, py in pts[1:]:
        p.lineTo(x0 + px * w, y0 + py * h)
    c.drawPath(p, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(PURPLE)
    c.drawCentredString(x0 + w * 0.5, y0 + h + 10, "Head & Shoulders Top")
    c.setFont("Helvetica", 7)
    c.setFillColor(GRAY)
    c.drawCentredString(x0 + 0.14 * w, y0 + 0.55 * h + 8, "L")
    c.drawCentredString(x0 + 0.43 * w, y0 + 0.95 * h + 8, "Head")
    c.drawCentredString(x0 + 0.71 * w, y0 + 0.6 * h + 8, "R")
    c.drawString(x0, y0 - 12, "Neckline break confirms reversal")


def draw_double_top(c, x0, y0, w, h):
    pts = [(0, 0.05), (0.22, 0.9), (0.45, 0.25), (0.68, 0.9), (1.0, 0.05)]
    c.setStrokeColor(GRAY)
    c.setLineWidth(0.6)
    c.setDash(3, 2)
    c.line(x0, y0 + 0.25 * h, x0 + w, y0 + 0.25 * h)
    c.setDash(1, 0)
    c.setStrokeColor(DARK)
    c.setLineWidth(1.6)
    p = c.beginPath()
    p.moveTo(x0 + pts[0][0] * w, y0 + pts[0][1] * h)
    for px, py in pts[1:]:
        p.lineTo(x0 + px * w, y0 + py * h)
    c.drawPath(p, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(PURPLE)
    c.drawCentredString(x0 + w * 0.5, y0 + h + 10, "Double Top")
    c.setFont("Helvetica", 7)
    c.setFillColor(GRAY)
    c.drawString(x0, y0 - 12, "Break below the middle low confirms reversal")


def draw_triangle(c, x0, y0, w, h):
    pts = [(0, 0.05), (0.18, 0.9), (0.36, 0.35), (0.54, 0.75), (0.72, 0.45),
           (0.86, 0.6), (1.0, 0.5)]
    c.setStrokeColor(GREEN)
    c.setLineWidth(0.6)
    c.setDash(3, 2)
    c.line(x0, y0 + 0.05 * h, x0 + w * 0.86, y0 + 0.55 * h)
    c.line(x0, y0 + 0.9 * h, x0 + w * 0.86, y0 + 0.6 * h)
    c.setDash(1, 0)
    c.setStrokeColor(DARK)
    c.setLineWidth(1.6)
    p = c.beginPath()
    p.moveTo(x0 + pts[0][0] * w, y0 + pts[0][1] * h)
    for px, py in pts[1:]:
        p.lineTo(x0 + px * w, y0 + py * h)
    c.drawPath(p, stroke=1, fill=0)
    c.setStrokeColor(GREEN)
    c.setLineWidth(2.0)
    c.line(x0 + w * 0.86, y0 + h * 0.58, x0 + w, y0 + h * 0.95)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(PURPLE)
    c.drawCentredString(x0 + w * 0.5, y0 + h + 10, "Triangle")
    c.setFont("Helvetica", 7)
    c.setFillColor(GRAY)
    c.drawString(x0, y0 - 12, "Converging lines — breakout can go either way")


# ── EXPLAINER ────────────────────────────────────────────────────────────────

def build_explainer():
    path = "static/downloads/chart-patterns-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Chart Patterns — Lesson Explainer"

    # PAGE 1
    new_page(c, TAG, 1, running=False)
    y = PAGE_H - 90
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(DARK)
    c.drawString(LEFT, y, "Chart Patterns")
    y -= 26
    c.setFont("Helvetica", 10.5)
    c.setFillColor(GRAY)
    c.drawString(LEFT, y, "Head & Shoulders, Double Tops, Triangles — Lesson Explainer")
    y -= SECTION_GAP

    y = draw_heading(c, y, "The Concept", PURPLE)
    y = draw_body(c, y, "A chart pattern is a recognizable shape formed by price over time - not a random "
                         "squiggle, but a repeating footprint left by the same crowd behaviors: buyers and "
                         "sellers testing a level, losing conviction, and eventually giving way.")
    y -= PARA_GAP
    y = draw_body(c, y, "Patterns split into two camps: reversal patterns (head & shoulders, double tops) "
                         "that suggest a trend is running out of steam, and continuation patterns (triangles) "
                         "that suggest a pause before the existing trend resumes.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "The Three Patterns", TEAL)
    diagram_top = y - 10
    dw = (CONTENT_W - 40) / 3
    dh = 90
    draw_head_shoulders(c, LEFT, diagram_top - dh, dw, dh)
    draw_double_top(c, LEFT + dw + 20, diagram_top - dh, dw, dh)
    draw_triangle(c, LEFT + 2 * (dw + 20), diagram_top - dh, dw, dh)
    y = diagram_top - dh - 34

    c.showPage()

    # PAGE 2
    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "Illustrative Walkthrough: A Head & Shoulders Top", GREEN)
    y = draw_body(c, y, "Real head-and-shoulders tops don't come with round numbers, so here's a clean "
                         "illustrative version to see the mechanics clearly.")
    y -= PARA_GAP

    rows = [
        ("Left shoulder", "$118", "First peak, uptrend still looks healthy"),
        ("Neckline (low after left shoulder)", "$100", "Key support level to watch"),
        ("Head", "$130", "Higher peak - but often on weaker volume"),
        ("Right shoulder", "$117", "Fails to reach the head's high - momentum fading"),
        ("Neckline break", "$99", "Pattern confirms - reversal underway"),
    ]
    POINT_X, PRICE_X, ROLE_X = LEFT + 6, LEFT + 210, LEFT + 260
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(PURPLE)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(Color(1, 1, 1))
    c.drawString(POINT_X, y - 12, "Point")
    c.drawString(PRICE_X, y - 12, "Price")
    c.drawString(ROLE_X, y - 12, "Role")
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (a, b, d) in enumerate(rows):
        role_lines = wrap(d, 44)
        row_h = max(18, 12 * len(role_lines) + 6)
        if i % 2 == 1:
            c.setFillColor(Color(0.95, 0.95, 0.97))
            c.rect(LEFT, y - row_h + 2, CONTENT_W, row_h, fill=1, stroke=0)
        c.setFillColor(DARK)
        c.drawString(POINT_X, y - 12, a)
        c.drawString(PRICE_X, y - 12, b)
        c.setFillColor(GRAY)
        for j, line in enumerate(role_lines):
            c.drawString(ROLE_X, y - 12 - j * 12, line)
        y -= row_h + 2
    y -= 10
    y = draw_body(c, y, "The classic 'measured move' price target after confirmation is the head-to-neckline "
                         "distance projected below the neckline: $130 - $100 = $30, so $100 - $30 = $70 as a "
                         "rough downside target. It's a rule of thumb, not a guarantee.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "5 Things to Know About Chart Patterns", GOLD)
    facts = [
        "A pattern isn't confirmed until the key line breaks - plenty of near-misses never confirm.",
        "Volume should support the story - ideally fading through formation, picking up on breakout.",
        "The measured move is a rule of thumb, not a promise.",
        "Triangles can break either way - wait for the actual breakout, don't assume direction.",
        "Patterns are probabilistic, not mechanical - false patterns and failed breakouts happen.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    c.setFillColor(Color(0.98, 0.94, 0.86))
    box_h = 46
    c.rect(LEFT, y - box_h, CONTENT_W, box_h, fill=1, stroke=0)
    c.setStrokeColor(GOLD)
    c.setLineWidth(3)
    c.line(LEFT, y, LEFT, y - box_h)
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(DARK)
    c.drawString(LEFT + 12, y - 16, "Worth knowing:")
    c.setFont("Helvetica", 8.5)
    for i, line in enumerate(wrap(
        "chart patterns describe how crowds have behaved before - a probability tool, not a "
        "prediction machine. Always pair a pattern with volume and the broader trend.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    # PAGE 3 — Quiz
    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", PURPLE, size=12)
    y -= 10

    questions = [
        ("1. In a head & shoulders top, what does the \"neckline\" represent?", [
            "A. The highest price the head reaches",
            "B. The support level connecting the lows between the shoulders and the head",
            "C. The average of all three peaks",
            "D. The 200-day moving average"]),
        ("2. What distinguishes a double top from a random pair of highs?", [
            "A. The two highs must be on the exact same calendar day",
            "B. A double top has no confirming level at all",
            "C. Two similar highs failing at the same resistance, then a break below the middle low",
            "D. The pattern only appears on weekly charts"]),
        ("3. Why can't a triangle be assumed to break with the prior trend?", [
            "A. Triangles only ever form at market tops",
            "B. Triangles always break downward regardless of trend",
            "C. Triangles are not a real pattern",
            "D. The lines can resolve either way - wait for the actual breakout"]),
        ("4. Neckline $100, head $130 - what is the rough measured-move target?", [
            "A. $70", "B. $130", "C. $30", "D. $100"]),
        ("5. Why trust a neckline break on high volume more than on thin volume?", [
            "A. Volume has no relationship to pattern reliability",
            "B. High volume always means an immediate reversal back",
            "C. High volume shows real conviction behind the move",
            "D. Volume only matters for cryptocurrencies"]),
    ]
    for qtext, opts in questions:
        y = draw_body(c, y, qtext, size=9.5, width_chars=98)
        y -= 4
        for opt in opts:
            y = draw_body(c, y, opt, size=8.5, color=GRAY, width_chars=100)
        y -= PARA_GAP

    c.showPage()

    # PAGE 4 — Answer key
    new_page(c, TAG, 4)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Answer Key", PURPLE, size=12)
    y -= 10

    answers = [
        ("1. In a head & shoulders top, what does the \"neckline\" represent?",
         "B. The support level connecting the lows between the shoulders and the head",
         "The neckline connects the lows on either side of the head - the key support level whose break confirms the pattern."),
        ("2. What distinguishes a double top from a random pair of highs?",
         "C. Two similar highs failing at the same resistance, then a break below the middle low",
         "A double top needs two comparable highs rejected at similar resistance, confirmed only once price breaks the low between them."),
        ("3. Why can't a triangle be assumed to break with the prior trend?",
         "D. The lines can resolve either way - wait for the actual breakout",
         "Triangles usually continue the prior trend, but can break against it - the breakout itself tells you the direction."),
        ("4. Neckline $100, head $130 - what is the rough measured-move target?",
         "A. $70",
         "Head-to-neckline distance is $130 - $100 = $30, projected below the neckline: $100 - $30 = $70."),
        ("5. Why trust a neckline break on high volume more than on thin volume?",
         "C. High volume shows real conviction behind the move",
         "A high-volume confirmation shows genuine participation rather than a handful of trades nudging price through the line."),
    ]
    for qtext, correct, explain in answers:
        y = draw_body(c, y, qtext, size=9.5, width_chars=98)
        y -= 4
        y = draw_body(c, y, "Correct answer: " + correct, size=8.5, color=GREEN, width_chars=98)
        y -= 2
        y = draw_body(c, y, explain, size=8.5, color=GRAY, width_chars=100)
        y -= PARA_GAP

    c.save()
    print("done:", path)


# ── WORKSHEET ─────────────────────────────────────────────────────────────────

def draw_answer_box(c, y, h=40):
    c.setStrokeColor(GRAY)
    c.setLineWidth(0.8)
    c.roundRect(LEFT, y - h, CONTENT_W, h, 6, stroke=1, fill=0)
    return y - h


def build_worksheet():
    path = "static/downloads/chart-patterns-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Chart Patterns — Practice Worksheet · Intermediate"

    new_page(c, TAG, 1, running=False)
    y = PAGE_H - 90
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(DARK)
    c.drawString(LEFT, y, "Chart Patterns")
    y -= 26
    c.setFont("Helvetica", 10.5)
    c.setFillColor(GRAY)
    c.drawString(LEFT, y, "INTERMEDIATE PRACTICE WORKSHEET")
    y -= SECTION_GAP
    y = draw_body(c, y, "Grab a real chart (any free charting site works) and a stock or index you're "
                         "curious about. Look for a head & shoulders, double top, or triangle on its daily "
                         "or weekly chart. There's no wrong answer, the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Find a Candidate Pattern", TEAL)
    y = draw_body(c, y, "Which stock or index are you looking at, and what timeframe? Which of the three "
                         "patterns (head & shoulders, double top, triangle) does it most resemble?")
    y -= 6
    y = draw_answer_box(c, y, 50)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Mark the Key Levels", GREEN)
    y = draw_body(c, y, "Write down the neckline (or trend lines, for a triangle) and, if it's a head & "
                         "shoulders or double top, the price of the head or the two tops.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Calculate the Measured Move", GOLD)
    y = draw_body(c, y, "Using the neckline and head price from Section 2, calculate the measured-move "
                         "target: |head - neckline|, projected from the neckline in the breakout direction.")
    y -= 6
    y = draw_answer_box(c, y, 50)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Check for Confirmation", PURPLE)
    y = draw_body(c, y, "Has the pattern actually broken its key line (neckline, or one side of the "
                         "triangle) with a decisive close, or is it still forming? Has volume picked up on "
                         "the break?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "Looking at just this one pattern, what would you still need to know before "
                         "trusting it as a signal?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


# ── FURTHER READING ────────────────────────────────────────────────────────────

def build_further_reading():
    path = "static/downloads/chart-patterns-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Chart Patterns — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = PAGE_H - 90
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(DARK)
    c.drawString(LEFT, y, "Chart Patterns")
    y -= 26
    c.setFont("Helvetica", 10.5)
    c.setFillColor(GRAY)
    c.drawString(LEFT, y, "INTERMEDIATE FURTHER READING")
    y -= SECTION_GAP
    y = draw_body(c, y, "Want to go deeper on chart patterns? These are free, reputable, and worth "
                         "bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("StockCharts ChartSchool - Chart Pattern Dictionary",
         "https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns",
         "A reference covering head & shoulders, double tops/bottoms, triangles and more, with real chart examples."),
        ("Investopedia - Head and Shoulders Pattern",
         "https://www.investopedia.com/terms/h/head-shoulders.asp",
         "A focused walkthrough of the head & shoulders pattern, including the measured-move target used in this lesson."),
        ("Investopedia - Triangle Pattern",
         "https://www.investopedia.com/terms/t/triangle.asp",
         "Covers ascending, descending, and symmetrical triangles and how each tends to resolve."),
        ("Investor.gov",
         "https://www.investor.gov/",
         "The U.S. Securities and Exchange Commission's official investor education site - search 'technical analysis' for plain-English background."),
        ("StockCharts ChartSchool",
         "https://chartschool.stockcharts.com/",
         "A free, well-regarded reference on chart reading fundamentals generally."),
    ]
    for title, url, desc in entries:
        y = draw_heading(c, y, title, PURPLE, size=11)
        c.setFont("Helvetica", 8.5)
        c.setFillColor(TEAL)
        c.drawString(LEFT, y, url)
        y -= LINE_H
        y = draw_body(c, y, desc, size=8.5, color=GRAY)
        y -= SECTION_GAP - 8

    y -= 10
    c.setFillColor(Color(0.98, 0.94, 0.86))
    box_h = 50
    c.rect(LEFT, y - box_h, CONTENT_W, box_h, fill=1, stroke=0)
    c.setStrokeColor(GOLD)
    c.setLineWidth(3)
    c.line(LEFT, y, LEFT, y - box_h)
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(DARK)
    c.drawString(LEFT + 12, y - 16, "Please note:")
    c.setFont("Helvetica", 8.5)
    for i, line in enumerate(wrap(
        "these are general educational resources, not personalized financial advice. Consult a "
        "licensed financial advisor before making investment decisions.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.save()
    print("done:", path)


if __name__ == "__main__":
    build_explainer()
    build_worksheet()
    build_further_reading()
