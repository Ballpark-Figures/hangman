"""SCRATCH — letter-view animations: the letter grid + per-letter position heatmaps.

BEAT MAP
  slide_in — the grid enters from off the left edge (asset .slide_in).
  choose   — pick 'K': grid → top-left, chosen letter grows → bottom (asset .choose).
  heat     — fade in 'K's length-2..10 position heatmaps in the middle.
  swap     — send 'K' back, 'R' takes its place; the heatmaps update K → R.
  restore  — fade the heatmaps out and send 'R' back, grid returns home.

Render:  render 96a --fast   …   render 96e --fast
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.letter_grid import letter_grid
from assets.letter_heatmaps import letter_heatmaps


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

    # c : fade in 'K's per-length position heatmaps in the horizontal middle
    @subscene
    def heat(self):
        self.heat = letter_heatmaps("k")
        self.play(FadeIn(self.heat), run_time=0.8)

    # d : swap — 'K' returns to the grid while 'R' takes over; heatmaps track it
    @subscene
    def swap(self):
        self.play(FadeOut(self.heat), run_time=0.4)
        self.chosen = self.grid.swap(self, "R", run_time=1.3)
        self.heat = letter_heatmaps("r")
        self.play(FadeIn(self.heat), run_time=0.5)

    # e : restore — heatmaps fade out, 'R' returns, the grid slides back home
    @subscene
    def restore(self):
        self.play(FadeOut(self.heat), run_time=0.4)
        self.heat = None
        self.grid.restore(self, run_time=1.3)
