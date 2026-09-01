"""Generate the 3 downloadable PDFs for the Intermediate 'MACD' lesson:
macd-explainer.pdf, -worksheet.pdf, -further-reading.pdf. Same branding/spacing
approach as gen_rsi_pdfs.py (wider gaps, per Gary's 2026-09-01 rule).
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
RED = Color(0.973, 0.443, 0.443)
RIBBON = [PURPLE, TEAL, GREEN, GOLD]

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


def draw_body(c, y, text, size=BODY_SIZE, color=DARK, width_chars=98):
    c.setFont("Helvetica", size)
    c.setFillColor(color)
    for line in wrap(text, width_chars):
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


def draw_title_block(c, title, subtitle_text):
    y = PAGE_H - 90
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(DARK)
    c.drawString(LEFT, y, title)
    y -= 26
    c.setFont("Helvetica", 10.5)
    c.setFillColor(GRAY)
    c.drawString(LEFT, y, subtitle_text)
    y -= SECTION_GAP
    return y


def draw_macd_chart(c, x0, y0, w, h):
    """Price line above, MACD+signal+histogram below, inside (x0,y0,w,h)."""
    price_h = h * 0.3
    macd_h = h * 0.55
    gap = h * 0.12
    price_y0 = y0 + macd_h + gap
    price_pts = [(0, 0.2), (0.15, 0.4), (0.3, 0.1), (0.45, 0.55), (0.6, 0.8), (0.75, 0.9), (0.9, 0.5), (1.0, 0.35)]
    c.setStrokeColor(GRAY)
    c.setLineWidth(1.3)
    p = c.beginPath()
    p.moveTo(x0 + price_pts[0][0] * w, price_y0 + price_pts[0][1] * price_h)
    for px, py in price_pts[1:]:
        p.lineTo(x0 + px * w, price_y0 + py * price_h)
    c.drawPath(p, stroke=1, fill=0)
    c.setFont("Helvetica", 7)
    c.setFillColor(GRAY)
    c.drawString(x0, price_y0 + price_h + 6, "Price")

    zero_y = y0 + macd_h * 0.5
    c.setStrokeColor(Color(0.3, 0.32, 0.38))
    c.setLineWidth(0.8)
    c.line(x0, zero_y, x0 + w, zero_y)
    c.setFont("Helvetica", 7)
    c.setFillColor(GRAY)
    c.drawString(x0 + w + 4, zero_y - 3, "0")

    n_bars = 14
    hist_vals = [-0.3, -0.5, -0.2, 0.1, 0.4, 0.6, 0.5, 0.2, -0.1, -0.4, -0.3, 0.15, 0.5, 0.3]
    bar_w = (w * 0.9) / n_bars
    for i, v in enumerate(hist_vals):
        bx = x0 + i * (w * 0.9 / n_bars) + w * 0.05
        bh = abs(v) * macd_h * 0.35
        by = zero_y if v >= 0 else zero_y - bh
        color = GREEN if v >= 0 else RED
        c.setFillColor(color)
        c.rect(bx, by, bar_w * 0.7, bh, fill=1, stroke=0)

    macd_pts = [(0, 0.35), (0.15, 0.25), (0.3, 0.4), (0.45, 0.65), (0.6, 0.85), (0.75, 0.75), (0.9, 0.4), (1.0, 0.55)]
    c.setStrokeColor(PURPLE)
    c.setLineWidth(1.8)
    p2 = c.beginPath()
    p2.moveTo(x0 + macd_pts[0][0] * w, y0 + macd_pts[0][1] * macd_h)
    for px, py in macd_pts[1:]:
        p2.lineTo(x0 + px * w, y0 + py * macd_h)
    c.drawPath(p2, stroke=1, fill=0)

    signal_pts = [(0, 0.4), (0.15, 0.35), (0.3, 0.3), (0.45, 0.45), (0.6, 0.65), (0.75, 0.8), (0.9, 0.6), (1.0, 0.45)]
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.6)
    c.setDash(4, 3)
    p3 = c.beginPath()
    p3.moveTo(x0 + signal_pts[0][0] * w, y0 + signal_pts[0][1] * macd_h)
    for px, py in signal_pts[1:]:
        p3.lineTo(x0 + px * w, y0 + py * macd_h)
    c.drawPath(p3, stroke=1, fill=0)
    c.setDash(1, 0)

    c.setFont("Helvetica", 7)
    c.setFillColor(GRAY)
    c.drawString(x0, y0 - 4, "MACD (purple) / Signal (gold, dashed) / Histogram")


def build_explainer():
    path = "static/downloads/macd-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "MACD — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "MACD", "Reading Momentum and Trend Shifts — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", PURPLE)
    y = draw_body(c, y, "MACD is built from two exponential moving averages (EMAs) of price: a fast "
                         "12-period EMA and a slower 26-period EMA. The MACD line is the fast EMA minus "
                         "the slow EMA.")
    y -= PARA_GAP
    y = draw_body(c, y, "A 9-period EMA of the MACD line itself is the signal line. When MACD crosses "
                         "above the signal line, that's read as bullish - momentum picking up. When it "
                         "crosses below, that's bearish - momentum fading.")
    y -= PARA_GAP
    y = draw_body(c, y, "The gap between the two is often drawn as a histogram. A growing histogram means "
                         "the lines are pulling apart; a shrinking one means they're converging - often "
                         "visible before the crossover itself.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "MACD Alongside Price", TEAL)
    chart_h = 190
    draw_macd_chart(c, LEFT + 10, y - chart_h, CONTENT_W - 60, chart_h)
    y -= chart_h + 30

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About MACD", GOLD)
    facts = [
        "MACD is a lagging indicator built from moving averages - it confirms a shift after it's begun.",
        "The crossover is the headline signal, but the histogram often moves first.",
        "MACD can diverge from price, just like RSI - a classic warning sign.",
        "The zero line matters too - crossing zero means the fast EMA has overtaken the slow EMA outright.",
        "MACD works best in trending markets - in a choppy, sideways market it can whipsaw.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check When Reading MACD", GREEN)
    tips = [
        "Watch the histogram shrink - often more useful than reacting to the cross itself.",
        "Note the zero-line cross - a crossover that also crosses zero carries more weight.",
        "Check for divergence - compare MACD's recent peaks/troughs to price's.",
        "Confirm the market isn't choppy - MACD is far more reliable in a trending market.",
    ]
    for t in tips:
        y = draw_body(c, y, "• " + t)
        y -= 8
    y -= SECTION_GAP - 16

    c.setFillColor(Color(0.98, 0.94, 0.86))
    box_h = 56
    c.rect(LEFT, y - box_h, CONTENT_W, box_h, fill=1, stroke=0)
    c.setStrokeColor(GOLD)
    c.setLineWidth(3)
    c.line(LEFT, y, LEFT, y - box_h)
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(DARK)
    c.drawString(LEFT + 12, y - 16, "Worth knowing:")
    c.setFont("Helvetica", 8.5)
    for i, line in enumerate(wrap(
        "MACD is a lagging indicator built from moving averages - it confirms a momentum shift after "
        "it's begun, not before. In choppy, range-bound markets it can generate frequent false "
        "crossovers. Pair it with trend context and volume.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", PURPLE, size=12)
    y -= 10

    questions = [
        ("1. How is the MACD line calculated?", [
            "A. Today's closing price minus yesterday's closing price",
            "B. The 12-period EMA minus the 26-period EMA",
            "C. Total volume divided by average volume",
            "D. The highest high minus the lowest low"]),
        ("2. What does the MACD histogram represent?", [
            "A. Total trading volume for the day",
            "B. The company's earnings per share",
            "C. The gap between the MACD line and the signal line",
            "D. The stock's dividend yield"]),
        ("3. Why might a shrinking histogram be useful before a crossover?", [
            "A. It never provides any useful information",
            "B. It guarantees a crossover within 24 hours",
            "C. It means volume has stopped entirely",
            "D. It can hint momentum is fading and a crossover may be approaching"]),
        ("4. Why does a crossover that also crosses zero carry more weight?", [
            "A. It means the fast EMA has overtaken the slow EMA outright",
            "B. Zero-line crosses are purely decorative",
            "C. It means the stock has been delisted",
            "D. It only happens once per year"]),
        ("5. Why can MACD generate false signals in a sideways market?", [
            "A. MACD only works on cryptocurrencies",
            "B. With no sustained trend, the averages cross back and forth without a real shift",
            "C. The MACD formula breaks down mathematically in sideways markets",
            "D. Sideways markets have no volume at all"]),
    ]
    for qtext, opts in questions:
        y = draw_body(c, y, qtext, size=9.5, width_chars=98)
        y -= 4
        for opt in opts:
            y = draw_body(c, y, opt, size=8.5, color=GRAY, width_chars=100)
        y -= PARA_GAP

    c.showPage()

    new_page(c, TAG, 4)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Answer Key", PURPLE, size=12)
    y -= 10

    answers = [
        ("1. How is the MACD line calculated?",
         "B. The 12-period EMA minus the 26-period EMA",
         "The MACD line is the fast (12-period) EMA minus the slow (26-period) EMA of price."),
        ("2. What does the MACD histogram represent?",
         "C. The gap between the MACD line and the signal line",
         "The histogram bars plot MACD minus signal - growing means pulling apart, shrinking means converging."),
        ("3. Why might a shrinking histogram be useful before a crossover?",
         "D. It can hint momentum is fading and a crossover may be approaching",
         "A shrinking histogram shows the lines converging - often visible before the actual crossover."),
        ("4. Why does a crossover that also crosses zero carry more weight?",
         "A. It means the fast EMA has overtaken the slow EMA outright",
         "Crossing zero means the fast EMA has actually moved past the slow EMA, a more decisive shift."),
        ("5. Why can MACD generate false signals in a sideways market?",
         "B. With no sustained trend, the averages cross back and forth without a real shift",
         "MACD works best when there's an actual trend to track - a choppy market causes frequent crosses without a genuine shift underway."),
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


def draw_answer_box(c, y, h=40):
    c.setStrokeColor(GRAY)
    c.setLineWidth(0.8)
    c.roundRect(LEFT, y - h, CONTENT_W, h, 6, stroke=1, fill=0)
    return y - h


def build_worksheet():
    path = "static/downloads/macd-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "MACD — Practice Worksheet · Intermediate"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "MACD", "INTERMEDIATE PRACTICE WORKSHEET")
    y = draw_body(c, y, "Pull up a real chart (any free charting site works, most show MACD as a built-in "
                         "indicator) for a stock or index you're curious about. There's no wrong answer, "
                         "the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Read the Current MACD", TEAL)
    y = draw_body(c, y, "Which stock or index, and what timeframe? Is the MACD line currently above or "
                         "below the signal line? Above or below zero?")
    y -= 6
    y = draw_answer_box(c, y, 50)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Find the Most Recent Crossover", GREEN)
    y = draw_body(c, y, "Scroll back and find the most recent point where MACD crossed the signal line. "
                         "Was it bullish or bearish? Did it also cross zero?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Watch the Histogram", GOLD)
    y = draw_body(c, y, "In the few periods before that crossover, was the histogram growing or "
                         "shrinking? Did it give any early warning of the crossover to come?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Check the Trend Context", PURPLE)
    y = draw_body(c, y, "Was the broader market trending or choppy/sideways when this crossover "
                         "happened? Does that make you trust the signal more or less?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "What other tool from an earlier lesson (RSI, support/resistance, volume) would "
                         "you want to check alongside this MACD signal before trusting it?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/macd-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "MACD — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "MACD", "INTERMEDIATE FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on MACD? These are free, reputable, and worth bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("StockCharts ChartSchool - MACD",
         "https://chartschool.stockcharts.com/table-of-contents/technical-indicators/moving-average-convergence-divergence-macd",
         "A detailed walkthrough of the MACD formula, the histogram, and common crossover strategies."),
        ("Investopedia - Moving Average Convergence Divergence (MACD)",
         "https://www.investopedia.com/terms/m/macd.asp",
         "Covers the MACD formula, signal-line crossovers, and the zero-line cross."),
        ("Investopedia - Divergence",
         "https://www.investopedia.com/terms/d/divergence.asp",
         "A deeper look at bullish and bearish divergence across momentum indicators, including MACD."),
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
