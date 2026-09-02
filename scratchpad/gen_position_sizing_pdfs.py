"""Generate the 3 downloadable PDFs for the Intermediate 'Position Sizing' lesson
(fourth lesson in the Balancing a Portfolio track).
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


def draw_sizing_table(c, y):
    rows = [
        ("5% Position", "$2,500", "-$750", "-1.5%", False),
        ("10% Position", "$5,000", "-$1,500", "-3.0%", False),
        ("25% Position", "$12,500", "-$3,750", "-7.5%", True),
        ("50% Position", "$25,000", "-$7,500", "-15.0%", False),
    ]
    col_x = [LEFT + 6, LEFT + 150, LEFT + 270, LEFT + 380]
    labels = ["Position Size", "Position Value", "Loss at -30%", "Loss as % Port."]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(PURPLE)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(Color(1, 1, 1))
    for x, lab in zip(col_x, labels):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (name, pv, loss, pct, bold) in enumerate(rows):
        if bold:
            c.setFillColor(Color(0.90, 0.85, 0.98))
        elif i % 2 == 1:
            c.setFillColor(Color(0.95, 0.95, 0.97))
        else:
            c.setFillColor(Color(1, 1, 1))
        c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 8)
        c.setFillColor(DARK)
        for x, val in zip(col_x, [name, pv, loss, pct]):
            c.drawString(x, y - 9, val)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/position-sizing-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Position Sizing — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Position Sizing", "How Much Is Too Much in One Holding? — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", PURPLE)
    y = draw_body(c, y, "Two investors can hold the exact same stock and end up with very different "
                         "outcomes, purely because of how much of their portfolio they put into it. A "
                         "2% position that halves costs 1% of the total portfolio - a 40% position that "
                         "halves costs 20%.")
    y -= PARA_GAP
    y = draw_body(c, y, "Position sizing is the decision, made before you buy, of what percentage of "
                         "your total portfolio a single holding is allowed to occupy. A great company "
                         "can still be a bad position if it's sized too large.")
    y -= PARA_GAP
    y = draw_body(c, y, "Two common approaches: a maximum-weight rule (e.g. no single stock over 10%) "
                         "and a risk-based rule (e.g. risk no more than 1-2% of the account on any one "
                         "trade's stop-loss distance). Both answer the same question: how much can this "
                         "one position hurt me if I'm wrong?")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: Same Loss, Different Position Sizes", TEAL)
    y = draw_body(c, y, "A $50,000 portfolio holds a stock that drops 30%. The dollar loss depends "
                         "entirely on the position size going in.")
    y = draw_sizing_table(c, y)
    y = draw_body(c, y, "Same stock, same -30% move - but the portfolio-level damage ranges from a "
                         "shrug (-1.5%) to a serious setback (-15%), purely as a function of position size.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About Position Sizing", GOLD)
    facts = [
        "Conviction isn't a sizing plan - overconfidence is exactly what precedes oversized positions.",
        "Sizing rules are set before you buy - deciding the cap after a big gain just rationalizes it.",
        "A max-weight rule protects against concentration risk from any one company.",
        "A risk-based rule protects against a single trade blowing up an account.",
        "Winners can outgrow their cap on their own - that's what rebalancing exists to fix.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check Before You Buy", GREEN)
    tips = [
        "Set a max weight in advance - decide your cap before you're attached to a specific idea.",
        "Know your risk-per-trade - size so a stopped-out trade only costs a small, defined slice.",
        "Use a calculator, not a gut feel - work backward from risk amount and stop distance.",
        "Re-check after big moves - a winning position can drift past your cap on its own.",
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
        "this explains the mechanics and reasoning behind position sizing rules using illustrative "
        "numbers - it isn't personalized financial advice. Speak to a licensed advisor about what's "
        "appropriate for your own portfolio.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", PURPLE, size=12)
    y -= 10

    questions = [
        ("1. What is position sizing?", [
            "A. Predicting which stock will perform best",
            "B. Deciding when to buy or sell a stock",
            "C. Deciding, before buying, what percentage of the portfolio a single holding may occupy",
            "D. Choosing which broker to trade through"]),
        ("2. In the illustrative example, why did the same -30% move cause such different damage?", [
            "A. Because different investors paid different prices for the stock",
            "B. Because the position sizes relative to the total portfolio were different",
            "C. Because some investors used stop-losses and others didn't",
            "D. Because the stock dropped by different amounts for different people"]),
        ("3. What are the two common position sizing approaches described in this lesson?", [
            "A. Buy low, sell high",
            "B. Technical and fundamental analysis",
            "C. Long-term and short-term",
            "D. A maximum-weight rule and a risk-based rule"]),
        ("4. Why should sizing rules be set before buying, not after?", [
            "A. Deciding the cap after a position is up big just rationalizes letting it run unchecked",
            "B. It's required by law in most markets",
            "C. It has no effect on the outcome either way",
            "D. Brokers automatically enforce sizing rules for you"]),
        ("5. What should you do if a winning position naturally grows past your size cap?", [
            "A. Nothing - winners should always be left alone",
            "B. Sell the entire position immediately",
            "C. Treat it as a cue to rebalance, trimming it back toward its target weight",
            "D. Raise the size cap to match wherever the position has grown to"]),
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
        ("1. What is position sizing?",
         "C. Deciding, before buying, what percentage of the portfolio a single holding may occupy",
         "Position sizing is separate from stock-picking - it's about how much capital any one idea is allowed to control."),
        ("2. In the illustrative example, why did the same -30% move cause such different damage?",
         "B. Because the position sizes relative to the total portfolio were different",
         "Same stock, same percentage move - but different weights translate that into very different portfolio-level dents."),
        ("3. What are the two common position sizing approaches described in this lesson?",
         "D. A maximum-weight rule and a risk-based rule",
         "A max-weight rule caps a position's share of the portfolio; a risk-based rule sizes from your stop-loss distance."),
        ("4. Why should sizing rules be set before buying, not after?",
         "A. Deciding the cap after a position is up big just rationalizes letting it run unchecked",
         "Setting the cap in advance removes the temptation to keep raising it because a position is doing well."),
        ("5. What should you do if a winning position naturally grows past your size cap?",
         "C. Treat it as a cue to rebalance, trimming it back toward its target weight",
         "This is exactly the drift problem the Rebalancing lesson covers."),
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
    path = "static/downloads/position-sizing-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Position Sizing — Practice Worksheet · Intermediate"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Position Sizing", "INTERMEDIATE PRACTICE WORKSHEET")
    y = draw_body(c, y, "Look at your own portfolio, or a hypothetical one. There's no wrong answer, "
                         "the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Set Your Max-Weight Cap", TEAL)
    y = draw_body(c, y, "What percentage of your total portfolio are you comfortable letting a single "
                         "stock occupy? Why that number?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Calculate a Risk-Based Size", GREEN)
    y = draw_body(c, y, "Pick a risk percentage per trade and a stop-loss distance. Using the lesson's "
                         "method, calculate the resulting position size.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Which Rule Wins?", GOLD)
    y = draw_body(c, y, "Compare your risk-based size and your max-weight cap from Sections 1-2. Which "
                         "one is smaller? That's the position size you'd actually use.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Check a Past Decision", PURPLE)
    y = draw_body(c, y, "Think of a real or hypothetical position you've held that was oversized. What "
                         "would applying your rule from Section 1 have changed?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "Be honest: when a stock you own is up a lot and now exceeds your cap, would "
                         "you actually trim it? What would make it easier to follow through?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/position-sizing-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Position Sizing — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Position Sizing", "INTERMEDIATE FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on position sizing? These are free, reputable, and worth "
                         "bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Position Sizing",
         "https://www.investopedia.com/terms/p/positionsizing.asp",
         "A detailed walkthrough of position sizing and why it matters as much as the pick itself."),
        ("Investopedia - Kelly Criterion",
         "https://www.investopedia.com/terms/k/kellycriterion.asp",
         "Explains the risk-based sizing formula referenced by GCG's own Position Size Calculator tool."),
        ("Investor.gov - Beginners' Guide to Asset Allocation",
         "https://www.investor.gov/introduction-investing/investing-basics/save-and-invest/asset-allocation",
         "The SEC's own plain-English guide to spreading risk across a portfolio."),
        ("Investor.gov",
         "https://www.investor.gov/",
         "The U.S. Securities and Exchange Commission's official investor education site."),
        ("Investopedia",
         "https://www.investopedia.com/",
         "A huge library of plain-English financial explainers, useful for looking up any term from this lesson."),
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
