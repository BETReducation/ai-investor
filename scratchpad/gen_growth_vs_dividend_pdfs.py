"""Generate the 3 downloadable PDFs for the Intermediate 'Growth vs Dividend
Stocks' lesson (fourth lesson in the Stock Picking track).
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


def draw_gd_table(c, y):
    rows = [
        ("Starting Share Price", "$100.00", "$100.00", False),
        ("Ending Share Price", "$122.00", "$106.00", False),
        ("Dividends Paid That Year", "$0.00", "$4.00", False),
        ("Price Return", "+22.0%", "+6.0%", False),
        ("Dividend Yield", "0.0%", "4.0%", False),
        ("Total Return", "+22.0%", "+10.0%", True),
        ("Payout Ratio", "0%", "60%", False),
    ]
    col_x = [LEFT + 6, LEFT + 260, LEFT + 380]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(PURPLE)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(Color(1, 1, 1))
    for x, lab in zip(col_x, ["Metric", "Growth Co", "Dividend Co"]):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (name, g, d, bold) in enumerate(rows):
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
        c.drawString(col_x[1], y - 9, g)
        c.drawString(col_x[2], y - 9, d)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/growth-vs-dividend-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Growth vs Dividend Stocks — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Growth vs Dividend Stocks", "Matching Companies to Your Goals — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", PURPLE)
    y = draw_body(c, y, "Once a company generates free cash flow, it can reinvest it (growth stocks - "
                         "little/no dividend, valued on future growth) or return it directly to "
                         "shareholders (dividend stocks - typically mature, stable businesses).")
    y -= PARA_GAP
    y = draw_body(c, y, "Dividend yield = annual dividend per share / share price. Payout ratio = "
                         "dividend per share / EPS - a low payout ratio means room to grow the dividend; "
                         "near or above 100% means it may not be sustainable.")
    y -= PARA_GAP
    y = draw_body(c, y, "Total return = price appreciation + dividends received. Comparing only price "
                         "performance between growth and dividend stocks misses half of a dividend "
                         "stock's actual return.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: Growth Co vs Dividend Co, One Year", TEAL)
    y = draw_gd_table(c, y)
    y = draw_body(c, y, "Growth Co delivered a higher total return this year - but that alone doesn't "
                         "settle which is 'better'. Dividend Co's return came with more stability and "
                         "cash along the way. Both are legitimate strategies depending on goals.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About Growth vs Dividend Stocks", GOLD)
    facts = [
        "Total return includes dividends, not just price - comparing only price understates dividend stocks.",
        "A payout ratio near or above 100% is a sustainability flag.",
        "Growth stocks are valued on the future, dividend stocks more on the present.",
        "Neither category is inherently safer - dividends can be cut, growth valuations can reset.",
        "This isn't strictly binary - many companies sit in between.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check Before Choosing Either Style", GREEN)
    tips = [
        "Know your own goal - income now vs growth later.",
        "Check the payout ratio - little cushion if it's near/above 100%.",
        "Look at total return, not just yield.",
        "Match to your time horizon - growth needs a longer runway.",
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
        "neither growth nor dividend investing is universally 'better' - they suit different goals and "
        "time horizons. Diversifying across both styles is common practice, not an admission of "
        "indecision.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", PURPLE, size=12)
    y -= 10

    questions = [
        ("1. What does total return include that a plain price chart misses?", [
            "A. Nothing, they're the same thing",
            "B. The company's revenue growth rate",
            "C. Dividends received along the way",
            "D. The company's employee headcount"]),
        ("2. What does a payout ratio near or above 100% suggest?", [
            "A. The company has no dividend at all",
            "B. The stock is definitely a good buy",
            "C. The company's revenue is growing rapidly",
            "D. The dividend may not be sustainable if earnings dip"]),
        ("3. Why are growth stocks generally more sensitive to changes in growth expectations?", [
            "A. They pay the highest dividends of any stock category",
            "B. They're valued mainly on future earnings, so price reacts sharply to outlook changes",
            "C. They never report earnings",
            "D. Growth stocks are immune to market swings"]),
        ("4. Why is neither growth nor dividend investing inherently 'safer'?", [
            "A. A 'safe' dividend can be cut, and a growth stock's valuation can reset - both carry risk",
            "B. Dividend stocks can never lose value",
            "C. Growth stocks are guaranteed to outperform over any period",
            "D. Risk only applies to growth stocks"]),
        ("5. Why doesn't Growth Co's higher total return automatically make it the 'better' pick?", [
            "A. Because Growth Co's numbers were fabricated",
            "B. Because Dividend Co technically returned more money",
            "C. Because which is 'better' depends on the investor's goals and time horizon",
            "D. Because total return doesn't apply to growth stocks"]),
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
        ("1. What does total return include that a plain price chart misses?",
         "C. Dividends received along the way",
         "Total return = price appreciation plus dividends - comparing only price understates dividend stocks."),
        ("2. What does a payout ratio near or above 100% suggest?",
         "D. The dividend may not be sustainable if earnings dip",
         "Most or all earnings are being paid out, leaving little cushion for a bad year."),
        ("3. Why are growth stocks generally more sensitive to changes in growth expectations?",
         "B. They're valued mainly on future earnings, so price reacts sharply to outlook changes",
         "Any shift in how investors see a growth stock's future tends to move the price more sharply."),
        ("4. Why is neither growth nor dividend investing inherently 'safer'?",
         "A. A 'safe' dividend can be cut, and a growth stock's valuation can reset - both carry risk",
         "Both styles carry real, different risks."),
        ("5. Why doesn't Growth Co's higher total return automatically make it the 'better' pick?",
         "C. Because which is 'better' depends on the investor's goals and time horizon",
         "One year's result doesn't settle which strategy fits an investor best."),
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
    path = "static/downloads/growth-vs-dividend-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Growth vs Dividend Stocks — Practice Worksheet · Intermediate"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Growth vs Dividend Stocks", "INTERMEDIATE PRACTICE WORKSHEET")
    y = draw_body(c, y, "Pick two real companies you're curious about - one you'd call a growth stock, "
                         "one you'd call a dividend stock. There's no wrong answer, the goal is just "
                         "practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Calculate Total Return", TEAL)
    y = draw_body(c, y, "For each company over the last year: starting price, ending price, dividends "
                         "paid. Calculate price return, dividend yield, and total return for both.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Calculate the Payout Ratio", GREEN)
    y = draw_body(c, y, "For the dividend-paying company, find its dividend per share and EPS. Calculate "
                         "the payout ratio - does it look sustainable?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Compare the Two", GOLD)
    y = draw_body(c, y, "Which company had the higher total return this year? Does that alone tell you "
                         "which is the 'better' investment? Why or why not?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Match to a Goal", PURPLE)
    y = draw_body(c, y, "If you needed steady income next year, which company would fit better? If you "
                         "had a 20-year time horizon and didn't need income now, which might fit better?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "What would make you trust a high dividend yield less, even if the payout ratio "
                         "looks fine today?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/growth-vs-dividend-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Growth vs Dividend Stocks — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Growth vs Dividend Stocks", "INTERMEDIATE FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on growth vs dividend investing? These are free, reputable, "
                         "and worth bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Growth Stock",
         "https://www.investopedia.com/terms/g/growthstock.asp",
         "Covers what defines a growth stock and how they're typically valued."),
        ("Investopedia - Dividend Stock",
         "https://www.investopedia.com/terms/d/dividend.asp",
         "Covers dividends, dividend yield, and payout ratio in more depth."),
        ("Investopedia - Total Return",
         "https://www.investopedia.com/terms/t/totalreturn.asp",
         "Explains the total return concept used in this lesson, including reinvested dividends."),
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
