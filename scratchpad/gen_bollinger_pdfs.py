"""Generate the 3 downloadable PDFs for the Intermediate 'Bollinger Bands' lesson.
Same branding/spacing approach as gen_macd_pdfs.py (wider gaps, per Gary's
2026-09-01 rule).
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


def draw_bb_chart(c, x0, y0, w, h):
    """Price with squeezing then expanding bands, inside (x0,y0,w,h)."""
    def bez(t, p0, p1, p2, p3):
        u = 1 - t
        return u**3 * p0 + 3 * u*u * t * p1 + 3 * u * t*t * p2 + t**3 * p3

    upper_ctrl = [(0, 0.85), (0.35, 0.83), (0.6, 0.6), (1.0, 0.05)]
    lower_ctrl = [(0, 0.55), (0.35, 0.58), (0.6, 0.85), (1.0, 1.0)]

    def draw_curve(ctrl, color, dash=True):
        c.setStrokeColor(color)
        c.setLineWidth(1.5)
        if dash:
            c.setDash(4, 3)
        p = c.beginPath()
        n = 40
        for i in range(n + 1):
            t = i / n
            x = x0 + t * w
            # simple cubic bezier interpolation across 4 control points (x fraction as t)
            cx = [pt[0] for pt in ctrl]
            cy = [pt[1] for pt in ctrl]
            y_frac = bez(t, cy[0], cy[1], cy[2], cy[3])
            y = y0 + y_frac * h
            if i == 0:
                p.moveTo(x, y)
            else:
                p.lineTo(x, y)
        c.drawPath(p, stroke=1, fill=0)
        c.setDash(1, 0)

    draw_curve(upper_ctrl, PURPLE)
    draw_curve(lower_ctrl, PURPLE)

    price_pts = [(0, 0.68), (0.08, 0.72), (0.16, 0.66), (0.24, 0.70), (0.32, 0.67),
                 (0.40, 0.69), (0.48, 0.55), (0.56, 0.58), (0.64, 0.40), (0.72, 0.45),
                 (0.80, 0.25), (0.88, 0.32), (0.94, 0.15), (1.0, 0.22)]
    c.setStrokeColor(GREEN)
    c.setLineWidth(2.2)
    p2 = c.beginPath()
    p2.moveTo(x0 + price_pts[0][0] * w, y0 + price_pts[0][1] * h)
    for px, py in price_pts[1:]:
        p2.lineTo(x0 + px * w, y0 + py * h)
    c.drawPath(p2, stroke=1, fill=0)

    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(GOLD)
    c.drawCentredString(x0 + 0.32 * w, y0 + 0.78 * h, "SQUEEZE")
    c.setFont("Helvetica", 7)
    c.setFillColor(GRAY)
    c.drawCentredString(x0 + 0.32 * w, y0 + 0.74 * h, "bands pull tight")

    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(GREEN)
    c.drawCentredString(x0 + 0.85 * w, y0 + 0.98 * h, "EXPANSION")


def build_explainer():
    path = "static/downloads/bollinger-bands-explainer.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Bollinger Bands — Lesson Explainer"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Bollinger Bands", "Measuring Volatility in Real Time — Lesson Explainer")

    y = draw_heading(c, y, "The Concept", PURPLE)
    y = draw_body(c, y, "A Bollinger Band is three lines plotted around price: a middle band (typically a "
                         "20-period SMA), an upper band (middle + 2 standard deviations), and a lower band "
                         "(middle - 2 standard deviations). Bollinger Bands measure volatility, not momentum.")
    y -= PARA_GAP
    y = draw_body(c, y, "Standard deviation grows when price swings widely and shrinks when price is calm, "
                         "so the bands widen during volatile stretches and narrow during quiet ones.")
    y -= PARA_GAP
    y = draw_body(c, y, "A squeeze (bands pulled tight) suggests volatility has compressed and often "
                         "precedes a sharp move - in either direction. Touching a band isn't automatically "
                         "overbought/oversold the way RSI's 70/30 is - in a strong trend price can ride a "
                         "band for a long stretch.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Bands Squeezing, Then Expanding", TEAL)
    chart_h = 180
    draw_bb_chart(c, LEFT + 10, y - chart_h, CONTENT_W - 60, chart_h)
    y -= chart_h + 30

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60

    y = draw_heading(c, y, "5 Things to Know About Bollinger Bands", GOLD)
    facts = [
        "Bands measure volatility, not momentum or direction - unlike RSI or MACD.",
        "A squeeze often precedes a big move, but doesn't tell you which direction.",
        "Riding the band isn't automatically a reversal signal - trends can walk a band for a long stretch.",
        "The bands adapt automatically as volatility changes, with no manual adjustment needed.",
        "Bandwidth (the gap between bands) is a useful standalone measure to spot squeezes more precisely.",
    ]
    for i, f in enumerate(facts, 1):
        y = draw_body(c, y, f"{i}. {f}")
        y -= 8
    y -= SECTION_GAP - 16

    y = draw_heading(c, y, "4 Things to Check When Reading Bollinger Bands", GREEN)
    tips = [
        "Watch for the squeeze - the tighter the bands, the more likely a significant move is building.",
        "Check the trend first - price hugging the upper band in an uptrend is strength, not overbought.",
        "Pair it with momentum - combine a band touch with RSI or MACD to judge if the move looks stretched.",
        "Watch for the walk - repeated touches of one band without reverting signals sustained trend strength.",
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
        "Bollinger Bands describe how much price has recently moved, not which direction it will move "
        "next. A squeeze flags rising odds of a breakout, but the breakout can go either way - pair it "
        "with trend and momentum tools.", 100)):
        c.drawString(LEFT + 12, y - 28 - i * 12, line)

    c.showPage()

    new_page(c, TAG, 3)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Quiz — Answer the questions, then check the key on the next page", PURPLE, size=12)
    y -= 10

    questions = [
        ("1. What do Bollinger Bands primarily measure?", [
            "A. The company's dividend yield",
            "B. Volatility - how much price has recently moved",
            "C. Trading volume",
            "D. Momentum direction"]),
        ("2. What does a \"squeeze\" (bands pulled tight together) suggest?", [
            "A. The stock is about to be delisted",
            "B. Trading has been halted",
            "C. Volatility has compressed, and a significant move may be building",
            "D. The company just paid a dividend"]),
        ("3. Does price riding the upper band in a strong uptrend automatically mean overbought and reversal?", [
            "A. Yes, always - price must revert to the middle band immediately",
            "B. Yes, because bands can never be touched",
            "C. No, because Bollinger Bands don't exist in uptrends",
            "D. No - in a strong trend, price can \"walk the band\" for an extended stretch"]),
        ("4. SMA of $100, standard deviation of $1.5 - what is the upper band (SMA + 2xstdev)?", [
            "A. $103.00", "B. $101.50", "C. $100.00", "D. $97.00"]),
        ("5. Why combine Bollinger Bands with a momentum tool like RSI or MACD?", [
            "A. It isn't useful, they measure the exact same thing",
            "B. Bands show how much price is moving; RSI/MACD help judge if that move looks stretched",
            "C. Combining indicators is against exchange rules",
            "D. RSI and MACD replace the need for price data entirely"]),
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
        ("1. What do Bollinger Bands primarily measure?",
         "B. Volatility - how much price has recently moved",
         "Bollinger Bands are built from standard deviation, a measure of volatility - not momentum or direction like RSI or MACD."),
        ("2. What does a \"squeeze\" (bands pulled tight together) suggest?",
         "C. Volatility has compressed, and a significant move may be building",
         "A squeeze reflects compressed volatility, historically often followed by an expansion - though it doesn't say which direction."),
        ("3. Does price riding the upper band in a strong uptrend automatically mean overbought and reversal?",
         "D. No - in a strong trend, price can \"walk the band\" for an extended stretch",
         "Unlike RSI's overbought reading, touching a Bollinger Band isn't automatically a reversal signal."),
        ("4. SMA of $100, standard deviation of $1.5 - what is the upper band (SMA + 2xstdev)?",
         "A. $103.00",
         "Upper band = $100 + (2 x $1.5) = $100 + $3 = $103.00."),
        ("5. Why combine Bollinger Bands with a momentum tool like RSI or MACD?",
         "B. Bands show how much price is moving; RSI/MACD help judge if that move looks stretched",
         "Bands measure volatility (how much), while RSI/MACD measure momentum (how stretched) - together they give a fuller picture."),
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
    path = "static/downloads/bollinger-bands-worksheet.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Bollinger Bands — Practice Worksheet · Intermediate"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Bollinger Bands", "INTERMEDIATE PRACTICE WORKSHEET")
    y = draw_body(c, y, "Pull up a real chart (any free charting site works, most show Bollinger Bands as "
                         "a built-in indicator) for a stock or index you're curious about. There's no "
                         "wrong answer, the goal is just practice.")
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 1 - Read the Current Bands", TEAL)
    y = draw_body(c, y, "Which stock or index, and what timeframe? Is price currently near the upper "
                         "band, lower band, or the middle band?")
    y -= 6
    y = draw_answer_box(c, y, 50)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 2 - Calculate the Bands by Hand", GREEN)
    y = draw_body(c, y, "Using a 20-period SMA of $50 and a standard deviation of $2, calculate the upper "
                         "and lower bands.")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.showPage()

    new_page(c, TAG, 2)
    y = PAGE_H - 60
    y = draw_heading(c, y, "Section 3 - Spot a Squeeze", GOLD)
    y = draw_body(c, y, "Scroll back on your chart - can you find a point where the bands pulled unusually "
                         "tight together? What happened to price shortly afterward?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 4 - Check for a Band Walk", PURPLE)
    y = draw_body(c, y, "Can you find a stretch where price rode along one band for several periods "
                         "without reverting to the middle? What was the broader trend doing at the time?")
    y -= 6
    y = draw_answer_box(c, y, 60)
    y -= SECTION_GAP

    y = draw_heading(c, y, "Section 5 - Reflection", TEAL)
    y = draw_body(c, y, "What other tool from an earlier lesson (RSI, MACD, volume) would you want to "
                         "check alongside a Bollinger Band signal before trusting it?")
    y -= 6
    y = draw_answer_box(c, y, 60)

    c.save()
    print("done:", path)


def build_further_reading():
    path = "static/downloads/bollinger-bands-further-reading.pdf"
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    TAG = "Bollinger Bands — Further Reading"

    new_page(c, TAG, 1, running=False)
    y = draw_title_block(c, "Bollinger Bands", "INTERMEDIATE FURTHER READING")
    y = draw_body(c, y, "Want to go deeper on Bollinger Bands? These are free, reputable, and worth "
                         "bookmarking.")
    y -= SECTION_GAP

    entries = [
        ("StockCharts ChartSchool - Bollinger Bands",
         "https://chartschool.stockcharts.com/table-of-contents/technical-indicators/bollinger-bands",
         "A detailed walkthrough of the Bollinger Band formula, squeezes, and common band-based strategies."),
        ("Investopedia - Bollinger Bands",
         "https://www.investopedia.com/terms/b/bollingerbands.asp",
         "Covers the Bollinger Band formula, standard deviation, and bandwidth."),
        ("Investopedia - Standard Deviation",
         "https://www.investopedia.com/terms/s/standarddeviation.asp",
         "The statistical concept the bands are built from, explained in plain English."),
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
