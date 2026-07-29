"""SCRATCH — sample animations for assets.letter_grid.

BEAT MAP
  slide_in — the grid enters from off the left edge (asset .slide_in).
  choose   — pick 'K': grid → top-left, chosen letter grows → bottom (asset .choose).
  swap     — send 'K' back, 'R' takes its place at the bottom (asset .swap).
  restore  — send 'R' back and the grid returns to its home (asset .restore).

Render:  render 96a --fast   …   render 96d --fast
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

    # c : swap — 'K' returns to the grid while 'R' takes over at the bottom
    @subscene
    def swap(self):
        self.chosen = self.grid.swap(self, "R", run_time=1.3)

    # d : restore — 'R' returns and the grid slides back to its home position
    @subscene
    def restore(self):
        self.grid.restore(self, run_time=1.3)
