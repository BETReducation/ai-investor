"""Plain-English descriptions for each pattern the detector can report.

Written to the site's educational/historical framing: what a pattern is, what it has
historically tended to suggest, and what would invalidate it. Edit freely — the
detector in patterns.py only references entries by key.
"""

CANDLESTICKS = {
    "doji": {
        "label": "Doji",
        "what": "The open and close were almost the same, so buyers and sellers ended the period level.",
        "suggests": "Indecision. After a strong move, dojis have historically often preceded a pause or a change of direction.",
        "invalidation": "A strong candle in the same direction as the prior move on the next bar.",
    },
    "hammer": {
        "label": "Hammer",
        "what": "A small body near the top with a long lower wick: sellers pushed price down but buyers drove it back up.",
        "suggests": "After a decline, hammers have historically been read as a sign that selling pressure is fading.",
        "invalidation": "A close below the hammer's low on a following bar.",
    },
    "hanging_man": {
        "label": "Hanging man",
        "what": "The same shape as a hammer, but appearing after a rise.",
        "suggests": "It shows sellers appearing after an advance; historically a mild warning that the rise may be tiring.",
        "invalidation": "A close above the hanging man's high on a following bar.",
    },
    "inverted_hammer": {
        "label": "Inverted hammer",
        "what": "A small body near the bottom with a long upper wick, appearing after a decline: buyers tried to push up but couldn't hold it.",
        "suggests": "Historically a tentative sign that buyers are starting to test the market; it usually needs a follow-up bar to confirm.",
        "invalidation": "A close below the candle's low on a following bar.",
    },
    "shooting_star": {
        "label": "Shooting star",
        "what": "A small body near the bottom with a long upper wick, appearing after a rise: buyers pushed price up but were rejected.",
        "suggests": "Historically a sign that buying pressure is running into sellers, most meaningful near resistance.",
        "invalidation": "A close above the candle's high on a following bar.",
    },
    "bullish_engulfing": {
        "label": "Bullish engulfing",
        "what": "A green candle whose body fully covers the previous red candle's body.",
        "suggests": "Buyers overpowered sellers within a bar; after a decline it has historically been read as a possible turn upward.",
        "invalidation": "A close below the engulfing candle's low.",
    },
    "bearish_engulfing": {
        "label": "Bearish engulfing",
        "what": "A red candle whose body fully covers the previous green candle's body.",
        "suggests": "Sellers overpowered buyers within a bar; after a rise it has historically been read as a possible turn downward or a pause.",
        "invalidation": "A close above the engulfing candle's high.",
    },
    "inside_bar": {
        "label": "Inside bar",
        "what": "The whole bar sits inside the previous bar's high-to-low range.",
        "suggests": "Price is pausing and volatility is compressing; a break out of the prior bar's range has historically often set the next short-term direction.",
        "invalidation": "Not applicable until price closes outside the prior bar's range.",
    },
    "morning_star": {
        "label": "Morning star",
        "what": "Three bars: a large red candle, a small-bodied candle, then a large green candle closing well into the first.",
        "suggests": "A shift from selling to buying; historically one of the more widely watched bullish reversal shapes after a decline.",
        "invalidation": "A close below the middle candle's low.",
    },
    "evening_star": {
        "label": "Evening star",
        "what": "Three bars: a large green candle, a small-bodied candle, then a large red candle closing well into the first.",
        "suggests": "A shift from buying to selling; historically a widely watched bearish reversal shape after a rise.",
        "invalidation": "A close above the middle candle's high.",
    },
    "three_white_soldiers": {
        "label": "Three white soldiers",
        "what": "Three consecutive strong green candles, each opening within the previous body and closing higher.",
        "suggests": "Steady, persistent buying; historically read as a sign of a strengthening up-move, though it can also mean the move is stretched.",
        "invalidation": "A close back below the first soldier's open.",
    },
    "three_black_crows": {
        "label": "Three black crows",
        "what": "Three consecutive strong red candles, each opening within the previous body and closing lower.",
        "suggests": "Steady, persistent selling; historically read as a sign of a strengthening down-move, though it can also mean the move is stretched.",
        "invalidation": "A close back above the first crow's open.",
    },
    "piercing_line": {
        "label": "Piercing line",
        "what": "After a red candle, a green candle opens lower but closes above the red candle's midpoint.",
        "suggests": "Buyers reclaimed more than half of the prior drop; historically a mild bullish reversal sign after a decline.",
        "invalidation": "A close below the green candle's low.",
    },
    "dark_cloud_cover": {
        "label": "Dark cloud cover",
        "what": "After a green candle, a red candle opens higher but closes below the green candle's midpoint.",
        "suggests": "Sellers erased more than half of the prior gain; historically a mild bearish reversal sign after a rise.",
        "invalidation": "A close above the red candle's high.",
    },
    "bullish_marubozu": {
        "label": "Bullish marubozu",
        "what": "A large green candle with almost no wicks: buyers were in control from open to close.",
        "suggests": "Strong buying conviction; historically often seen at the start or continuation of an up-move.",
        "invalidation": "A close below the candle's open.",
    },
    "bearish_marubozu": {
        "label": "Bearish marubozu",
        "what": "A large red candle with almost no wicks: sellers were in control from open to close.",
        "suggests": "Strong selling conviction; historically often seen at the start or continuation of a down-move.",
        "invalidation": "A close above the candle's open.",
    },
}

