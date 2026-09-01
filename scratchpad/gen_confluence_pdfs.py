"""Generate the 3 downloadable PDFs for the Intermediate 'Confluence' lesson
(final lesson in the Technical Analysis track). Same branding/spacing approach
as the other Intermediate PDF generators (wider gaps, per Gary's 2026-09-01 rule).
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
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(DARK)
    c.drawString(LEFT, y, title)
    y -= 26
    c.setFont("Helvetica", 10.5)
    c.setFillColor(GRAY)
    c.drawString(LEFT, y, subtitle_text)
    y -= SECTION_GAP
    return y


def draw_confluence_chart(c, x0, y0, w, h):
    """Three stacked indicator lanes with a vertical alignment marker."""
    lane_h = h / 3.4
    gap = h * 0.06
    align_x = x0 + w * 0.5

    c.setStrokeColor(GREEN)
    c.setLineWidth(1.2)
    c.setDash(4, 3)
    c.line(align_x, y0, align_x, y0 + h)
    c.setDash(1, 0)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(GREEN)
    c.drawCentredString(align_x, y0 - 12, "signals align here")

    lanes = [
        ("RSI", PURPLE, [(0, 0.3), (0.15, 0.42), (0.3, 0.55), (0.5, 0.75), (0.7, 0.5), (0.85, 0.35), (1.0, 0.45)], "oversold bounce"),
        ("MACD", GOLD, [(0, 0.35), (0.15, 0.3), (0.3, 0.4), (0.5, 0.65), (0.7, 0.55), (0.85, 0.4), (1.0, 0.5)], "bullish crossover"),
        ("Price / Support", GREEN, [(0, 0.6), (0.15, 0.45), (0.3, 0.3), (0.5, 0.2), (0.7, 0.5), (0.85, 0.65), (1.0, 0.75)], "bounces off support"),
    ]
    for i, (label, color, pts, note) in enumerate(lanes):
        ly0 = y0 + h - (i + 1) * (lane_h + gap) + gap
        c.setFont("Helvetica", 8)
        c.setFillColor(GRAY)
        c.drawString(x0, ly0 + lane_h + 4, label)
        c.setStrokeColor(Color(0.3, 0.32, 0.38))
        c.setLineWidth(0.6)
        c.line(x0, ly0 + lane_h * 0.5, x0 + w, ly0 + lane_h * 0.5)
        c.setStrokeColor(color)
        c.setLineWidth(1.8)
        p = c.beginPath()
        p.moveTo(x0 + pts[0][0] * w, ly0 + pts[0][1] * lane_h)
        for px, py in pts[1:]:
            p.lineTo(x0 + px * w, ly0 + py * lane_h)
        c.drawPath(p, stroke=1, fill=0)
        # marker at x=0.5 (aligns with vertical line)
        mid_y = ly0 + 0.6 * lane_h if i != 2 else ly0 + 0.2 * lane_h
        c.setFillColor(GREEN)
        c.circle(align_x, ly0 + pts[3][1] * lane_h, 3.2, fill=1, stroke=0)
        c.setFont("Helvetica", 7)
        c.setFillColor(GREEN)
        c.drawRightString(x0 + w, ly0 + lane_h + 4, note)


def build_explainer():
    path = "static/downloads/confluence-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Confluence — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Confluence", "Stacking Indicators for Confluence — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", PURPLE)
    y = draw_body(c, y, "Every indicator in this track has a blind spot. RSI can stay overbought for weeks "
                         "in a strong trend. MACD confirms a shift only after it's begun. Bollinger Bands "
                         "say nothing about direction. None is wrong to use, but none is enough alone.")
    y -= PARA_GAP
    y = draw_body(c, y, "Confluence means waiting until two or three independent signals line up before "
                         "treating a setup as worth acting on. If RSI is oversold, MACD just crossed "
                         "bullish, and price sits at known support - that's three different tools agreeing "
                         "at once.")
    y -= PARA_GAP
    y = draw_body(c, y, "The goal isn't demanding every indicator agree - that almost never happens. It's "
                         "recognizing that more independent confirmation lowers the odds you're reacting "
                         "to noise, not a real signal.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Three Independent Signals Lining Up", TEAL)
    chart_h = 190
    draw_confluence_chart(c, LEFT + 10, y - chart_h, CONTENT_W - 40, chart_h)
    y -= chart_h + 30

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About Confluence", GOLD)
    facts = [
        "Independence matters more than quantity - different categories agreeing beats similar tools agreeing.",
        "Demanding perfect agreement means missing most opportunities - two solid confirmations is often enough.",
        "Confluence reduces false signals, it doesn't eliminate them - it shifts the odds, not a guarantee.",
        "Contradicting signals are information too - disagreement is itself useful to notice.",
        "More isn't always better - piling on many indicators tends to just add lag and noise.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check for Confluence", GREEN)
    tips = [
        "Mix categories, not just tools - combine momentum, volatility, and price-level indicators.",
        "Check the same point in time - signals need to line up at roughly the same moment.",
        "Confirm with volume - volume backing a setup adds a fourth, independent layer of confidence.",
        "Respect the bigger trend - confluence signals working with the trend are historically more reliable.",
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
        "confluence is a way to filter out noise, not a guarantee. Even a strong multi-signal setup can "
        "fail - always pair it with sensible position sizing and a risk management plan.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", PURPLE, size=12)
    y -= 10

    questions = [
        ("1. What does \"confluence\" mean in technical analysis?", [
            "A. Using only one indicator at a time",
            "B. A type of candlestick pattern",
            "C. Multiple independent signals lining up and pointing the same way at once",
            "D. A company's earnings report"]),
        ("2. Why is independence between signals more important than the raw number of signals?", [
            "A. It isn't - more signals of any kind is always better",
            "B. Independence has no effect on signal quality",
            "C. Only price-based signals count as real signals",
            "D. Several similar momentum tools agreeing is weaker than different categories agreeing"]),
        ("3. Why shouldn't you demand every possible indicator agree before acting?", [
            "A. Indicators are never useful, so it doesn't matter",
            "B. Perfect agreement across every tool is rare, so you'd act on almost nothing",
            "C. It's against exchange rules to check more than one indicator",
            "D. All indicators always agree anyway, so checking is pointless"]),
        ("4. Does confluence guarantee a signal will play out correctly?", [
            "A. No - it lowers the odds of reacting to noise, but it's not a guarantee",
            "B. Yes, three aligned signals always play out correctly",
            "C. Yes, but only on Fridays",
            "D. Confluence has nothing to do with signal reliability"]),
        ("5. RSI says oversold but trend and volume both suggest price is still falling - what does that mean?", [
            "A. Always trust RSI over every other tool",
            "B. Ignore the disagreement entirely and act on RSI alone",
            "C. The disagreement itself is useful - this is a weaker, less confirmed setup",
            "D. RSI is broken and should never be used again"]),
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
        ("1. What does \"confluence\" mean in technical analysis?",
         "C. Multiple independent signals lining up and pointing the same way at once",
         "Confluence is waiting until two or three independent tools agree before treating a setup as worth acting on."),
        ("2. Why is independence between signals more important than the raw number of signals?",
         "D. Several similar momentum tools agreeing is weaker than different categories agreeing",
         "Similar tools tend to move together anyway, so their agreement adds less real confirmation than genuinely different types agreeing."),
        ("3. Why shouldn't you demand every possible indicator agree before acting?",
         "B. Perfect agreement across every tool is rare, so you'd act on almost nothing",
         "Two or three solid, independent confirmations is a more practical standard than total agreement."),
        ("4. Does confluence guarantee a signal will play out correctly?",
         "A. No - it lowers the odds of reacting to noise, but it's not a guarantee",
         "Confluence shifts the odds in your favor by filtering out noise - it never eliminates the possibility of being wrong."),
        ("5. RSI says oversold but trend and volume both suggest price is still falling - what does that mean?",
         "C. The disagreement itself is useful - this is a weaker, less confirmed setup",
         "Contradicting signals are information too - when tools disagree, treat the setup with more caution."),
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
    path = "static/downloads/confluence-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Confluence — Practice Worksheet · Intermediate"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Confluence", "INTERMEDIATE PRACTICE WORKSHEET")
    y = draw_body(c, y, "Pull up a real chart with RSI, MACD, and Bollinger Bands visible (any free "
                         "charting site works) for a stock or index you're curious about. There's no "
                         "wrong answer, the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Check Each Tool", TEAL)
    y = draw_body(c, y, "Which stock or index, and what timeframe? For the current moment, note: RSI "
                         "reading, MACD position (above/below signal), and whether price is near a "
                         "support/resistance level.")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Count the Confirmations", GREEN)
    y = draw_body(c, y, "Of the signals you noted in Section 1, how many are pointing the same direction? "
                         "How many are pointing the opposite way, or are neutral?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Check for Independence", GOLD)
    y = draw_body(c, y, "Are your confirming signals genuinely independent (e.g. one momentum tool, one "
                         "volatility tool, one price-level tool), or are they all measuring something "
                         "similar?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Add Volume and Trend", PURPLE)
    y = draw_body(c, y, "Is volume backing up the move? Is the broader trend working with your setup or "
                         "against it? Does this raise or lower your confidence?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "Looking back across this whole Technical Analysis track, which single tool do "
                         "you find yourself trusting most, and why? What's one thing you'd still want to "
                         "double-check before acting on any signal?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/confluence-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Confluence — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Confluence", "INTERMEDIATE FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on combining indicators? These are free, reputable, and worth "
                         "bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("StockCharts ChartSchool - Technical Indicators Overview",
         "https://chartschool.stockcharts.com/table-of-contents/technical-indicators",
         "A full reference covering every indicator in this track, useful for cross-checking how each is meant to be read."),
        ("Investopedia - Confirmation",
         "https://www.investopedia.com/terms/c/confirmation.asp",
         "Covers the broader concept of using multiple signals to confirm a trade idea before acting on it."),
        ("Investopedia - Technical Analysis",
         "https://www.investopedia.com/terms/t/technicalanalysis.asp",
         "A broad overview of technical analysis as a discipline, useful context for how these tools fit together."),
        ("Investor.gov",
         "https://www.investor.gov/",
         "The U.S. Securities and Exchange Commission's official investor education site - search 'technical analysis' for plain-English background."),
        ("StockCharts ChartSchool",
         "https://chartschool.stockcharts.com/",
         "A free, well-regarded reference on chart reading fundamentals generally."),
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
