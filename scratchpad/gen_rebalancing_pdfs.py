"""Generate the 3 downloadable PDFs for the Intermediate 'Rebalancing' lesson
(third lesson in the Balancing a Portfolio track).
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


def draw_rebal_table(c, y):
    rows = [
        ("Starting Portfolio ($100,000)", "$60,000", "$40,000", "60%", "40%", False),
        ("After a Strong Stock Rally", "$84,000", "$42,000", "67%", "33%", False),
        ("After Rebalancing Back to 60/40", "$75,600", "$50,400", "60%", "40%", True),
    ]
    col_x = [LEFT + 6, LEFT + 210, LEFT + 290, LEFT + 370, LEFT + 420]
    labels = ["Stage", "Stocks Value", "Bonds Value", "Stocks %", "Bonds %"]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(PURPLE)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(Color(1, 1, 1))
    for x, lab in zip(col_x, labels):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (name, sv, bv, sp, bp, bold) in enumerate(rows):
        if bold:
            c.setFillColor(Color(0.90, 0.85, 0.98))
        elif i % 2 == 1:
            c.setFillColor(Color(0.95, 0.95, 0.97))
        else:
            c.setFillColor(Color(1, 1, 1))
        c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 8)
        c.setFillColor(DARK)
        for x, val in zip(col_x, [name, sv, bv, sp, bp]):
            c.drawString(x, y - 9, val)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/rebalancing-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Rebalancing — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Rebalancing", "Keeping Your Portfolio on Target — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", PURPLE)
    y = draw_body(c, y, "If stocks rally while bonds stay flat, stocks naturally grow to take up more "
                         "than their original share - not from any action, just because they grew "
                         "faster. Left alone, a portfolio quietly drifts toward higher risk.")
    y -= PARA_GAP
    y = draw_body(c, y, "Rebalancing means periodically trimming oversized positions and topping up "
                         "shrunk ones, back to target - a disciplined 'sell high, buy low' that doesn't "
                         "depend on predicting anything.")
    y -= PARA_GAP
    y = draw_body(c, y, "Two common approaches: calendar-based (fixed schedule) and threshold-based "
                         "(rebalance when drift exceeds a set amount). What matters most is having a "
                         "rule and following it.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: A 60/40 Portfolio After a Stock Rally", TEAL)
    y = draw_rebal_table(c, y)
    y = draw_body(c, y, "Stocks drifted from 60% to 67% - nobody chose that, it just happened. "
                         "Rebalancing means selling $8,400 of stocks and buying $8,400 of bonds to "
                         "restore the 60/40 target.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About Rebalancing", GOLD)
    facts = [
        "Drift happens automatically - strong performers simply grow faster.",
        "Rebalancing systematizes 'sell high, buy low' without needing to predict anything.",
        "Calendar-based and threshold-based are both valid - the key is having a rule and following it.",
        "Rebalancing can have costs - trading fees and potential tax consequences.",
        "It's emotionally uncomfortable by design - selling winners to buy laggards feels wrong.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check When Rebalancing", GREEN)
    tips = [
        "Pick a rule and stick to it - calendar or threshold-based, either works if followed.",
        "Watch trading costs - frequent rebalancing racks up fees and possible capital gains tax.",
        "Use new contributions first - directing deposits to underweight positions rebalances without selling.",
        "Expect the discomfort - if it doesn't feel uncomfortable, you're probably not actually doing it.",
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
        "rebalancing is a risk-management discipline, not a way to boost returns on its own - its main "
        "job is keeping your portfolio's risk level where you actually intended it.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", PURPLE, size=12)
    y -= 10

    questions = [
        ("1. Why does a portfolio's allocation drift even if you never trade?", [
            "A. It doesn't - allocations stay fixed unless you actively change them",
            "B. Because brokers automatically change your holdings",
            "C. Because different assets grow at different rates, shifting their share of the total",
            "D. Because of currency exchange rates only"]),
        ("2. What does rebalancing mechanically involve?", [
            "A. Buying more of whatever has performed best recently",
            "B. Trimming positions that have grown oversized and topping up ones that have shrunk",
            "C. Selling your entire portfolio and starting over",
            "D. Never touching your portfolio under any circumstances"]),
        ("3. What are the two common rebalancing approaches mentioned in this lesson?", [
            "A. Random and emotional",
            "B. Daily and hourly",
            "C. Only when a financial advisor tells you to",
            "D. Calendar-based (fixed schedule) and threshold-based (drift trigger)"]),
        ("4. Why should rebalancing not be done excessively often?", [
            "A. Trading fees and potential capital gains tax add real costs",
            "B. It's illegal to rebalance more than once a year",
            "C. Rebalancing has no costs, so frequency doesn't matter at all",
            "D. Rebalancing always increases your allocation to stocks"]),
        ("5. Why did rebalancing feel emotionally uncomfortable in the illustrative example?", [
            "A. Because it required predicting the market's next move",
            "B. Because it involved no actual trading",
            "C. Because it meant selling the recently-strong performer to buy the laggard",
            "D. Because bonds are always a bad investment"]),
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
        ("1. Why does a portfolio's allocation drift even if you never trade?",
         "C. Because different assets grow at different rates, shifting their share of the total",
         "Stronger-performing assets naturally grow to take up a larger share of the portfolio over time."),
        ("2. What does rebalancing mechanically involve?",
         "B. Trimming positions that have grown oversized and topping up ones that have shrunk",
         "Rebalancing means selling some of what's grown and buying more of what's lagged."),
        ("3. What are the two common rebalancing approaches mentioned in this lesson?",
         "D. Calendar-based (fixed schedule) and threshold-based (drift trigger)",
         "Calendar-based happens on a fixed schedule; threshold-based triggers when drift exceeds a set amount."),
        ("4. Why should rebalancing not be done excessively often?",
         "A. Trading fees and potential capital gains tax add real costs",
         "Rebalancing has real costs, so excessive frequency erodes its benefit."),
        ("5. Why did rebalancing feel emotionally uncomfortable in the illustrative example?",
         "C. Because it meant selling the recently-strong performer to buy the laggard",
         "Selling what's been winning to buy what's been lagging feels counterintuitive in the moment."),
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
    path = "static/downloads/rebalancing-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Rebalancing — Practice Worksheet · Intermediate"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Rebalancing", "INTERMEDIATE PRACTICE WORKSHEET")
    y = draw_body(c, y, "Look at your own portfolio, or a hypothetical one. There's no wrong answer, "
                         "the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Check Your Current Drift", TEAL)
    y = draw_body(c, y, "What is your target allocation? What is your current actual allocation? How "
                         "far has it drifted?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Calculate the Rebalancing Trade", GREEN)
    y = draw_body(c, y, "Using the lesson's method, calculate how much you'd need to sell of the "
                         "overweight asset and buy of the underweight one to get back to target.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Pick a Rebalancing Rule", GOLD)
    y = draw_body(c, y, "Would you rather rebalance on a calendar schedule (e.g. annually) or a "
                         "threshold trigger (e.g. 5 percentage points drift)? Why?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Consider the Costs", PURPLE)
    y = draw_body(c, y, "Is your portfolio in a taxable account? How might trading fees or capital "
                         "gains tax affect how often you'd want to rebalance?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "Be honest: if your portfolio drifted 10 percentage points from target right "
                         "now, would you actually rebalance? What would make it easier to follow through?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/rebalancing-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Rebalancing — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Rebalancing", "INTERMEDIATE FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on rebalancing? These are free, reputable, and worth "
                         "bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Rebalancing",
         "https://www.investopedia.com/terms/r/rebalancing.asp",
         "A detailed walkthrough of rebalancing and the different approaches to it."),
        ("Investor.gov - Beginners' Guide to Asset Allocation",
         "https://www.investor.gov/introduction-investing/investing-basics/save-and-invest/asset-allocation",
         "The SEC's own plain-English guide to asset allocation, closely related to rebalancing."),
        ("Investopedia - Threshold Rebalancing",
         "https://www.investopedia.com/terms/r/rebalancing.asp",
         "Covers threshold-based rebalancing rules referenced in this lesson."),
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
