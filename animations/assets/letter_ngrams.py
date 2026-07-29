"""Letter-view top n-grams — the top-5 n-grams (bigrams + trigrams, ranked
together by word count) containing a letter, each row laid out so the letter sits
on a shared CENTER column.

Font size is normalized PER LETTER: this letter's most-common n-gram is drawn at
`top_font`, and every other row scales by sqrt(count / top_count) — so the top
n-gram is a fixed size for every letter while the rest show their relative
frequency within that letter. Within a row the (first) occurrence of the letter is
placed on the center column and the other characters step out left/right by a
per-row `char_ratio · font`. The anchored letter is tinted `letter_color`.

The five rows are distributed to FILL a vertical span: the first row's TOP sits at
`top_y` and the last row's BOTTOM at `bottom_y`, with equal gaps between — so the
stack lines up with an adjacent panel (e.g. the top of the length-2 heatmap box to
the bottom of the length-10 box). Numbers are read from `letter_ngram_cache`.
"""
import math

from config import *
from assets import letter_ngram_data as lnd


def letter_ngrams(letter, *, center_x=0.0, top_y=2.0, bottom_y=-2.0, top_font=46.0,
                  min_font=12.0, char_ratio=0.0145,
                  letter_color=ACCENT_FILL, other_color=BLACK):
    """Top-5 combined n-grams for `letter`, per-letter normalized (top n-gram at
    `top_font`, rest at `top_font · sqrt(count / top_count)` ≥ `min_font`). The
    anchored-letter column sits at `center_x`; the five rows fill the vertical span
    so row 1's top is at `top_y` and row 5's bottom at `bottom_y` (equal gaps).
    Returns a VGroup with `.rows` (one VGroup per n-gram, top→bottom)."""
    lc = letter.lower()
    data = lnd.get(letter)
    top_count = data[0][1] if data else 1

    # build each row with the anchor letter at local (0, 0), then measure heights
    built, heights = [], []
    for gram, count in data:
        font = max(min_font, top_font * math.sqrt(count / top_count)) if top_count \
            else top_font
        char_w = char_ratio * font
        p = gram.index(lc)                        # anchor on the first occurrence
        row = VGroup()
        for i, ch in enumerate(gram):
            glyph = crisp_text(ch.upper(), font_size=font,
                               color=letter_color if i == p else other_color)
            glyph.move_to([(i - p) * char_w, 0, 0])   # letter char at local x = 0
            row.add(glyph)
        built.append(row)
        heights.append(row.height)

    # equal gaps so row 1 top = top_y and row n bottom = bottom_y
    n = len(built)
    gap = ((top_y - bottom_y) - sum(heights)) / (n - 1) if n > 1 else 0.0
    content = VGroup()
    rows = VGroup()
    edge = top_y                                  # top edge of the next row
    for row, h in zip(built, heights):
        row.shift([center_x, edge - h / 2, 0])    # local (0,0) [center] → its slot
        content.add(row)
        rows.add(row)
        edge = edge - h - gap

    content.rows = rows
    return content