EVENTS = {
    "breakout_up": {
        "label": "Breakout above a level",
        "what": "Price closed clearly above a level that had previously held it back.",
        "suggests": "Historically a sign that buyers have absorbed the sellers at that price; more reliable when volume is above average.",
        "invalidation": "A close back below the level (a failed breakout).",
    },
    "breakout_down": {
        "label": "Breakdown below a level",
        "what": "Price closed clearly below a level that had previously held it up.",
        "suggests": "Historically a sign that sellers have overcome the buyers at that price; more reliable when volume is above average.",
        "invalidation": "A close back above the level (a failed breakdown).",
    },
    "retest_held_up": {
        "label": "Retest held (former resistance now support)",
        "what": "After breaking above a level, price pulled back to it and held.",
        "suggests": "Historically read as confirmation that the broken level has flipped from a ceiling to a floor.",
        "invalidation": "A close back below the level.",
    },
    "retest_held_down": {
        "label": "Retest held (former support now resistance)",
        "what": "After breaking below a level, price bounced back to it and was rejected.",
        "suggests": "Historically read as confirmation that the broken level has flipped from a floor to a ceiling.",
        "invalidation": "A close back above the level.",
    },
    "failed_breakout_up": {
        "label": "Failed breakout",
        "what": "Price broke above a level but then closed back below it.",
        "suggests": "Historically a caution sign: the move lacked follow-through, and failed breakouts are sometimes followed by moves the other way.",
        "invalidation": "A renewed close above the level.",
    },
    "failed_breakout_down": {
        "label": "Failed breakdown",
        "what": "Price broke below a level but then closed back above it.",
        "suggests": "Historically a sign the selling lacked follow-through, sometimes followed by moves the other way.",
        "invalidation": "A renewed close below the level.",
    },
}

LEVELS = {
    "what": "Support is a price where the market has repeatedly stopped falling; resistance is one where it has repeatedly stopped rising. The more times a level has been touched, the more attention it tends to draw.",
    "suggests": "Historically, price often reacts near these levels, and a decisive close through one is treated as meaningful.",
}

CHART_PATTERNS = {
    "double_top": {
        "label": "Double top",
        "what": "Price rose to a high, pulled back, then rose to about the same high again and was turned back a second time.",
        "suggests": "Two failures at the same level have historically been read as a sign buyers are running out of strength. The pattern is only considered confirmed once price closes below the low between the two peaks (the neckline).",
        "invalidation": "A close above both peaks.",
    },
    "double_bottom": {
        "label": "Double bottom",
        "what": "Price fell to a low, bounced, then fell to about the same low again and held a second time.",
        "suggests": "Two holds at the same level have historically been read as a sign sellers are running out of strength. The pattern is only considered confirmed once price closes above the high between the two lows (the neckline).",
        "invalidation": "A close below both lows.",
    },
    "range": {
        "label": "Sideways range",
        "what": "Price has bounced between a floor and a ceiling several times without making progress in either direction.",
        "suggests": "A range shows buyers and sellers in balance. Moves inside it tend to be choppy, and the direction of the eventual break has historically often set the next larger move.",
        "invalidation": "A close beyond either boundary ends the range.",
    },
}

CHART_PATTERNS.update({
    "head_and_shoulders": {
        "label": "Head and shoulders",
        "what": "Three peaks, with the middle one (the head) higher than the two either side (the shoulders). A line through the two dips between them is the neckline.",
        "suggests": "Historically read as a sign an uptrend is losing strength. It is only considered confirmed once price closes below the neckline.",
        "invalidation": "A close above the head.",
    },
    "inverse_head_and_shoulders": {
        "label": "Inverse head and shoulders",
        "what": "Three troughs, with the middle one (the head) lower than the two either side (the shoulders). A line through the two bounces between them is the neckline.",
        "suggests": "Historically read as a sign a downtrend is losing strength. It is only considered confirmed once price closes above the neckline.",
        "invalidation": "A close below the head.",
    },
    "ascending_triangle": {
        "label": "Ascending triangle",
        "what": "Highs stall at a flat ceiling while the lows keep rising, squeezing price into a tightening wedge shape.",
        "suggests": "Buyers are pressing on a fixed level. Historically the break has more often been upward, though it can fail; the break is what counts, not the shape.",
        "invalidation": "A close below the rising lower line.",
    },
    "descending_triangle": {
        "label": "Descending triangle",
        "what": "Lows hold at a flat floor while the highs keep falling, squeezing price into a tightening wedge shape.",
        "suggests": "Sellers are pressing on a fixed level. Historically the break has more often been downward, though it can fail; the break is what counts, not the shape.",
        "invalidation": "A close above the falling upper line.",
    },
    "symmetrical_triangle": {
        "label": "Symmetrical triangle",
        "what": "Highs are falling and lows are rising at the same time, so price is squeezed into a narrowing point.",
        "suggests": "Volatility is compressing. It has no built-in direction; historically the eventual break, in either direction, has often set the next move.",
        "invalidation": "Not applicable until price closes outside either line.",
    },
})
