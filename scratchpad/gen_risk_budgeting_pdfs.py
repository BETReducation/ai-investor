"""Generate the 3 downloadable PDFs for the Pro 'Position Sizing & Risk
Budgeting' lesson (fifth and final lesson in the Quantitative Strategy
Design track).
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


def draw_risk_table(c, y):
    rows = [
        ("Bonds (Low Vol)", "6%", "$100,000", "$192,000", False),
        ("Large-Cap Stocks (Med Vol)", "16%", "$100,000", "$72,000", False),
        ("Small-Cap Stock (High Vol)", "32%", "$100,000", "$36,000", True),
    ]
    col_x = [LEFT + 6, LEFT + 220, LEFT + 280, LEFT + 380]
    labels = ["Asset", "Volatility", "Equal-Dollar Size", "Risk-Budgeted Size"]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(TEAL)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(DARK)
    for x, lab in zip(col_x, labels):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (name, vol, eq, rb, bold) in enumerate(rows):
        if bold:
            c.setFillColor(Color(0.85, 0.98, 0.96))
        elif i % 2 == 1:
            c.setFillColor(Color(0.95, 0.95, 0.97))
        else:
            c.setFillColor(Color(1, 1, 1))
        c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 8)
        c.setFillColor(DARK)
        for x, val in zip(col_x, [name, vol, eq, rb]):
            c.drawString(x, y - 9, val)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/risk-budgeting-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Position Sizing & Risk Budgeting — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Position Sizing & Risk Budgeting", "At the Strategy Level — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", TEAL)
    y = draw_body(c, y, "Risk budgeting extends the Intermediate Position Sizing idea - 'how much can "
                         "this hurt me if I'm wrong?' - from a single stock to an entire multi-strategy "
                         "or multi-asset portfolio.")
    y -= PARA_GAP
    y = draw_body(c, y, "Key insight: an equal dollar amount in two different assets is not an equal "
                         "amount of risk. $10,000 in a low-volatility bond and $10,000 in a high-"
                         "volatility small-cap stock contribute very different amounts of risk, even "
                         "with matching dollar amounts.")
    y -= PARA_GAP
    y = draw_body(c, y, "A common formula: position size = (target risk contribution) / (asset's "
                         "volatility). A more volatile asset gets a smaller dollar allocation for the "
                         "same risk budget; a calmer asset gets a larger one.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: Equal Dollars vs. Equal Risk", PURPLE)
    y = draw_body(c, y, "Three hypothetical assets with very different volatility, sized two ways from "
                         "a $300,000 total allocation.")
    y = draw_risk_table(c, y)
    y = draw_body(c, y, "Under equal-dollar sizing, the small-cap stock (32% volatility) contributes "
                         "over 5x as much risk as the bonds (6% volatility), despite the identical "
                         "dollar size. Risk-budgeted sizing balances the risk contributions instead.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About Risk Budgeting", GOLD)
    facts = [
        "Equal dollars is not equal risk - the single most important idea in this lesson.",
        "Volatility estimates are themselves uncertain and can shift quickly around regime changes.",
        "Risk parity isn't automatically 'safer' - total risk still depends on overall exposure/leverage.",
        "This scales the Intermediate idea up, not replaces it - same logic, applied to a whole book.",
        "Correlation between positions still matters - volatility alone ignores how positions move together.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check When Risk-Budgeting a Book", GREEN)
    tips = [
        "Measure volatility consistently - same lookback window and method across every asset compared.",
        "Don't ignore correlation - positions that move together still concentrate risk.",
        "Rebalance as volatility shifts - revisit sizing periodically as estimates change.",
        "Set an overall risk budget first - risk parity distributes risk, it doesn't cap it.",
    ]
    for t in tips:
        y = draw_body(c, y, "• " + t)
        y -= 8
    y -= SECTION_GAP - 16

    c.setFillColor(Color(0.98, 0.94, 0.86))
    box_h = 66
    c.rect(LEFT, y - box_h, CONTENT_W, box_h, fill=1, stroke=0)
    c.setStrokeColor(GOLD)
    c.setLineWidth(3)
    c.line(LEFT, y, LEFT, y - box_h)
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(DARK)
    c.drawString(LEFT + 12, y - 16, "Worth knowing:")
    c.setFont("Helvetica", 8.5)
    for i, line in enumerate(wrap(
        "this explains risk-budgeting methodology using illustrative numbers - it isn't personalized "
        "financial advice, and no allocation here is a recommendation for your own portfolio. "
        "Volatility-based sizing depends on estimates that are never certain, and past volatility is "
        "not a guarantee of future volatility.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", TEAL, size=12)
    y -= 10

    questions = [
        ("1. What is the key insight behind risk budgeting?", [
            "A. Every asset should get exactly the same dollar allocation",
            "B. Only bonds should be held in a portfolio",
            "C. An equal dollar amount in two different assets is not an equal amount of risk",
            "D. Risk cannot be measured or estimated"]),
        ("2. In the illustrative example, why did the small-cap stock get a smaller risk-budgeted dollar size?", [
            "A. Because small-cap stocks are illegal to hold in large amounts",
            "B. Because it had the lowest expected return",
            "C. Because it was the newest position in the portfolio",
            "D. Because its higher volatility meant a smaller dollar size was needed to contribute the same risk"]),
        ("3. What does this lesson say risk parity does NOT automatically do?", [
            "A. Distribute risk more evenly across positions",
            "B. Make a portfolio automatically 'safer' - total risk still depends on overall exposure and leverage",
            "C. Use volatility estimates in its sizing formula",
            "D. Apply the position-sizing idea across multiple assets"]),
        ("4. What does this lesson say a fuller risk-budgeting approach should also account for, beyond volatility alone?", [
            "A. Correlation between positions",
            "B. The color scheme of the trading platform",
            "C. The number of employees at each company",
            "D. The alphabetical order of ticker symbols"]),
        ("5. How does risk budgeting relate to the Intermediate Position Sizing lesson?", [
            "A. They are unrelated, completely different concepts",
            "B. Risk budgeting replaces and contradicts single-stock position sizing",
            "C. Risk budgeting scales the same 'size by risk, not dollars' idea up to a whole book",
            "D. Risk budgeting only applies to cryptocurrency portfolios"]),
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
        ("1. What is the key insight behind risk budgeting?",
         "C. An equal dollar amount in two different assets is not an equal amount of risk",
         "A flat dollar allocation silently over-weights risk toward the most volatile positions."),
        ("2. In the illustrative example, why did the small-cap stock get a smaller risk-budgeted dollar size?",
         "D. Because its higher volatility meant a smaller dollar size was needed to contribute the same risk",
         "More volatile assets get smaller dollar allocations so each position contributes similar risk."),
        ("3. What does this lesson say risk parity does NOT automatically do?",
         "B. Make a portfolio automatically 'safer' - total risk still depends on overall exposure and leverage",
         "Risk parity changes how risk is distributed, but total portfolio risk still depends on overall exposure."),
        ("4. What does this lesson say a fuller risk-budgeting approach should also account for, beyond volatility alone?",
         "A. Correlation between positions",
         "Sizing by volatility alone ignores how positions move together, which still concentrates risk."),
        ("5. How does risk budgeting relate to the Intermediate Position Sizing lesson?",
         "C. Risk budgeting scales the same 'size by risk, not dollars' idea up to a whole book",
         "Risk budgeting extends the same core idea from single-stock position sizing to an entire portfolio."),
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
    path = "static/downloads/risk-budgeting-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Position Sizing & Risk Budgeting — Practice Worksheet · Pro"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Position Sizing & Risk Budgeting", "PRO PRACTICE WORKSHEET")
    y = draw_body(c, y, "Work through these by hand or with a spreadsheet. There's no wrong answer, "
                         "the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Size a 2-Asset Book by Risk", TEAL)
    y = draw_body(c, y, "You have $200,000 to split between an asset with 8% volatility and one with "
                         "24% volatility. Using the lesson's formula, calculate the risk-budgeted "
                         "dollar size for each.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Compare to Equal-Dollar Sizing", GREEN)
    y = draw_body(c, y, "Using the same two assets, what would equal-dollar sizing look like instead? "
                         "How much more risk would the higher-volatility asset contribute?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Think About Correlation", GOLD)
    y = draw_body(c, y, "If your two risk-budgeted assets are highly correlated (move together), how "
                         "might that change how much real diversification benefit you're getting?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Set an Overall Risk Budget", PURPLE)
    y = draw_body(c, y, "Before allocating across positions, how would you decide the total portfolio "
                         "risk target in the first place?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Plan for Volatility Shifts", TEAL)
    y = draw_body(c, y, "If a regime shift (previous lesson) doubled one asset's volatility overnight, "
                         "how would its risk-budgeted dollar size need to change?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/risk-budgeting-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Position Sizing & Risk Budgeting — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Position Sizing & Risk Budgeting", "PRO FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on risk budgeting and risk parity? These are free, "
                         "reputable, and worth bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Risk Parity",
         "https://www.investopedia.com/terms/r/riskparity.asp",
         "A detailed walkthrough of risk parity, the strategy family referenced in this lesson."),
        ("Investopedia - Volatility",
         "https://www.investopedia.com/terms/v/volatility.asp",
         "Covers the volatility measure central to the sizing formula in this lesson."),
        ("Investopedia - Position Sizing",
         "https://www.investopedia.com/terms/p/positionsizing.asp",
         "The single-stock version of this idea, covered in GCG's Intermediate track."),
        ("Investopedia - Correlation Coefficient",
         "https://www.investopedia.com/terms/c/correlationcoefficient.asp",
         "Explains correlation, which a fuller risk-budgeting approach also accounts for."),
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
        "these are general educational resources, not personalized financial advice. No allocation "
        "described is a recommendation for your own portfolio. Consult a licensed financial advisor "
        "before making investment decisions.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.save()
    print("done:", path)


if __name__ == "__main__":
    build_explainer()
    build_worksheet()
    build_further_reading()
