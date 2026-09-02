"""Generate the 3 downloadable PDFs for the Pro 'Momentum & Factor Models'
lesson (second lesson in the Quantitative Strategy Design track).
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


def draw_momentum_table(c, y):
    rows = [
        ("Stock A", "+42%", "1", "Hold (Top Momentum)", True),
        ("Stock B", "+31%", "2", "Hold (Top Momentum)", True),
        ("Stock C", "+8%", "3", "No Position", False),
        ("Stock D", "-6%", "4", "No Position", False),
        ("Stock E", "-19%", "5", "No Position (Bottom)", False),
    ]
    col_x = [LEFT + 6, LEFT + 150, LEFT + 260, LEFT + 340]
    labels = ["Stock", "6-Month Return", "Rank", "Illustrative Action"]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(TEAL)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(DARK)
    for x, lab in zip(col_x, labels):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (name, ret, rank, action, bold) in enumerate(rows):
        if bold:
            c.setFillColor(Color(0.85, 0.98, 0.96))
        elif i % 2 == 1:
            c.setFillColor(Color(0.95, 0.95, 0.97))
        else:
            c.setFillColor(Color(1, 1, 1))
        c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 8)
        c.setFillColor(DARK)
        for x, val in zip(col_x, [name, ret, rank, action]):
            c.drawString(x, y - 9, val)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/momentum-factors-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Momentum & Factor Models — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Momentum & Factor Models", "Lesson Explainer")

    y = draw_heading(c, y, "The Concept", TEAL)
    y = draw_body(c, y, "Momentum is the observed tendency for assets that have recently performed "
                         "well to keep outperforming, and for recent laggards to keep lagging - the "
                         "mirror image of mean reversion. It's one of the most studied patterns in "
                         "academic finance, though not guaranteed and prone to sharp reversals.")
    y -= PARA_GAP
    y = draw_body(c, y, "A factor is a specific, measurable characteristic historically associated "
                         "with different returns across securities. Momentum is one factor; others "
                         "include value, quality, and size.")
    y -= PARA_GAP
    y = draw_body(c, y, "A factor model builds a portfolio systematically around one or more of these "
                         "characteristics - ranking a universe and holding the top slice - rather than "
                         "relying on any single stock-specific thesis.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: Ranking a Universe by 6-Month Momentum", PURPLE)
    y = draw_body(c, y, "A simple momentum factor ranks stocks by trailing 6-month return and holds "
                         "the top slice.")
    y = draw_momentum_table(c, y)
    y = draw_body(c, y, "Stocks A and B are held not because of any specific business view, but "
                         "purely because their trailing return ranks them at the top - the same rule "
                         "applied systematically across a whole universe.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About Momentum & Factors", GOLD)
    facts = [
        "Momentum and mean reversion aren't contradictions - they operate over different timeframes.",
        "Momentum crashes are a known, documented risk, especially around market turning points.",
        "Factors can underperform for long periods - value lagged growth for much of the 2010s.",
        "Factor investing is diversification across bets, not stocks - hold many names, not a few.",
        "Factors can crowd - many funds chasing the same definitions can itself become a risk.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check Before Trusting a Factor Strategy", GREEN)
    tips = [
        "Define the lookback precisely - 3, 6, or 12-month momentum ranks names very differently.",
        "Set a rebalancing rule - decide how often to re-rank and how much turnover that implies.",
        "Diversify across names - the edge comes from many small bets, not a concentrated handful.",
        "Plan for drawdowns in the factor itself - expect extended underperformance stretches.",
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
        "this explains the historical, academic evidence behind momentum and factor investing using "
        "illustrative numbers - it isn't personalized financial advice, and no strategy here is a "
        "recommendation to trade. Past patterns are never guaranteed to repeat.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", TEAL, size=12)
    y -= 10

    questions = [
        ("1. What does a momentum strategy bet on?", [
            "A. That a stretched price will snap back to its average",
            "B. That assets which have recently performed well will keep outperforming",
            "C. That all stocks will converge to the same return",
            "D. That interest rates determine all stock returns"]),
        ("2. What is a \"factor\" in this context?", [
            "A. A company's stock ticker symbol",
            "B. A type of brokerage account",
            "C. A specific, measurable characteristic historically associated with different returns",
            "D. A government regulation on trading"]),
        ("3. In the illustrative example, why were Stocks A and B held?", [
            "A. Their trailing 6-month return ranked them at the top of the universe",
            "B. They had the lowest P/E ratios in the universe",
            "C. They paid the highest dividends",
            "D. They were the largest companies by market cap"]),
        ("4. What is a documented risk specific to momentum strategies?", [
            "A. They require no rebalancing at all",
            "B. They can only be used on bonds",
            "C. They are immune to market downturns",
            "D. \"Momentum crashes\" - sharp, sudden reversals, particularly around market turning points"]),
        ("5. Why does the lesson recommend diversifying across many names in a factor strategy?", [
            "A. Because factors only work with exactly one stock",
            "B. Because diversification eliminates all risk entirely",
            "C. Because the statistical edge comes from holding many names, not a few",
            "D. Because regulators require a minimum number of holdings"]),
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
        ("1. What does a momentum strategy bet on?",
         "B. That assets which have recently performed well will keep outperforming",
         "Momentum is the tendency for recent winners to keep outperforming - the mirror image of mean reversion."),
        ("2. What is a \"factor\" in this context?",
         "C. A specific, measurable characteristic historically associated with different returns",
         "Momentum, value, quality and size are all examples of factors."),
        ("3. In the illustrative example, why were Stocks A and B held?",
         "A. Their trailing 6-month return ranked them at the top of the universe",
         "A momentum factor strategy ranks purely on trailing return, regardless of any company-specific view."),
        ("4. What is a documented risk specific to momentum strategies?",
         "D. \"Momentum crashes\" - sharp, sudden reversals, particularly around market turning points",
         "Momentum strategies have historically suffered sharp, sudden reversals known as momentum crashes."),
        ("5. Why does the lesson recommend diversifying across many names in a factor strategy?",
         "C. Because the statistical edge comes from holding many names, not a few",
         "Factor investing works as diversification across many small, uncorrelated bets, not concentrated theses."),
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
    path = "static/downloads/momentum-factors-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Momentum & Factor Models — Practice Worksheet · Pro"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Momentum & Factor Models", "PRO PRACTICE WORKSHEET")
    y = draw_body(c, y, "Work through these by hand or with a spreadsheet. There's no wrong answer, "
                         "the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Rank a Hypothetical Universe", TEAL)
    y = draw_body(c, y, "List 6 hypothetical stocks with made-up 6-month returns. Rank them by "
                         "momentum and mark the top 2 as 'Hold'.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Choose a Lookback Window", GREEN)
    y = draw_body(c, y, "Would you rank by 3-month, 6-month, or 12-month trailing return? What's the "
                         "trade-off between a shorter and a longer window?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Plan a Rebalancing Rule", GOLD)
    y = draw_body(c, y, "How often would you re-rank and rebalance a momentum portfolio? What "
                         "turnover and trading costs might that imply?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Think About Crowding", PURPLE)
    y = draw_body(c, y, "If many funds all chase the same momentum definition, what could happen "
                         "during a sudden market reversal?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Compare to Mean Reversion", TEAL)
    y = draw_body(c, y, "In your own words, explain how momentum and mean reversion can both be true "
                         "at once, over different timeframes.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/momentum-factors-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Momentum & Factor Models — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Momentum & Factor Models", "PRO FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on momentum and factor investing? These are free, "
                         "reputable, and worth bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Momentum Investing",
         "https://www.investopedia.com/terms/m/momentum_investing.asp",
         "A detailed walkthrough of momentum investing and its academic evidence."),
        ("Investopedia - Factor Investing",
         "https://www.investopedia.com/terms/f/factor-investing.asp",
         "Covers the broader factor investing framework referenced in this lesson."),
        ("Investopedia - Fama-French Three-Factor Model",
         "https://www.investopedia.com/terms/f/famaandfrenchthreefactormodel.asp",
         "The foundational academic model behind much of modern factor investing."),
        ("Investopedia - Value Investing",
         "https://www.investopedia.com/terms/v/valueinvesting.asp",
         "Explains the value factor mentioned alongside momentum in this lesson."),
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
