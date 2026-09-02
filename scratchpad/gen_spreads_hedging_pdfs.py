"""Generate the 3 downloadable PDFs for the Pro 'Spreads & Hedging' lesson
(fifth and final lesson in the Options & Derivatives track).
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


def draw_spread_table(c, y):
    rows = [
        ("$95", "-$6 (Max Loss)", "-$4 (Max Loss)", False),
        ("$105", "-$1", "+$1", False),
        ("$115", "+$9", "+$6 (Max Gain)", True),
        ("$130", "+$24", "+$6 (Still Capped)", False),
    ]
    col_x = [LEFT + 6, LEFT + 170, LEFT + 340]
    labels = ["Stock at Expiration", "Single Call P&L", "Bull Spread P&L"]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(TEAL)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(DARK)
    for x, lab in zip(col_x, labels):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (price, single, spread, bold) in enumerate(rows):
        if bold:
            c.setFillColor(Color(0.85, 0.98, 0.96))
        elif i % 2 == 1:
            c.setFillColor(Color(0.95, 0.95, 0.97))
        else:
            c.setFillColor(Color(1, 1, 1))
        c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 8)
        c.setFillColor(DARK)
        for x, val in zip(col_x, [price, single, spread]):
            c.drawString(x, y - 9, val)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/spreads-hedging-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Spreads & Hedging — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Spreads & Hedging", "Defining Your Risk on Both Sides — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", TEAL)
    y = draw_body(c, y, "A spread combines two or more options of the same type on the same underlying, "
                         "at different strikes or expirations, to create a position with a precisely "
                         "defined maximum gain and maximum loss.")
    y -= PARA_GAP
    y = draw_body(c, y, "A bull call spread buys a lower-strike call and sells a higher-strike call - "
                         "cheaper than the call alone, but with upside capped at the higher strike. A "
                         "bear put spread does the mirror image with puts.")
    y -= PARA_GAP
    y = draw_body(c, y, "Hedging uses an option to offset risk already present elsewhere in a "
                         "portfolio. A protective put acts like insurance on stock you own. A collar "
                         "combines a protective put with a covered call, often structured so the "
                         "premiums roughly offset.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: A Bull Call Spread vs. a Single Call", PURPLE)
    y = draw_body(c, y, "Stock at $100. Single $100 call for $6, versus a spread: buy the $100 call for "
                         "$6, sell a $110 call for $2 (net cost $4).")
    y = draw_spread_table(c, y)
    y = draw_body(c, y, "The spread costs less upfront, has a smaller max loss, and breaks even sooner "
                         "- but sacrifices unlimited upside for a hard cap at $6 gain, no matter how "
                         "high the stock eventually goes.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About Spreads & Hedging", GOLD)
    facts = [
        "Spreads trade unlimited potential for defined risk - both max gain and max loss are known upfront.",
        "A spread is cheaper because you're also selling one - the short leg partially offsets the cost.",
        "Hedging costs something, by design - a protective put's premium is the price of a floor.",
        "A collar can be structured near zero-cost - but that typically means giving up upside.",
        "Spreads and hedges reduce risk, they don't eliminate exposure - a loss within range is still possible.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check Before Using a Spread or Hedge", GREEN)
    tips = [
        "Confirm both legs match - same expiration, underlying, and contract sizes.",
        "Know your max gain and max loss upfront - calculate both before placing the trade.",
        "Weigh the hedge cost against what it protects - size the premium against the real downside.",
        "Watch both legs into expiration - assignment risk applies to the short leg of a spread too.",
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
        "this explains spreads and hedging using illustrative numbers - it isn't personalized "
        "financial advice, and no strategy here is a recommendation to trade. All options strategies "
        "carry risk, and defined-risk positions can still result in a loss within their stated range.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", TEAL, size=12)
    y -= 10

    questions = [
        ("1. What is a vertical spread?", [
            "A. Buying stock and a call at the same time",
            "B. Buying one option and selling another of the same type and expiration, at a different strike",
            "C. Selling an uncovered call with no other position",
            "D. A type of stock, not an options strategy"]),
        ("2. In the illustrative example, why did the bull call spread cost less than the single call?", [
            "A. Because spreads are always free to enter",
            "B. Because the stock price was lower for the spread trade",
            "C. Because the premium collected from selling the higher-strike call offset part of the cost",
            "D. Because the broker waived the commission"]),
        ("3. What is a protective put?", [
            "A. Buying a put against stock you own, to put a floor under potential losses",
            "B. Selling a put with no other position",
            "C. A put option that never expires",
            "D. A type of covered call"]),
        ("4. What is a collar, according to this lesson?", [
            "A. Two calls bought at the same strike",
            "B. A type of bond, not an options strategy",
            "C. Selling both a call and a put with no stock position",
            "D. A protective put combined with a covered call, often structured so the premiums roughly offset"]),
        ("5. Do spreads and hedges eliminate all risk?", [
            "A. Yes, defined-risk strategies guarantee a profit",
            "B. Yes, but only for call spreads specifically",
            "C. No, they reduce and bound risk, but a position can still lose money within its defined range",
            "D. No, spreads always increase total risk compared to a single option"]),
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
        ("1. What is a vertical spread?",
         "B. Buying one option and selling another of the same type and expiration, at a different strike",
         "A vertical spread combines a long and short option of the same type and expiration at different strikes."),
        ("2. In the illustrative example, why did the bull call spread cost less than the single call?",
         "C. Because the premium collected from selling the higher-strike call offset part of the cost",
         "Selling the $110 call for $2 offset part of the $6 cost of the $100 call."),
        ("3. What is a protective put?",
         "A. Buying a put against stock you own, to put a floor under potential losses",
         "A protective put means buying a put against stock you own, acting like insurance."),
        ("4. What is a collar, according to this lesson?",
         "D. A protective put combined with a covered call, often structured so the premiums roughly offset",
         "A collar combines a protective put with a covered call, trading upside for a cheaper floor."),
        ("5. Do spreads and hedges eliminate all risk?",
         "C. No, they reduce and bound risk, but a position can still lose money within its defined range",
         "Spreads and hedges reduce and define risk, but don't eliminate market exposure entirely."),
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
    path = "static/downloads/spreads-hedging-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Spreads & Hedging — Practice Worksheet · Pro"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Spreads & Hedging", "PRO PRACTICE WORKSHEET")
    y = draw_body(c, y, "Work through these by hand or with a spreadsheet. There's no wrong answer, "
                         "the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Build a Bull Call Spread", TEAL)
    y = draw_body(c, y, "Buy a $50 call for $3, sell a $60 call for $1. Calculate the net cost, max "
                         "gain, max loss, and breakeven.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Compare to a Single Call", GREEN)
    y = draw_body(c, y, "Using the same $50 call from Section 1, calculate the P&L of just the single "
                         "call (no spread) if the stock finishes at $58 and at $70. Compare to the "
                         "spread's outcome at those same prices.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Price a Protective Put", GOLD)
    y = draw_body(c, y, "You own stock at $80 and buy a $75 put for $2 as protection. What is your "
                         "maximum possible loss on the combined position, per share?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Structure a Collar", PURPLE)
    y = draw_body(c, y, "Using the $75 put from Section 3 (cost $2), what strike and premium would a "
                         "covered call need to roughly offset that cost and create a near-zero-cost collar?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "In your own words, explain the trade-off a trader accepts when moving from a "
                         "single option position to a defined-risk spread.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/spreads-hedging-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Spreads & Hedging — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Spreads & Hedging", "PRO FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on spreads and hedging? These are free, reputable, and "
                         "worth bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Vertical Spread",
         "https://www.investopedia.com/terms/v/verticalspread.asp",
         "A detailed walkthrough of vertical spreads, including bull call and bear put spreads."),
        ("Investopedia - Bull Call Spread",
         "https://www.investopedia.com/terms/b/bullcallspread.asp",
         "A deeper dive into the specific spread used in this lesson's illustrative example."),
        ("Investopedia - Protective Put",
         "https://www.investopedia.com/terms/p/protective-put.asp",
         "Explains the protective put hedging strategy referenced in this lesson."),
        ("Investopedia - Collar",
         "https://www.investopedia.com/terms/c/collar.asp",
         "Covers the collar strategy, combining a protective put and a covered call."),
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
        "these are general educational resources, not personalized financial advice. Options trading "
        "carries substantial risk. Consult a licensed financial advisor before making investment "
        "decisions.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.save()
    print("done:", path)


if __name__ == "__main__":
    build_explainer()
    build_worksheet()
    build_further_reading()
