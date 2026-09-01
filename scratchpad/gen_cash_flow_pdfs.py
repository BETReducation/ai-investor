"""Generate the 3 downloadable PDFs for the Intermediate 'Cash Flow' lesson
(third lesson in the Stock Picking track).
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
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(DARK)
    c.drawString(LEFT, y, title)
    y -= 24
    c.setFont("Helvetica", 10.5)
    c.setFillColor(GRAY)
    c.drawString(LEFT, y, subtitle_text)
    y -= SECTION_GAP
    return y


def draw_three_boxes(c, y):
    box_w = (CONTENT_W - 24) / 3
    box_h = 90
    boxes = [
        ("Operating", "+$68M", "Cash from the core business - compare against net income."),
        ("Investing", "-$25M", "Spent on equipment/property - negative usually means reinvesting."),
        ("Financing", "-$15M", "Paid to lenders/shareholders - debt repayment, dividends, buybacks."),
    ]
    for i, (title, val, desc) in enumerate(boxes):
        x = LEFT + i * (box_w + 12)
        c.setStrokeColor(GRAY)
        c.setLineWidth(0.8)
        c.roundRect(x, y - box_h, box_w, box_h, 6, stroke=1, fill=0)
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(PURPLE)
        c.drawString(x + 8, y - 16, title)
        c.setFont("Helvetica-Bold", 13)
        c.setFillColor(DARK)
        c.drawString(x + 8, y - 34, val)
        c.setFont("Helvetica", 7)
        c.setFillColor(GRAY)
        ty = y - 48
        for line in wrap(desc, 30):
            c.drawString(x + 8, ty, line)
            ty -= 9
    return y - box_h - 14


def draw_divergence_table(c, y):
    rows = [
        ("Net Income (from income statement)", "$40.0M", "$52.0M", True),
        ("+ Depreciation & Amortization", "$12.0M", "$13.0M", False),
        ("- Increase in Receivables", "$4.0M", "$38.0M", False),
        ("- Increase in Inventory", "$3.0M", "$5.0M", False),
        ("Operating Cash Flow", "$45.0M", "$22.0M", True),
    ]
    col_x = [LEFT + 6, LEFT + 300, LEFT + 390]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(PURPLE)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(Color(1, 1, 1))
    for x, lab in zip(col_x, ["Line Item", "Year 1", "Year 2"]):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (name, y1, y2, bold) in enumerate(rows):
        if bold:
            c.setFillColor(Color(0.90, 0.85, 0.98))
        elif i % 2 == 1:
            c.setFillColor(Color(0.95, 0.95, 0.97))
        else:
            c.setFillColor(Color(1, 1, 1))
        c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 8)
        c.setFillColor(DARK)
        c.drawString(col_x[0], y - 9, name)
        c.drawString(col_x[1], y - 9, y1)
        c.drawString(col_x[2], y - 9, y2)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/cash-flow-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Cash Flow — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Cash Flow", "Following the Money, Not Just the Profit — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", PURPLE)
    y = draw_body(c, y, "The cash flow statement shows real money moving in and out, split into three "
                         "sections: operating (core business), investing (long-term assets), and "
                         "financing (lenders and shareholders).")
    y -= PARA_GAP
    y = draw_body(c, y, "Free cash flow (FCF) = operating cash flow minus capital expenditures - what's "
                         "actually left to pay dividends, buy back stock, or pay down debt. Compare net "
                         "income to operating cash flow: a persistent gap often means profit is being "
                         "recognized before cash is collected.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "The Three Sections of a Cash Flow Statement", TEAL)
    y = draw_three_boxes(c, y)
    y = draw_body(c, y, "FCF here: $68M operating cash flow minus $22M of capex = $46M free cash flow - "
                         "real money generated after keeping physical assets maintained.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: When Profit and Cash Diverge", GREEN)
    y = draw_divergence_table(c, y)
    y = draw_body(c, y, "Year 2 net income grew 30%, but operating cash flow fell - receivables jumped "
                         "from $4.0M to $38.0M. The company booked more sales but collected proportionally "
                         "less cash.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About Cash Flow", GOLD)
    facts = [
        "Free cash flow is often more trustworthy than net income - harder to manipulate.",
        "Operating cash flow persistently below net income is a warning sign.",
        "Negative investing cash flow is usually healthy - it means investing in growth.",
        "Negative financing cash flow can be a good sign - paying down debt or returning cash.",
        "FCF funds everything discretionary - dividends, buybacks, and debt paydown.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check When Reading a Cash Flow Statement", GREEN)
    tips = [
        "Compare net income to operating cash flow - a widening gap is worth digging into.",
        "Read investing activities in context - maintenance capex vs growth/acquisitions.",
        "Check what financing activities fund - debt paydown funded by real FCF is healthier.",
        "Track FCF trend over several years, not just one.",
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
        "cash flow completes the picture started by the income statement and balance sheet. A company "
        "can report solid profit and a clean balance sheet while cash flow quietly tells a different "
        "story.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", PURPLE, size=12)
    y -= 10

    questions = [
        ("1. What is free cash flow?", [
            "A. Total revenue for the year",
            "B. Net income minus taxes",
            "C. Operating cash flow minus capital expenditures",
            "D. The cash a company has in the bank right now"]),
        ("2. What does it usually mean when operating cash flow falls well below net income?", [
            "A. The company is definitely committing fraud",
            "B. It's always a sign the stock will rise",
            "C. Nothing - it happens completely at random",
            "D. Rising receivables/inventory may be quietly tying up cash"]),
        ("3. Why is negative investing cash flow usually not alarming?", [
            "A. It always means the company is going bankrupt",
            "B. It typically means the company is spending on its own growth",
            "C. Investing cash flow is never negative in practice",
            "D. It means the company has stopped operating"]),
        ("4. Why can negative financing cash flow be a good sign?", [
            "A. It can reflect paying down debt or returning cash via dividends/buybacks",
            "B. Negative numbers are always bad in every context",
            "C. It means the company borrowed a lot of new debt",
            "D. Financing cash flow is unrelated to debt or dividends"]),
        ("5. Why did operating cash flow fall in Year 2 despite net income growing 30%?", [
            "A. Because revenue fell that year",
            "B. Because depreciation went to zero",
            "C. Because receivables jumped sharply, tying up uncollected cash",
            "D. Because the company paid off all its debt"]),
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
        ("1. What is free cash flow?",
         "C. Operating cash flow minus capital expenditures",
         "Free cash flow is real money left over after maintaining/growing the business's physical assets."),
        ("2. What does it usually mean when operating cash flow falls well below net income?",
         "D. Rising receivables/inventory may be quietly tying up cash",
         "A persistent, widening gap often means profit is being recognized before cash is collected."),
        ("3. Why is negative investing cash flow usually not alarming?",
         "B. It typically means the company is spending on its own growth",
         "Negative investing activities usually reflect reinvestment in physical assets - normal and healthy."),
        ("4. Why can negative financing cash flow be a good sign?",
         "A. It can reflect paying down debt or returning cash via dividends/buybacks",
         "Financing cash flow going negative often means paying down debt or returning cash to shareholders."),
        ("5. Why did operating cash flow fall in Year 2 despite net income growing 30%?",
         "C. Because receivables jumped sharply, tying up uncollected cash",
         "Receivables jumped from $4.0M to $38.0M - more sales booked but proportionally less cash collected."),
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
    path = "static/downloads/cash-flow-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Cash Flow — Practice Worksheet · Intermediate"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Cash Flow", "INTERMEDIATE PRACTICE WORKSHEET")
    y = draw_body(c, y, "Pull up a real company's cash flow statement (any investor relations site or "
                         "free financial data site works) for a company you're curious about. There's no "
                         "wrong answer, the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Find the Three Sections", TEAL)
    y = draw_body(c, y, "Which company, and what period? Write down cash flow from operating, investing, "
                         "and financing activities.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Calculate Free Cash Flow", GREEN)
    y = draw_body(c, y, "Using operating cash flow and the capital expenditure line (usually within "
                         "investing activities), calculate free cash flow.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Compare Cash to Profit", GOLD)
    y = draw_body(c, y, "Compare operating cash flow to net income for the same period. Are they close, "
                         "or is there a meaningful gap? If there's a gap, can you find why in the notes?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Read What Financing Activities Fund", PURPLE)
    y = draw_body(c, y, "Is financing cash flow positive or negative? Is the company raising debt, "
                         "repaying it, paying dividends, or buying back stock?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "Based only on the cash flow statement, does this company's profit look backed "
                         "up by real cash? What would you still want to check before deciding?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/cash-flow-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Cash Flow — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Cash Flow", "INTERMEDIATE FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on cash flow statements? These are free, reputable, and worth "
                         "bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Cash Flow Statement",
         "https://www.investopedia.com/investing/what-is-a-cash-flow-statement/",
         "A detailed walkthrough of all three sections of a standard cash flow statement."),
        ("Investopedia - Free Cash Flow (FCF)",
         "https://www.investopedia.com/terms/f/freecashflow.asp",
         "Covers the free cash flow formula used in this lesson and why it matters."),
        ("Investopedia - Quality of Earnings",
         "https://www.investopedia.com/terms/q/qualityofearnings.asp",
         "Explains the net-income-vs-cash-flow divergence check covered in this lesson."),
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
