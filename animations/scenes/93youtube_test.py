"""SCRATCH — mock YouTube UI (bpkfigures.youtube_card): card, watch page, homepage.

Tried with a single real video, Jan Misali's "hangman is a weird game".

  a card     — the grid card (light + dark, side by side)
  b watch_lt — full-screen watch page (light)
  c watch_dk — full-screen watch page (dark)
  d home_lt  — full-screen homepage grid (3 cols, light); Misali present, rest greyed
  e home_dk  — full-screen homepage grid (dark)

These are just a SERIES OF IMAGES with no animation between them, so each frame is
a `@still` subscene: the framework renders it from a CLEAN, EMPTY frame (no
carry-over, no snapshot) and emits a still PNG (manim `-s`) under
`media/images/93youtube_test/<res>/` — not a video. Build each with `self.add`.

Render:  render 93 all   (one PNG per subscene)   /   render 93a --fast
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from bpkfigures.youtube_card import youtube_card, youtube_watch, youtube_home
from assets.youtube_data import get as yt_get

# Jan Misali's "hangman is a weird game" — SOURCED from the analytics DB via the
# committed youtube_cache.json (title/channel/views/duration). To refresh the
# numbers: run assets/youtube_data.py with the analytics venv, then re-render.
MISALI = yt_get("hangman")


class YouTubeTest(HangmanScene):

    # a : the grid card, light and dark
    @still
    def card(self):
        light = youtube_card(**MISALI, width=6.4).to_edge(LEFT, buff=0.6)
        dark = youtube_card(**MISALI, width=6.4, dark=True).to_edge(RIGHT, buff=0.6)
        self.add(light, dark)

    # b : full-screen watch page (light)
    @still
    def watch_lt(self):
        self.add(youtube_watch(**MISALI, dark=False))

    # c : full-screen watch page (dark)
    @still
    def watch_dk(self):
        self.add(youtube_watch(**MISALI, dark=True))

    # d : full-screen homepage grid (light) — Misali present, the rest greyed out
    @still
    def home_lt(self):
        cells = [MISALI, None, None, None, None, None]     # 3 cols × 2 rows
        self.add(youtube_home(cells, cols=3, dark=False))

    # e : full-screen homepage grid (dark)
    @still
    def home_dk(self):
        cells = [MISALI, None, None, None, None, None]     # 3 cols × 2 rows
        self.add(youtube_home(cells, cols=3, dark=True))
