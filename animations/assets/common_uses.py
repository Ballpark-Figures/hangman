"""Common-uses view — a vertical list of GAME STATES in which the strategy's next
guess is a given letter (scene 07's top tier E/I/A, and the later tier scenes).

Each row = a blanked word, with any letters MISSED so far listed to its RIGHT in
red (the running wrong-guess tally). For a BEST FIRST GUESS (E len 5-11, I len
12-20, A len 1-4) the state is a fresh game, so a row is just a blank word of that
length with NO misses. A consonant guessed only AFTER misses shows a partially-
revealed board + its red missed letters.

Brand light-blue world (crisp_text + ACCENT_FILL board): built on `hangman_board.py`
(blanked_board / missed_letters), NOT the chalk `game_board.py`. Rows are left-
aligned (board left edges line up, like the heatmap stack) and sit on a common rule
BASELINE, so blank and lettered rows align and letters grow upward. The length label
(and any misses) align to the LETTER band — level with where a revealed letter sits,
not the middle of the blanks — so the numbers read correctly once later tiers fill in
some blanks.

A spec is (length,) for a blank first-guess row, or (length, board, missed) to pin
a partially-played state: `board` a pattern string ("_a__t_"), `missed` an iterable
of wrong letters. `board=None` -> all underscores.
"""
from config import *
from assets.hangman_board import blanked_board, missed_letters


# ── row geometry (every knob a kwarg; defaults tuned for the 9-row I case) ─────
ROW_PITCH   = 0.62        # vertical centre-to-centre between rows
BOARD_SLOT  = 0.26        # one underscore rule width
BOARD_GAP   = 0.12        # gap between blanks
BOARD_FS    = 22          # revealed-letter font size
LABEL_FS    = 24          # the length number, left of each row
LABEL_BUFF  = 0.35
MISS_FS     = 22          # the red missed-letter tally, right of the word
MISS_BUFF   = 0.45


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


def _letter_cy(slot, gap, board_fs):
    """Vertical offset from a board's baseline (the rule line) up to a REVEALED
    letter's centre. Labels + misses align to THIS (where letters sit), not to the
    middle of the blanks — so a length number reads level with a filled-in letter,
    and blank vs lettered rows line up on a common baseline. Measured off a real
    revealed cell (no magic buff duplicated from hangman_board)."""
    ref = blanked_board("A", slot=slot, gap=gap, font_size=board_fs)
    return ref[0][1].get_center()[1] - ref.get_bottom()[1]


def _row(spec, *, slot, gap, board_fs, miss_fs, miss_buff, letter_cy):
    length, pattern, missed = _spec(spec)
    brd = blanked_board(pattern, slot=slot, gap=gap, font_size=board_fs)
    row = VGroup(brd)
    if missed:
        miss = missed_letters(missed, font_size=miss_fs)
        miss.next_to(brd, RIGHT, buff=miss_buff)
        miss.set_y(brd.get_bottom()[1] + letter_cy)     # align with the letters
        row.add(miss)
    row.brd, row.length = brd, length
    return row


def common_uses(rows, *, board_left_x=0.0, center_y=0.0, row_pitch=ROW_PITCH,
                slot=BOARD_SLOT, gap=BOARD_GAP, board_fs=BOARD_FS, label_fs=LABEL_FS,
                label_buff=LABEL_BUFF, miss_fs=MISS_FS, miss_buff=MISS_BUFF):
    """Build the vertical common-uses list for `rows` (each a spec, top→bottom).
    The board LEFT edges align at `board_left_x` (so lists of different word lengths
    all start at the same x); rows sit on a common RULE BASELINE (pitch = baseline to
    baseline), so blank and lettered rows line up and letters grow upward. The length
    label + any misses align to the LETTER band (not the blanks). Stack centred
    vertically on `center_y`. Returns a VGroup with `.rows` (top→bottom) + `.labels`."""
    off = _letter_cy(slot, gap, board_fs)
    built = [_row(s, slot=slot, gap=gap, board_fs=board_fs, miss_fs=miss_fs,
                  miss_buff=miss_buff, letter_cy=off) for s in rows]

    group, rowgrp, labels = VGroup(), VGroup(), VGroup()
    for i, row in enumerate(built):
        # anchor by the rule baseline (get_bottom) so rows align regardless of letters
        row.shift([-row.brd.get_left()[0], -i * row_pitch - row.brd.get_bottom()[1], 0])
        lab = crisp_text(str(row.length), font_size=label_fs, color=BLACK)
        lab.next_to(row.brd, LEFT, buff=label_buff)
        lab.set_y(row.brd.get_bottom()[1] + off)         # align number with letters
        rowgrp.add(row)
        labels.add(lab)
        group.add(lab, row)

    n = len(built)
    group.shift([board_left_x, (n - 1) * row_pitch / 2 + center_y, 0])
    group.rows = rowgrp
    group.labels = labels
    return group
