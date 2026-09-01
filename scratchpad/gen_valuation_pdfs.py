"""Generate the 3 downloadable PDFs for the Intermediate 'Valuation' lesson
(fifth and final lesson in the Stock Picking track).
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


def draw_val_table(c, y):
    rows = [
        ("Share Price", "$75.00", "$75.00", False),
        ("Earnings Per Share", "$3.00", "$3.00", False),
        ("P/E Ratio", "25.0", "25.0", True),
        ("Expected Annual Earnings Growth", "30%", "10%", False),
        ("PEG Ratio", "0.83", "2.50", True),
    ]
    col_x = [LEFT + 6, LEFT + 260, LEFT + 380]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(PURPLE)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(Color(1, 1, 1))
    for x, lab in zip(col_x, ["Metric", "Company A", "Company B"]):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (name, a, b, bold) in enumerate(rows):
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
        c.drawString(col_x[1], y - 9, a)
        c.drawString(col_x[2], y - 9, b)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/valuation-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Valuation — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Valuation", "What's a Fair Price to Pay? — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", PURPLE)
    y = draw_body(c, y, "Share price alone tells you nothing - what matters is price relative to "
                         "something, usually earnings. P/E ratio (price / EPS) tells you how many "
                         "dollars investors pay today for each dollar of current annual profit.")
    y -= PARA_GAP
    y = draw_body(c, y, "PEG ratio (P/E / expected annual earnings growth) adjusts P/E for growth. "
                         "Around 1.0 suggests price roughly matches growth; well below 1.0 can suggest a "
                         "bargain; well above 2.0 often suggests price has run ahead of growth.")
    y -= PARA_GAP
    y = draw_body(c, y, "No ratio works in isolation - always compare against the company's own "
                         "historical range and against direct industry peers.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: Same P/E, Very Different Growth", TEAL)
    y = draw_val_table(c, y)
    y = draw_body(c, y, "Both companies trade at an identical P/E of 25 - equally 'expensive' on that "
                         "number alone. But Company A grows 3x faster, giving it a much lower, more "
                         "attractive PEG of 0.83 vs Company B's 2.50.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About Valuation", GOLD)
    facts = [
        "Share price alone tells you nothing about value - always look at a ratio like P/E.",
        "A high P/E isn't automatically bad, a low P/E isn't automatically good - context matters.",
        "PEG adjusts P/E for growth - identical P/E ratios can hide very different PEG ratios.",
        "Valuation only means something in comparison - to history and to industry peers.",
        "A 'cheap' valuation can be cheap for a reason - declining businesses trade at low multiples too.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check Before Trusting a Valuation", GREEN)
    tips = [
        "Compare to industry peers - a P/E of 30 means different things in different industries.",
        "Compare to the company's own history - rich or cheap vs its own average?",
        "Sanity-check growth assumptions - a low PEG on an unrealistic forecast isn't really cheap.",
        "Combine with everything else in this track - margins, debt, and cash flow all matter too.",
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
        "no single valuation metric tells the whole story - a low P/E can mean a bargain or a business "
        "in decline. Always read valuation ratios together with the income statement, balance sheet, "
        "and cash flow picture from earlier in this track.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", PURPLE, size=12)
    y -= 10

    questions = [
        ("1. What does the P/E ratio measure?", [
            "A. The company's total debt",
            "B. The company's dividend yield",
            "C. How many dollars investors pay today for each dollar of current annual profit",
            "D. The number of shares outstanding"]),
        ("2. What does the PEG ratio add on top of the plain P/E ratio?", [
            "A. A measure of trading volume",
            "B. The company's dividend history",
            "C. Nothing, they're identical",
            "D. It adjusts P/E for the company's expected earnings growth rate"]),
        ("3. Why did Company A and Company B have different PEGs despite an identical P/E of 25?", [
            "A. Because their share prices were different",
            "B. Because their expected earnings growth rates were very different (30% vs 10%)",
            "C. Because one company paid a dividend",
            "D. PEG ratios are always identical when P/E is identical"]),
        ("4. Why can a 'cheap' low P/E stock actually be a warning sign?", [
            "A. Declining businesses often trade at low multiples because the market expects trouble",
            "B. Low P/E stocks are always fraudulent",
            "C. P/E has no relationship to how the market views a company",
            "D. Low P/E only happens to companies with no earnings at all"]),
        ("5. Why is comparing a valuation ratio to industry peers important?", [
            "A. It isn't important, one number works for every industry",
            "B. Peers only matter for dividend stocks",
            "C. A given P/E can be normal in one industry and expensive in another",
            "D. Industry comparisons are illegal under securities law"]),
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
        ("1. What does the P/E ratio measure?",
         "C. How many dollars investors pay today for each dollar of current annual profit",
         "P/E = share price divided by earnings per share."),
        ("2. What does the PEG ratio add on top of the plain P/E ratio?",
         "D. It adjusts P/E for the company's expected earnings growth rate",
         "PEG divides P/E by the expected growth rate, letting you compare on a growth-adjusted basis."),
        ("3. Why did Company A and Company B have different PEGs despite an identical P/E of 25?",
         "B. Because their expected earnings growth rates were very different (30% vs 10%)",
         "Company A's much faster growth gave it a lower, more attractive PEG."),
        ("4. Why can a 'cheap' low P/E stock actually be a warning sign?",
         "A. Declining businesses often trade at low multiples because the market expects trouble",
         "A low multiple can reflect the market pricing in real risk or decline."),
        ("5. Why is comparing a valuation ratio to industry peers important?",
         "C. A given P/E can be normal in one industry and expensive in another",
         "A P/E of 30 is unremarkable in software, expensive in banking - comparisons need context."),
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
    path = "static/downloads/valuation-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Valuation — Practice Worksheet · Intermediate"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Valuation", "INTERMEDIATE PRACTICE WORKSHEET")
    y = draw_body(c, y, "Pick a real company you're curious about, and a direct competitor. There's no "
                         "wrong answer, the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Calculate P/E and PEG", TEAL)
    y = draw_body(c, y, "For your chosen company: share price, EPS, and expected annual earnings growth. "
                         "Calculate the P/E ratio and PEG ratio.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Compare to a Peer", GREEN)
    y = draw_body(c, y, "Calculate the same ratios for a direct competitor. Which looks more expensive "
                         "on a plain P/E basis? Does that change once you adjust for growth (PEG)?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Compare to History", GOLD)
    y = draw_body(c, y, "If you can find the company's P/E from 1-2 years ago, is it trading richer or "
                         "cheaper than its own recent history right now?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Sanity-Check the Growth Assumption", PURPLE)
    y = draw_body(c, y, "Where did the expected growth rate you used come from? How confident are you "
                         "in it, and what would happen to the PEG if growth came in lower than expected?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "Combining everything from this track (margins, debt, cash flow, dividend/growth "
                         "style, and now valuation) - would you call this company reasonably priced?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/valuation-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Valuation — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Valuation", "INTERMEDIATE FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on valuation? These are free, reputable, and worth "
                         "bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Price-to-Earnings (P/E) Ratio",
         "https://www.investopedia.com/terms/p/price-earningsratio.asp",
         "A detailed walkthrough of the P/E ratio, including trailing vs forward P/E."),
        ("Investopedia - PEG Ratio",
         "https://www.investopedia.com/terms/p/pegratio.asp",
         "Covers the growth-adjusted PEG ratio used in this lesson."),
        ("Investopedia - Price-to-Sales (P/S) Ratio",
         "https://www.investopedia.com/terms/p/price-to-salesratio.asp",
         "A useful alternative valuation metric for companies without positive earnings."),
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
