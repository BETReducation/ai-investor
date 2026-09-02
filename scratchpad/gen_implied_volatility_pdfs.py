"""Generate the 3 downloadable PDFs for the Pro 'Implied Volatility & Skew'
lesson (third lesson in the Options & Derivatives track).
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


def draw_skew_table(c, y):
    rows = [
        ("$85", "Put", "15% OTM", "28%", True),
        ("$95", "Put", "5% OTM", "21%", False),
        ("$100", "Both", "At the Money", "18%", False),
        ("$105", "Call", "5% OTM", "16%", False),
        ("$115", "Call", "15% OTM", "14%", False),
    ]
    col_x = [LEFT + 6, LEFT + 100, LEFT + 190, LEFT + 330]
    labels = ["Strike", "Type", "Moneyness", "Implied Volatility"]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(TEAL)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(DARK)
    for x, lab in zip(col_x, labels):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (strike, typ, moneyness, iv, bold) in enumerate(rows):
        if bold:
            c.setFillColor(Color(0.85, 0.98, 0.96))
        elif i % 2 == 1:
            c.setFillColor(Color(0.95, 0.95, 0.97))
        else:
            c.setFillColor(Color(1, 1, 1))
        c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 8)
        c.setFillColor(DARK)
        for x, val in zip(col_x, [strike, typ, moneyness, iv]):
            c.drawString(x, y - 9, val)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/implied-volatility-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Implied Volatility & Skew — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Implied Volatility & Skew", "Lesson Explainer")

    y = draw_heading(c, y, "The Concept", TEAL)
    y = draw_body(c, y, "Implied volatility (IV) is the volatility level that, plugged into an options "
                         "pricing model, produces the option's actual current market price. Unlike "
                         "realized volatility (backward-looking), IV is a forward-looking, market-"
                         "implied forecast embedded in option prices.")
    y -= PARA_GAP
    y = draw_body(c, y, "IV is rarely flat across strikes. Plotting it typically produces a curve - "
                         "the volatility skew. For equity index options, the skew is usually downward-"
                         "sloping: out-of-the-money puts trade at higher IV than calls, reflecting "
                         "persistent demand for downside protection.")
    y -= PARA_GAP
    y = draw_body(c, y, "A steepening skew (puts relatively more expensive) signals rising demand for "
                         "crash protection, often a sign of building fear before the stock has moved "
                         "much. Reading the skew reveals what the options market is actually worried "
                         "about.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: A Downward-Sloping Skew", PURPLE)
    y = draw_body(c, y, "Implied volatility across five strikes on a hypothetical index option, stock "
                         "at $100.")
    y = draw_skew_table(c, y)
    y = draw_body(c, y, "The deep out-of-the-money put carries nearly double the IV of the equivalent "
                         "call - reflecting the market pricing in persistent demand for downside crash "
                         "protection, a pattern seen consistently in equity index options.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About Implied Volatility", GOLD)
    facts = [
        "IV is forward-looking, realized volatility is backward-looking - they can diverge substantially.",
        "IV tends to spike around known events, then drop sharply after - 'volatility crush'.",
        "Equity index skew is usually downward-sloping - crash protection demand makes puts pricier.",
        "A steepening skew often signals rising fear, even before the stock has actually moved much.",
        "High IV doesn't guarantee a big move - it means a wider range of outcomes is priced as likely.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check Before Trading Around IV", GREEN)
    tips = [
        "Compare IV to its own history - a level only means something relative to recent IV.",
        "Watch for volatility crush - buying options before a known event risks IV collapsing after.",
        "Read the skew, not just one IV number - the shape across strikes carries real information.",
        "Connect back to vega - vega tells you exactly how much an IV shift moves your position.",
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
        "this explains implied volatility and skew using illustrative numbers - it isn't personalized "
        "financial advice, and no reading or level here is a recommendation to trade. Implied "
        "volatility is a market-derived estimate, not a guarantee of future price movement.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", TEAL, size=12)
    y -= 10

    questions = [
        ("1. What is implied volatility?", [
            "A. How much a stock has already moved in the past year",
            "B. The option's strike price divided by the stock price",
            "C. The volatility level that, plugged into a pricing model, produces the option's current market price",
            "D. A guaranteed forecast of the stock's future price"]),
        ("2. What shape does equity index volatility skew usually take?", [
            "A. Perfectly flat across every strike",
            "B. Downward-sloping, with out-of-the-money puts trading at higher IV than calls",
            "C. Upward-sloping, with calls always more expensive than puts",
            "D. Random, with no consistent pattern ever observed"]),
        ("3. In the illustrative example, what did the wide gap between put and call IV suggest?", [
            "A. The options were mispriced by mistake",
            "B. Calls always cost more than puts",
            "C. The stock was guaranteed to fall",
            "D. Persistent demand for downside crash protection, a pattern seen consistently in index options"]),
        ("4. What is \"volatility crush\"?", [
            "A. A sharp drop in implied volatility right after a known event like earnings",
            "B. A stock crashing more than 50% in one day",
            "C. An option expiring worthless",
            "D. A broker closing a position without permission"]),
        ("5. Does high implied volatility guarantee a stock will move a lot?", [
            "A. Yes, IV is a guaranteed forecast",
            "B. No, IV has no relationship to expected movement at all",
            "C. No, it means a wider range of outcomes is being priced as more likely, not a guarantee of one",
            "D. Yes, but only for put options"]),
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
        ("1. What is implied volatility?",
         "C. The volatility level that, plugged into a pricing model, produces the option's current market price",
         "Implied volatility is a forward-looking, market-implied estimate embedded in the option's current price."),
        ("2. What shape does equity index volatility skew usually take?",
         "B. Downward-sloping, with out-of-the-money puts trading at higher IV than calls",
         "Equity index skew is usually downward-sloping, reflecting persistent demand for crash protection."),
        ("3. In the illustrative example, what did the wide gap between put and call IV suggest?",
         "D. Persistent demand for downside crash protection, a pattern seen consistently in index options",
         "The 28% put IV versus 14% call IV reflects the market's ongoing willingness to pay up for downside protection."),
        ("4. What is \"volatility crush\"?",
         "A. A sharp drop in implied volatility right after a known event like earnings",
         "Volatility crush refers to IV spiking ahead of an event, then dropping sharply once uncertainty resolves."),
        ("5. Does high implied volatility guarantee a stock will move a lot?",
         "C. No, it means a wider range of outcomes is being priced as more likely, not a guarantee of one",
         "High IV reflects a wider expected range of outcomes being priced in, not a certainty of any specific move."),
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
    path = "static/downloads/implied-volatility-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Implied Volatility & Skew — Practice Worksheet · Pro"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Implied Volatility & Skew", "PRO PRACTICE WORKSHEET")
    y = draw_body(c, y, "Work through these by hand or with a spreadsheet. There's no wrong answer, "
                         "the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Read a Skew Gap", TEAL)
    y = draw_body(c, y, "A stock's out-of-the-money put trades at 25% IV and its equivalent call trades "
                         "at 15% IV. Calculate the skew gap and classify it using the lesson's thresholds.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Distinguish IV From Realized Volatility", GREEN)
    y = draw_body(c, y, "In your own words, explain the difference between implied volatility and "
                         "realized (historical) volatility.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Plan Around a Known Event", GOLD)
    y = draw_body(c, y, "A stock reports earnings next week and its IV has risen sharply. What risk "
                         "does a trader buying an option now face from volatility crush after the event?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Interpret a Steepening Skew", PURPLE)
    y = draw_body(c, y, "If a market's put-call IV skew gap widened from 4 points to 12 points over a "
                         "week, what might that suggest is happening in the market?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "Why does the lesson caution that high IV doesn't guarantee a stock will "
                         "actually move a lot?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/implied-volatility-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Implied Volatility & Skew — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Implied Volatility & Skew", "PRO FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on implied volatility and skew? These are free, reputable, "
                         "and worth bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Implied Volatility",
         "https://www.investopedia.com/terms/i/iv.asp",
         "A detailed walkthrough of implied volatility and how it's derived from option prices."),
        ("Investopedia - Volatility Skew",
         "https://www.investopedia.com/terms/v/volatilityskew.asp",
         "Covers volatility skew specifically, the shape referenced throughout this lesson."),
        ("Investopedia - Volatility Smile",
         "https://www.investopedia.com/terms/v/volatilitysmile.asp",
         "Explains the related 'smile' pattern seen in some options markets."),
        ("Cboe VIX Overview",
         "https://www.cboe.com/tradable_products/vix/",
         "The CBOE's own overview of the VIX, the best-known implied volatility index."),
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
