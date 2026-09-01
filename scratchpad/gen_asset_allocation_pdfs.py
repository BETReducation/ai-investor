"""Generate the 3 downloadable PDFs for the Intermediate 'Asset Allocation'
lesson (first lesson in the Balancing a Portfolio track).
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


def draw_alloc_table(c, y):
    rows = [
        ("Conservative", "30%", "70%", "~5.2%/yr", "Lower swings", False),
        ("Balanced", "60%", "40%", "~6.8%/yr", "Moderate swings", True),
        ("Aggressive", "90%", "10%", "~8.2%/yr", "Larger swings", False),
    ]
    col_x = [LEFT + 6, LEFT + 130, LEFT + 200, LEFT + 270, LEFT + 370]
    labels = ["Allocation", "Stocks", "Bonds", "Illustr. Return", "Illustr. Volatility"]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(PURPLE)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(Color(1, 1, 1))
    for x, lab in zip(col_x, labels):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (name, s, b, ret, vol, bold) in enumerate(rows):
        if bold:
            c.setFillColor(Color(0.90, 0.85, 0.98))
        elif i % 2 == 1:
            c.setFillColor(Color(0.95, 0.95, 0.97))
        else:
            c.setFillColor(Color(1, 1, 1))
        c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 8)
        c.setFillColor(DARK)
        for x, val in zip(col_x, [name, s, b, ret, vol]):
            c.drawString(x, y - 9, val)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/asset-allocation-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Asset Allocation — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Asset Allocation", "Your Most Important Decision — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", PURPLE)
    y = draw_body(c, y, "Asset allocation is how you split money across broad categories - stocks, "
                         "bonds, cash, alternatives. Research consistently finds this split explains the "
                         "vast majority of a portfolio's long-term risk and return - more than which "
                         "specific stocks you pick.")
    y -= PARA_GAP
    y = draw_body(c, y, "Stocks: higher expected return, bigger swings. Bonds: lower return, more "
                         "stability. Cash: least growth, most stability. Blending them in different "
                         "proportions produces a completely different risk/return profile.")
    y -= PARA_GAP
    y = draw_body(c, y, "There's no single 'correct' allocation - the right mix depends on your time "
                         "horizon and risk tolerance (the next lessons in this section).")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: Three Model Allocations", TEAL)
    y = draw_alloc_table(c, y)
    y = draw_body(c, y, "Same universe of assets, three completely different outcomes - purely from "
                         "changing the split. Higher expected return comes paired with larger swings, "
                         "not for free.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About Asset Allocation", GOLD)
    facts = [
        "Allocation drives more of your outcome than security selection.",
        "Higher expected return comes with higher volatility - the trade-off is real.",
        "There's no universally 'correct' allocation - it depends on your time horizon and risk tolerance.",
        "Allocation isn't a one-time decision - revisit it as your goals and life stage change.",
        "Drift happens automatically - without rebalancing, winners grow to dominate your mix.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check When Setting an Allocation", GREEN)
    tips = [
        "Start with time horizon - a longer runway generally allows more room for stocks.",
        "Be honest about risk tolerance - an allocation you can't stick with isn't the right one.",
        "Think beyond just stocks and bonds - cash and alternatives can play a role too.",
        "Plan to revisit it - allocation is a decision you'll periodically reconsider.",
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
        "asset allocation is a framework for thinking about risk and return, not a formula with one "
        "right answer. Illustrative figures use simplified long-run assumptions for teaching purposes - "
        "actual results vary by period and by the specific assets held.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", PURPLE, size=12)
    y -= 10

    questions = [
        ("1. What is asset allocation?", [
            "A. Picking which individual stock to buy",
            "B. Timing when to buy and sell",
            "C. How you split your money across broad categories like stocks, bonds, and cash",
            "D. The fee a broker charges"]),
        ("2. What explains the vast majority of a portfolio's long-term risk and return?", [
            "A. Which specific stocks you pick within your allocation",
            "B. How often you check your portfolio",
            "C. Your broker's trading platform",
            "D. The asset allocation split itself"]),
        ("3. Why does higher expected return typically come with higher volatility?", [
            "A. There's no allocation offering stock-like returns with bond-like stability",
            "B. It doesn't - return and volatility are unrelated",
            "C. Bonds always outperform stocks over any period",
            "D. Volatility only affects cash holdings"]),
        ("4. Why isn't there one universally 'correct' asset allocation?", [
            "A. Because allocation doesn't actually matter",
            "B. Because the right mix depends on your own time horizon and risk tolerance",
            "C. Because regulators ban any specific allocation",
            "D. Because stocks and bonds always move together"]),
        ("5. What happens to an allocation if you never rebalance it?", [
            "A. It stays perfectly fixed forever automatically",
            "B. It's illegal not to rebalance",
            "C. It quietly drifts as winners grow faster than laggards",
            "D. Nothing changes regardless of market moves"]),
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
        ("1. What is asset allocation?",
         "C. How you split your money across broad categories like stocks, bonds, and cash",
         "Asset allocation is the split across broad asset categories."),
        ("2. What explains the vast majority of a portfolio's long-term risk and return?",
         "D. The asset allocation split itself",
         "The stocks/bonds/cash split explains most long-term outcomes - more than security selection."),
        ("3. Why does higher expected return typically come with higher volatility?",
         "A. There's no allocation offering stock-like returns with bond-like stability",
         "Higher expected returns come paired with larger swings - the trade-off is fundamental."),
        ("4. Why isn't there one universally 'correct' asset allocation?",
         "B. Because the right mix depends on your own time horizon and risk tolerance",
         "The 'right' allocation is personal, depending on time horizon and risk tolerance."),
        ("5. What happens to an allocation if you never rebalance it?",
         "C. It quietly drifts as winners grow faster than laggards",
         "Without rebalancing, strong performers grow to dominate the portfolio over time."),
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
    path = "static/downloads/asset-allocation-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Asset Allocation — Practice Worksheet · Intermediate"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Asset Allocation", "INTERMEDIATE PRACTICE WORKSHEET")
    y = draw_body(c, y, "There's no wrong answer here - the goal is to think through your own situation, "
                         "not to get a 'correct' score.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Your Time Horizon", TEAL)
    y = draw_body(c, y, "When will you likely need this money? 5 years, 15 years, 30+ years? How does "
                         "that change how much short-term volatility you can afford to take on?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Your Risk Tolerance", GREEN)
    y = draw_body(c, y, "If your portfolio dropped 25% in a bad year, would you stay invested or feel "
                         "pressure to sell? Be honest - this matters more than what looks good on paper.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Sketch a Starting Allocation", GOLD)
    y = draw_body(c, y, "Based on Sections 1 and 2, sketch a rough stocks/bonds/cash split for yourself. "
                         "There's no single right answer - just a starting point to refine.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Estimate the Trade-Off", PURPLE)
    y = draw_body(c, y, "Using the illustrative assumptions from the explainer (stocks ~9%/16%, bonds "
                         "~4%/6%, cash ~2%/1%), estimate your blended return and volatility.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "What would make you want to revisit this allocation in the future - a change in "
                         "goals, age, or something else?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/asset-allocation-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Asset Allocation — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Asset Allocation", "INTERMEDIATE FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on asset allocation? These are free, reputable, and worth "
                         "bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Asset Allocation",
         "https://www.investopedia.com/terms/a/assetallocation.asp",
         "A detailed walkthrough of asset allocation and how it's typically approached."),
        ("Investor.gov - Beginners' Guide to Asset Allocation",
         "https://www.investor.gov/introduction-investing/investing-basics/save-and-invest/asset-allocation",
         "The SEC's own plain-English guide to diversification and asset allocation."),
        ("Investopedia - Risk Tolerance",
         "https://www.investopedia.com/terms/r/risktolerance.asp",
         "Covers how to think about your own risk tolerance, referenced in this lesson."),
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
