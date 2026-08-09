"""Chalkboard — a dark-navy slate in a wooden frame, the backdrop for the
hangman gameplay mock (scenes/94chalkgame). Chalk-white marks (blanks, letters,
the gallows, the hangman) are Create/Write-animated on top so they read as
chalked on.

The colours here are asset-local (chalkboard-specific), not general style
values: navy slate, wood frame, and an off-white CHALK the scene draws with.

``chalk_letter`` builds a capital as a set of hand-drawn STROKES (an E is four
lines: top, middle, bottom, left), so ``Create`` writes it stroke-by-stroke like
a hand — unlike a font glyph, whose outline only traces the letter's silhouette.
The full A–Z alphabet AND the digits 0–9 are defined.
"""
import numpy as np
from manim import *

BOARD_NAVY   = ManimColor("#16283F")   # dark navy slate
FRAME_WOOD   = ManimColor("#6E4A2A")   # wooden frame
FRAME_WOOD_D = ManimColor("#3E2A14")   # darker frame edge / inner shadow
CHALK        = ManimColor("#EDE9DC")   # off-white chalk


def chalkboard(width=15.2, height=8.4, *, frame=0.34, corner_radius=0.14,
               center=ORIGIN):
    """A wooden-framed navy chalkboard filling ``width``×``height``.

    Returns VGroup(frame, board) with handles:
        .frame   the wooden border (outer rounded rect)
        .board   the inner navy slate — use ``.get_left/right/top/bottom`` for
                 the writable area.
    """
    outer = RoundedRectangle(width=width, height=height,
                             corner_radius=corner_radius)
    outer.set_fill(FRAME_WOOD, opacity=1.0).set_stroke(FRAME_WOOD_D, width=4)

    board = RoundedRectangle(width=width - 2 * frame, height=height - 2 * frame,
                             corner_radius=corner_radius * 0.6)
    board.set_fill(BOARD_NAVY, opacity=1.0).set_stroke(FRAME_WOOD_D, width=2)
    board.move_to(outer.get_center())

    grp = VGroup(outer, board).move_to(center)
    grp.frame = outer
    grp.board = board
    return grp


