"""Generate the 3 downloadable PDFs for the Pro 'Cross-Asset Correlation'
lesson (fourth lesson in the Macro & Cross-Asset Analysis track).
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


def draw_corr_table(c, y):
    rows = [
        ("Stocks vs. Government Bonds", "-0.30", "+0.55", False),
        ("Stocks vs. Corporate Bonds", "+0.40", "+0.85", True),
        ("Stocks vs. Commodities", "+0.15", "+0.60", False),
        ("Stocks vs. Safe-Haven Currency", "-0.20", "-0.65", True),
    ]
    col_x = [LEFT + 6, LEFT + 260, LEFT + 380]
    labels = ["Asset Pair", "Calm-Regime Corr.", "Crisis-Regime Corr."]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(TEAL)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(DARK)
    for x, lab in zip(col_x, labels):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (pair, calm, crisis, bold) in enumerate(rows):
        if bold:
            c.setFillColor(Color(0.85, 0.98, 0.96))
        elif i % 2 == 1:
            c.setFillColor(Color(0.95, 0.95, 0.97))
        else:
            c.setFillColor(Color(1, 1, 1))
        c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 8)
        c.setFillColor(DARK)
        for x, val in zip(col_x, [pair, calm, crisis]):
            c.drawString(x, y - 9, val)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/cross-asset-correlation-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Cross-Asset Correlation — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Cross-Asset Correlation", "When Everything Moves Together — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", TEAL)
    y = draw_body(c, y, "Stocks, bonds, currencies, and commodities each have typical correlation "
                         "relationships, but those relationships aren't fixed - they shift depending "
                         "on the market regime (calm versus crisis).")
    y -= PARA_GAP
    y = draw_body(c, y, "In calm markets, stocks and government bonds often show low or negative "
                         "correlation - genuine diversification. In a genuine crisis, a broad 'risk-"
                         "off' panic can cause investors to sell everything simultaneously, pushing "
                         "correlations across many asset classes sharply toward +1.")
    y -= PARA_GAP
    y = draw_body(c, y, "This makes cross-asset correlation a real risk-management concern: a "
                         "portfolio that looks diversified based on calm-market history can behave "
                         "like a concentrated bet exactly when a crisis hits.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: Correlation Across Two Regimes", PURPLE)
    y = draw_corr_table(c, y)
    y = draw_body(c, y, "Most pairs move toward +1 in the crisis regime, except the safe-haven "
                         "currency, whose negative correlation to stocks actually strengthens in a "
                         "crisis - exactly what makes it valuable as a hedge when it's needed most.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About Cross-Asset Correlation", GOLD)
    facts = [
        "Correlations are regime-dependent, not fixed - relationships can reverse or intensify.",
        "Most assets correlate upward in a crisis - a sell-everything dynamic pushes toward +1.",
        "Not every asset behaves the same way - some maintain or strengthen negative correlation.",
        "Historical correlation is a guide, not a guarantee - values shift across different crisis types.",
        "This is why stress-testing matters - evaluate a portfolio under both calm and crisis assumptions.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check When Assessing Cross-Asset Risk", GREEN)
    tips = [
        "Check correlations across regimes - look at both calm-period and stress-period history.",
        "Identify genuine crisis diversifiers - assets that held up under stress historically.",
        "Stress-test the full portfolio - model it under a crisis-correlation scenario, not just calm.",
        "Track cross-asset signals for regime shifts - rising correlation can itself be an early sign.",
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
        "this explains cross-asset correlation dynamics using illustrative numbers - it isn't "
        "personalized financial advice, and no correlation value or diversification claim here is a "
        "recommendation for your own portfolio. Correlations shift over time and no asset is "
        "guaranteed to behave the same way in every future stress event.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", TEAL, size=12)
    y -= 10

    questions = [
        ("1. What does this lesson mean by correlations being \"regime-dependent\"?", [
            "A. Correlations are set by government regulation",
            "B. Correlations are the same in every market condition",
            "C. Correlation relationships between assets can shift depending on whether markets are calm or stressed",
            "D. Correlations only apply to cryptocurrency markets"]),
        ("2. What typically happens to most cross-asset correlations during a genuine crisis?", [
            "A. They all drop to exactly zero",
            "B. They tend to rise toward +1, as a broad sell-everything dynamic takes hold",
            "C. They become impossible to measure",
            "D. They reverse to become perfectly negative for every pair"]),
        ("3. In the illustrative example, what was notable about the safe-haven currency's correlation to stocks?", [
            "A. It became positive during the crisis, like most other pairs",
            "B. It stayed at exactly zero in both regimes",
            "C. It was impossible to calculate",
            "D. Its negative correlation to stocks actually strengthened during the crisis"]),
        ("4. Why is cross-asset correlation described as a real risk-management concern?", [
            "A. A portfolio that looks diversified based on calm-market history can behave like a concentrated bet exactly when a crisis hits",
            "B. Correlation has no real-world consequences for portfolios",
            "C. It only matters for academic research papers",
            "D. Correlation is purely a theoretical concept with no practical use"]),
        ("5. What does this lesson recommend when assessing a portfolio's risk?", [
            "A. Only ever use calm-market correlation assumptions",
            "B. Ignore correlation entirely and focus only on individual asset returns",
            "C. Stress-test the portfolio under both calm and crisis correlation assumptions",
            "D. Assume all assets are always perfectly correlated"]),
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
        ("1. What does this lesson mean by correlations being \"regime-dependent\"?",
         "C. Correlation relationships between assets can shift depending on whether markets are calm or stressed",
         "Correlation relationships aren't fixed - they shift depending on the market regime."),
        ("2. What typically happens to most cross-asset correlations during a genuine crisis?",
         "B. They tend to rise toward +1, as a broad sell-everything dynamic takes hold",
         "A broad 'risk-off' panic tends to push correlations across many asset classes toward +1."),
        ("3. In the illustrative example, what was notable about the safe-haven currency's correlation to stocks?",
         "D. Its negative correlation to stocks actually strengthened during the crisis",
         "Unlike most other pairs, its negative correlation strengthened, making it valuable as a hedge."),
        ("4. Why is cross-asset correlation described as a real risk-management concern?",
         "A. A portfolio that looks diversified based on calm-market history can behave like a concentrated bet exactly when a crisis hits",
         "A portfolio diversified based on calm-market correlations can behave like a concentrated bet in a crisis."),
        ("5. What does this lesson recommend when assessing a portfolio's risk?",
         "C. Stress-test the portfolio under both calm and crisis correlation assumptions",
         "A portfolio should be evaluated under both calm and crisis correlation assumptions."),
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
    path = "static/downloads/cross-asset-correlation-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Cross-Asset Correlation — Practice Worksheet · Pro"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Cross-Asset Correlation", "PRO PRACTICE WORKSHEET")
    y = draw_body(c, y, "Work through these by hand or with a spreadsheet. There's no wrong answer, "
                         "the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Compare Portfolio Volatility Across Regimes", TEAL)
    y = draw_body(c, y, "A 70/30 stock/bond portfolio has stock volatility of 18% and bond volatility "
                         "of 6%. Using the two-asset formula, estimate portfolio volatility at a calm "
                         "correlation of -0.25 and a crisis correlation of +0.5.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Identify a Genuine Diversifier", GREEN)
    y = draw_body(c, y, "List an asset you believe has historically held up as a diversifier during "
                         "stress, and explain why you think it behaves differently from stocks in a crisis.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Spot a Regime Shift Signal", GOLD)
    y = draw_body(c, y, "If you noticed correlations across several asset classes all rising sharply "
                         "over a short period, what might that suggest is happening in the market?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Audit Your Own Diversification Assumptions", PURPLE)
    y = draw_body(c, y, "Think of a hypothetical portfolio. What correlation assumptions might it be "
                         "relying on that could break down in a genuine crisis?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "In your own words, explain why 'diversified on paper' and 'diversified in a "
                         "crisis' can be two very different things.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/cross-asset-correlation-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Cross-Asset Correlation — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Cross-Asset Correlation", "PRO FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on cross-asset correlation? These are free, reputable, and "
                         "worth bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Correlation Coefficient",
         "https://www.investopedia.com/terms/c/correlationcoefficient.asp",
         "A refresher on the correlation statistic this lesson builds on."),
        ("Investopedia - Diversification",
         "https://www.investopedia.com/terms/d/diversification.asp",
         "Covers the diversification concept and how correlation underpins it."),
        ("Investopedia - Risk-On, Risk-Off",
         "https://www.investopedia.com/terms/r/risk-on-risk-off.asp",
         "Explains the risk sentiment shifts referenced throughout this lesson."),
        ("Investopedia - Contagion",
         "https://www.investopedia.com/terms/c/contagion.asp",
         "Covers financial contagion, related to correlations spiking during a crisis."),
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
