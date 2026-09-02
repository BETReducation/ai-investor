"""Generate the 3 downloadable PDFs for the Pro 'Income Strategies' lesson
(fourth lesson in the Options & Derivatives track).
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


def draw_cc_table(c, y):
    rows = [
        ("$95 (Below Strike)", "Expires worthless", "-$500", "+$300", "-$200", False),
        ("$108 (Below Strike)", "Expires worthless", "+$800", "+$300", "+$1,100", False),
        ("$120 (Above Strike)", "Called away at $110", "+$1,000 (capped)", "+$300", "+$1,300 (capped)", True),
    ]
    col_x = [LEFT + 6, LEFT + 130, LEFT + 240, LEFT + 320, LEFT + 390]
    labels = ["Stock at Expiration", "Call Outcome", "Stock P&L", "Premium", "Total P&L"]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(TEAL)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(DARK)
    for x, lab in zip(col_x, labels):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (price, outcome, stock, prem, total, bold) in enumerate(rows):
        if bold:
            c.setFillColor(Color(0.85, 0.98, 0.96))
        elif i % 2 == 1:
            c.setFillColor(Color(0.95, 0.95, 0.97))
        else:
            c.setFillColor(Color(1, 1, 1))
        c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 8)
        c.setFillColor(DARK)
        for x, val in zip(col_x, [price, outcome, stock, prem, total]):
            c.drawString(x, y - 9, val)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/income-strategies-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Income Strategies — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Income Strategies", "Covered Calls & Cash-Secured Puts — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", TEAL)
    y = draw_body(c, y, "A covered call means selling a call option against stock you already own, "
                         "collecting the premium in exchange for agreeing to sell at the strike if "
                         "exercised. It's 'covered' because you already hold the shares that would be "
                         "delivered.")
    y -= PARA_GAP
    y = draw_body(c, y, "A cash-secured put means selling a put while setting aside enough cash to buy "
                         "the shares at the strike if assigned. If the stock stays above the strike, "
                         "the put expires worthless and you keep the premium.")
    y -= PARA_GAP
    y = draw_body(c, y, "Both strategies collect premium upfront in exchange for a trade-off: a covered "
                         "call caps upside above the strike; a cash-secured put commits you to buying "
                         "more shares if the stock falls. Neither eliminates stock risk - they reshape "
                         "it, in exchange for income.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: A Covered Call at Three Outcomes", PURPLE)
    y = draw_body(c, y, "100 shares owned at $100, a call sold at a $110 strike for a $3 premium.")
    y = draw_cc_table(c, y)
    y = draw_body(c, y, "Even though the stock rallied to $120, total gain is capped at $1,300 - the "
                         "shares are called away at $110, missing the additional $1,000 of upside a "
                         "plain stockholder would have captured.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About Income Strategies", GOLD)
    facts = [
        "A covered call caps upside, it doesn't remove downside - you still lose if the stock falls.",
        "A cash-secured put commits capital, not just risk - cash must genuinely be set aside.",
        "Both work best on stock you already have a view on - happy to sell, or happy to buy.",
        "Assignment can happen before expiration - most common near expiration or dividend dates.",
        "These are income-generation strategies, not risk-free ones - the premium compensates for a real trade-off.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check Before Selling a Covered Call or Cash-Secured Put", GREEN)
    tips = [
        "Pick a strike you're genuinely fine with - happy to sell at, or happy to buy at.",
        "Confirm the cash or shares are truly set aside - don't count on capital needed elsewhere.",
        "Check for dividend and earnings dates - early assignment risk rises around ex-dividend dates.",
        "Compare the premium to the capped upside - weigh income against upside given away.",
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
        "this explains covered calls and cash-secured puts using illustrative numbers - it isn't "
        "personalized financial advice, and no strategy here is a recommendation to trade. Both "
        "strategies involve real downside risk in the underlying stock, and past option premiums are "
        "not a guarantee of future income.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", TEAL, size=12)
    y -= 10

    questions = [
        ("1. What is a covered call?", [
            "A. Buying a call option with borrowed money",
            "B. Selling a call option against stock you already own",
            "C. Selling a call option with no underlying stock position",
            "D. A guarantee that a stock will not fall"]),
        ("2. In the illustrative example, why was the total P&L capped at $1,300 even though the stock rose to $120?", [
            "A. Because the premium was refunded",
            "B. Because the stock actually fell, not rose",
            "C. Because the shares were called away at the $110 strike, missing further upside",
            "D. Because covered calls always lose money above the strike"]),
        ("3. What must be true for a cash-secured put?", [
            "A. The seller must already own the underlying stock",
            "B. No cash is required at all",
            "C. The put must be sold at an out-of-the-money strike only",
            "D. Enough cash must be set aside to buy the shares at the strike if assigned"]),
        ("4. Does a covered call eliminate downside risk in the stock?", [
            "A. No - you still own the stock and lose alongside it if it falls, cushioned only slightly by the premium",
            "B. Yes, covered calls fully protect against any stock decline",
            "C. Yes, but only for stocks that pay dividends",
            "D. Covered calls cannot be sold on stocks that might decline"]),
        ("5. According to this lesson, what compensates the seller in both strategies?", [
            "A. A government subsidy for options sellers",
            "B. Guaranteed profit regardless of outcome",
            "C. The premium collected upfront, in exchange for capping upside or committing to a purchase",
            "D. A refund from the options exchange"]),
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
        ("1. What is a covered call?",
         "B. Selling a call option against stock you already own",
         "A covered call means selling a call option against stock you already own."),
        ("2. In the illustrative example, why was the total P&L capped at $1,300 even though the stock rose to $120?",
         "C. Because the shares were called away at the $110 strike, missing further upside",
         "The shares are sold at the $110 strike once called away, capping the gain there."),
        ("3. What must be true for a cash-secured put?",
         "D. Enough cash must be set aside to buy the shares at the strike if assigned",
         "A cash-secured put requires setting aside enough cash to buy the shares at the strike if assigned."),
        ("4. Does a covered call eliminate downside risk in the stock?",
         "A. No - you still own the stock and lose alongside it if it falls, cushioned only slightly by the premium",
         "A covered call caps upside but does not remove downside risk in the underlying stock."),
        ("5. According to this lesson, what compensates the seller in both strategies?",
         "C. The premium collected upfront, in exchange for capping upside or committing to a purchase",
         "Both strategies collect premium income upfront in exchange for a real trade-off."),
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
    path = "static/downloads/income-strategies-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Income Strategies — Practice Worksheet · Pro"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Income Strategies", "PRO PRACTICE WORKSHEET")
    y = draw_body(c, y, "Work through these by hand or with a spreadsheet. There's no wrong answer, "
                         "the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Calculate a Covered Call Outcome", TEAL)
    y = draw_body(c, y, "You own stock at a $50 cost basis and sell a $55 call for $1.50 premium. "
                         "Calculate the total P&L per share if the stock is at $48, $53, and $60 at "
                         "expiration.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Calculate a Cash-Secured Put Outcome", GREEN)
    y = draw_body(c, y, "You sell a put with a $50 strike for a $2 premium, with $5,000 cash set "
                         "aside. What happens if the stock is at $55 at expiration? What about $42?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Weigh the Trade-Off", GOLD)
    y = draw_body(c, y, "For a stock you own that you think could rally significantly, would selling a "
                         "covered call still make sense? Why or why not?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Pick a Strike You're Comfortable With", PURPLE)
    y = draw_body(c, y, "For a stock currently at $75 that you'd be happy to buy more of at $65, would "
                         "a cash-secured put with a $65 strike make sense as an entry strategy? Explain.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "In your own words, explain why these are called 'income strategies' rather "
                         "than risk-free strategies.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/income-strategies-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Income Strategies — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Income Strategies", "PRO FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on covered calls and cash-secured puts? These are free, "
                         "reputable, and worth bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Covered Call",
         "https://www.investopedia.com/terms/c/coveredcall.asp",
         "A detailed walkthrough of the covered call strategy."),
        ("Investopedia - Cash-Secured Put",
         "https://www.investopedia.com/terms/c/cashsecuredput.asp",
         "A detailed walkthrough of the cash-secured put strategy."),
        ("Investopedia - Assignment",
         "https://www.investopedia.com/terms/a/assignment.asp",
         "Explains option assignment, referenced throughout this lesson."),
        ("Cboe Options Institute",
         "https://www.cboe.com/optionsinstitute/",
         "The CBOE's own free education hub covering options income strategies."),
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
