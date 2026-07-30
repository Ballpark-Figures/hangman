"""MOCK — a game of hangman played out on a chalkboard (word: BALLPARK).

A dark-navy chalkboard fills the screen (backdrop, on from frame 0). Word blanks
sit on the LEFT, the gallows on the RIGHT. Everything ON the board is CHALKED on
with a drawing animation (Create for lines, Write for letters). Each guess: a
white speech bubble pops up on the right with the next letter, then that letter
is written into its blank (HIT) or below the gallows (MISS); a miss also draws
the next hangman body part.

Guess order = scene 95's BALLPARK walk (the converged len-8 uniform optimal
tree), played to completion:  e·i (the two misses) → a l k b p r (hits).

BEAT MAP
  a blanks    — draw the 8 word blanks, one at a time
  b gallows   — draw the gallows
  c guess_e   — bubble 'E' → MISS below gallows + head        (miss #1)
  d guess_i   — bubble 'I' → MISS below gallows + torso       (miss #2)
  e guess_a   — bubble 'A' → HIT, fills positions 2 & 6
  f guess_l   — bubble 'L' → HIT, fills positions 3 & 4
  g guess_k   — bubble 'K' → HIT, fills position 8
  h guess_b   — bubble 'B' → HIT, fills position 1
  i guess_p   — bubble 'P' → HIT, fills position 5
  j guess_r   — bubble 'R' → HIT, fills position 7 → BALLPARK complete

Render:  render 94a --fast   (…94j)   /   render 94 sub  for the whole game
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from bpkfigures.speech_bubble import speech_bubble
from assets.chalkboard import chalkboard, CHALK
from assets.hangman_board import hangman_drawing

# ── the game (guess order from scene 95; hits derived from the word) ───────────
WORD    = "ballpark"
GUESSES = ["e", "i", "a", "l", "k", "b", "p", "r"]

# ── layout (frame 16×9 → x-radius 8.0, y-radius 4.5) ──────────────────────────
BOARD_W, BOARD_H = 15.2, 8.4

BLANK_SLOT   = 0.50     # width of one underscore rule
BLANK_GAP    = 0.22     # gap between blanks
BLANK_CX     = -3.0     # blank-row centre x (left side of the board)
BLANK_Y      = -0.2     # blank-row baseline y
BLANK_SW     = 6.0      # chalk stroke width for the rules
LETTER_FS    = 44       # a revealed letter, sitting above its rule
LETTER_SW    = 3.0      # chalk-outline stroke: letters are DRAWN, not filled
LETTER_BUFF  = 0.12

HANG_SCALE   = 1.2                      # gallows on the RIGHT
HANG_POS     = np.array([4.3, 0.5, 0])
HANG_SW      = 6.0
MISS_FS      = 40                       # wrong letters, chalked below the gallows
MISS_SW      = 2.6
MISS_X       = 3.3                      # left edge of the miss row
MISS_Y       = -2.75
MISS_GAP     = 0.30

# the guesser is off the LEFT edge: the bubble sits upper-left, its left-pointing
# tail reaching toward the screen edge (BALLPARK's blanks sit lower, clear of it).
BUBBLE_POS   = np.array([-5.2, 2.7, 0])
BUBBLE_FS    = 56
BUBBLE_TAIL  = 1.5      # tail length — reaches the board's left edge


class ChalkGame(HangmanScene):
    """Play BALLPARK out on a chalkboard, one guess per subscene (c–j).

    chalkboard/CHALK from assets.chalkboard; gallows from
    assets.hangman_board.hangman_drawing (chalk-white); the guesser's speech
    bubble from bpkfigures.speech_bubble.

    _guess(i) is the recurring beat: pop the bubble on the right, write the
    letter into its blank(s) (HIT) or below the gallows (MISS), and on a miss
    draw the next hangman part, then dismiss the bubble.
    """

    # the chalkboard is the backdrop — on screen from frame 0
    def setup_scene(self):
        self.cb = chalkboard(BOARD_W, BOARD_H)
        self.cb.set_z_index(-10)
        self.add(self.cb)

    # ── small chalk builders ──────────────────────────────────────────────────
    def _chalk(self, ch, font_size, stroke_width):
        """A chalk-OUTLINE letter (no fill, chalk stroke) so Create draws it on
        like the gallows/blanks, rather than a filled glyph fading in."""
        t = crisp_text(ch.upper(), font_size=font_size, color=CHALK)
        t.set_fill(opacity=0.0).set_stroke(CHALK, width=stroke_width)
        return t

    def _reveal_letter(self, ch, rule):
        t = self._chalk(ch, LETTER_FS, LETTER_SW)
        t.next_to(rule, UP, buff=LETTER_BUFF)
        t.set_x(rule.get_center()[0])
        return t

    def _miss_letter(self, ch):
        t = self._chalk(ch, MISS_FS, MISS_SW)
        if len(self.miss_row):
            t.next_to(self.miss_row[-1], RIGHT, buff=MISS_GAP)
        else:
            t.move_to([MISS_X, MISS_Y, 0]).align_to([MISS_X, 0, 0], LEFT)
        self.miss_row.add(t)
        return t

    def _bubble(self, ch):
        b = speech_bubble(ch.upper(), font_size=BUBBLE_FS, tail="left",
                          tail_len=BUBBLE_TAIL)
        return b.move_to(BUBBLE_POS)

    # ── the recurring "play one guess" beat (subscenes c–j) ───────────────────
    def _guess(self, i, *, rt_bubble, rt_write, rt_part, rt_out):
        g = GUESSES[i]
        positions = [p for p, c in enumerate(WORD) if c == g]
        hit = bool(positions)

        # 1. the guesser's speech bubble pops up on the right
        bub = self._bubble(g)
        self.play(GrowFromPoint(bub, bub.tip_dot.get_center()), run_time=rt_bubble)

        # 2. the letter is chalked onto the board
        if hit:
            letters = [self._reveal_letter(g, self.rules[p]) for p in positions]
            self.play(*[Create(t) for t in letters], run_time=rt_write)
        else:
            # a miss: the letter goes below the gallows, THEN the next body part
            miss = self._miss_letter(g)
            self.play(Create(miss), run_time=rt_write)
            part = self.hang_parts[self.miss_n]
            self.hang.add(part)
            self.miss_n += 1
            self.play(Create(part), run_time=rt_part)

        # 3. dismiss the bubble
        self.play(FadeOut(bub), run_time=rt_out)

    # ── setup for the blanks (owner: subscene a) ──────────────────────────────
    def _setup_blanks(self):
        n = len(WORD)
        total = n * BLANK_SLOT + (n - 1) * BLANK_GAP
        x0 = BLANK_CX - total / 2 + BLANK_SLOT / 2
        self.rules = VGroup()
        for k in range(n):
            x = x0 + k * (BLANK_SLOT + BLANK_GAP)
            self.rules.add(Line([x - BLANK_SLOT / 2, BLANK_Y, 0],
                                [x + BLANK_SLOT / 2, BLANK_Y, 0],
                                color=CHALK, stroke_width=BLANK_SW))

    # ── setup for the gallows (owner: subscene b) ─────────────────────────────
    def _setup_gallows(self):
        # build with ALL parts so scale/move places them too, THEN detach the
        # parts (revealed one per miss); the gallows stays, drawn in subscene b.
        full = hangman_drawing(6, color=CHALK, stroke_width=HANG_SW)
        full.scale(HANG_SCALE).move_to(HANG_POS)
        self.hang_parts = list(full.parts)     # 6 body parts, in draw order
        for p in self.hang_parts:
            full.remove(p)
        self.hang = full
        self.miss_n = 0
        self.miss_row = VGroup()               # wrong letters, chalked below

    # a : draw the 8 word blanks, one at a time
    @subscene
    def blanks(self):
        self._setup_blanks()
        self.play(LaggedStartMap(Create, self.rules, lag_ratio=0.8), run_time=2.2)

    # b : draw the gallows on the right
    @subscene
    def gallows(self):
        self._setup_gallows()
        self.play(LaggedStartMap(Create, self.hang.gallows, lag_ratio=0.6),
                  run_time=1.6)

    # c : 'E' → MISS below gallows + head (miss #1)
    @subscene
    def guess_e(self):
        self._guess(0, rt_bubble=0.7, rt_write=0.9, rt_part=0.7, rt_out=0.4)

    # d : 'I' → MISS below gallows + torso (miss #2)
    @subscene
    def guess_i(self):
        self._guess(1, rt_bubble=0.7, rt_write=0.9, rt_part=0.7, rt_out=0.4)

    # e : 'A' → HIT, positions 2 & 6
    @subscene
    def guess_a(self):
        self._guess(2, rt_bubble=0.7, rt_write=0.9, rt_part=0.7, rt_out=0.4)

    # f : 'L' → HIT, positions 3 & 4
    @subscene
    def guess_l(self):
        self._guess(3, rt_bubble=0.7, rt_write=0.9, rt_part=0.7, rt_out=0.4)

    # g : 'K' → HIT, position 8
    @subscene
    def guess_k(self):
        self._guess(4, rt_bubble=0.7, rt_write=0.9, rt_part=0.7, rt_out=0.4)

    # h : 'B' → HIT, position 1
    @subscene
    def guess_b(self):
        self._guess(5, rt_bubble=0.7, rt_write=0.9, rt_part=0.7, rt_out=0.4)

    # i : 'P' → HIT, position 5
    @subscene
    def guess_p(self):
        self._guess(6, rt_bubble=0.7, rt_write=0.9, rt_part=0.7, rt_out=0.4)

    # j : 'R' → HIT, position 7 → BALLPARK complete
    @subscene
    def guess_r(self):
        self._guess(7, rt_bubble=0.7, rt_write=0.9, rt_part=0.7, rt_out=0.4)
