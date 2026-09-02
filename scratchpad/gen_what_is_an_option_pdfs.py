"""Generate the 3 downloadable PDFs for the Pro 'What Is an Option?' lesson
(first lesson in the Options & Derivatives track).
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


def draw_payoff_table(c, y):
    rows = [
        ("$90 (Out of the Money)", "$0", "$4", "-$4 (Max Loss)", False),
        ("$100 (At the Money)", "$0", "$4", "-$4 (Max Loss)", False),
        ("$104 (Breakeven)", "$4", "$4", "$0", False),
        ("$115 (In the Money)", "$15", "$4", "+$11", True),
    ]
    col_x = [LEFT + 6, LEFT + 220, LEFT + 300, LEFT + 380]
    labels = ["Stock Price at Expiration", "Option Value", "Premium Paid", "Buyer's P&L"]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(TEAL)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(DARK)
    for x, lab in zip(col_x, labels):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (price, val, prem, pnl, bold) in enumerate(rows):
        if bold:
            c.setFillColor(Color(0.85, 0.98, 0.96))
        elif i % 2 == 1:
            c.setFillColor(Color(0.95, 0.95, 0.97))
        else:
            c.setFillColor(Color(1, 1, 1))
        c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 8)
        c.setFillColor(DARK)
        for x, val2 in zip(col_x, [price, val, prem, pnl]):
            c.drawString(x, y - 9, val2)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/what-is-an-option-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "What Is an Option? — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "What Is an Option?", "Rights, Not Obligations — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", TEAL)
    y = draw_body(c, y, "A call option gives its buyer the right - not the obligation - to buy 100 "
                         "shares of an underlying stock at a fixed strike price on or before expiration. "
                         "A put gives the right to sell. The buyer pays an upfront premium for that right.")
    y -= PARA_GAP
    y = draw_body(c, y, "The buyer's maximum loss is capped at the premium paid, no matter how far the "
                         "stock moves against them, while potential gain (for a call) is theoretically "
                         "uncapped. The seller takes the opposite side - collecting the premium upfront "
                         "but carrying open-ended or substantial risk.")
    y -= PARA_GAP
    y = draw_body(c, y, "An option is 'in the money' if it would be exercised profitably, 'at the "
                         "money' if the strike equals the current price, or 'out of the money' if it "
                         "would expire worthless.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: A Call Option's Payoff at Expiration", PURPLE)
    y = draw_body(c, y, "A hypothetical call option with a $100 strike, bought for a $4 premium.")
    y = draw_payoff_table(c, y)
    y = draw_body(c, y, "Below $100, the option is worthless and the loss is capped at the $4 premium. "
                         "Above the $104 breakeven, the gain grows directly with the stock price - "
                         "capped downside, open-ended upside is the defining shape of a long call.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About Options", GOLD)
    facts = [
        "Buying an option is a right, selling one is an obligation if exercised against.",
        "Options can expire worthless - the premium paid is simply gone.",
        "The premium reflects time remaining, volatility, and distance from the strike, not just price.",
        "Options are typically for 100 shares per contract.",
        "Selling uncovered (naked) options carries very different, potentially unlimited, risk versus buying.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check Before Trading an Option", GREEN)
    tips = [
        "Know your maximum loss - as a buyer, confirm it's genuinely capped at the premium paid.",
        "Check the expiration date - time works against a long option buyer.",
        "Understand the breakeven - for a call buyer, it's strike + premium paid.",
        "Know your obligation as a seller - understand what exercise would require of you.",
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
        "this explains options mechanics using illustrative numbers - it isn't personalized financial "
        "advice, and no strategy here is a recommendation. Options trading carries substantial risk, "
        "including loss of the entire premium paid, or for uncovered sellers, losses well beyond the "
        "premium received.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", TEAL, size=12)
    y -= 10

    questions = [
        ("1. What does a call option give its buyer?", [
            "A. The obligation to buy the stock at expiration",
            "B. The right, but not the obligation, to buy the stock at a set price by a set date",
            "C. Automatic ownership of the underlying company",
            "D. The right to sell the stock at a set price"]),
        ("2. In the illustrative example, what was the buyer's maximum possible loss?", [
            "A. Unlimited",
            "B. $100, the strike price",
            "C. $4, the premium paid",
            "D. $115, the highest stock price shown"]),
        ("3. What does it mean for a call option to be \"in the money\"?", [
            "A. The option has already expired",
            "B. The stock price equals the strike price exactly",
            "C. The premium was very expensive",
            "D. The stock price is above the strike price, so it would be exercised profitably"]),
        ("4. Why does an option seller carry different risk than a buyer?", [
            "A. The seller has an obligation if exercised against, and can face open-ended risk on an uncovered call",
            "B. Sellers never actually lose money on options",
            "C. Sellers automatically receive the underlying stock for free",
            "D. Sellers and buyers always have identical risk"]),
        ("5. What typically happens to an out-of-the-money option at expiration?", [
            "A. It automatically converts into shares of stock",
            "B. It doubles in value",
            "C. It expires worthless, and the premium paid is gone",
            "D. The seller must pay the buyer the full premium back"]),
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
        ("1. What does a call option give its buyer?",
         "B. The right, but not the obligation, to buy the stock at a set price by a set date",
         "A call option gives the buyer the right, not the obligation, to buy at the strike price by expiration."),
        ("2. In the illustrative example, what was the buyer's maximum possible loss?",
         "C. $4, the premium paid",
         "An option buyer's maximum loss is capped at the premium paid."),
        ("3. What does it mean for a call option to be \"in the money\"?",
         "D. The stock price is above the strike price, so it would be exercised profitably",
         "A call is in the money when the underlying stock price is above the strike price."),
        ("4. Why does an option seller carry different risk than a buyer?",
         "A. The seller has an obligation if exercised against, and can face open-ended risk on an uncovered call",
         "The seller collects the premium upfront but carries an obligation, with open-ended risk on an uncovered call."),
        ("5. What typically happens to an out-of-the-money option at expiration?",
         "C. It expires worthless, and the premium paid is gone",
         "An out-of-the-money option at expiration is worth exactly zero, and the premium paid is gone."),
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
    path = "static/downloads/what-is-an-option-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "What Is an Option? — Practice Worksheet · Pro"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "What Is an Option?", "PRO PRACTICE WORKSHEET")
    y = draw_body(c, y, "Work through these by hand or with a spreadsheet. There's no wrong answer, "
                         "the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Calculate a Call Payoff", TEAL)
    y = draw_body(c, y, "A call option has a $50 strike and a $2.50 premium. Calculate the option "
                         "value and buyer's P&L if the stock is at $48, $52.50, and $60 at expiration.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Calculate a Put Payoff", GREEN)
    y = draw_body(c, y, "A put option has a $50 strike and a $2 premium. Calculate the option value "
                         "and buyer's P&L if the stock is at $55, $48, and $40 at expiration.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Find the Breakeven", GOLD)
    y = draw_body(c, y, "For a call with a $75 strike and a $3 premium, what is the breakeven stock "
                         "price? What about a put with the same strike and premium?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Compare Buyer and Seller Risk", PURPLE)
    y = draw_body(c, y, "For the call in Section 1, describe the seller's position: what is their "
                         "maximum gain, and what is their risk if the stock keeps rising?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "In your own words, explain why a long option's maximum loss is capped but a "
                         "short (sold) uncovered call's maximum loss is not.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/what-is-an-option-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "What Is an Option? — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "What Is an Option?", "PRO FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on options basics? These are free, reputable, and worth "
                         "bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Options Basics",
         "https://www.investopedia.com/options-basics-tutorial-4583012",
         "A comprehensive tutorial covering calls, puts, and the core mechanics of options."),
        ("Investopedia - Call Option",
         "https://www.investopedia.com/terms/c/calloption.asp",
         "A detailed walkthrough of call options specifically."),
        ("Investopedia - Put Option",
         "https://www.investopedia.com/terms/p/putoption.asp",
         "A detailed walkthrough of put options specifically."),
        ("Investopedia - In the Money",
         "https://www.investopedia.com/terms/i/inthemoney.asp",
         "Explains in-the-money, at-the-money, and out-of-the-money, referenced in this lesson."),
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
