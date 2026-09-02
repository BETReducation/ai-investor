"""Generate the 3 downloadable PDFs for the Pro 'Commodities & Safe Havens'
lesson (fifth and final lesson in the Macro & Cross-Asset Analysis track,
and the final lesson in the entire Pro curriculum).
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


def draw_reaction_table(c, y):
    rows = [
        ("Stocks", "Sharp Decline", "Broad risk-off selling", False),
        ("Gold", "Rises", "Store-of-value demand as confidence wavers", True),
        ("Oil", "Often Falls", "Growth-scare fears reduce expected energy demand", False),
        ("Safe-Haven Currency", "Strengthens", "Capital flows toward perceived safety", True),
    ]
    col_x = [LEFT + 6, LEFT + 145, LEFT + 240]
    labels = ["Asset", "Typical Reaction", "Why"]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(TEAL)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(DARK)
    for x, lab in zip(col_x, labels):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (asset, reaction, why, bold) in enumerate(rows):
        if bold:
            c.setFillColor(Color(0.85, 0.98, 0.96))
        elif i % 2 == 1:
            c.setFillColor(Color(0.95, 0.95, 0.97))
        else:
            c.setFillColor(Color(1, 1, 1))
        c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 8)
        c.setFillColor(DARK)
        for x, val in zip(col_x, [asset, reaction, why]):
            c.drawString(x, y - 9, val)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/commodities-safe-havens-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Commodities & Safe Havens — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Commodities & Safe Havens", "Gold, Oil, and Risk Sentiment — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", TEAL)
    y = draw_body(c, y, "Commodities are physical goods traded on their own supply and demand. Oil "
                         "responds to production, inventory, and global growth expectations. Industrial "
                         "metals like copper track manufacturing closely enough to be nicknamed "
                         "'Dr. Copper' for its economic diagnostic value.")
    y -= PARA_GAP
    y = draw_body(c, y, "Gold behaves differently - limited industrial use relative to supply means it "
                         "trades largely as a store of value, rising during high inflation, currency "
                         "weakness, or geopolitical stress even when its own supply/demand is unchanged.")
    y -= PARA_GAP
    y = draw_body(c, y, "Gold and certain currencies have historically behaved as safe havens, often "
                         "strengthening a negative correlation to stocks exactly when it matters most. "
                         "Oil, more tied to the real economy, often falls alongside stocks in a growth "
                         "scare rather than hedging them.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: Reactions to a Hypothetical Risk-Off Event", PURPLE)
    y = draw_reaction_table(c, y)
    y = draw_body(c, y, "Gold and the safe-haven currency move opposite to stocks, reinforcing their "
                         "role as crisis diversifiers, while oil - more tied to real economic activity "
                         "- often falls alongside stocks rather than hedging them.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About Commodities & Safe Havens", GOLD)
    facts = [
        "Not all commodities behave the same in a crisis - gold's role differs sharply from oil's.",
        "Gold's price reflects sentiment as much as supply and demand - confidence is a major driver.",
        "'Safe haven' status isn't fixed forever - a strong historical pattern, not an ironclad rule.",
        "Oil is a genuine economic bellwether - it often reacts before other data confirms a slowdown.",
        "Commodities can add real diversification, but selectively - which one matters as much as holding any.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check When Reading Commodity Signals", GREEN)
    tips = [
        "Distinguish gold from other commodities - treat its sentiment-driven behavior separately.",
        "Read oil as a growth signal - a falling price alongside weak data reinforces a growth-scare read.",
        "Cross-check against currencies - a consistent gold and safe-haven-currency signal is stronger.",
        "Don't assume permanence - check historical safe-haven relationships are holding in this episode.",
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
        "this explains commodity and safe-haven dynamics using illustrative numbers - it isn't "
        "personalized financial advice, and no reaction or asset here is a recommendation to trade. "
        "Historical safe-haven behavior is a strong pattern, not a guarantee, and can vary across "
        "different crisis types.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", TEAL, size=12)
    y -= 10

    questions = [
        ("1. Why does gold behave differently from most other commodities, according to this lesson?", [
            "A. Gold has no price at all",
            "B. Gold is only traded by central banks",
            "C. Gold has limited industrial use relative to supply and trades largely as a store of value",
            "D. Gold's price is fixed by law in every country"]),
        ("2. Why does oil often behave differently from gold during a growth scare?", [
            "A. Oil and gold always move in perfect lockstep",
            "B. Oil is more tied to the real economy, so it often falls alongside stocks rather than hedging them",
            "C. Oil has no relationship to economic activity at all",
            "D. Oil is not considered a commodity"]),
        ("3. In the illustrative example, what happened to gold and the safe-haven currency during the risk-off event?", [
            "A. Both fell sharply alongside stocks",
            "B. Both became worthless",
            "C. Neither asset moved at all",
            "D. Both moved opposite to stocks, rising or strengthening as stocks fell"]),
        ("4. Is \"safe haven\" status a permanent, guaranteed feature of an asset?", [
            "A. No - it's a strong historical pattern, not an ironclad rule, and can vary across different crisis types",
            "B. Yes, safe-haven assets are legally guaranteed to rise in every crisis",
            "C. Yes, but only for gold specifically, never for currencies",
            "D. Safe-haven status is determined by a vote among central banks"]),
        ("5. What does \"Dr. Copper\" refer to in this lesson?", [
            "A. A nickname for the Federal Reserve chair",
            "B. A type of gold-backed currency",
            "C. Copper's price being used as a diagnostic read on economic health, given its tie to manufacturing and construction",
            "D. A medical device made from copper"]),
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
        ("1. Why does gold behave differently from most other commodities, according to this lesson?",
         "C. Gold has limited industrial use relative to supply and trades largely as a store of value",
         "Gold's limited industrial use means it trades largely on sentiment and confidence."),
        ("2. Why does oil often behave differently from gold during a growth scare?",
         "B. Oil is more tied to the real economy, so it often falls alongside stocks rather than hedging them",
         "Oil is more tied to real economic activity, so growth-scare fears push it down alongside stocks."),
        ("3. In the illustrative example, what happened to gold and the safe-haven currency during the risk-off event?",
         "D. Both moved opposite to stocks, rising or strengthening as stocks fell",
         "Gold rose and the safe-haven currency strengthened while stocks fell."),
        ("4. Is \"safe haven\" status a permanent, guaranteed feature of an asset?",
         "A. No - it's a strong historical pattern, not an ironclad rule, and can vary across different crisis types",
         "Safe-haven behavior is a strong historical pattern, not a guarantee."),
        ("5. What does \"Dr. Copper\" refer to in this lesson?",
         "C. Copper's price being used as a diagnostic read on economic health, given its tie to manufacturing and construction",
         "Copper's price tracks manufacturing and construction closely enough to earn the nickname."),
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
    path = "static/downloads/commodities-safe-havens-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Commodities & Safe Havens — Practice Worksheet · Pro"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Commodities & Safe Havens", "PRO PRACTICE WORKSHEET")
    y = draw_body(c, y, "Work through these by hand or with a spreadsheet. There's no wrong answer, "
                         "the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Estimate a Safe-Haven Buffer", TEAL)
    y = draw_body(c, y, "A portfolio is 80% stocks, 20% gold. Stocks fall 25% in a sell-off while gold "
                         "rises 15%. Calculate the blended portfolio return and the buffer versus a "
                         "stock-only portfolio.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Classify Commodity Reactions", GREEN)
    y = draw_body(c, y, "For a hypothetical sudden growth scare (not a geopolitical shock), predict "
                         "how you'd expect gold, oil, and industrial metals to react, and explain why.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Cross-Check Signals", GOLD)
    y = draw_body(c, y, "If gold is rising but a typical safe-haven currency is weakening at the same "
                         "time, what might that inconsistency suggest about the current environment?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Question a Historical Pattern", PURPLE)
    y = draw_body(c, y, "Think of a scenario where a traditional safe haven might NOT behave as "
                         "expected during a crisis. What would make that crisis type unusual?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "Looking back across this entire Macro & Cross-Asset Analysis track, in your "
                         "own words summarize how central bank policy, the yield curve, currencies, "
                         "correlation, and safe havens all connect to one another.")
    y -= 6
    y = draw_answer_box(c, y, 70)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/commodities-safe-havens-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Commodities & Safe Havens — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Commodities & Safe Havens", "PRO FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on commodities and safe havens? These are free, reputable, "
                         "and worth bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Commodity",
         "https://www.investopedia.com/terms/c/commodity.asp",
         "A detailed walkthrough of commodities as an asset class."),
        ("Investopedia - Safe Haven",
         "https://www.investopedia.com/terms/s/safe-haven.asp",
         "Covers safe-haven assets specifically, referenced throughout this lesson."),
        ("Investopedia - Gold as an Investment",
         "https://www.investopedia.com/articles/basics/08/invest-in-gold.asp",
         "Explains gold's role as a store of value and portfolio diversifier."),
        ("Investopedia - Dr. Copper",
         "https://www.investopedia.com/terms/d/dr-copper.asp",
         "Covers the 'Dr. Copper' concept referenced in this lesson."),
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
