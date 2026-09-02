"""Generate the 3 downloadable PDFs for the Pro 'Backtesting' lesson
(third lesson in the Quantitative Strategy Design track).
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


def draw_cost_table(c, y):
    rows = [
        ("No Costs Assumed", "240", "+18.0%", "0.0%", "+18.0%", False),
        ("Realistic Costs Assumed", "240", "+18.0%", "-11.5%", "+6.5%", True),
    ]
    col_x = [LEFT + 6, LEFT + 165, LEFT + 230, LEFT + 320, LEFT + 410]
    labels = ["Version", "Trades/Yr", "Gross Return", "Est. Cost Drag", "Net Return"]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(TEAL)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(DARK)
    for x, lab in zip(col_x, labels):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (name, trades, gross, drag, net, bold) in enumerate(rows):
        if bold:
            c.setFillColor(Color(0.85, 0.98, 0.96))
        elif i % 2 == 1:
            c.setFillColor(Color(0.95, 0.95, 0.97))
        else:
            c.setFillColor(Color(1, 1, 1))
        c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 8)
        c.setFillColor(DARK)
        for x, val in zip(col_x, [name, trades, gross, drag, net]):
            c.drawString(x, y - 9, val)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/backtesting-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Backtesting — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Backtesting", "Proving an Idea Before Risking Real Money — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", TEAL)
    y = draw_body(c, y, "A backtest takes a strategy's precisely defined rules and simulates applying "
                         "them to historical data. It answers 'if I had followed this exact rule in the "
                         "past, what result would it have produced?' - a necessary first filter before "
                         "risking real capital.")
    y -= PARA_GAP
    y = draw_body(c, y, "Two failure modes dominate: lookahead bias (using information that wouldn't "
                         "have been available at the time) and overfitting (tuning rules so precisely "
                         "to historical data that the strategy has memorized the past rather than found "
                         "a real, repeatable pattern).")
    y -= PARA_GAP
    y = draw_body(c, y, "A realistic backtest also accounts for commissions, the bid-ask spread, and "
                         "slippage. A strategy that looks great with zero costs can turn unprofitable "
                         "once realistic frictions are added.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: Same Backtest, With and Without Realistic Costs", PURPLE)
    y = draw_cost_table(c, y)
    y = draw_body(c, y, "240 trades a year at even a small per-trade cost compounds into a large "
                         "annual drag - the 'no costs' version looks like a great strategy, the "
                         "realistic version looks merely decent. Always ask which one you're looking at.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About Backtesting", GOLD)
    facts = [
        "A great backtest is necessary, not sufficient - it filters bad ideas, doesn't guarantee good ones.",
        "Overfitting gets worse the more you tune - more adjusted parameters means more risk of fitting noise.",
        "Out-of-sample testing is the standard defense - test rules on data they never saw during tuning.",
        "Survivorship bias can silently inflate results - testing only on companies that still exist today.",
        "A backtest is a simulation, not a guarantee - conditions change, and history never repeats exactly.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check in Any Backtest", GREEN)
    tips = [
        "Check for lookahead bias - confirm every input would genuinely have been known at that time.",
        "Include realistic costs - model commissions, spread, and slippage, especially for frequent trading.",
        "Hold out a true test period - never tune parameters on the same data used to judge the result.",
        "Stress-test across regimes - check performance separately across calm, trending, volatile periods.",
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
        "this explains backtesting methodology using illustrative numbers - it isn't personalized "
        "financial advice, and no strategy or backtest result here is a recommendation to trade. Past "
        "backtested performance is never a guarantee of future results.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", TEAL, size=12)
    y -= 10

    questions = [
        ("1. What does a backtest do?", [
            "A. Predicts exactly what a strategy will return in the future",
            "B. Simulates a strategy's precisely defined rules against historical data",
            "C. Automatically executes trades in a live account",
            "D. Guarantees a strategy is profitable if the result is positive"]),
        ("2. What is lookahead bias?", [
            "A. Trading too infrequently",
            "B. Using too many years of historical data",
            "C. Accidentally using information that wouldn't have been available at the time",
            "D. Ignoring trading costs in a simulation"]),
        ("3. In the illustrative example, why did realistic costs matter so much for the frequent-trading strategy?", [
            "A. Because the strategy only traded once a year",
            "B. Because costs only apply to losing trades",
            "C. Because commissions are the same regardless of trade frequency",
            "D. Because 240 trades a year compounds even a small per-trade cost into a large annual drag"]),
        ("4. What is the standard defense against overfitting described in this lesson?", [
            "A. Out-of-sample testing - testing rules, unchanged, on data they never saw during tuning",
            "B. Adding more parameters to the strategy",
            "C. Testing only on the most recent month of data",
            "D. Ignoring the backtest result entirely"]),
        ("5. What is survivorship bias in this context?", [
            "A. Only trading strategies that have never lost money",
            "B. Backtesting only during bull markets",
            "C. Testing only on companies that still exist today, ignoring ones that went bankrupt or were delisted",
            "D. Using too short a historical data window"]),
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
        ("1. What does a backtest do?",
         "B. Simulates a strategy's precisely defined rules against historical data",
         "A backtest answers 'if I had followed this exact rule in the past, what would have happened?' - not a guarantee."),
        ("2. What is lookahead bias?",
         "C. Accidentally using information that wouldn't have been available at the time",
         "Lookahead bias inflates a backtest's apparent result by using data before it would genuinely have been known."),
        ("3. In the illustrative example, why did realistic costs matter so much for the frequent-trading strategy?",
         "D. Because 240 trades a year compounds even a small per-trade cost into a large annual drag",
         "A high trade count multiplies small per-trade frictions into a substantial annual cost."),
        ("4. What is the standard defense against overfitting described in this lesson?",
         "A. Out-of-sample testing - testing rules, unchanged, on data they never saw during tuning",
         "Out-of-sample testing checks whether rules still hold up on a separate period they never influenced."),
        ("5. What is survivorship bias in this context?",
         "C. Testing only on companies that still exist today, ignoring ones that went bankrupt or were delisted",
         "Survivorship bias inflates results by silently excluding companies that failed along the way."),
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
    path = "static/downloads/backtesting-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Backtesting — Practice Worksheet · Pro"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Backtesting", "PRO PRACTICE WORKSHEET")
    y = draw_body(c, y, "Work through these by hand or with a spreadsheet. There's no wrong answer, "
                         "the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Audit for Lookahead Bias", TEAL)
    y = draw_body(c, y, "Pick a hypothetical trading rule (e.g. 'buy when quarterly earnings beat "
                         "estimates'). What data would need to be timestamped carefully to avoid "
                         "lookahead bias?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Calculate Cost Drag", GREEN)
    y = draw_body(c, y, "A strategy trades 100 times a year at an estimated 0.08% cost per trade. "
                         "Calculate the annual cost drag and the net return if gross return is 14%.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Design an Out-of-Sample Split", GOLD)
    y = draw_body(c, y, "If you had 10 years of historical data, how would you split it into a "
                         "'training' period for tuning and a 'test' period for judging the result?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Spot Survivorship Bias", PURPLE)
    y = draw_body(c, y, "Think of a backtest using 'today's S&P 500 constituents' over the past 20 "
                         "years. What companies would be missing, and how might that skew the result?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "Think of a strategy you've heard claimed 'great backtested returns.' What "
                         "questions from this lesson would you ask before trusting that number?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/backtesting-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Backtesting — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Backtesting", "PRO FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on backtesting methodology? These are free, reputable, and "
                         "worth bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Backtesting",
         "https://www.investopedia.com/terms/b/backtesting.asp",
         "A detailed walkthrough of backtesting and common pitfalls."),
        ("Investopedia - Overfitting",
         "https://www.investopedia.com/terms/o/overfitting.asp",
         "Explains overfitting, one of the two failure modes covered in this lesson."),
        ("Investopedia - Survivorship Bias",
         "https://www.investopedia.com/terms/s/survivorshipbias.asp",
         "Covers survivorship bias and how it can silently inflate backtested results."),
        ("Investopedia - Slippage",
         "https://www.investopedia.com/terms/s/slippage.asp",
         "Explains slippage, one of the realistic trading costs referenced in this lesson."),
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
        "these are general educational resources, not personalized financial advice. No strategy or "
        "backtest result described is a recommendation to trade. Consult a licensed financial advisor "
        "before making investment decisions.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.save()
    print("done:", path)


if __name__ == "__main__":
    build_explainer()
    build_worksheet()
    build_further_reading()