# ── stroke alphabet ───────────────────────────────────────────────────────────
# Each capital = a list of (smooth, points) STROKES, in the order a hand writes
# them, in a normalised box (x,y ∈ roughly [-0.3, 0.3] × [-0.5, 0.5]). ``smooth``
# curves the stroke (bowls of B/P/R); otherwise it's straight segments. Drawn one
# stroke at a time, this reads as writing — not tracing a glyph outline.
_ALPHABET = {
    "A": [(False, [(-0.30, -0.50), (0.0, 0.50)]),
          (False, [(0.0, 0.50), (0.30, -0.50)]),
          (False, [(-0.155, -0.05), (0.155, -0.05)])],
    "B": [(False, [(-0.28, 0.50), (-0.28, -0.50)]),
          (True,  [(-0.28, 0.50), (0.14, 0.45), (0.30, 0.25),
                   (0.14, 0.03), (-0.28, 0.00)]),
          (True,  [(-0.28, 0.00), (0.16, -0.03), (0.34, -0.26),
                   (0.16, -0.47), (-0.28, -0.50)])],
    "C": [(True,  [(0.28, 0.30), (0.06, 0.50), (-0.28, 0.26),
                   (-0.28, -0.26), (0.06, -0.50), (0.28, -0.30)])],
    "D": [(False, [(-0.28, 0.50), (-0.28, -0.50)]),
          (True,  [(-0.28, 0.50), (0.16, 0.42), (0.34, 0.0),
                   (0.16, -0.42), (-0.28, -0.50)])],
    "E": [(False, [(-0.28, 0.50), (-0.28, -0.50)]),
          (False, [(-0.28, 0.50), (0.28, 0.50)]),
          (False, [(-0.28, 0.00), (0.20, 0.00)]),
          (False, [(-0.28, -0.50), (0.28, -0.50)])],
    "F": [(False, [(-0.28, 0.50), (-0.28, -0.50)]),
          (False, [(-0.28, 0.50), (0.28, 0.50)]),
          (False, [(-0.28, 0.00), (0.18, 0.00)])],
    "G": [(True,  [(0.30, 0.28), (0.06, 0.50), (-0.28, 0.26),
                   (-0.28, -0.26), (0.06, -0.50), (0.30, -0.28), (0.30, -0.06)]),
          (False, [(0.30, -0.06), (0.10, -0.06)])],
    "H": [(False, [(-0.28, 0.50), (-0.28, -0.50)]),
          (False, [(0.28, 0.50), (0.28, -0.50)]),
          (False, [(-0.28, 0.00), (0.28, 0.00)])],
    "I": [(False, [(0.0, 0.50), (0.0, -0.50)]),
          (False, [(-0.16, 0.50), (0.16, 0.50)]),
          (False, [(-0.16, -0.50), (0.16, -0.50)])],
    "J": [(False, [(0.18, 0.50), (0.18, -0.28)]),
          (True,  [(0.18, -0.28), (0.10, -0.46), (-0.08, -0.50),
                   (-0.24, -0.36)])],
    "K": [(False, [(-0.28, 0.50), (-0.28, -0.50)]),
          (False, [(-0.28, 0.02), (0.30, 0.50)]),
          (False, [(-0.28, 0.02), (0.32, -0.50)])],
    "L": [(False, [(-0.28, 0.50), (-0.28, -0.50)]),
          (False, [(-0.28, -0.50), (0.28, -0.50)])],
    "M": [(False, [(-0.34, -0.50), (-0.34, 0.50)]),
          (False, [(-0.34, 0.50), (0.0, -0.12)]),
          (False, [(0.0, -0.12), (0.34, 0.50)]),
          (False, [(0.34, 0.50), (0.34, -0.50)])],
    "N": [(False, [(-0.28, -0.50), (-0.28, 0.50)]),
          (False, [(-0.28, 0.50), (0.28, -0.50)]),
          (False, [(0.28, -0.50), (0.28, 0.50)])],
    "O": [(True,  [(0.0, 0.50), (0.30, 0.25), (0.30, -0.25), (0.0, -0.50),
                   (-0.30, -0.25), (-0.30, 0.25), (0.0, 0.50)])],
    "P": [(False, [(-0.28, 0.50), (-0.28, -0.50)]),
          (True,  [(-0.28, 0.50), (0.16, 0.45), (0.32, 0.25),
                   (0.16, 0.05), (-0.28, 0.04)])],
    "Q": [(True,  [(0.0, 0.50), (0.30, 0.25), (0.30, -0.25), (0.0, -0.50),
                   (-0.30, -0.25), (-0.30, 0.25), (0.0, 0.50)]),
          (False, [(0.08, -0.20), (0.34, -0.50)])],
    "R": [(False, [(-0.28, 0.50), (-0.28, -0.50)]),
          (True,  [(-0.28, 0.50), (0.16, 0.45), (0.32, 0.25),
                   (0.16, 0.05), (-0.28, 0.04)]),
          (False, [(-0.06, 0.04), (0.32, -0.50)])],
    "S": [(True,  [(0.26, 0.30), (0.06, 0.50), (-0.24, 0.40),
                   (-0.14, 0.12), (0.14, -0.12), (0.24, -0.40),
                   (-0.06, -0.50), (-0.26, -0.30)])],
    "T": [(False, [(-0.28, 0.50), (0.28, 0.50)]),
          (False, [(0.0, 0.50), (0.0, -0.50)])],
    "U": [(True,  [(-0.28, 0.50), (-0.28, -0.30), (-0.12, -0.50),
                   (0.12, -0.50), (0.28, -0.30), (0.28, 0.50)])],
    "V": [(False, [(-0.30, 0.50), (0.0, -0.50)]),
          (False, [(0.0, -0.50), (0.30, 0.50)])],
    "W": [(False, [(-0.38, 0.50), (-0.22, -0.50)]),
          (False, [(-0.22, -0.50), (0.0, 0.22)]),
          (False, [(0.0, 0.22), (0.22, -0.50)]),
          (False, [(0.22, -0.50), (0.38, 0.50)])],
    "X": [(False, [(-0.28, 0.50), (0.28, -0.50)]),
          (False, [(0.28, 0.50), (-0.28, -0.50)])],
    "Y": [(False, [(-0.28, 0.50), (0.0, 0.02)]),
          (False, [(0.28, 0.50), (0.0, 0.02)]),
          (False, [(0.0, 0.02), (0.0, -0.50)])],
    "Z": [(False, [(-0.28, 0.50), (0.28, 0.50)]),
          (False, [(0.28, 0.50), (-0.28, -0.50)]),
          (False, [(-0.28, -0.50), (0.28, -0.50)])],
}


