"""Chalkboard — a dark-navy slate in a wooden frame, the backdrop for the
hangman gameplay mock (scenes/94chalkgame). Chalk-white marks (blanks, letters,
the gallows, the hangman) are Create/Write-animated on top so they read as
chalked on.

The colours here are asset-local (chalkboard-specific), not general style
values: navy slate, wood frame, and an off-white CHALK the scene draws with.
"""
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
