"""Generate the 3 downloadable PDFs for the Intermediate 'Time Horizon & Risk
Tolerance' lesson (fifth and final lesson in the Balancing a Portfolio track).
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


def draw_horizon_table(c, y):
    rows = [
        ("Age 25, 40 Years to Retirement", "Long", "90%", "8%", "2%", False),
        ("Age 45, 20 Years to Retirement", "Medium", "70%", "25%", "5%", False),
        ("Age 63, 2 Years to Retirement", "Short", "40%", "50%", "10%", True),
    ]
    col_x = [LEFT + 6, LEFT + 215, LEFT + 285, LEFT + 345, LEFT + 405]
    labels = ["Investor", "Horizon", "Stocks", "Bonds", "Cash"]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(PURPLE)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(Color(1, 1, 1))
    for x, lab in zip(col_x, labels):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (name, horizon, stocks, bonds, cash, bold) in enumerate(rows):
        if bold:
            c.setFillColor(Color(0.90, 0.85, 0.98))
        elif i % 2 == 1:
            c.setFillColor(Color(0.95, 0.95, 0.97))
        else:
            c.setFillColor(Color(1, 1, 1))
        c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 8)
        c.setFillColor(DARK)
        for x, val in zip(col_x, [name, horizon, stocks, bonds, cash]):
            c.drawString(x, y - 9, val)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/time-horizon-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Time Horizon & Risk Tolerance — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Time Horizon & Risk Tolerance", "Matching the Plan to You — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", PURPLE)
    y = draw_body(c, y, "Time horizon is how long until you need the money. A 25-year-old investing "
                         "for retirement 40 years away can ride out a downturn - there's time for "
                         "markets to recover. A 60-year-old retiring next year doesn't have that luxury.")
    y -= PARA_GAP
    y = draw_body(c, y, "Risk tolerance is a different question: how much volatility can you handle "
                         "emotionally and financially without abandoning the plan? Even a young investor "
                         "with decades to go can have low risk tolerance.")
    y -= PARA_GAP
    y = draw_body(c, y, "The two interact: a long time horizon generally supports taking more risk, but "
                         "risk tolerance is the ceiling on how much of that capacity you should actually "
                         "use. The right allocation sits at the overlap of both.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: Same Goal, Different Stages, Different Mixes", TEAL)
    y = draw_horizon_table(c, y)
    y = draw_body(c, y, "As the time horizon shortens, the mix shifts steadily away from stocks toward "
                         "bonds and cash - because there's less time to recover from a bad stretch before "
                         "the money is actually needed.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know", GOLD)
    facts = [
        "Time horizon and risk tolerance are two separate questions - timeline versus temperament.",
        "A longer horizon generally supports more risk, since there's more time to recover.",
        "Risk tolerance is the ceiling, not the goal - exceeding it usually leads to panic-selling.",
        "Horizon shortens as goals approach - the mix commonly shifts toward bonds and cash over time.",
        "The 'right' allocation is personal - it depends on your timeline, income, and real behavior under stress.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check When Setting Your Mix", GREEN)
    tips = [
        "Know your actual timeline - be specific about when you'll need the money.",
        "Be honest about your temperament - think about how you reacted to past downturns.",
        "Stress-test the downside - picture a 30-40% drop and size your risk to the honest answer.",
        "Revisit as your horizon shortens - shift the mix gradually as a goal approaches.",
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
        "this explains the reasoning behind matching a portfolio to time horizon and risk tolerance "
        "using illustrative allocations - it isn't personalized financial advice. Speak to a licensed "
        "advisor about what's appropriate for your situation.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", PURPLE, size=12)
    y -= 10

    questions = [
        ("1. What is \"time horizon\" in this context?", [
            "A. How long you've been investing so far",
            "B. How long until you actually need the money",
            "C. How many hours a day you spend researching stocks",
            "D. The length of a typical market cycle"]),
        ("2. Why might a 25-year-old with 40 years to retirement still have low risk tolerance?", [
            "A. Because young investors are legally required to hold less risk",
            "B. Because a long time horizon always means low risk tolerance",
            "C. Because risk tolerance is about temperament, not just how much time is available",
            "D. Because 25-year-olds have no income"]),
        ("3. In the illustrative example, why did the mix shift toward bonds and cash as retirement approached?", [
            "A. Less time remained to recover from a downturn before the money would be needed",
            "B. Bonds always outperform stocks over any period",
            "C. Stocks become illegal to hold after a certain age",
            "D. Cash provides the highest long-term returns"]),
        ("4. Why is risk tolerance described as \"the ceiling, not the goal\"?", [
            "A. Because higher risk tolerance always produces higher returns",
            "B. Because risk tolerance doesn't actually matter to portfolio construction",
            "C. Because it's set by regulators, not the individual",
            "D. Because taking on more volatility than you can stomach usually leads to panic-selling"]),
        ("5. What determines the \"right\" allocation according to this lesson?", [
            "A. A single formula that applies to everyone the same way",
            "B. Whatever allocation had the best return last year",
            "C. The overlap between how much risk you can afford to take and how much you can live with",
            "D. Your age alone, with no other factors considered"]),
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
        ("1. What is \"time horizon\" in this context?",
         "B. How long until you actually need the money",
         "Time horizon is simply how long until the money is needed - a longer horizon means more time to recover from a downturn."),
        ("2. Why might a 25-year-old with 40 years to retirement still have low risk tolerance?",
         "C. Because risk tolerance is about temperament, not just how much time is available",
         "Risk tolerance is a separate question from time horizon - it's about what you can emotionally handle, regardless of timeline."),
        ("3. In the illustrative example, why did the mix shift toward bonds and cash as retirement approached?",
         "A. Less time remained to recover from a downturn before the money would be needed",
         "As a goal gets closer, there's less time to recover from a bad stretch, so the mix commonly shifts toward capital preservation."),
        ("4. Why is risk tolerance described as \"the ceiling, not the goal\"?",
         "D. Because taking on more volatility than you can stomach usually leads to panic-selling",
         "Exceeding your real risk tolerance tends to end in selling low during a downturn, locking in losses a calmer investor would have recovered from."),
        ("5. What determines the \"right\" allocation according to this lesson?",
         "C. The overlap between how much risk you can afford to take and how much you can live with",
         "The right mix sits where your financial capacity for risk and your emotional capacity for risk overlap."),
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
    path = "static/downloads/time-horizon-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Time Horizon & Risk Tolerance — Practice Worksheet · Intermediate"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Time Horizon & Risk Tolerance", "INTERMEDIATE PRACTICE WORKSHEET")
    y = draw_body(c, y, "Think about your own goals and honest reactions to past downturns. There's no "
                         "wrong answer, the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Map Your Time Horizon", TEAL)
    y = draw_body(c, y, "List your main financial goals and roughly how many years until each one needs "
                         "money (e.g. house deposit in 5 years, retirement in 30).")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Assess Your Risk Tolerance Honestly", GREEN)
    y = draw_body(c, y, "Think of a real market downturn you lived through (or ask someone who did). "
                         "How did you (or would you have) actually react?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Stress-Test the Downside", GOLD)
    y = draw_body(c, y, "Picture your portfolio dropping 30-40% in a single year. Would you hold on, "
                         "sell some, or sell everything? Be honest, not aspirational.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Find the Overlap", PURPLE)
    y = draw_body(c, y, "Given your time horizon (Section 1) and your honest risk tolerance (Sections "
                         "2-3), does your current portfolio actually match? What might need to change?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Plan for the Shift", TEAL)
    y = draw_body(c, y, "As your nearest goal gets closer, how do you plan to gradually shift your mix "
                         "toward capital preservation? What would trigger the first move?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/time-horizon-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Time Horizon & Risk Tolerance — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Time Horizon & Risk Tolerance", "INTERMEDIATE FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on matching a portfolio to your timeline and temperament? "
                         "These are free, reputable, and worth bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Time Horizon",
         "https://www.investopedia.com/terms/t/timehorizon.asp",
         "A detailed walkthrough of time horizon and how it shapes portfolio construction."),
        ("Investopedia - Risk Tolerance",
         "https://www.investopedia.com/terms/r/risktolerance.asp",
         "Covers risk tolerance and how it differs from risk capacity, referenced in this lesson."),
        ("Investor.gov - Beginners' Guide to Asset Allocation",
         "https://www.investor.gov/introduction-investing/investing-basics/save-and-invest/asset-allocation",
         "The SEC's own plain-English guide to asset allocation, closely related to this lesson."),
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
