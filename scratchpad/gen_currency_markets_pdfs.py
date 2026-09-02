"""Generate the 3 downloadable PDFs for the Pro 'Currency Markets & Capital
Flows' lesson (third lesson in the Macro & Cross-Asset Analysis track).
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


def draw_fx_table(c, y):
    rows = [
        ("Wide Gap Favoring A", "5.5%", "1.0%", "+4.5 pts", "Tends to Strengthen", False),
        ("Narrow Gap", "3.0%", "2.5%", "+0.5 pts", "Modest or Mixed", True),
        ("Gap Reverses", "2.0%", "4.5%", "-2.5 pts", "Tends to Weaken", False),
    ]
    col_x = [LEFT + 6, LEFT + 145, LEFT + 210, LEFT + 275, LEFT + 355]
    labels = ["Scenario", "Rate A", "Rate B", "Differential", "Currency A Direction"]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(TEAL)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(DARK)
    for x, lab in zip(col_x, labels):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (scenario, ra, rb, diff, direction, bold) in enumerate(rows):
        if bold:
            c.setFillColor(Color(0.85, 0.98, 0.96))
        elif i % 2 == 1:
            c.setFillColor(Color(0.95, 0.95, 0.97))
        else:
            c.setFillColor(Color(1, 1, 1))
        c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 8)
        c.setFillColor(DARK)
        for x, val in zip(col_x, [scenario, ra, rb, diff, direction]):
            c.drawString(x, y - 9, val)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/currency-markets-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Currency Markets & Capital Flows — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Currency Markets & Capital Flows", "Lesson Explainer")

    y = draw_heading(c, y, "The Concept", TEAL)
    y = draw_body(c, y, "A currency's exchange rate is a relative price that moves as global capital "
                         "flows toward whichever country offers the best risk-adjusted return. The "
                         "biggest single driver is the interest rate differential - capital flows "
                         "toward the higher-yielding currency to capture the difference.")
    y -= PARA_GAP
    y = draw_body(c, y, "A country's trade balance also matters. A trade surplus generates steady "
                         "foreign demand for the currency; a persistent deficit creates steady selling "
                         "pressure over time.")
    y -= PARA_GAP
    y = draw_body(c, y, "Currency moves reshape corporate earnings. A stronger home currency shrinks "
                         "reported overseas earnings on translation, and the reverse when it weakens - "
                         "why multinationals routinely flag currency effects in earnings reports.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: Interest Rate Differentials and Currency Direction", PURPLE)
    y = draw_fx_table(c, y)
    y = draw_body(c, y, "All else equal, a widening rate advantage for Country A has historically "
                         "tended to attract capital toward Country A's currency; a reversal tends to "
                         "reverse the flow - though real currency moves reflect many factors at once.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About Currency Markets", GOLD)
    facts = [
        "Interest rate differentials are a major driver, not the only one - trade and sentiment matter too.",
        "Currencies affect multinational earnings both ways - stronger home currency can hurt translation.",
        "'Risk-on/risk-off' sentiment moves currencies - safe havens are sought during market stress.",
        "Central bank divergence is a direct currency driver - one cutting while another hikes widens the gap.",
        "Currency markets are enormous and trade nearly 24 hours a day - among the most liquid markets.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check When Reading Currency Moves", GREEN)
    tips = [
        "Compare the two central banks - check both current rates and expected future paths.",
        "Check the trade balance trend - a persistent, widening deficit or surplus is a real driver.",
        "Consider risk sentiment - in a sell-off, safe-haven flows can override rate logic.",
        "Check a multinational's currency exposure - how much revenue comes from overseas.",
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
        "this explains currency market mechanics using illustrative numbers - it isn't personalized "
        "financial advice, and no direction or level here is a recommendation to trade. Currency "
        "markets are influenced by many simultaneous factors and are never fully predictable.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", TEAL, size=12)
    y -= 10

    questions = [
        ("1. What is the biggest single driver of currency direction described in this lesson?", [
            "A. The number of tourists visiting a country",
            "B. The country's stock market index level",
            "C. The interest rate differential between two countries",
            "D. The price of gold"]),
        ("2. What does a large, persistent trade surplus tend to do to a country's currency?", [
            "A. Nothing - trade balances have no effect on currencies",
            "B. Generate steady foreign demand for the currency, supporting its value",
            "C. Automatically cause hyperinflation",
            "D. Force the central bank to cut interest rates to zero"]),
        ("3. In the illustrative example, what happened as the interest rate differential favoring Country A widened?", [
            "A. Country A's currency was guaranteed to collapse",
            "B. The two countries' currencies became identical",
            "C. Nothing changed at all",
            "D. Country A's currency tended to strengthen, all else equal"]),
        ("4. Why does a stronger home currency tend to hurt a multinational's reported overseas earnings?", [
            "A. Foreign revenue translates into fewer home-currency units when the home currency strengthens",
            "B. A stronger currency always increases foreign sales volume",
            "C. Currency moves have no effect on reported earnings",
            "D. Overseas earnings are never reported in the home currency"]),
        ("5. What is \"risk-off\" safe-haven currency demand, according to this lesson?", [
            "A. A rule that currencies never move during a crisis",
            "B. A tax on foreign currency trading",
            "C. Demand for certain currencies during market stress, which can override interest rate logic",
            "D. A type of central bank interest rate"]),
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
        ("1. What is the biggest single driver of currency direction described in this lesson?",
         "C. The interest rate differential between two countries",
         "The interest rate differential is described as the single biggest driver of currency direction."),
        ("2. What does a large, persistent trade surplus tend to do to a country's currency?",
         "B. Generate steady foreign demand for the currency, supporting its value",
         "A trade surplus generates steady foreign demand for the currency to pay for exports."),
        ("3. In the illustrative example, what happened as the interest rate differential favoring Country A widened?",
         "D. Country A's currency tended to strengthen, all else equal",
         "A wider rate advantage has historically tended to attract capital toward that currency."),
        ("4. Why does a stronger home currency tend to hurt a multinational's reported overseas earnings?",
         "A. Foreign revenue translates into fewer home-currency units when the home currency strengthens",
         "When the home currency strengthens, foreign revenue converts back into fewer home-currency units."),
        ("5. What is \"risk-off\" safe-haven currency demand, according to this lesson?",
         "C. Demand for certain currencies during market stress, which can override interest rate logic",
         "Certain currencies are often sought as havens during market stress, overriding normal rate-driven flows."),
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
    path = "static/downloads/currency-markets-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Currency Markets & Capital Flows — Practice Worksheet · Pro"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Currency Markets & Capital Flows", "PRO PRACTICE WORKSHEET")
    y = draw_body(c, y, "Work through these by hand or with a spreadsheet. There's no wrong answer, "
                         "the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Trace a Rate Differential Change", TEAL)
    y = draw_body(c, y, "Country A's rate rises from 2% to 4.5% while Country B's stays at 2%. What "
                         "would you expect to happen to Country A's currency, all else equal? Why?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Calculate a Translation Impact", GREEN)
    y = draw_body(c, y, "A company reports $500M total revenue, 40% from overseas. Its home currency "
                         "strengthens 6%. Estimate the translation impact in dollars and as a percent "
                         "of total revenue.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Consider a Trade Balance Shift", GOLD)
    y = draw_body(c, y, "A country's trade surplus has been shrinking for three years straight. What "
                         "might this suggest for its currency over that period, all else equal?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Identify Safe-Haven Demand", PURPLE)
    y = draw_body(c, y, "During a sudden global market sell-off, a currency from a country with lower "
                         "interest rates strengthens anyway. What concept from this lesson explains that?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "In your own words, explain why a domestic-focused company is less exposed to "
                         "currency swings than a heavily multinational one.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/currency-markets-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Currency Markets & Capital Flows — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Currency Markets & Capital Flows", "PRO FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on currency markets? These are free, reputable, and worth "
                         "bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Forex (FX) Market",
         "https://www.investopedia.com/terms/f/foreign-exchange-markets.asp",
         "A detailed walkthrough of how the foreign exchange market works."),
        ("Investopedia - Interest Rate Differential",
         "https://www.investopedia.com/terms/i/interest-rate-differential.asp",
         "Covers the specific driver referenced throughout this lesson."),
        ("Investopedia - Trade Balance",
         "https://www.investopedia.com/terms/b/bot.asp",
         "Explains the balance of trade and its relationship to currency values."),
        ("Investopedia - Safe-Haven Currency",
         "https://www.investopedia.com/terms/s/safe-haven-currency.asp",
         "Covers safe-haven currency demand referenced in this lesson."),
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
        "these are general educational resources, not personalized financial advice. Consult a "
        "licensed financial advisor before making investment decisions.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.save()
    print("done:", path)


if __name__ == "__main__":
    build_explainer()
    build_worksheet()
    build_further_reading()
