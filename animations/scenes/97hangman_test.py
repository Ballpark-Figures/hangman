"""SCRATCH — visual check of assets.hangman_board.hangman_drawing at 0..6 misses.

Render:  render 97a --fast
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.hangman_board import hangman_drawing


class HangmanTest(HangmanScene):

    # a : the gallows filling up, misses 0 → 6 side by side
    @subscene
    def grid(self):
        xs = [-6.6, -4.4, -2.2, 0.0, 2.2, 4.4, 6.6]
        for k, x in enumerate(xs):
            draw = hangman_drawing(k).scale(0.5).move_to([x, 0.5, 0])
            lab = crisp_text(f"{k}", font_size=22, color=ACCENT_GOLD)
            lab.next_to(draw, DOWN, buff=0.3)
            self.add(draw, lab)