# ── stroke digits 0–9 (same normalised box + hand-written stroke order) ────────
_DIGITS = {
    "0": [(True,  [(0.0, 0.48), (0.20, 0.30), (0.22, 0.0), (0.20, -0.30),
                   (0.0, -0.48), (-0.20, -0.30), (-0.22, 0.0), (-0.20, 0.30),
                   (0.0, 0.48)])],
    "1": [(False, [(-0.14, 0.32), (0.03, 0.50), (0.03, -0.50)]),
          (False, [(-0.17, -0.50), (0.21, -0.50)])],
    "2": [(True,  [(-0.20, 0.30), (-0.05, 0.48), (0.15, 0.43), (0.18, 0.20),
                   (-0.06, -0.12), (-0.20, -0.48)]),
          (False, [(-0.20, -0.48), (0.21, -0.48)])],
    "3": [(True,  [(-0.17, 0.34), (0.02, 0.50), (0.20, 0.33), (0.07, 0.08),
                   (0.0, 0.06)]),
          (True,  [(0.0, 0.06), (0.15, 0.03), (0.24, -0.17), (0.13, -0.44),
                   (-0.06, -0.50), (-0.18, -0.34)])],
    "4": [(False, [(0.08, 0.50), (-0.22, -0.07), (0.24, -0.07)]),
          (False, [(0.08, 0.50), (0.08, -0.50)])],
    "5": [(False, [(0.20, 0.50), (-0.18, 0.50), (-0.18, 0.07)]),
          (True,  [(-0.18, 0.07), (0.06, 0.15), (0.22, -0.06), (0.16, -0.38),
                   (-0.04, -0.50), (-0.20, -0.40)])],
    "6": [(True,  [(0.16, 0.40), (-0.02, 0.50), (-0.20, 0.20), (-0.21, -0.20),
                   (0.0, -0.50), (0.20, -0.28), (0.10, -0.02), (-0.12, 0.02),
                   (-0.21, -0.14)])],
    "7": [(False, [(-0.20, 0.50), (0.22, 0.50), (-0.04, -0.50)])],
    "8": [(True,  [(0.0, 0.04), (0.16, 0.20), (0.10, 0.46), (-0.10, 0.46),
                   (-0.16, 0.20), (0.0, 0.04), (0.18, -0.16), (0.10, -0.46),
                   (-0.10, -0.46), (-0.18, -0.16), (0.0, 0.04)])],
    "9": [(True,  [(0.18, 0.06), (0.04, 0.0), (-0.13, 0.14), (-0.11, 0.38),
                   (0.06, 0.50), (0.20, 0.36), (0.20, -0.14), (0.06, -0.50)])],
}

