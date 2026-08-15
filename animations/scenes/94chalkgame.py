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
from bpkfigures.chalkboard import chalkboard
from assets import game_board as gb

# ── the game (guess order from scene 95; hits derived from the word) ───────────
WORD    = "ballpark"
GUESSES = ["e", "i", "a", "l", "k", "b", "p", "r"]
MISSES  = [g for g in GUESSES if g not in WORD]   # e, i — for centred miss slots

# The fixed board layout (blanks/gallows/miss row/bubble + constants) lives in
# assets.game_board (gb) — shared with 02rules / 04greedy.


class ChalkGame(HangmanScene):
    """Play BALLPARK out on a chalkboard, one guess per subscene (c–j).

    chalkboard/CHALK from bpkfigures.chalkboard; gallows from
    assets.hangman_board.hangman_drawing (chalk-white); the guesser's speech
    bubble from bpkfigures.speech_bubble.

    _guess(i) is the recurring beat: pop the bubble on the right, write the
    letter into its blank(s) (HIT) or below the gallows (MISS), and on a miss
    draw the next hangman part, then dismiss the bubble.
    """

    # the chalkboard is the backdrop — on screen from frame 0
    def setup_scene(self):
        self.cb = chalkboard(gb.BOARD_W, gb.BOARD_H)
        self.cb.set_z_index(-10)
        self.add(self.cb)

    # ── small chalk builders (shared board layout: assets.game_board) ─────────
    def _reveal_letter(self, ch, rule):
        return gb.reveal_letter(ch, rule)

    def _miss_letter(self, ch):
        L = gb.miss_letter(ch, self.miss_slots_x[len(self.miss_row)])
        self.miss_row.add(L)
        return L

    def _bubble(self, ch):
        return gb.bubble(ch, tail="left")

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
            # multiple occurrences: write them one at a time, LEFT → RIGHT
            # (positions is ascending), each stroke-by-stroke
            for p in positions:
                L = self._reveal_letter(g, self.rules[p])
                self.play(LaggedStartMap(Create, L, lag_ratio=0.5),
                          run_time=rt_write)
        else:
            # a miss: the letter goes below the gallows, THEN the next body part
            miss = self._miss_letter(g)
            self.play(LaggedStartMap(Create, miss, lag_ratio=0.5), run_time=rt_write)
            part = self.hang_parts[self.miss_n]
            self.hang.add(part)
            self.miss_n += 1
            self.play(Create(part), run_time=rt_part)

        # 3. dismiss the bubble
        self.play(FadeOut(bub), run_time=rt_out)

    # ── setup for the blanks (owner: subscene a) ──────────────────────────────
    def _setup_blanks(self):
        self.rules = gb.build_rules(len(WORD))

    # ── setup for the gallows (owner: subscene b) ─────────────────────────────
    def _setup_gallows(self):
        # gallows on the RIGHT with parts detached (revealed one per miss); the two
        # misses (E, I) are centred under the gallows base.
        self.hang, self.hang_parts = gb.build_gallows()
        self.miss_n = 0
        self.miss_row = VGroup()               # wrong letters, chalked below
        self.miss_slots_x = gb.miss_slots(self.hang, MISSES)

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
