"""Generate the 3 downloadable PDFs for the Pro 'The Greeks' lesson
(second lesson in the Options & Derivatives track).
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


def draw_greeks_table(c, y):
    rows = [
        ("Delta", "+0.55", "Gains ~$0.55 per $1 the stock rises"),
        ("Gamma", "0.04", "Delta itself rises ~0.04 per $1 stock move"),
        ("Theta", "-0.08", "Loses ~$0.08 of value per day, all else equal"),
        ("Vega", "+0.12", "Gains ~$0.12 if implied volatility rises 1 point"),
    ]
    col_x = [LEFT + 6, LEFT + 110, LEFT + 200]
    labels = ["Greek", "Value", "What It's Saying"]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(TEAL)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(DARK)
    for x, lab in zip(col_x, labels):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (name, val, what) in enumerate(rows):
        if name == "Theta":
            c.setFillColor(Color(0.85, 0.98, 0.96))
        elif i % 2 == 1:
            c.setFillColor(Color(0.95, 0.95, 0.97))
        else:
            c.setFillColor(Color(1, 1, 1))
        c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        c.setFont("Helvetica-Bold" if name == "Theta" else "Helvetica", 8)
        c.setFillColor(DARK)
        for x, v in zip(col_x, [name, val, what]):
            c.drawString(x, y - 9, v)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/the-greeks-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "The Greeks — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "The Greeks", "Delta, Gamma, Theta & Vega Explained — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", TEAL)
    y = draw_body(c, y, "Before expiration, an option's premium moves constantly, not just because of "
                         "the stock price. The Greeks each isolate how sensitive an option's price is to "
                         "one specific factor at a time.")
    y -= PARA_GAP
    y = draw_body(c, y, "Delta: change per $1 move in the stock. Gamma: how much delta itself changes "
                         "('the delta of delta'). Theta: value lost purely from one day passing. Vega: "
                         "sensitivity to shifts in implied volatility.")
    y -= PARA_GAP
    y = draw_body(c, y, "Together they answer: if the stock moves, if time passes, or if volatility "
                         "expectations shift, what happens to this position? Watching only the stock "
                         "price ignores at least three of the four forces at work.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: Reading a Position's Greeks", PURPLE)
    y = draw_greeks_table(c, y)
    y = draw_body(c, y, "Every day this option is held, theta quietly erodes ~$0.08 of value even with "
                         "no stock move - a cost only a directional move, an accelerating move, or a "
                         "rise in volatility expectations can offset.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About the Greeks", GOLD)
    facts = [
        "Delta also approximates probability of expiring in the money, as a rough rule of thumb.",
        "Gamma is highest near the strike, close to expiration - delta can shift fastest here.",
        "Theta accelerates as expiration nears - decay isn't linear, it speeds up in the final weeks.",
        "Vega matters most for longer-dated options - more time means more sensitivity to volatility.",
        "The Greeks interact, not operate in isolation - real P&L reflects all four moving together.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check Before Holding an Options Position", GREEN)
    tips = [
        "Check your delta exposure - know roughly how much your position moves per $1 in the underlying.",
        "Respect theta as a buyer - a long option bleeds value every day, even if the stock stays flat.",
        "Watch vega around known events - implied volatility often drops sharply after earnings.",
        "Mind gamma near expiration - directional exposure can change quickly in the final days.",
    ]
    for t in tips:
        y = draw_body(c, y, "• " + t)
        y -= 8
    y -= SECTION_GAP - 16

    c.setFillColor(Color(0.98, 0.94, 0.86))
    box_h = 66
    c.rect(LEFT, y - box_h, CONTENT_W, box_h, fill=1, stroke=0)
    c.setStrokeColor(GOLD)
    c.setLineWidth(3)
    c.line(LEFT, y, LEFT, y - box_h)
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(DARK)
    c.drawString(LEFT + 12, y - 16, "Worth knowing:")
    c.setFont("Helvetica", 8.5)
    for i, line in enumerate(wrap(
        "this explains the Greeks using illustrative numbers - it isn't personalized financial advice, "
        "and no position or value here is a recommendation. The Greeks are theoretical sensitivities "
        "from a pricing model, not guarantees of how an option will actually behave.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", TEAL, size=12)
    y -= 10

    questions = [
        ("1. What does Delta measure?", [
            "A. How much value an option loses per day",
            "B. How much the option's price changes for a $1 move in the underlying stock",
            "C. The option's strike price",
            "D. How many days remain until expiration"]),
        ("2. What does Theta represent?", [
            "A. Sensitivity to the stock price",
            "B. Sensitivity to implied volatility",
            "C. Time decay - value lost purely from one day passing, all else equal",
            "D. The maximum possible loss on the position"]),
        ("3. In the illustrative example, what happened to the option's value every day it was held, even with no stock move?", [
            "A. It lost about $0.08 of value from theta decay",
            "B. It gained value automatically",
            "C. Its strike price changed",
            "D. Delta dropped to zero"]),
        ("4. According to this lesson, when is Gamma typically highest?", [
            "A. Only on options with no expiration date",
            "B. When the stock price is far from the strike",
            "C. Immediately after the option is purchased, regardless of other factors",
            "D. Near the strike price, close to expiration"]),
        ("5. What does Vega measure?", [
            "A. The option's delta squared",
            "B. The number of shares per contract",
            "C. Sensitivity to changes in implied volatility",
            "D. The commission cost of the trade"]),
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
        ("1. What does Delta measure?",
         "B. How much the option's price changes for a $1 move in the underlying stock",
         "Delta measures how much the option's price is expected to change for a $1 move in the underlying."),
        ("2. What does Theta represent?",
         "C. Time decay - value lost purely from one day passing, all else equal",
         "Theta measures how much value an option loses purely from the passage of time."),
        ("3. In the illustrative example, what happened to the option's value every day it was held, even with no stock move?",
         "A. It lost about $0.08 of value from theta decay",
         "Theta of -0.08 means the option loses about $0.08 of value each day purely from time passing."),
        ("4. According to this lesson, when is Gamma typically highest?",
         "D. Near the strike price, close to expiration",
         "Gamma tends to be highest near the strike price as expiration approaches."),
        ("5. What does Vega measure?",
         "C. Sensitivity to changes in implied volatility",
         "Vega measures how much an option's price changes if volatility expectations shift, stock price unchanged."),
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
    path = "static/downloads/the-greeks-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "The Greeks — Practice Worksheet · Pro"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "The Greeks", "PRO PRACTICE WORKSHEET")
    y = draw_body(c, y, "Work through these by hand or with a spreadsheet. There's no wrong answer, "
                         "the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Estimate a Delta Impact", TEAL)
    y = draw_body(c, y, "An option has a delta of 0.40. If the stock rises $5, roughly how much would "
                         "you expect the option's value to change?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Estimate a Theta Impact", GREEN)
    y = draw_body(c, y, "An option has a theta of -0.12. If 4 days pass with no stock move, roughly "
                         "how much value would it lose to time decay alone?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Estimate a Vega Impact", GOLD)
    y = draw_body(c, y, "An option has a vega of 0.20. If implied volatility drops 3 points after "
                         "earnings, roughly how much value would it lose from vega alone?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Combine the Greeks", PURPLE)
    y = draw_body(c, y, "Using the Sections 1-3 numbers together (delta, theta, and vega impacts), "
                         "estimate the option's total value change.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "In your own words, explain why a trader holding a long option into a company's "
                         "earnings announcement should think carefully about vega, not just delta.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/the-greeks-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "The Greeks — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "The Greeks", "PRO FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on the option Greeks? These are free, reputable, and worth "
                         "bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - The Greeks",
         "https://www.investopedia.com/trading/getting-to-know-the-greeks/",
         "A comprehensive tutorial covering Delta, Gamma, Theta, Vega, and Rho."),
        ("Investopedia - Delta",
         "https://www.investopedia.com/terms/d/delta.asp",
         "A detailed walkthrough of delta specifically."),
        ("Investopedia - Theta",
         "https://www.investopedia.com/terms/t/theta.asp",
         "A detailed walkthrough of theta and time decay specifically."),
        ("Investopedia - Vega",
         "https://www.investopedia.com/terms/v/vega.asp",
         "A detailed walkthrough of vega and volatility sensitivity specifically."),
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
    box_h = 56
    c.rect(LEFT, y - box_h, CONTENT_W, box_h, fill=1, stroke=0)
    c.setStrokeColor(GOLD)
    c.setLineWidth(3)
    c.line(LEFT, y, LEFT, y - box_h)
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(DARK)
    c.drawString(LEFT + 12, y - 16, "Please note:")
    c.setFont("Helvetica", 8.5)
    for i, line in enumerate(wrap(
        "these are general educational resources, not personalized financial advice. Options trading "
        "carries substantial risk. Consult a licensed financial advisor before making investment "
        "decisions.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.save()
    print("done:", path)


if __name__ == "__main__":
    build_explainer()
    build_worksheet()
    build_further_reading()
