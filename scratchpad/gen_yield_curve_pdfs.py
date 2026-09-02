"""Generate the 3 downloadable PDFs for the Pro 'The Yield Curve' lesson
(second lesson in the Macro & Cross-Asset Analysis track).
"""
import textwrap

from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.colors import Color

PAGE_W, PAGE_H = 595.2756, 841.8898
LEFT = 62.69291
RIGHT = PAGE_W - LEFT
CONTENT_W = RIGHT - LEFT

TEAL = Color(0.176471, 0.831373, 0.749020)
PURPLE = Color(0.486275, 0.227451, 0.929412)
GREEN = Color(0.290196, 0.870588, 0.501961)
GOLD = Color(0.960784, 0.72549, 0.258824)
DARK = Color(0.078431, 0.094118, 0.14902)
GRAY = Color(0.356863, 0.392157, 0.470588)
RIBBON = [TEAL, PURPLE, GREEN, GOLD]

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
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(DARK)
    c.drawString(LEFT, y, title)
    y -= 24
    c.setFont("Helvetica", 10.5)
    c.setFillColor(GRAY)
    c.drawString(LEFT, y, subtitle_text)
    y -= SECTION_GAP
    return y


def draw_curve_table(c, y):
    rows = [
        ("3-Month", "3.0%", "5.2%", False),
        ("2-Year", "3.4%", "4.8%", True),
        ("5-Year", "3.7%", "4.3%", False),
        ("10-Year", "4.0%", "4.0%", True),
        ("30-Year", "4.3%", "4.2%", False),
    ]
    col_x = [LEFT + 6, LEFT + 220, LEFT + 350]
    labels = ["Maturity", "Normal Curve Yield", "Inverted Curve Yield"]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(TEAL)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(DARK)
    for x, lab in zip(col_x, labels):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (maturity, normal, inverted, bold) in enumerate(rows):
        if bold:
            c.setFillColor(Color(0.85, 0.98, 0.96))
        elif i % 2 == 1:
            c.setFillColor(Color(0.95, 0.95, 0.97))
        else:
            c.setFillColor(Color(1, 1, 1))
        c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 8)
        c.setFillColor(DARK)
        for x, val in zip(col_x, [maturity, normal, inverted]):
            c.drawString(x, y - 9, val)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/yield-curve-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "The Yield Curve — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "The Yield Curve", "The Bond Market's Early Warning System — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", TEAL)
    y = draw_body(c, y, "The yield curve plots the interest rate on government bonds of the same "
                         "issuer against how long until each bond matures. Normally it slopes gently "
                         "upward - investors demand a higher yield to lock money up for longer.")
    y -= PARA_GAP
    y = draw_body(c, y, "An inversion happens when that flips - short-term yields rise above long-term "
                         "yields. This typically reflects the market believing the central bank will be "
                         "forced to cut rates in the future, usually anticipating a slowdown.")
    y -= PARA_GAP
    y = draw_body(c, y, "The 2-year/10-year spread is the most widely watched inversion signal. "
                         "Historically, inversions have preceded most U.S. recessions by many months to "
                         "over a year - useful, but a poor short-term timing tool.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: A Normal Curve vs. an Inverted Curve", PURPLE)
    y = draw_curve_table(c, y)
    y = draw_body(c, y, "In the inverted scenario, the 2-year (4.8%) yields more than the 10-year "
                         "(4.0%) - the classic inversion signal, with short rates pricing in near-term "
                         "tightness while long rates reflect expectations of future cuts.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About the Yield Curve", GOLD)
    facts = [
        "The 2-year/10-year spread is the most cited measure, though other pairs are also watched.",
        "Inversions have a long, variable lead time - many months to over a year before a recession.",
        "Not every inversion is followed by a recession - a strong signal, not a guarantee.",
        "The curve can steepen again before a recession hits - un-inverting doesn't mean risk has passed.",
        "The curve reflects expectations, not certainty - it can and does change as information arrives.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check When Reading the Yield Curve", GREEN)
    tips = [
        "Track the 2s/10s spread over time - the trend matters more than a single day's snapshot.",
        "Check multiple maturity pairs - different pairs can send slightly different signals.",
        "Don't expect precise timing - treat an inversion as a warning, not a short-term trading signal.",
        "Connect it back to central bank policy - an inversion is a bet on the future rate path.",
    ]
    for t in tips:
        y = draw_body(c, y, "• " + t)
        y -= 8
    y -= SECTION_GAP - 16

    c.setFillColor(Color(0.98, 0.94, 0.86))
    box_h = 60
    c.rect(LEFT, y - box_h, CONTENT_W, box_h, fill=1, stroke=0)
    c.setStrokeColor(GOLD)
    c.setLineWidth(3)
    c.line(LEFT, y, LEFT, y - box_h)
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(DARK)
    c.drawString(LEFT + 12, y - 16, "Worth knowing:")
    c.setFont("Helvetica", 8.5)
    for i, line in enumerate(wrap(
        "this explains yield curve mechanics using illustrative numbers - it isn't personalized "
        "financial advice, and no reading or signal here is a recommendation to trade. Past inversion "
        "patterns are not a guarantee of future recessions or market moves.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", TEAL, size=12)
    y -= 10

    questions = [
        ("1. What does the yield curve normally look like?", [
            "A. Perfectly flat across all maturities",
            "B. Upward-sloping - longer maturities pay higher yields",
            "C. Downward-sloping - longer maturities pay lower yields",
            "D. Completely random with no typical shape"]),
        ("2. What is an inversion?", [
            "A. When all bond yields become exactly equal",
            "B. When bond prices are quoted in a foreign currency",
            "C. When short-term yields rise above long-term yields",
            "D. When a bond defaults on its payments"]),
        ("3. What does an inversion typically reflect, according to this lesson?", [
            "A. That inflation has permanently disappeared",
            "B. That the government has stopped issuing long-term bonds",
            "C. That short-term bonds have become illegal to trade",
            "D. The market's belief the central bank will be forced to cut rates, often due to a coming slowdown"]),
        ("4. Is the yield curve a precise short-term timing tool for a recession?", [
            "A. No - inversions have historically had a long and variable lead time before a recession begins",
            "B. Yes, recessions begin exactly one month after every inversion",
            "C. Yes, but only for recessions outside the United States",
            "D. The yield curve has no relationship to recessions at all"]),
        ("5. In the illustrative example, what made the \"inverted curve\" scenario an inversion?", [
            "A. The 30-year yield was the highest of all maturities",
            "B. All yields were exactly the same",
            "C. The 2-year yield (4.8%) was higher than the 10-year yield (4.0%)",
            "D. The 3-month yield was the lowest of all maturities"]),
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
    y = draw_heading(c, y, "Answer Key", TEAL, size=12)
    y -= 10

    answers = [
        ("1. What does the yield curve normally look like?",
         "B. Upward-sloping - longer maturities pay higher yields",
         "Normally the curve slopes gently upward, since investors demand a higher yield for longer commitments."),
        ("2. What is an inversion?",
         "C. When short-term yields rise above long-term yields",
         "An inversion happens when the normal relationship flips."),
        ("3. What does an inversion typically reflect, according to this lesson?",
         "D. The market's belief the central bank will be forced to cut rates, often due to a coming slowdown",
         "An inversion typically reflects the market pricing in future rate cuts, anticipating a slowdown."),
        ("4. Is the yield curve a precise short-term timing tool for a recession?",
         "A. No - inversions have historically had a long and variable lead time before a recession begins",
         "Inversions have preceded recessions by many months to over a year, a variable lead time."),
        ("5. In the illustrative example, what made the \"inverted curve\" scenario an inversion?",
         "C. The 2-year yield (4.8%) was higher than the 10-year yield (4.0%)",
         "The 2-year yielding more than the 10-year is the classic 2s/10s inversion signal."),
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
    path = "static/downloads/yield-curve-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "The Yield Curve — Practice Worksheet · Pro"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "The Yield Curve", "PRO PRACTICE WORKSHEET")
    y = draw_body(c, y, "Work through these by hand or with a spreadsheet. There's no wrong answer, "
                         "the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Calculate a 2s/10s Spread", TEAL)
    y = draw_body(c, y, "The 2-year yield is 4.6% and the 10-year yield is 4.1%. Calculate the spread "
                         "and classify the curve as normal, flat, or inverted.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Interpret a Shifting Spread", GREEN)
    y = draw_body(c, y, "The 2s/10s spread was +1.2 points six months ago and is now -0.4 points. "
                         "What does this trend suggest is happening in the bond market's expectations?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Connect to Central Bank Policy", GOLD)
    y = draw_body(c, y, "Explain, in your own words, why an inverted curve reflects a bet about future "
                         "central bank rate decisions rather than current conditions alone.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Check Multiple Pairs", PURPLE)
    y = draw_body(c, y, "If the 3-month/10-year spread is inverted but the 2-year/10-year spread is "
                         "not, what might that suggest? Why check more than one pair?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "Why does this lesson caution against treating an inversion as a precise "
                         "short-term trading signal?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/yield-curve-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "The Yield Curve — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "The Yield Curve", "PRO FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on the yield curve? These are free, reputable, and worth "
                         "bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Yield Curve",
         "https://www.investopedia.com/terms/y/yieldcurve.asp",
         "A detailed walkthrough of the yield curve and its typical shapes."),
        ("Investopedia - Inverted Yield Curve",
         "https://www.investopedia.com/terms/i/invertedyieldcurve.asp",
         "Covers yield curve inversions specifically, referenced throughout this lesson."),
        ("FRED - 10-Year Minus 2-Year Treasury Spread",
         "https://fred.stlouisfed.org/series/T10Y2Y",
         "The St. Louis Fed's own historical data series for the 2s/10s spread."),
        ("New York Fed - Yield Curve as a Predictor of Recessions",
         "https://www.newyorkfed.org/research/capital_markets/ycfaq",
         "The New York Fed's own research overview on the yield curve as a recession indicator."),
        ("Investopedia",
         "https://www.investopedia.com/",
         "A huge library of plain-English financial explainers, useful for looking up any term from this lesson."),
    ]
    for title, url, desc in entries:
        y = draw_heading(c, y, title, TEAL, size=11)
        c.setFont("Helvetica", 8.5)
        c.setFillColor(PURPLE)
        c.drawString(LEFT, y, url)
        y -= LINE_H
        y = draw_body(c, y, desc, size=8.5, color=GRAY)
        y -= SECTION_GAP - 8

    y -= 10
    c.setFillColor(Color(0.98, 0.94, 0.86))
    box_h = 56
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
