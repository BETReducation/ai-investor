"""Generate the 3 downloadable PDFs for the Intermediate 'Correlation' lesson
(second lesson in the Balancing a Portfolio track).
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
RED = Color(0.973, 0.443, 0.443)
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


def draw_corr_scale(c, y):
    h = 26
    seg_w = CONTENT_W / 3
    labels = ["-1.0 (opposite)", "0.0 (unrelated)", "+1.0 (lockstep)"]
    colors = [RED, GOLD, GREEN]
    for i, (lab, col) in enumerate(zip(labels, colors)):
        x = LEFT + i * seg_w
        c.setFillColor(col)
        c.rect(x, y - h, seg_w, h, fill=1, stroke=0)
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawCentredString(x + seg_w / 2, y - h / 2 - 3, lab)
    return y - h - 10


def draw_corr_table(c, y):
    rows = [
        ("20 Tech Stocks", "20", "~0.80", "~35%", "~32%", False),
        ("Mixed (Stocks+Bonds+Gold)", "20", "~0.25", "~35%", "~19%", True),
    ]
    col_x = [LEFT + 6, LEFT + 175, LEFT + 250, LEFT + 330, LEFT + 405]
    labels = ["Portfolio", "# Holdings", "Avg. Corr.", "Indiv. Vol.", "Port. Vol."]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(PURPLE)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(Color(1, 1, 1))
    for x, lab in zip(col_x, labels):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (name, n, corr, iv, pv, bold) in enumerate(rows):
        if bold:
            c.setFillColor(Color(0.90, 0.85, 0.98))
        else:
            c.setFillColor(Color(0.95, 0.95, 0.97))
        c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 8)
        c.setFillColor(DARK)
        for x, val in zip(col_x, [name, n, corr, iv, pv]):
            c.drawString(x, y - 9, val)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/correlation-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Correlation — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Correlation", "Why Owning 20 Stocks Isn't Always Diversified — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", PURPLE)
    y = draw_body(c, y, "Diversification isn't about how many holdings you have - it's about how "
                         "independently they move. Correlation measures this on a scale from -1 to +1. "
                         "+1 means two assets move in perfect lockstep; -1 means perfectly opposite; 0 "
                         "means unrelated.")
    y -= PARA_GAP
    y = draw_body(c, y, "Twenty tech stocks are typically highly correlated - they share economic "
                         "drivers. Real diversification comes from combining assets with low or negative "
                         "correlation - different sectors, asset classes, or geographies.")
    y -= PARA_GAP
    y = draw_body(c, y, "Blending low-correlation assets can reduce portfolio volatility below a simple "
                         "average of the individual volatilities - a genuine, near-free benefit of "
                         "diversification.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "The Correlation Scale", TEAL)
    y = draw_corr_scale(c, y)
    y -= 10
    y = draw_body(c, y, "Twenty tech stocks typically cluster around +0.7 to +0.9. Stocks and long-term "
                         "government bonds have often sat closer to 0, though this relationship can shift.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: 20 Tech Stocks vs a Mixed Portfolio", GREEN)
    y = draw_corr_table(c, y)
    y = draw_body(c, y, "Both hold 20 positions with similar individual volatility - but the correlated "
                         "tech portfolio barely reduces volatility, while the mixed portfolio's lower "
                         "correlation cuts volatility by nearly half.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About Correlation", GOLD)
    facts = [
        "Number of holdings isn't the same as diversification.",
        "Correlation ranges from -1 to +1 - closer to 0 or negative is where real benefit lives.",
        "Combining low-correlation assets can reduce volatility below a simple average.",
        "Correlations aren't fixed - they tend to rise during market crises.",
        "Different sectors or asset classes usually beat different stocks in the same sector.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check for Real Diversification", GREEN)
    tips = [
        "Check sector spread - genuinely different sectors, or clustered in one or two?",
        "Check asset class spread - stocks, bonds, cash, and alternatives respond differently.",
        "Remember correlations can rise in crises - don't assume history repeats exactly.",
        "Count real diversification, not just ticker count.",
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
        "correlation is estimated from historical data and can shift, especially in market stress. "
        "Treat correlation figures as a useful guide to structuring a portfolio, not a guaranteed, "
        "fixed relationship.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", PURPLE, size=12)
    y -= 10

    questions = [
        ("1. What does correlation measure?", [
            "A. The total number of holdings in a portfolio",
            "B. A company's dividend yield",
            "C. How closely two assets' prices move in relation to each other",
            "D. A stock's price-to-earnings ratio"]),
        ("2. Why might 20 tech stocks not provide much real diversification?", [
            "A. Because tech stocks are always a bad investment",
            "B. Because 20 is not enough holdings",
            "C. Because tech stocks never make money",
            "D. Because they tend to be highly correlated, moving together on shared drivers"]),
        ("3. What is the range of possible correlation values?", [
            "A. 0 to 100", "B. -1 to +1", "C. -100 to +100", "D. 0 to 1 only, never negative"]),
        ("4. Why is combining low-correlation assets sometimes called a 'free lunch'?", [
            "A. It can reduce portfolio volatility below a simple average of the assets' volatility",
            "B. It guarantees higher returns with zero risk",
            "C. It eliminates all fees",
            "D. It only works for bonds"]),
        ("5. Why should you be cautious about relying on historical correlation figures?", [
            "A. Correlation figures are always completely wrong",
            "B. Correlation never changes once measured",
            "C. Correlations can shift over time, and often rise during market crises",
            "D. Correlation only matters for cryptocurrency"]),
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
        ("1. What does correlation measure?",
         "C. How closely two assets' prices move in relation to each other",
         "Correlation ranges from -1 to +1 and measures how closely two assets move together."),
        ("2. Why might 20 tech stocks not provide much real diversification?",
         "D. Because they tend to be highly correlated, moving together on shared drivers",
         "High correlation concentrates risk in shared drivers, even with many holdings."),
        ("3. What is the range of possible correlation values?",
         "B. -1 to +1",
         "From -1 (perfectly opposite) through 0 (unrelated) to +1 (perfectly in lockstep)."),
        ("4. Why is combining low-correlation assets sometimes called a 'free lunch'?",
         "A. It can reduce portfolio volatility below a simple average of the assets' volatility",
         "Blending imperfectly-correlated assets can lower overall volatility - a genuine benefit."),
        ("5. Why should you be cautious about relying on historical correlation figures?",
         "C. Correlations can shift over time, and often rise during market crises",
         "Correlations aren't fixed - they can rise sharply during crises, right when needed most."),
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
    path = "static/downloads/correlation-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Correlation — Practice Worksheet · Intermediate"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Correlation", "INTERMEDIATE PRACTICE WORKSHEET")
    y = draw_body(c, y, "Look at your own portfolio, or a hypothetical one you're considering. There's "
                         "no wrong answer, the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - List Your Holdings", TEAL)
    y = draw_body(c, y, "List your (or a hypothetical) portfolio's holdings. For each, note the sector "
                         "and asset class (stock, bond, cash, other).")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Assess Sector Spread", GREEN)
    y = draw_body(c, y, "Are your holdings concentrated in one or two sectors, or genuinely spread "
                         "across different ones? What would happen to the portfolio if that dominant "
                         "sector had a bad year?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Assess Asset Class Spread", GOLD)
    y = draw_body(c, y, "Do you hold more than one asset class (stocks, bonds, cash, alternatives)? If "
                         "not, what might adding a second asset class do to your portfolio's volatility?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Use the Diversification Calculator", PURPLE)
    y = draw_body(c, y, "Using the lesson's calculator (or the formula), estimate the blended volatility "
                         "of two of your largest holdings. How much diversification benefit are they "
                         "actually providing each other?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "If a major market crisis hit tomorrow, do you think your holdings' correlations "
                         "would stay the same, or rise? What would that mean for your portfolio?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/correlation-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Correlation — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Correlation", "INTERMEDIATE FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on correlation and diversification? These are free, reputable, "
                         "and worth bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Correlation",
         "https://www.investopedia.com/terms/c/correlation.asp",
         "A detailed walkthrough of correlation and how it's calculated and interpreted."),
        ("Investopedia - Diversification",
         "https://www.investopedia.com/terms/d/diversification.asp",
         "Covers diversification more broadly, including the role correlation plays in it."),
        ("Investor.gov - Beginners' Guide to Asset Allocation",
         "https://www.investor.gov/introduction-investing/investing-basics/save-and-invest/asset-allocation",
         "The SEC's own plain-English guide to diversification, closely related to this lesson."),
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