# ── stroke punctuation (same normalised box + hand-written stroke order) ───────
# Enough to write the chalkboard's data text: apostrophes, decimal points, commas,
# a colon, a percent sign, and a small grawlix set (# * !) for a censored word.
_PUNCT = {
    "'": [(True,  [(0.03, 0.50), (-0.01, 0.42), (-0.06, 0.30)])],
    ".": [(True,  [(0.0, -0.38), (0.06, -0.44), (0.0, -0.50),
                   (-0.06, -0.44), (0.0, -0.38)])],
    ",": [(True,  [(0.05, -0.34), (0.0, -0.42), (-0.06, -0.50), (-0.12, -0.58)])],
    ":": [(True,  [(0.0, 0.22), (0.05, 0.16), (0.0, 0.10), (-0.05, 0.16),
                   (0.0, 0.22)]),
          (True,  [(0.0, -0.28), (0.05, -0.34), (0.0, -0.40), (-0.05, -0.34),
                   (0.0, -0.28)])],
    "%": [(False, [(-0.20, -0.48), (0.20, 0.48)]),
          (True,  [(-0.12, 0.36), (-0.02, 0.26), (-0.12, 0.16), (-0.22, 0.26),
                   (-0.12, 0.36)]),
          (True,  [(0.12, -0.16), (0.22, -0.26), (0.12, -0.36), (0.02, -0.26),
                   (0.12, -0.16)])],
    "#": [(False, [(-0.10, 0.50), (-0.16, -0.50)]),
          (False, [(0.16, 0.50), (0.10, -0.50)]),
          (False, [(-0.24, 0.18), (0.22, 0.22)]),
          (False, [(-0.26, -0.20), (0.20, -0.16)])],
    "*": [(False, [(-0.20, 0.10), (0.20, 0.10)]),
          (False, [(-0.16, -0.10), (0.16, 0.30)]),
          (False, [(-0.16, 0.30), (0.16, -0.10)])],
    "!": [(False, [(0.0, 0.50), (0.0, -0.18)]),
          (True,  [(0.0, -0.34), (0.05, -0.40), (0.0, -0.46), (-0.05, -0.40),
                   (0.0, -0.34)])],
    "-": [(False, [(-0.18, 0.0), (0.18, 0.0)])],
    "×": [(False, [(-0.16, -0.16), (0.16, 0.16)]),
          (False, [(-0.16, 0.16), (0.16, -0.16)])],
}

_GLYPHS = {**_ALPHABET, **_DIGITS, **_PUNCT}


def chalk_letter(ch, *, height=0.6, stroke_width=4.5, color=CHALK):
    """A capital OR digit drawn as ordered chalk STROKES, centred on the origin.

    Returns a VGroup whose submobjects are the strokes in writing order — animate
    with ``LaggedStartMap(Create, letter, lag_ratio=…)`` to write it on. ``height``
    is the cap height in scene units (width follows the glyph, ~0.6·height)."""
    ch = ch.upper()
    if ch not in _GLYPHS:
        raise ValueError(f"chalk_letter: no strokes defined for {ch!r}")
    letter = VGroup()
    for smooth, pts in _GLYPHS[ch]:
        p3 = [np.array([x * height, y * height, 0.0]) for x, y in pts]
        stroke = VMobject(stroke_color=color, stroke_width=stroke_width)
        if smooth:
            stroke.set_points_smoothly(p3)
        else:
            stroke.set_points_as_corners(p3)
        letter.add(stroke)
    return letter


def chalk_phrase(text, *, height=0.4, stroke_width=3.2, buff=0.10, space=0.34,
                 color=CHALK):
    """A phrase in the chalk (written) font — one row of `chalk_letter` glyphs,
    left→right, spaces as gaps. CAPITALS-ONLY (letters are upper-cased); digits and
    the _PUNCT set (``' . , : % # * !``) are supported. Returns a VGroup whose
    submobjects are the glyphs, centred on the origin. (Promoted from the byte-
    identical scene-04 helper when scene 03 needed it too.)"""
    grp = VGroup()
    x = 0.0
    for ch in str(text).upper():
        if ch == " ":
            x += space
            continue
        L = chalk_letter(ch, height=height, stroke_width=stroke_width, color=color)
        # set the left edge to x but PRESERVE the glyph's intrinsic y (so a comma /
        # period sits low and an apostrophe rides high — never recentre to mid-line)
        L.shift(np.array([x - L.get_left()[0], 0.0, 0.0]))
        grp.add(L)
        x += L.width + buff
    grp.move_to(ORIGIN)
    return grp


def chalk_number(n, *, height=0.4, stroke_width=2.6, buff=0.06, color=CHALK,
                 commas=True):
    """An integer in the chalk font, thousands-separated by default (needs the ','
    glyph). Tighter digit spacing than `chalk_phrase`."""
    s = f"{n:,}" if commas else str(n)
    return chalk_phrase(s, height=height, stroke_width=stroke_width, buff=buff,
                        color=color)
