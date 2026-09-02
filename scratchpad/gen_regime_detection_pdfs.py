"""Generate the 3 downloadable PDFs for the Pro 'Regime Detection' lesson
(fourth lesson in the Quantitative Strategy Design track).
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


def draw_regime_table(c, y):
    rows = [
        ("Jan-Jun", "11% (annualized)", "0.35", "Low-Vol Trending", False),
        ("Jul-Sep", "14% (annualized)", "0.42", "Range-Bound / Choppy", False),
        ("Oct-Nov", "34% (annualized)", "0.81", "High-Vol Crisis", True),
    ]
    col_x = [LEFT + 6, LEFT + 110, LEFT + 270, LEFT + 360]
    labels = ["Period", "Rolling Volatility", "Avg. Correlation", "Illustrative Regime"]
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(TEAL)
    c.rect(LEFT, y - 16, CONTENT_W, 18, fill=1, stroke=0)
    c.setFillColor(DARK)
    for x, lab in zip(col_x, labels):
        c.drawString(x, y - 12, lab)
    y -= 20
    c.setFont("Helvetica", 8)
    for i, (period, vol, corr, regime, bold) in enumerate(rows):
        if bold:
            c.setFillColor(Color(0.85, 0.98, 0.96))
        elif i % 2 == 1:
            c.setFillColor(Color(0.95, 0.95, 0.97))
        else:
            c.setFillColor(Color(1, 1, 1))
        c.rect(LEFT, y - 12, CONTENT_W, 15, fill=1, stroke=0)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 8)
        c.setFillColor(DARK)
        for x, val in zip(col_x, [period, vol, corr, regime]):
            c.drawString(x, y - 9, val)
        y -= 17
    return y - 6


def build_explainer():
    path = "static/downloads/regime-detection-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Regime Detection — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Regime Detection", "Knowing When the Rules Change — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", TEAL)
    y = draw_body(c, y, "A backtest produces one overall number, but that number is an average across "
                         "many different market conditions. Markets move through distinct regimes: "
                         "low-volatility trending, range-bound/choppy, and high-volatility crisis.")
    y -= PARA_GAP
    y = draw_body(c, y, "A strategy tuned for one regime can behave very differently in another. "
                         "Momentum can shine in a steady trend and get whipsawed range-bound; mean "
                         "reversion can work range-bound and suffer in a strongly trending regime.")
    y -= PARA_GAP
    y = draw_body(c, y, "Regime detection uses measurable signals - rolling volatility, correlation "
                         "between assets, trend strength - to estimate which regime the market is "
                         "currently in, so exposure can be adjusted accordingly.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Illustrative Example: Three Regimes, Same Index", PURPLE)
    y = draw_regime_table(c, y)
    y = draw_body(c, y, "Correlation spikes alongside volatility in the crisis period - in sharp "
                         "sell-offs, assets that normally move somewhat independently start falling "
                         "together, which is why diversification tends to work worse precisely when "
                         "it's needed most.")

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About Regime Detection", GOLD)
    facts = [
        "No single strategy dominates every regime - momentum and mean reversion each have their spot.",
        "Volatility tends to cluster - high-vol periods tend to be followed by more high-vol periods.",
        "Correlation often spikes in crises - 'diversified' holdings can start moving together.",
        "Regime detection is probabilistic, not a light switch - signals estimate likelihood, not certainty.",
        "Adjusting exposure, not abandoning the strategy, is the usual response to a shifting regime.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check When Reading Regime Signals", GREEN)
    tips = [
        "Track rolling volatility - a rising reading is often the earliest signal of shifting conditions.",
        "Watch cross-asset correlation - a jump between normally-independent assets warns of stress.",
        "Use multiple signals, not one - combine volatility, correlation, and trend strength.",
        "Adjust sizing gradually - scale exposure down rather than abrupt full on/off decisions.",
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
        "this explains regime detection concepts using illustrative numbers - it isn't personalized "
        "financial advice, and no signal or threshold here is a recommendation to trade. Regime signals "
        "are probabilistic estimates, not guarantees, and markets can shift faster or differently than "
        "any model expects.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", TEAL, size=12)
    y -= 10

    questions = [
        ("1. What is a \"market regime\" in this lesson?", [
            "A. A government policy that controls stock prices",
            "B. A fixed calendar period like a fiscal quarter",
            "C. A broad market condition, like low-volatility trending, range-bound, or high-volatility crisis",
            "D. The exchange a stock is listed on"]),
        ("2. Why can a momentum strategy underperform in a range-bound regime?", [
            "A. Momentum strategies only work on bonds",
            "B. A choppy, directionless market can whipsaw a strategy designed to ride a trend",
            "C. Momentum strategies are illegal in range-bound markets",
            "D. Range-bound markets have no prices at all"]),
        ("3. In the illustrative example, what happened to cross-asset correlation during the crisis period?", [
            "A. It dropped to zero",
            "B. It became negative",
            "C. It stayed exactly the same as the calm period",
            "D. It spiked sharply higher, alongside volatility"]),
        ("4. Why does correlation spiking in a crisis matter for diversification?", [
            "A. Diversification tends to work worse exactly when it's needed most, as holdings start falling together",
            "B. Diversification becomes more effective during a crisis",
            "C. Correlation has no relationship to diversification",
            "D. Crises only affect a single asset class"]),
        ("5. What is the usual practitioner response to a shifting regime signal, according to this lesson?", [
            "A. Ignore it completely and keep the strategy unchanged",
            "B. Immediately liquidate the entire portfolio",
            "C. Adjust exposure or position size gradually, rather than an abrupt full on/off decision",
            "D. Switch to a completely different asset class permanently"]),
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
        ("1. What is a \"market regime\" in this lesson?",
         "C. A broad market condition, like low-volatility trending, range-bound, or high-volatility crisis",
         "Regimes are broad market conditions that markets move between, each with characteristic behavior."),
        ("2. Why can a momentum strategy underperform in a range-bound regime?",
         "B. A choppy, directionless market can whipsaw a strategy designed to ride a trend",
         "Momentum strategies rely on trends continuing; a choppy market lacks the sustained direction they depend on."),
        ("3. In the illustrative example, what happened to cross-asset correlation during the crisis period?",
         "D. It spiked sharply higher, alongside volatility",
         "Correlation rose from 0.35 in the calm period to 0.81 in the crisis period."),
        ("4. Why does correlation spiking in a crisis matter for diversification?",
         "A. Diversification tends to work worse exactly when it's needed most, as holdings start falling together",
         "Rising correlation during stress periods weakens diversification exactly when it matters most."),
        ("5. What is the usual practitioner response to a shifting regime signal, according to this lesson?",
         "C. Adjust exposure or position size gradually, rather than an abrupt full on/off decision",
         "Many practitioners scale position size down in high-volatility regimes rather than abrupt on/off decisions."),
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
    path = "static/downloads/regime-detection-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Regime Detection — Practice Worksheet · Pro"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Regime Detection", "PRO PRACTICE WORKSHEET")
    y = draw_body(c, y, "Work through these by hand or with a spreadsheet. There's no wrong answer, "
                         "the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Classify a Hypothetical Period", TEAL)
    y = draw_body(c, y, "Given a rolling volatility of 20% and an average correlation of 0.60, which "
                         "illustrative regime does this suggest? Explain using the lesson's thresholds.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Match Strategy to Regime", GREEN)
    y = draw_body(c, y, "Would you lean toward a momentum or mean-reversion strategy in a low-vol "
                         "trending regime? What about a range-bound one?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Track Real Signals", GOLD)
    y = draw_body(c, y, "Pick a real or hypothetical index. What data would you need to compute its "
                         "rolling volatility and cross-asset correlation over the past year?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Plan a Sizing Response", PURPLE)
    y = draw_body(c, y, "If your regime signal shifted from Low-Vol Trending to High-Vol Crisis, how "
                         "would you gradually adjust position size rather than an abrupt full exit?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "Think of a past market crisis you're aware of. What would rising correlation "
                         "and volatility have looked like in the lead-up, with hindsight?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/regime-detection-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Regime Detection — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Regime Detection", "PRO FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on regime detection? These are free, reputable, and worth "
                         "bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("Investopedia - Market Regime",
         "https://www.investopedia.com/terms/m/market-regime.asp",
         "A detailed walkthrough of market regimes and how they're identified."),
        ("Investopedia - Volatility Clustering",
         "https://www.investopedia.com/terms/v/volatility-clustering.asp",
         "Explains the tendency of volatility to cluster, referenced in this lesson."),
        ("Investopedia - Correlation Coefficient",
         "https://www.investopedia.com/terms/c/correlationcoefficient.asp",
         "Covers the correlation statistic used as a regime signal in this lesson."),
        ("Investopedia - Risk-On, Risk-Off",
         "https://www.investopedia.com/terms/r/risk-on-risk-off.asp",
         "A related concept describing shifts in broad market sentiment and regime."),
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
        "these are general educational resources, not personalized financial advice. No signal or "
        "strategy described is a recommendation to trade. Consult a licensed financial advisor before "
        "making investment decisions.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.save()
    print("done:", path)


if __name__ == "__main__":
    build_explainer()
    build_worksheet()
    build_further_reading()
