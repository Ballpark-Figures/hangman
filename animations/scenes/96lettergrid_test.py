"""SCRATCH — sample animations for assets.letter_grid.

BEAT MAP
  slide_in — the grid enters from off the left edge (asset .slide_in).
  choose   — pick a letter: grid → top-left, chosen letter grows → bottom-left
             (asset .choose).

Render:  render 96a --fast   /   render 96b --fast
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.letter_grid import letter_grid


class LetterGridTest(HangmanScene):

    # a : the grid slides in from off the left edge (asset method)
    @subscene
    def slide_in(self):
        self.grid = letter_grid()
        self.grid.to_edge(LEFT, buff=0.8).set_y(0)   # home (left side, centered)
        self.grid.slide_in(self, run_time=1.2)

    # b : choose 'K' — grid to top-left, chosen letter grows to bottom-left
    @subscene
    def choose(self):
        self.chosen = self.grid.choose(self, "K", run_time=1.3)
