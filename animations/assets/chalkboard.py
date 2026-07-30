"""Chalkboard — a dark-navy slate in a wooden frame, the backdrop for the
hangman gameplay mock (scenes/94chalkgame). Chalk-white marks (blanks, letters,
the gallows, the hangman) are Create/Write-animated on top so they read as
chalked on.

The colours here are asset-local (chalkboard-specific), not general style
values: navy slate, wood frame, and an off-white CHALK the scene draws with.

``chalk_letter`` builds a capital as a set of hand-drawn STROKES (an E is four
lines: top, middle, bottom, left), so ``Create`` writes it stroke-by-stroke like
a hand — unlike a font glyph, whose outline only traces the letter's silhouette.
Only the letters the hangman mock needs are defined (BALLPARK + the misses).
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
    "E": [(False, [(-0.28, 0.50), (-0.28, -0.50)]),
          (False, [(-0.28, 0.50), (0.28, 0.50)]),
          (False, [(-0.28, 0.00), (0.20, 0.00)]),
          (False, [(-0.28, -0.50), (0.28, -0.50)])],
    "I": [(False, [(0.0, 0.50), (0.0, -0.50)]),
          (False, [(-0.16, 0.50), (0.16, 0.50)]),
          (False, [(-0.16, -0.50), (0.16, -0.50)])],
    "K": [(False, [(-0.28, 0.50), (-0.28, -0.50)]),
          (False, [(-0.28, 0.02), (0.30, 0.50)]),
          (False, [(-0.28, 0.02), (0.32, -0.50)])],
    "L": [(False, [(-0.28, 0.50), (-0.28, -0.50)]),
          (False, [(-0.28, -0.50), (0.28, -0.50)])],
    "P": [(False, [(-0.28, 0.50), (-0.28, -0.50)]),
          (True,  [(-0.28, 0.50), (0.16, 0.45), (0.32, 0.25),
                   (0.16, 0.05), (-0.28, 0.04)])],
    "R": [(False, [(-0.28, 0.50), (-0.28, -0.50)]),
          (True,  [(-0.28, 0.50), (0.16, 0.45), (0.32, 0.25),
                   (0.16, 0.05), (-0.28, 0.04)]),
          (False, [(-0.06, 0.04), (0.32, -0.50)])],
}


def chalk_letter(ch, *, height=0.6, stroke_width=4.5, color=CHALK):
    """A capital drawn as ordered chalk STROKES, centred on the origin.

    Returns a VGroup whose submobjects are the strokes in writing order — animate
    with ``LaggedStartMap(Create, letter, lag_ratio=…)`` to write it on. ``height``
    is the cap height in scene units (width follows the glyph, ~0.6·height)."""
    ch = ch.upper()
    if ch not in _ALPHABET:
        raise ValueError(f"chalk_letter: no strokes defined for {ch!r}")
    letter = VGroup()
    for smooth, pts in _ALPHABET[ch]:
        p3 = [np.array([x * height, y * height, 0.0]) for x, y in pts]
        stroke = VMobject(stroke_color=color, stroke_width=stroke_width)
        if smooth:
            stroke.set_points_smoothly(p3)
        else:
            stroke.set_points_as_corners(p3)
        letter.add(stroke)
    return letter
