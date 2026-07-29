"""Letter-view top n-grams — the top-5 n-grams (bigrams + trigrams, ranked
together) containing a letter, each row laid out so the letter sits on a shared
CENTER column.

For a row, the (first) occurrence of the letter is placed at the center x and the
other characters step out left/right by a fixed `char_w` (monospace-style), so the
letter lines up down the whole stack — e.g. for 'r', ER has its R centered with E
to the left, RE has its R centered with E to the right. The anchored letter is
tinted `letter_color`. Numbers are read from the committed `letter_ngram_cache`.
"""
from config import *
from assets import letter_ngram_data as lnd


def letter_ngrams(letter, *, char_w=0.46, row_pitch=0.6, font_size=32,
                  top_center=ORIGIN, letter_color=ACCENT_FILL, other_color=BLACK):
    """Build the top-5 combined n-gram stack for `letter`. `top_center` is where
    the anchored-letter column meets the TOP row (so a title can sit centered
    above it). Returns a VGroup with `.rows` (one VGroup per n-gram, top→bottom)."""
    lc = letter.lower()
    content = VGroup()
    rows = VGroup()
    y = 0.0
    for gram, _n in lnd.get(letter):
        p = gram.index(lc)                       # anchor on the first occurrence
        row = VGroup()
        for i, ch in enumerate(gram):
            glyph = crisp_text(ch.upper(), font_size=font_size,
                               color=letter_color if i == p else other_color)
            glyph.move_to([(i - p) * char_w, y, 0])   # letter char at local x = 0
            row.add(glyph)
        content.add(row)
        rows.add(row)
        y -= row_pitch

    content.shift(np.array(top_center, dtype=float))   # local (0,0) → top_center
    content.rows = rows
    return content
