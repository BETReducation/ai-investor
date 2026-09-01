"""Generate the 3 downloadable PDFs for the Intermediate 'RSI' lesson:
rsi-explainer.pdf, -worksheet.pdf, -further-reading.pdf. Same branding/spacing
approach as gen_chart_patterns_pdfs.py (wider gaps, per Gary's 2026-09-01 rule
for Intermediate-onward PDFs).
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


def draw_title_block(c, subtitle_text):
    y = PAGE_H - 90
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(DARK)
    c.drawString(LEFT, y, "RSI")
    y -= 26
    c.setFont("Helvetica", 10.5)
    c.setFillColor(GRAY)
    c.drawString(LEFT, y, subtitle_text)
    y -= SECTION_GAP
    return y


def draw_rsi_chart(c, x0, y0, w, h):
    """Price line above, RSI oscillator with 30/70 bands below, inside (x0,y0,w,h)."""
    price_h = h * 0.35
    rsi_h = h * 0.55
    gap = h * 0.10
    price_y0 = y0 + rsi_h + gap
    price_pts = [(0, 0.1), (0.15, 0.5), (0.3, 0.2), (0.45, 0.6), (0.6, 0.85), (0.75, 0.95), (1.0, 0.55)]
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

    band70_y = y0 + rsi_h * 0.7
    band30_y = y0 + rsi_h * 0.3
    c.setStrokeColor(RED)
    c.setLineWidth(0.8)
    c.setDash(3, 2)
    c.line(x0, band70_y, x0 + w, band70_y)
    c.setStrokeColor(GREEN)
    c.line(x0, band30_y, x0 + w, band30_y)
    c.setDash(1, 0)
    c.setFont("Helvetica", 7)
    c.setFillColor(RED)
    c.drawString(x0 + w + 4, band70_y - 3, "70")
    c.setFillColor(GREEN)
    c.drawString(x0 + w + 4, band30_y - 3, "30")

    rsi_pts = [(0, 0.55), (0.15, 0.4), (0.3, 0.6), (0.45, 0.75), (0.6, 0.9), (0.75, 0.95), (1.0, 0.5)]
    c.setStrokeColor(PURPLE)
    c.setLineWidth(1.8)
    p2 = c.beginPath()
    p2.moveTo(x0 + rsi_pts[0][0] * w, y0 + rsi_pts[0][1] * rsi_h)
    for px, py in rsi_pts[1:]:
        p2.lineTo(x0 + px * w, y0 + py * rsi_h)
    c.drawPath(p2, stroke=1, fill=0)
    c.setFillColor(RED)
    c.circle(x0 + 0.75 * w, y0 + 0.95 * rsi_h, 3, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(RED)
    c.drawCentredString(x0 + 0.75 * w, y0 + 0.95 * rsi_h + 10, "overbought")
    c.setFont("Helvetica", 7)
    c.setFillColor(GRAY)
    c.drawString(x0, y0 - 4, "RSI (14)")


def build_explainer():
    path = "static/downloads/rsi-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "RSI — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Spotting Overbought & Oversold Conditions — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", PURPLE)
    y = draw_body(c, y, "The Relative Strength Index (RSI) is a momentum oscillator that compares the "
                         "size of recent gains to recent losses, plotted on a scale of 0 to 100. It's "
                         "typically calculated over a 14-period lookback.")
    y -= PARA_GAP
    y = draw_body(c, y, "RSI above 70 suggests an asset may be overbought - a pullback or pause becomes "
                         "more likely. RSI below 30 suggests oversold - a bounce becomes more likely. "
                         "These are guidelines, not hard rules.")
    y -= PARA_GAP
    y = draw_body(c, y, "Formula: RSI = 100 - (100 / (1 + RS)), where RS is the average gain over the "
                         "lookback period divided by the average loss.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "RSI Alongside Price", TEAL)
    chart_h = 190
    draw_rsi_chart(c, LEFT + 10, y - chart_h, CONTENT_W - 60, chart_h)
    y -= chart_h + 30

    c.showPage()

    # PAGE 2
    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About RSI", GOLD)
    facts = [
        "70/30 are guidelines, not laws - a strong trend can keep RSI pinned above 70 (or below 30) for a long stretch.",
        "Divergence is often more useful than the level itself - price making a new high while RSI makes a lower high is a classic warning.",
        "Shorter lookback periods react faster but whipsaw more - 14 is the standard balance.",
        "RSI works best paired with trend context - an oversold reading in a healthy uptrend pullback differs from one at a real breakdown.",
        "RSI is a momentum tool, not a valuation tool - it says nothing about whether a stock is cheap or expensive.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check When Reading RSI", GREEN)
    tips = [
        "Check for divergence first - compare RSI's recent peaks/troughs to price's.",
        "Read it with the trend - in a strong uptrend, treat dips toward 40-50 as the zone that matters.",
        "Don't trade the first touch - wait for RSI to actually turn back before treating a 70/30 cross as confirmation.",
        "Pair it with support/resistance - an oversold reading at a known support level is a stronger combination.",
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
        "RSI describes recent momentum, not the future. A stock can stay 'overbought' for weeks in "
        "a strong trend, and an 'oversold' reading can keep falling further. Use it alongside trend "
        "and volume, never in isolation.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    # PAGE 3 — Quiz
    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", PURPLE, size=12)
    y -= 10

    questions = [
        ("1. What does RSI measure?", [
            "A. The company's price-to-earnings ratio",
            "B. The total trading volume over a period",
            "C. The size of recent gains relative to recent losses, on a 0-100 scale",
            "D. The distance between support and resistance"]),
        ("2. What does an RSI reading above 70 traditionally suggest?", [
            "A. The stock is definitely about to crash",
            "B. The asset may be overbought - a pullback or pause becomes more likely",
            "C. The company has high debt",
            "D. Trading has been halted"]),
        ("3. What is \"bearish divergence\" in RSI?", [
            "A. When RSI and price both make new highs together",
            "B. When RSI is exactly 50",
            "C. When volume falls to zero",
            "D. When price makes a new high but RSI makes a lower high"]),
        ("4. Why can RSI stay above 70 for weeks during a strong uptrend?", [
            "A. 70/30 are guidelines, not hard rules - strong trends sustain overbought readings",
            "B. RSI can only go from 0-70, never higher",
            "C. It's always a data error",
            "D. Overbought readings automatically reset every Friday"]),
        ("5. Avg gain 2.4, avg loss 0.5 - is RSI closer to overbought or oversold?", [
            "A. Oversold (RSI near 20)",
            "B. Exactly neutral (RSI = 50)",
            "C. Overbought (RSI well above 70)",
            "D. RSI cannot be calculated from this information"]),
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
        ("1. What does RSI measure?",
         "C. The size of recent gains relative to recent losses, on a 0-100 scale",
         "RSI compares average gains to average losses over a lookback period (typically 14) to produce a single 0-100 momentum reading."),
        ("2. What does an RSI reading above 70 traditionally suggest?",
         "B. The asset may be overbought - a pullback or pause becomes more likely",
         "Above 70 is the classic overbought zone - a signal to watch for exhaustion, not a guarantee of an immediate reversal."),
        ("3. What is \"bearish divergence\" in RSI?",
         "D. When price makes a new high but RSI makes a lower high",
         "Bearish divergence is often considered more informative than the raw overbought/oversold level."),
        ("4. Why can RSI stay above 70 for weeks during a strong uptrend?",
         "A. 70/30 are guidelines, not hard rules - strong trends sustain overbought readings",
         "RSI reflects recent momentum, not a countdown timer - a strong enough trend can keep it pinned in overbought territory."),
        ("5. Avg gain 2.4, avg loss 0.5 - is RSI closer to overbought or oversold?",
         "C. Overbought (RSI well above 70)",
         "RS = 2.4 / 0.5 = 4.8; RSI = 100 - (100 / (1 + 4.8)) ~ 82.8 - solidly overbought."),
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
    path = "static/downloads/rsi-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "RSI — Practice Worksheet · Intermediate"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "INTERMEDIATE PRACTICE WORKSHEET")
    y = draw_body(c, y, "Pull up a real chart (any free charting site works, most show RSI as a built-in "
                         "indicator) for a stock or index you're curious about. There's no wrong answer, "
                         "the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Read the Current RSI", TEAL)
    y = draw_body(c, y, "Which stock or index, and what timeframe? What is its current RSI(14) reading? "
                         "Is it overbought (>70), oversold (<30), or neutral?")
    y -= 6
    y = draw_answer_box(c, y, 50)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Calculate RSI by Hand", GREEN)
    y = draw_body(c, y, "Using an average gain of 1.8 and an average loss of 0.6 over the lookback period, "
                         "calculate RS and then RSI using the formula from the explainer.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Spot Divergence", GOLD)
    y = draw_body(c, y, "Looking at your chart's last few weeks, does price and RSI agree on direction "
                         "(both making higher highs, or both making lower lows)? Or do you see divergence?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Combine With Another Tool", PURPLE)
    y = draw_body(c, y, "Is the current RSI reading lining up with a support or resistance level, or a "
                         "trend line from an earlier lesson? Does that make the signal stronger or weaker?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "What would make you trust this RSI reading more, and what would make you "
                         "trust it less?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/rsi-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "RSI — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "INTERMEDIATE FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on RSI? These are free, reputable, and worth bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("StockCharts ChartSchool - Relative Strength Index (RSI)",
         "https://chartschool.stockcharts.com/table-of-contents/technical-indicators/relative-strength-index-rsi",
         "A detailed walkthrough of the RSI formula, standard settings, and how to read divergence."),
        ("Investopedia - Relative Strength Index (RSI)",
         "https://www.investopedia.com/terms/r/rsi.asp",
         "Covers the RSI formula, the 70/30 thresholds, and common pitfalls of over-relying on the raw level."),
        ("Investopedia - Divergence",
         "https://www.investopedia.com/terms/d/divergence.asp",
         "A deeper look at bullish and bearish divergence across momentum indicators, including RSI."),
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
