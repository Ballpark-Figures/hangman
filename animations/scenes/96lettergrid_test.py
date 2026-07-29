"""SCRATCH — sample entrance for assets.letter_grid: slide in from the left.

Render:  render 96a --fast
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.letter_grid import letter_grid


class LetterGridTest(HangmanScene):

    # a : the letter grid slides in from off the left edge to its resting spot
    @subscene
    def slide_in(self):
        self.grid = letter_grid()
        self.grid.to_edge(LEFT, buff=0.8).set_y(0)   # resting position (left side)
        self.grid.shift(LEFT * 6)                     # start fully off the left edge
        self.play(self.grid.animate.shift(RIGHT * 6), run_time=1.2)
