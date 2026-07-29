"""Letter-view top n-grams — the top-5 n-grams (bigrams + trigrams, ranked
together by word count) containing a letter, each row laid out so the letter sits
on a shared CENTER column.

Each row's FONT SIZE is proportional to sqrt(the n-gram's word count) — so the
most common n-grams read biggest — clamped to [min_font, max_font]. Rows stack
downward from `top_center`; within a row the (first) occurrence of the letter is
placed on the center column and the other characters step out left/right by a
per-row `char_ratio · font`. The anchored letter is tinted `letter_color`.
Numbers are read from the committed `letter_ngram_cache`.
"""
import math

from config import *
from assets import letter_ngram_data as lnd


def letter_ngrams(letter, *, top_center=ORIGIN, size_coef=0.75, min_font=16.0,
                  max_font=56.0, char_ratio=0.0145, row_gap=0.16,
                  letter_color=ACCENT_FILL, other_color=BLACK):
    """Top-5 combined n-grams for `letter`, biggest = most common (font ∝
    sqrt(count)). `top_center` is where the anchored-letter column meets the TOP of
    the stack. Returns a VGroup with `.rows` (one VGroup per n-gram, top→bottom)."""
    lc = letter.lower()
    cx, top_y = float(top_center[0]), float(top_center[1])
    content = VGroup()
    rows = VGroup()
    anchor_y = prev_half = 0.0
    for k, (gram, count) in enumerate(lnd.get(letter)):
        font = max(min_font, min(max_font, size_coef * math.sqrt(count)))
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
