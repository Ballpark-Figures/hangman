"""Letter-view top n-grams — the top-5 n-grams (bigrams + trigrams, ranked
together by word count) containing a letter, each row laid out so the letter sits
on a shared CENTER column.

Font size is normalized PER LETTER: this letter's most-common n-gram is drawn at
`top_font`, and every other row scales by sqrt(count / top_count) — so the top
n-gram is a fixed size for every letter while the rest show their relative
frequency within that letter. Rows stack downward from `top_center`; within a row
the (first) occurrence of the letter is placed on the center column and the other
characters step out left/right by a per-row `char_ratio · font`. The anchored
letter is tinted `letter_color`. Numbers are read from `letter_ngram_cache`.
"""
import math

from config import *
from assets import letter_ngram_data as lnd


def letter_ngrams(letter, *, top_center=ORIGIN, top_font=46.0, min_font=12.0,
                  char_ratio=0.0145, row_gap=0.16,
                  letter_color=ACCENT_FILL, other_color=BLACK):
    """Top-5 combined n-grams for `letter`, per-letter normalized: the most common
    is drawn at `top_font`, the rest at `top_font · sqrt(count / top_count)` (≥
    `min_font`). `top_center` is where the anchored-letter column meets the TOP of
    the stack. Returns a VGroup with `.rows` (one VGroup per n-gram, top→bottom)."""
    lc = letter.lower()
    cx, top_y = float(top_center[0]), float(top_center[1])
    data = lnd.get(letter)
    top_count = data[0][1] if data else 1
    content = VGroup()
    rows = VGroup()
    anchor_y = prev_half = 0.0
    for k, (gram, count) in enumerate(data):
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
        h = row.height
        anchor_y = (top_y - h / 2) if k == 0 else (anchor_y - prev_half - row_gap - h / 2)
        row.shift([cx, anchor_y, 0])              # local (0,0) → (center col, row)
        prev_half = h / 2
        content.add(row)
        rows.add(row)

    content.rows = rows
    return content
