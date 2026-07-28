"""SCRATCH — assets.hangman_board.hangman_drawing checks.

BEAT MAP
  draw — line-drawing (Create) animation: gallows, then each body part one at
         a time (head → torso → arm → arm → leg → leg).
  grid — static geometry check: misses 0 → 6 side by side.

Render:  render 97a --fast   (the animation)   /   render 97b --fast  (the grid)
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.hangman_board import hangman_drawing


class HangmanTest(HangmanScene):

    # a : draw the hangman with a line-drawing animation, one part at a time
    @subscene
    def draw(self):
        d = hangman_drawing(0)                       # gallows added; .parts all built
        # one VGroup for layout so scale/position moves the not-yet-drawn parts too
        self.figure = VGroup(d.gallows, *d.parts).scale(1.5).move_to(ORIGIN)

        self.play(Create(self.figure[0]), run_time=1.0)   # the gallows
        for part in self.figure[1:]:                      # 6 body parts, in order
            self.play(Create(part), run_time=0.5)

    # b : the gallows filling up, misses 0 → 6 side by side (static check)
    @subscene
    def grid(self):
        for m in list(self.mobjects):    # drop the figure carried from subscene a
            self.remove(m)
        xs = [-6.6, -4.4, -2.2, 0.0, 2.2, 4.4, 6.6]
        for k, x in enumerate(xs):
            fig = hangman_drawing(k).scale(0.5).move_to([x, 0.5, 0])
            lab = crisp_text(f"{k}", font_size=22, color=ACCENT_GOLD)
            lab.next_to(fig, DOWN, buff=0.3)
            self.add(fig, lab)
