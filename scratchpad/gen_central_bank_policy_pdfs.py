"""Generate the 3 downloadable PDFs for the Pro 'Central Bank Policy' lesson
(first lesson in the Macro & Cross-Asset Analysis track).
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


def draw_ripple_table(c, y):
    rows = [
        ("New Mortgage Rates", "Rise", "Lenders' costs rise, passed to consumers", False),
        ("Bond Prices (Existing)", "Fall", "Fixed rates less attractive vs. new bonds", False),
        ("High-Growth Stock Valuations", "Fall", "Distant cash flows discounted more heavily", True),
        ("Currency (Domestic)", "Often Rises", "Higher rates can attract foreign capital", False),
    ]
    col_x = [LEFT + 6, LEFT + 205, LEFT + 290]
    labels = ["Area", "Typical Direction", "Why"]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(TEAL)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(DARK)
    for x, lab in zip(col_x, labels):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (area, direction, why, bold) in enumerate(rows):
        if bold:
            c.setFillColor(Color(0.85, 0.98, 0.96))
        elif i % 2 == 1:
            c.setFillColor(Color(0.95, 0.95, 0.97))
        else:
            c.setFillColor(Color(1, 1, 1))
        c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 8)
        c.setFillColor(DARK)
        for x, val in zip(col_x, [area, direction, why]):
            c.drawString(x, y - 9, val)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/central-bank-policy-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Central Bank Policy — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Central Bank Policy", "Why Interest Rates Move Everything — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", TEAL)
    y = draw_body(c, y, "Central banks set a benchmark short-term interest rate that ripples through "
                         "the entire economy. Raising it makes borrowing more expensive, cooling "
                         "spending and investment; cutting it does the reverse. This is monetary "
                         "policy's primary tool, balancing inflation control and employment support.")
    y -= PARA_GAP
    y = draw_body(c, y, "Higher rates make bonds relatively more attractive versus stocks, and directly "
                         "reduce the present value of future cash flows - hitting high-growth stocks "
                         "hardest, since more of their value sits in cash flows further out.")
    y -= PARA_GAP
    y = draw_body(c, y, "Markets react to what a central bank signals about the future, not just what "
                         "it does now. Forward guidance about future rate paths can move markets more "
                         "than the announced change itself.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: A Rate Hike's Ripple Effect", PURPLE)
    y = draw_body(c, y, "A hypothetical 1-percentage-point rate hike and its typical, illustrative "
                         "effects.")
    y = draw_ripple_table(c, y)
    y = draw_body(c, y, "A single rate decision ripples across mortgages, bonds, stocks, and "
                         "currencies simultaneously - one of the most closely-watched forces in all of "
                         "macro investing.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About Central Bank Policy", GOLD)
    facts = [
        "Rate decisions balance inflation and employment - too aggressive either way carries risk.",
        "Forward guidance often moves markets more than the decision itself.",
        "Rate changes act with a lag - the full effect typically takes many months to show up.",
        "Different central banks can diverge - creating currency and capital-flow effects.",
        "Markets price in expected future moves - an already-expected decision moves markets less.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check Around a Rate Decision", GREEN)
    tips = [
        "Know the meeting calendar - major central banks announce on a fixed, published schedule.",
        "Read the guidance, not just the number - the statement often carries more information.",
        "Check what was already priced in - a decision matching consensus moves markets less.",
        "Remember the lag - don't expect an immediate, full economic effect.",
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
        "this explains central bank policy mechanics using illustrative numbers - it isn't "
        "personalized financial advice, and no market reaction here is a recommendation to trade. "
        "Actual market reactions to rate decisions vary and are never fully predictable.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", TEAL, size=12)
    y -= 10

    questions = [
        ("1. What happens when a central bank raises its benchmark interest rate?", [
            "A. Borrowing becomes cheaper across the economy",
            "B. Stock prices are guaranteed to rise",
            "C. Borrowing becomes more expensive, which tends to cool spending and investment",
            "D. Nothing changes in the broader economy"]),
        ("2. Why do higher interest rates tend to hit high-growth stocks harder than mature ones?", [
            "A. High-growth stocks are always illegal to trade during rate hikes",
            "B. High-growth stocks pay higher dividends",
            "C. High-growth stocks have lower trading volume",
            "D. More of their value sits in distant future cash flows, discounted more heavily at higher rates"]),
        ("3. Why can forward guidance move markets more than the rate decision itself?", [
            "A. Forward guidance is always ignored by markets",
            "B. It reveals information about likely future decisions, which markets price in ahead of time",
            "C. Forward guidance is a legal requirement with no market impact",
            "D. It only applies to currency markets, not stocks or bonds"]),
        ("4. What does it mean that rate changes \"act with a lag\"?", [
            "A. The full economic effect of a rate move typically takes many months to fully show up",
            "B. Rate changes only affect markets, never the real economy",
            "C. Rate changes are announced with no advance notice",
            "D. Rate changes reverse themselves automatically after a year"]),
        ("5. What two goals does monetary policy typically try to balance, according to this lesson?", [
            "A. Stock prices and bond prices",
            "B. Currency strength and gold prices",
            "C. Controlling inflation and supporting employment",
            "D. Government tax revenue and spending"]),
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
        ("1. What happens when a central bank raises its benchmark interest rate?",
         "C. Borrowing becomes more expensive, which tends to cool spending and investment",
         "Raising the benchmark rate makes borrowing more expensive across the economy."),
        ("2. Why do higher interest rates tend to hit high-growth stocks harder than mature ones?",
         "D. More of their value sits in distant future cash flows, discounted more heavily at higher rates",
         "A higher discount rate reduces the present value of distant cash flows more than near-term ones."),
        ("3. Why can forward guidance move markets more than the rate decision itself?",
         "B. It reveals information about likely future decisions, which markets price in ahead of time",
         "Markets are forward-looking, so hints about future rate paths can move prices significantly."),
        ("4. What does it mean that rate changes \"act with a lag\"?",
         "A. The full economic effect of a rate move typically takes many months to fully show up",
         "Rate changes work through the economy over time, not instantly."),
        ("5. What two goals does monetary policy typically try to balance, according to this lesson?",
         "C. Controlling inflation and supporting employment",
         "Central banks typically balance controlling inflation against supporting employment."),
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
    path = "static/downloads/central-bank-policy-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Central Bank Policy — Practice Worksheet · Pro"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Central Bank Policy", "PRO PRACTICE WORKSHEET")
    y = draw_body(c, y, "Work through these by hand or with a spreadsheet. There's no wrong answer, "
                         "the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Trace a Rate Cut's Ripple Effect", TEAL)
    y = draw_body(c, y, "A central bank cuts rates by 0.5 points. Predict the likely direction for "
                         "mortgage rates, existing bond prices, growth stock valuations, and the "
                         "domestic currency.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Calculate a Present Value Impact", GREEN)
    y = draw_body(c, y, "A $100 cash flow arrives in 10 years. Calculate its present value at an 8% "
                         "discount rate, then again at a 9% discount rate. What's the percentage change?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Distinguish the Decision From the Guidance", GOLD)
    y = draw_body(c, y, "Think of a hypothetical rate decision that matches expectations exactly, but "
                         "comes with surprisingly hawkish guidance. Would you expect markets to move? Why?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Consider the Lag", PURPLE)
    y = draw_body(c, y, "If a central bank cuts rates today, would you expect unemployment to improve "
                         "immediately? Explain using the concept of policy lag.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "In your own words, explain why growth stocks are often called 'rate-"
                         "sensitive' while mature, dividend-paying stocks are less so.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/central-bank-policy-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Central Bank Policy — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Central Bank Policy", "PRO FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on central bank policy? These are free, reputable, and "
                         "worth bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Federal Reserve - Monetary Policy",
         "https://www.federalreserve.gov/monetarypolicy.htm",
         "The Federal Reserve's own overview of how U.S. monetary policy works."),
        ("Investopedia - Monetary Policy",
         "https://www.investopedia.com/terms/m/monetarypolicy.asp",
         "A detailed walkthrough of monetary policy tools and goals."),
        ("Investopedia - Federal Funds Rate",
         "https://www.investopedia.com/terms/f/federalfundsrate.asp",
         "Explains the specific benchmark rate referenced throughout this lesson."),
        ("Investopedia - Forward Guidance",
         "https://www.investopedia.com/terms/f/forward-guidance.asp",
         "Covers forward guidance, the communication tool referenced in this lesson."),
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
