"""Common-uses view — a vertical list of GAME STATES in which the strategy's next
guess is a given letter (scene 07's top tier E/I/A, and the later tier scenes).

Each row = a blanked word + a small gallows to its right (body parts = misses so
far) + the missed-letter tally beneath the gallows — the board at the moment that
letter gets guessed. For a BEST FIRST GUESS (E len 5-11, I len 12-20, A len 1-4)
the state is a fresh game, so a row is literally a blank word of that length + an
EMPTY gallows (no body parts, no misses). A consonant guessed only AFTER misses
shows a partially-revealed board + hung body parts + a red miss row.

Brand light-blue world (crisp_text + ACCENT_FILL board): built on
`hangman_board.py` (blanked_board / hangman_drawing / missed_letters), NOT the
chalk `game_board.py`. Rows are left-aligned (board left edges line up, like the
heatmap stack) with the length label to the left of each; each row's gallows hugs
the RIGHT end of its own word (a staircase, no dead space for the shorter words).

A spec is (length,) for a blank first-guess row, or (length, board, missed) to
pin a partially-played state: `board` a pattern string ("_a__t_"), `missed` an
iterable of wrong letters. `board=None` -> all underscores.
"""
from config import *
from assets.hangman_board import blanked_board, hangman_drawing, missed_letters


# ── row geometry (tuned for the 9-row I case; every knob is a kwarg) ───────────
ROW_PITCH     = 0.90       # vertical centre-to-centre between rows
BOARD_SLOT    = 0.28       # one underscore rule width
BOARD_GAP     = 0.12       # gap between blanks
BOARD_FS      = 22         # revealed-letter font size
GALLOWS_SCALE = 0.17       # mini gallows (full drawing is ~4.4 tall)
GALLOWS_SW    = 3.0
GALLOWS_BUFF  = 0.35       # gap from word's right end to the gallows
LABEL_FS      = 24         # the length number, left of each row
LABEL_BUFF    = 0.35
MISS_FS       = 18
MISS_BUFF     = 0.12


def _spec(s):
    """Normalise a row spec to (length, pattern, missed)."""
    if isinstance(s, int):
        length, board, missed = s, None, ()
    else:
        length = s[0]
        board = s[1] if len(s) > 1 else None
        missed = s[2] if len(s) > 2 else ()
    pattern = board if board is not None else "_" * length
    return length, pattern, list(missed)


def _row(spec, *, slot, gap, board_fs, gallows_scale, gallows_sw, gallows_buff,
         miss_fs, miss_buff):
    length, pattern, missed = _spec(spec)
    brd = blanked_board(pattern, slot=slot, gap=gap, font_size=board_fs)
    gal = hangman_drawing(len(missed), stroke_width=gallows_sw).scale(gallows_scale)
    gal.next_to(brd, RIGHT, buff=gallows_buff)
    gal.set_y(brd.get_center()[1])                       # centre gallows on the word
    row = VGroup(brd, gal)
    if missed:
        miss = missed_letters(missed, font_size=miss_fs)
        miss.next_to(gal, DOWN, buff=miss_buff)
        row.add(miss)
    row.brd, row.gal, row.length = brd, gal, length
    return row


def common_uses(rows, *, center=ORIGIN, row_pitch=ROW_PITCH, slot=BOARD_SLOT,
                gap=BOARD_GAP, board_fs=BOARD_FS, gallows_scale=GALLOWS_SCALE,
                gallows_sw=GALLOWS_SW, gallows_buff=GALLOWS_BUFF, label_fs=LABEL_FS,
                label_buff=LABEL_BUFF, miss_fs=MISS_FS, miss_buff=MISS_BUFF):
    """Build the vertical common-uses list for `rows` (each a spec, top→bottom).
    Board left edges align; the length label sits to their left; the whole block
    is centred at `center`. Returns a VGroup with `.rows` (top→bottom) and
    `.labels`."""
    built = [_row(s, slot=slot, gap=gap, board_fs=board_fs,
                  gallows_scale=gallows_scale, gallows_sw=gallows_sw,
                  gallows_buff=gallows_buff, miss_fs=miss_fs, miss_buff=miss_buff)
             for s in rows]

    group, rowgrp, labels = VGroup(), VGroup(), VGroup()
    for i, row in enumerate(built):
        y = -i * row_pitch
        row.shift([-row.brd.get_left()[0], y - row.brd.get_center()[1], 0])
        lab = crisp_text(str(row.length), font_size=label_fs, color=BLACK)
        lab.next_to(row.brd, LEFT, buff=label_buff)
        rowgrp.add(row)
        labels.add(lab)
        group.add(lab, row)

    group.move_to(center)
    group.rows = rowgrp
    group.labels = labels
    return group
