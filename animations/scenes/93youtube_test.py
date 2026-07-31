"""SCRATCH — mock YouTube thumbnail card (bpkfigures.youtube_card).

A light-mode card (left) and a dark-mode card (right) to compare. All text is
placeholder; the thumbnail is a grey play-button box (drop a real still in via the
`thumbnail=` arg, or a live clip in DaVinci).

Render:  render 93a --fast
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from bpkfigures.youtube_card import youtube_card


class YouTubeTest(HangmanScene):

    @subscene
    def card(self):
        light = youtube_card(
            title="The Optimal Hangman Strategy (and the math behind it)",
            channel="Ballpark Figures",
            meta="1.2M views · 3 days ago",
            duration="17:42",
            width=6.4,
        )
        dark = youtube_card(
            title="The Optimal Hangman Strategy (and the math behind it)",
            channel="Ballpark Figures",
            meta="1.2M views · 3 days ago",
            duration="17:42",
            width=6.4, dark=True,
        )
        light.to_edge(LEFT, buff=0.6)
        dark.to_edge(RIGHT, buff=0.6)
        self.play(FadeIn(light, shift=UP * 0.2), FadeIn(dark, shift=UP * 0.2),
                  run_time=0.7)
