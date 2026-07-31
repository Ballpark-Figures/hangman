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

# Jan Misali's "hangman is a weird game" — SOURCED from the analytics DB (pinned
# video le5uGqHKll8, latest sample 2026-07-31): 7,325,604 views, published
# 2020-04-24, 1170s runtime. Shown YouTube-style (7.3M / 6 years / 19:30).
MISALI = dict(title="hangman is a weird game", channel="jan Misali",
              meta="7.3M views · 6 years ago", duration="19:30")


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
