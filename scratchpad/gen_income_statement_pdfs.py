"""Generate the 3 downloadable PDFs for the Intermediate 'Reading the Income
Statement' lesson (first lesson in the Stock Picking track). Same
branding/spacing approach as the other Intermediate PDF generators.
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


def draw_income_table(c, y):
    rows = [
        ("Revenue", "$400.0M", "$460.0M", "+15.0%", False),
        ("Cost of Goods Sold", "$240.0M", "$262.2M", "+9.3%", False),
        ("Gross Profit", "$160.0M", "$197.8M", "+23.6%", True),
        ("Gross Margin", "40.0%", "43.0%", "+3.0 pts", False),
        ("Operating Expenses", "$104.0M", "$124.2M", "+19.4%", False),
        ("Operating Income", "$56.0M", "$73.6M", "+31.4%", True),
        ("Operating Margin", "14.0%", "16.0%", "+2.0 pts", False),
        ("One-Off Gain (asset sale)", "$0.0M", "$18.0M", "new", False),
        ("Interest & Tax", "$16.8M", "$22.1M", "+31.5%", False),
        ("Net Income", "$39.2M", "$69.5M", "+77.3%", True),
        ("Net Margin", "9.8%", "15.1%", "+5.3 pts", False),
    ]
    col_x = [LEFT + 6, LEFT + 220, LEFT + 300, LEFT + 380]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(PURPLE)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(Color(1, 1, 1))
    labels = ["Line Item", "Year 1", "Year 2", "Change"]
    for x, lab in zip(col_x, labels):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (name, y1, y2, chg, bold) in enumerate(rows):
        if bold:
            c.setFillColor(Color(0.90, 0.85, 0.98))
            c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        elif i % 2 == 1:
            c.setFillColor(Color(0.95, 0.95, 0.97))
            c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 8)
        c.setFillColor(DARK)
        c.drawString(col_x[0], y - 9, name)
        c.drawString(col_x[1], y - 9, y1)
        c.drawString(col_x[2], y - 9, y2)
        c.drawString(col_x[3], y - 9, chg)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/income-statement-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Income Statement — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Reading the Income Statement", "Is It Actually Profitable? — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", PURPLE)
    y = draw_body(c, y, "The income statement walks from revenue down to net income. Gross profit "
                         "(revenue minus cost of goods sold) shows how much the core product makes. "
                         "Operating income (gross profit minus running costs) shows overall profitability. "
                         "Net income (operating income minus interest and tax) is the true bottom line.")
    y -= PARA_GAP
    y = draw_body(c, y, "Turning each into a margin (dividing by revenue) lets you compare companies of "
                         "different sizes fairly. Don't stop at the headline net income - check whether "
                         "profit is growing from the core business or propped up by a one-off item that "
                         "won't repeat.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: Two Years, One Real Improvement", TEAL)
    y = draw_body(c, y, "Real income statements don't come with round numbers, so here's a clean "
                         "illustrative example to see the mechanics clearly.")
    y -= 10
    y = draw_income_table(c, y)
    y -= 6
    y = draw_body(c, y, "Net income jumped 77.3% - but operating income (the core business) grew a more "
                         "modest 31.4%, while $18M came from a one-off asset sale. Strip that out and net "
                         "income growth is closer to 33% - still good, far less dramatic than the headline.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About the Income Statement", GOLD)
    facts = [
        "Revenue growth alone isn't the full picture - margins can shrink even as revenue grows.",
        "Margins matter more than the raw profit number - expanding margins mean rising efficiency.",
        "One-off items distort the headline - asset sales and settlements inflate net income temporarily.",
        "Operating income is often the most honest number - it sits above one-off items and interest/tax.",
        "Compare margins to history and peers - a good margin in one industry is mediocre in another.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check When Reading an Income Statement", GREEN)
    tips = [
        "Check multi-year trends - one good year means little on its own.",
        "Scan for one-off items in the filing notes.",
        "Compare margins to direct competitors in the same industry.",
        "Watch the expense lines - costs growing faster than revenue is an early warning sign.",
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
        "the income statement is one of three core financial statements - pair it with the balance "
        "sheet and cash flow statement for the full picture. A company can look profitable here while "
        "quietly running into trouble elsewhere.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", PURPLE, size=12)
    y -= 10

    questions = [
        ("1. What does gross profit measure?", [
            "A. Total cash in the bank",
            "B. Revenue after all expenses including tax",
            "C. Revenue minus the direct cost of making the product",
            "D. The company's stock price"]),
        ("2. Why can net income jump sharply without the core business improving much?", [
            "A. Net income can only change if revenue changes",
            "B. A one-off item like an asset sale can inflate net income for a single period",
            "C. Companies are required to grow net income every year",
            "D. It's always due to a stock split"]),
        ("3. Why is operating income often a more honest measure than net income?", [
            "A. It's always a bigger number",
            "B. It includes one-off gains, which net income excludes",
            "C. It's the same thing as revenue",
            "D. It sits above one-off items and interest/tax, unrelated to core performance"]),
        ("4. Why does a margin need context to be meaningful?", [
            "A. A given margin can be great in a low-margin industry and mediocre in a high-margin one",
            "B. Margins are always exactly 10% regardless of industry",
            "C. Margins only apply to technology companies",
            "D. Context never matters once you have the margin number"]),
        ("5. Why was the 77.3% net income growth in the example less impressive than it first appears?", [
            "A. Because revenue actually fell that year",
            "B. Because the company changed its accountant",
            "C. Because a large chunk came from a one-off asset sale that won't repeat",
            "D. Because net income growth is never a meaningful number"]),
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
        ("1. What does gross profit measure?",
         "C. Revenue minus the direct cost of making the product",
         "Gross profit is revenue minus cost of goods sold - it shows how much the core product makes."),
        ("2. Why can net income jump sharply without the core business improving much?",
         "B. A one-off item like an asset sale can inflate net income for a single period",
         "One-off gains can inflate the net income headline without reflecting the ongoing business."),
        ("3. Why is operating income often a more honest measure than net income?",
         "D. It sits above one-off items and interest/tax, unrelated to core performance",
         "Operating income reflects day-to-day performance before items that can swing for unrelated reasons."),
        ("4. Why does a margin need context to be meaningful?",
         "A. A given margin can be great in a low-margin industry and mediocre in a high-margin one",
         "A 10% margin is strong in groceries but mediocre in software - always compare against peers."),
        ("5. Why was the 77.3% net income growth in the example less impressive than it first appears?",
         "C. Because a large chunk came from a one-off asset sale that won't repeat",
         "Stripping out the $18M one-off gain, underlying growth was closer to 33% - still healthy, less dramatic."),
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
    path = "static/downloads/income-statement-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Income Statement — Practice Worksheet · Intermediate"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Reading the Income Statement", "INTERMEDIATE PRACTICE WORKSHEET")
    y = draw_body(c, y, "Pull up a real company's income statement (any investor relations site or free "
                         "financial data site works) for a company you're curious about. There's no wrong "
                         "answer, the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Calculate the Margins", TEAL)
    y = draw_body(c, y, "Which company, and what period? Write down revenue, gross profit, operating "
                         "income, and net income, then calculate gross/operating/net margin.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Check the Multi-Year Trend", GREEN)
    y = draw_body(c, y, "Compare this period's margins to the prior year (or prior quarter). Are they "
                         "expanding, holding steady, or shrinking?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Hunt for One-Off Items", GOLD)
    y = draw_body(c, y, "Check the filing notes for any one-off gains or losses (asset sales, "
                         "settlements, tax items). Do any of them materially affect net income?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Compare to a Peer", PURPLE)
    y = draw_body(c, y, "Find one direct competitor and compare its margins to the company you researched. "
                         "Which one looks more efficient, and why might that be?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "Based only on the income statement, would you call this a healthy, growing "
                         "business? What would you still want to check on the balance sheet or cash flow "
                         "statement before deciding?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/income-statement-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Income Statement — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Reading the Income Statement", "INTERMEDIATE FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on reading financial statements? These are free, reputable, "
                         "and worth bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Income Statement",
         "https://www.investopedia.com/terms/i/incomestatement.asp",
         "A detailed walkthrough of every line item on a standard income statement."),
        ("Investopedia - Gross, Operating, and Net Profit Margin",
         "https://www.investopedia.com/ask/answers/031815/what-difference-between-gross-profit-and-net-profit-margin.asp",
         "Covers the three margin types used in this lesson and how to interpret each."),
        ("SEC - How to Read a 10-K",
         "https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/how-read-8",
         "The SEC's own guide to reading the annual report (10-K) where income statements are published."),
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
