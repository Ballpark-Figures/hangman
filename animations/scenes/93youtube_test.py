"""SCRATCH — mock YouTube UI (bpkfigures.youtube_card): card, watch page, homepage.

Tried with a single real video, Jan Misali's "hangman is a weird game".

  a card  — the grid card (light + dark)
  b watch — full-screen watch page
  c home  — full-screen homepage grid (3 cols); Misali present, rest greyed out

NOTE: the view count / upload date / duration are PLACEHOLDERS — not in the repo.
Swap in the tracked analytics numbers (and a real thumbnail) when available.

Render:  render 93a --fast   /   render 93b --fast   /   render 93c --fast
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from bpkfigures.youtube_card import youtube_card, youtube_watch, youtube_home

# real title + channel; PLACEHOLDER stats until the real numbers are in: dashes for
# the meta line, and duration=None (no badge) rather than an invented time.
MISALI = dict(title="hangman is a weird game", channel="jan Misali",
              meta="— views · —", duration=None)


class YouTubeTest(HangmanScene):

    def _clear(self):
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.3)

    # a : the grid card, light and dark
    @subscene
    def card(self):
        light = youtube_card(**MISALI, width=6.4).to_edge(LEFT, buff=0.6)
        dark = youtube_card(**MISALI, width=6.4, dark=True).to_edge(RIGHT, buff=0.6)
        self.play(FadeIn(light, shift=UP * 0.2), FadeIn(dark, shift=UP * 0.2),
                  run_time=0.7)

    # b : full-screen watch page
    @subscene
    def watch(self):
        self._clear()
        page = youtube_watch(**MISALI, dark=True)
        self.play(FadeIn(page), run_time=0.6)

    # c : full-screen homepage grid — Misali present, the rest greyed out
    @subscene
    def home(self):
        self._clear()
        cells = [MISALI, None, None, None, None, None]     # 3 cols × 2 rows
        page = youtube_home(cells, cols=3, dark=False)
        self.play(FadeIn(page), run_time=0.6)
