"""Generate the 3 downloadable PDFs for the Pro 'Mean Reversion' lesson
(first lesson in the Quantitative Strategy Design track).
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


def draw_zscore_table(c, y):
    rows = [
        ("$115", "+$15", "+3.0", "Strong Sell / Fade", False),
        ("$110", "+$10", "+2.0", "Sell / Fade Threshold", True),
        ("$101", "+$1", "+0.2", "No Signal - Near Mean", False),
        ("$90", "-$10", "-2.0", "Buy / Fade Threshold", True),
        ("$82", "-$18", "-3.6", "Strong Buy / Fade", False),
    ]
    col_x = [LEFT + 6, LEFT + 130, LEFT + 250, LEFT + 340]
    labels = ["Current Price", "Distance From Mean", "Z-Score", "Illustrative Signal"]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(TEAL)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(DARK)
    for x, lab in zip(col_x, labels):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (price, dist, z, sig, bold) in enumerate(rows):
        if bold:
            c.setFillColor(Color(0.85, 0.98, 0.96))
        elif i % 2 == 1:
            c.setFillColor(Color(0.95, 0.95, 0.97))
        else:
            c.setFillColor(Color(1, 1, 1))
        c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 8)
        c.setFillColor(DARK)
        for x, val in zip(col_x, [price, dist, z, sig]):
            c.drawString(x, y - 9, val)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/mean-reversion-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Mean Reversion — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Mean Reversion", "Betting Prices Return to \"Normal\" — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", TEAL)
    y = draw_body(c, y, "Many prices and spreads oscillate around some underlying average rather than "
                         "trending forever. Mean reversion strategies formalize 'this has gone too far' "
                         "into a precise, repeatable rule based on statistical distance from that average.")
    y -= PARA_GAP
    y = draw_body(c, y, "The standard tool is the z-score: (current price - historical mean) / "
                         "historical standard deviation. A z-score of +2 means the price is two standard "
                         "deviations above its average - statistically unusual, and historically likely "
                         "(though never certain) to pull back.")
    y -= PARA_GAP
    y = draw_body(c, y, "Pairs trading and statistical arbitrage extend this to the spread between two "
                         "related assets, betting the gap itself reverts regardless of overall market "
                         "direction.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: Z-Score Signal Zones", PURPLE)
    y = draw_body(c, y, "A stock's 60-day historical mean is $100, standard deviation $5. Different "
                         "prices translate into these z-scores and illustrative signals.")
    y = draw_zscore_table(c, y)
    y = draw_body(c, y, "A common rule enters at +-2 (roughly the top/bottom 5% of a normal "
                         "distribution) and exits as price reverts toward zero - illustrative only; "
                         "real markets don't move in a neat bell curve.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About Mean Reversion", GOLD)
    facts = [
        "Not every asset mean-reverts - a genuinely trending asset can extend rather than revert.",
        "'Historical mean' is a moving target - too short a window is noisy, too long is slow to adapt.",
        "This is the same math as Bollinger Bands - a band touch is a z-score extreme, shown visually.",
        "'Catching a falling knife' is the classic failure - a stock cheap for real reasons can keep falling.",
        "Pairs trading isolates the spread, not market direction - it can profit in both up and down markets.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check Before Trusting a Signal", GREEN)
    tips = [
        "Choose your lookback window deliberately - test multiple windows, not just one.",
        "Ask why it's stretched - a fundamental change may mean it never reverts.",
        "Backtest with realistic costs - frequent, short-lived trades can be eaten by fees and slippage.",
        "Define an exit if it doesn't revert - a stop bounds the cost of a broken assumption.",
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
        "this explains the statistical reasoning behind mean-reversion strategies using illustrative "
        "numbers - it isn't personalized financial advice, and no strategy here is a recommendation to "
        "trade. Past patterns are never guaranteed to repeat.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", TEAL, size=12)
    y -= 10

    questions = [
        ("1. What does a mean-reversion strategy assume?", [
            "A. Prices always trend in one direction forever",
            "B. Trading volume predicts future prices",
            "C. A price that strays far from its historical average tends to pull back toward it",
            "D. Company earnings are irrelevant to price"]),
        ("2. How is a z-score calculated in this lesson?", [
            "A. Current price divided by trading volume",
            "B. (Current price - historical mean) / historical standard deviation",
            "C. Current price multiplied by the P/E ratio",
            "D. Yesterday's closing price minus today's opening price"]),
        ("3. What is the classic failure mode of mean reversion described in this lesson?", [
            "A. The strategy requires too much starting capital",
            "B. It only works on cryptocurrency markets",
            "C. It cannot be backtested at all",
            "D. 'Catching a falling knife' - a stock cheap for a genuine reason that keeps getting cheaper"]),
        ("4. What does pairs trading bet on, according to this lesson?", [
            "A. That the spread between two historically-linked assets will revert, regardless of market direction",
            "B. That the entire stock market will rise",
            "C. That interest rates will fall",
            "D. That one specific company will go bankrupt"]),
        ("5. Why should mean-reversion signals be backtested with realistic trading costs?", [
            "A. Trading costs don't affect mean-reversion strategies",
            "B. Regulators require it by law",
            "C. Mean-reversion trades are often frequent and short-lived, so costs can erase a paper edge",
            "D. It guarantees the strategy will be profitable"]),
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
        ("1. What does a mean-reversion strategy assume?",
         "C. A price that strays far from its historical average tends to pull back toward it",
         "Mean reversion assumes a stable underlying average exists and extreme deviations tend to correct over time."),
        ("2. How is a z-score calculated in this lesson?",
         "B. (Current price - historical mean) / historical standard deviation",
         "The z-score measures how many standard deviations the current price is from its historical mean."),
        ("3. What is the classic failure mode of mean reversion described in this lesson?",
         "D. 'Catching a falling knife' - a stock cheap for a genuine reason that keeps getting cheaper",
         "A statistically extreme z-score driven by real fundamental deterioration can keep extending past typical thresholds."),
        ("4. What does pairs trading bet on, according to this lesson?",
         "A. That the spread between two historically-linked assets will revert, regardless of market direction",
         "Pairs trading isolates the relationship between two related assets, aiming to profit regardless of overall market direction."),
        ("5. Why should mean-reversion signals be backtested with realistic trading costs?",
         "C. Mean-reversion trades are often frequent and short-lived, so costs can erase a paper edge",
         "Unrealistic cost assumptions in a backtest can make a losing strategy look profitable on paper."),
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
    path = "static/downloads/mean-reversion-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Mean Reversion — Practice Worksheet · Pro"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Mean Reversion", "PRO PRACTICE WORKSHEET")
    y = draw_body(c, y, "Work through these by hand or with a spreadsheet. There's no wrong answer, "
                         "the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Calculate Z-Scores by Hand", TEAL)
    y = draw_body(c, y, "A stock has a 60-day mean of $80 and standard deviation of $4. Calculate the "
                         "z-score for prices of $92, $84, and $70.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Set Your Own Thresholds", GREEN)
    y = draw_body(c, y, "Would you use a +-2 or a +-2.5 threshold for signals? What's the trade-off "
                         "between a tighter and a wider threshold?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Spot a Falling Knife", GOLD)
    y = draw_body(c, y, "Think of a real or hypothetical stock that fell hard on genuinely bad news. "
                         "How would you distinguish that from a normal statistical extreme?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Choose a Lookback Window", PURPLE)
    y = draw_body(c, y, "List the pros and cons of a 20-day versus a 120-day lookback window for "
                         "calculating the historical mean and standard deviation.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Design a Simple Exit Rule", TEAL)
    y = draw_body(c, y, "Sketch a rule for exiting a mean-reversion trade if the z-score keeps "
                         "extending instead of reverting, rather than holding indefinitely.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/mean-reversion-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Mean Reversion — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Mean Reversion", "PRO FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on mean reversion and statistical arbitrage? These are "
                         "free, reputable, and worth bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Mean Reversion",
         "https://www.investopedia.com/terms/m/meanreversion.asp",
         "A detailed walkthrough of mean reversion and how it's used across asset classes."),
        ("Investopedia - Z-Score",
         "https://www.investopedia.com/terms/z/zscore.asp",
         "Covers the z-score statistic referenced throughout this lesson."),
        ("Investopedia - Pairs Trading",
         "https://www.investopedia.com/terms/p/pairstrade.asp",
         "Explains how mean reversion is extended to the spread between two related assets."),
        ("Investopedia - Statistical Arbitrage",
         "https://www.investopedia.com/terms/s/statisticalarbitrage.asp",
         "A broader look at the systematic strategies built on mean-reversion logic."),
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
        "these are general educational resources, not personalized financial advice. No strategy "
        "described is a recommendation to trade. Consult a licensed financial advisor before making "
        "investment decisions.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.save()
    print("done:", path)


if __name__ == "__main__":
    build_explainer()
    build_worksheet()
    build_further_reading()
