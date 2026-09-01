"""Generate the 3 downloadable PDFs for the Intermediate 'The Balance Sheet'
lesson (second lesson in the Stock Picking track).
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


def draw_balance_boxes(c, y):
    box_w = (CONTENT_W - 20) / 2
    box_h = 120
    x1 = LEFT
    x2 = LEFT + box_w + 20

    def draw_box(x, title, rows, total):
        c.setStrokeColor(GRAY)
        c.setLineWidth(0.8)
        c.roundRect(x, y - box_h, box_w, box_h, 6, stroke=1, fill=0)
        c.setFont("Helvetica-Bold", 9.5)
        c.setFillColor(PURPLE)
        c.drawString(x + 10, y - 18, title)
        ry = y - 36
        c.setFont("Helvetica", 8.5)
        for label, val in rows:
            c.setFillColor(GRAY)
            c.drawString(x + 10, ry, label)
            c.setFillColor(DARK)
            c.drawRightString(x + box_w - 10, ry, val)
            ry -= 16
        c.setStrokeColor(GRAY)
        c.setLineWidth(0.8)
        c.line(x + 10, ry + 6, x + box_w - 10, ry + 6)
        ry -= 10
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(DARK)
        c.drawString(x + 10, ry, total[0])
        c.drawRightString(x + box_w - 10, ry, total[1])

    draw_box(x1, "Assets", [
        ("Cash & equivalents", "$40M"),
        ("Inventory & receivables", "$60M"),
        ("Property & equipment", "$150M"),
    ], ("Total Assets", "$250M"))
    draw_box(x2, "Liabilities + Equity", [
        ("Short-term debt & payables", "$45M"),
        ("Long-term debt", "$80M"),
        ("Shareholder equity", "$125M"),
    ], ("Total Liab. + Equity", "$250M"))
    return y - box_h - 14


def build_explainer():
    path = "static/downloads/balance-sheet-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Balance Sheet — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "The Balance Sheet", "How Much Debt Is Too Much? — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", PURPLE)
    y = draw_body(c, y, "The balance sheet is built on one identity: Assets = Liabilities + Equity. "
                         "Assets are everything owned; liabilities are everything owed; equity is what's "
                         "left for shareholders.")
    y -= PARA_GAP
    y = draw_body(c, y, "Current ratio (current assets / current liabilities) measures short-term "
                         "liquidity. Debt-to-equity (total debt / shareholder equity) measures leverage. "
                         "Neither has one 'correct' number - capital-intensive industries naturally carry "
                         "more debt than asset-light ones. The goal is spotting outliers.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "The Balance Sheet Equation, Illustrated", TEAL)
    y = draw_balance_boxes(c, y)
    y = draw_body(c, y, "Both sides match: $250M of assets is funded by $125M of debt and $125M of "
                         "equity. Debt-to-equity = $125M / $125M = 1.0 - a reasonably balanced position, "
                         "though the 'right' number depends heavily on the industry.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About the Balance Sheet", GOLD)
    facts = [
        "Assets always equal liabilities plus equity - if not, the accounting is wrong.",
        "Current ratio below 1 is a liquidity warning - current liabilities exceed current assets.",
        "Debt-to-equity has no universal 'good' number - it varies a lot by industry.",
        "Rising debt isn't automatically bad - growth-funding debt differs from loss-covering debt.",
        "The balance sheet is a snapshot, not a trend - compare several periods, not just one.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check When Reading a Balance Sheet", GREEN)
    tips = [
        "Check the current ratio - below 1 is a flag worth investigating further.",
        "Check debt-to-equity vs peers, not a generic benchmark.",
        "Track the trend over time - is debt rising faster than equity or assets?",
        "Ask why debt exists - check the cash flow statement for the answer.",
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
        "the balance sheet is a snapshot at one moment, not the full story. Pair it with the income "
        "statement and cash flow statement - a company can look fine here while its underlying trend "
        "is deteriorating.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", PURPLE, size=12)
    y -= 10

    questions = [
        ("1. What is the fundamental balance sheet equation?", [
            "A. Revenue = Expenses + Profit",
            "B. Cash = Assets - Liabilities",
            "C. Assets = Liabilities + Equity",
            "D. Equity = Revenue - Debt"]),
        ("2. What does a current ratio below 1.0 suggest?", [
            "A. The company has no debt at all",
            "B. Current liabilities exceed current assets - a potential liquidity warning",
            "C. The company is definitely about to go bankrupt",
            "D. The stock is undervalued"]),
        ("3. Why doesn't debt-to-equity have one universal 'good' number?", [
            "A. Because debt is always bad regardless of context",
            "B. Because equity never matters",
            "C. Because the ratio is calculated differently every year",
            "D. Because capital-intensive industries naturally carry more debt"]),
        ("4. Why isn't rising debt automatically a bad sign?", [
            "A. Growth-funding debt differs from debt covering ongoing losses",
            "B. Debt is always good no matter the reason",
            "C. Rising debt always means the stock will go up",
            "D. Debt has no effect on a company's risk"]),
        ("5. With $125M debt and $125M equity, what is the debt-to-equity ratio?", [
            "A. 0.5", "B. 2.0", "C. 1.0", "D. 125"]),
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
        ("1. What is the fundamental balance sheet equation?",
         "C. Assets = Liabilities + Equity",
         "Everything a company owns equals what it owes plus what belongs to shareholders."),
        ("2. What does a current ratio below 1.0 suggest?",
         "B. Current liabilities exceed current assets - a potential liquidity warning",
         "Worth investigating further, though not an automatic crisis."),
        ("3. Why doesn't debt-to-equity have one universal 'good' number?",
         "D. Because capital-intensive industries naturally carry more debt",
         "A utility or airline naturally runs higher debt-to-equity than an asset-light software company."),
        ("4. Why isn't rising debt automatically a bad sign?",
         "A. Growth-funding debt differs from debt covering ongoing losses",
         "The reason behind rising debt matters - expansion vs plugging losses are very different signals."),
        ("5. With $125M debt and $125M equity, what is the debt-to-equity ratio?",
         "C. 1.0",
         "Debt-to-equity = $125M / $125M = 1.0 - debt and equity fund the business equally."),
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
    path = "static/downloads/balance-sheet-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Balance Sheet — Practice Worksheet · Intermediate"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "The Balance Sheet", "INTERMEDIATE PRACTICE WORKSHEET")
    y = draw_body(c, y, "Pull up a real company's balance sheet (any investor relations site or free "
                         "financial data site works) for a company you're curious about. There's no "
                         "wrong answer, the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Calculate the Ratios", TEAL)
    y = draw_body(c, y, "Which company, and what period? Write down current assets, current liabilities, "
                         "total debt, and shareholder equity, then calculate the current ratio and "
                         "debt-to-equity ratio.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Compare to a Peer", GREEN)
    y = draw_body(c, y, "Find one direct competitor and compare its ratios to the company you researched. "
                         "Which one looks more conservatively financed, and why might that be?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Check the Trend", GOLD)
    y = draw_body(c, y, "Compare this period's ratios to 2-3 years ago. Is debt rising or falling "
                         "relative to equity? Is liquidity improving or deteriorating?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Ask Why", PURPLE)
    y = draw_body(c, y, "If debt has risen, check the cash flow statement or filing notes for why - was "
                         "it used to fund growth (expansion, acquisitions) or cover ongoing losses?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "Based only on the balance sheet, would you call this company financially "
                         "conservative or aggressive? What would you still want to check before deciding?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/balance-sheet-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Balance Sheet — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "The Balance Sheet", "INTERMEDIATE FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on balance sheets? These are free, reputable, and worth "
                         "bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Balance Sheet",
         "https://www.investopedia.com/terms/b/balancesheet.asp",
         "A detailed walkthrough of every section of a standard balance sheet."),
        ("Investopedia - Current Ratio",
         "https://www.investopedia.com/terms/c/currentratio.asp",
         "Covers the liquidity ratio used in this lesson and how to interpret it."),
        ("Investopedia - Debt-to-Equity Ratio",
         "https://www.investopedia.com/terms/d/debtequityratio.asp",
         "Covers the leverage ratio used in this lesson, including industry benchmarks."),
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
