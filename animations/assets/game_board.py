"""Shared hangman game board — the FIXED-LAYOUT blanks + gallows + miss row +
speech bubble every gameplay scene draws on (02rules, 94chalkgame, 04greedy).

One fixed arrangement on the chalkboard (15.2×8.4 slate in the 16×9 frame):
  • word blanks centred on the LEFT   (BLANK_CX, BLANK_Y)
  • the gallows on the RIGHT           (HANG_POS, scaled HANG_SCALE)
  • the wrong-guess tally centred under the gallows base (MISS_Y)
  • the guesser's speech bubble growing from the LEFT edge (BUBBLE_TIP, tail=left)
Every mark is CHALK — `chalk_letter` strokes and `hangman_drawing` — so a scene
writes them on with Create/Write.

Promoted from the byte-identical inline copies that lived in 02rules/94chalkgame;
these are stateless BUILDERS + the shared constants, so a scene keeps its own
`self.rules`/`self.hang`/… handles (and its snapshots) but stops re-deriving the
layout. 04greedy adds a variable word length + a bottom-left bar graph on top.
"""
import numpy as np
from manim import *

from bpkfigures.speech_bubble import speech_bubble
from bpkfigures.chalkboard import chalk_letter, CHALK
from assets.hangman_board import hangman_drawing

# ── layout constants (verbatim from 02rules / 94chalkgame) ────────────────────
BOARD_W, BOARD_H = 15.2, 8.4

BLANK_SLOT  = 0.50     # width of one underscore rule
BLANK_GAP   = 0.22     # gap between blanks
BLANK_CX    = -3.0     # blank-row centre x (left side of the board)
BLANK_Y     = -0.38    # rule baseline; a filled blank is vertically centred at y=0
BLANK_SW    = 6.0      # chalk stroke width for the rules
LETTER_H    = 0.62     # cap height of a revealed letter (drawn as strokes)
LETTER_SW   = 4.5      # chalk stroke width for a revealed letter
LETTER_BUFF = 0.14

HANG_SCALE  = 1.2                          # gallows on the RIGHT
HANG_POS    = np.array([4.3, 0.5, 0])
HANG_SW     = 6.0
MISS_H      = 0.50                          # wrong letters, chalked below the gallows
MISS_SW     = 4.0
MISS_Y      = -2.75                         # miss-row baseline (centred under gallows)
MISS_GAP    = 0.34

# the guesser is off the LEFT edge: the tail TIP sits at the screen edge and the
# bubble grows from there. Anchored by the tip — NOT move_to (its group-bbox
# centring would pull the tail inward).
BUBBLE_TIP  = np.array([-7.9, 2.4, 0])
BUBBLE_FS   = 56


def build_rules(length, *, cx=BLANK_CX, y=BLANK_Y, slot=BLANK_SLOT, gap=BLANK_GAP,
                stroke_width=BLANK_SW, color=CHALK):
    """A row of `length` underscore rules, centred at `cx` on baseline `y`.
    Longer words (04) pass a smaller slot/gap; the row stays centred at `cx`."""
    total = length * slot + (length - 1) * gap
    x0 = cx - total / 2 + slot / 2
    rules = VGroup()
    for k in range(length):
        x = x0 + k * (slot + gap)
        rules.add(Line([x - slot / 2, y, 0], [x + slot / 2, y, 0],
                       color=color, stroke_width=stroke_width))
    return rules


def build_gallows(*, scale=HANG_SCALE, pos=HANG_POS, color=CHALK,
                  stroke_width=HANG_SW):
    """The gallows placed on the RIGHT with its 6 body parts DETACHED (revealed
    one per miss). Returns ``(container, parts)`` where ``container.gallows`` is
    the gallows VGroup and ``parts`` is the 6 body-part mobjects in draw order."""
    full = hangman_drawing(6, color=color, stroke_width=stroke_width)
    full.scale(scale).move_to(pos)
    parts = list(full.parts)
    for p in parts:
        full.remove(p)
    return full, parts


def reveal_letter(ch, rule, *, color=CHALK, height=LETTER_H, stroke_width=LETTER_SW,
                  buff=LETTER_BUFF):
    """A chalk capital sitting above its `rule` (a HIT written into its blank)."""
    L = chalk_letter(ch, height=height, stroke_width=stroke_width, color=color)
    L.next_to(rule, UP, buff=buff)
    L.set_x(rule.get_center()[0])
    return L


def miss_slots(container, letters=None, *, capacity=6):
    """Centred x-positions for the wrong-guess tally under the gallows base.

    CONVENTION for gameplay scenes: call WITHOUT `letters` so misses drop into the
    fixed `capacity`-slot row (default 6 — the full width scene 2 uses). A miss then
    lands in its absolute slot regardless of how many misses the game actually gets,
    so the layout never gives away the eventual miss count. Only pass the ACTUAL miss
    letters when you deliberately want the finished row centred by its real glyph
    widths (e.g. scene 2, which happens to have all 6). Measured off the gallows base
    so it tracks the gallows if it moves."""
    gallows_cx = container.gallows[0].get_center()[0]
    chars = list(letters) if letters else ["n"] * capacity
    tmpl = VGroup(*[chalk_letter(c, height=MISS_H, stroke_width=MISS_SW, color=CHALK)
                    for c in chars])
    tmpl.arrange(RIGHT, buff=MISS_GAP).move_to([gallows_cx, MISS_Y, 0])
    return [m.get_center()[0] for m in tmpl]


def miss_letter(ch, x, *, color=CHALK):
    """A wrong-guess chalk letter dropped into miss slot centred at `x`."""
    L = chalk_letter(ch, height=MISS_H, stroke_width=MISS_SW, color=color)
    L.move_to([x, MISS_Y, 0])
    return L


def bubble(ch, *, font_size=BUBBLE_FS, tip=BUBBLE_TIP, **kwargs):
    """The guesser's speech bubble — the house pill look (speech_bubble defaults:
    warm CARD_FILL capsule, soft outline, navy ink, short left tail). Its tail tip
    is anchored at `tip` (off the left edge) so it grows from off-screen via
    GrowFromPoint(b, b.tip_dot...). Pass any speech_bubble kwarg to override."""
    b = speech_bubble(ch.upper(), font_size=font_size, **kwargs)
    b.shift(np.array(tip) - b.tip_dot.get_center())
    return b
