"""SCENE 07 — the TOP TIER of the tier list, letter by letter (E, I, A).

A continuation of scene 06 (the named tier list is already centred on screen, top
tier empty). Built on the shared `TierLetterScene` base (assets/tier_letter_scene.py)
— the tier-list letter mechanic + heatmap/n-gram/common-uses views live there; this
file only sets the tier + letters and lays out the beats.

Unlike the other tier scenes, the top tier HAS a common-uses view (script row 13),
leading each letter with a list of BLANK first-guess boards over the length range that
letter owns as the best first guess (E len 5–11, I len 12–20, A len 1–4 — sourced; see
hangman CLAUDE.md "Common uses view"). Ends on a blank screen (a talking head follows).

Script row 13, split on '—' → 12 beats a–l (voiceover ↔ animation zip 1:1) + close:
  a E intro     fill E; tier list → top-left; copy of E → ↙
  b E common    common-uses — blank first-guess words, lengths 5–11
  c E heatmap   position-frequency heatmaps
  d E ngram     add the n-gram view
  e I intro     E's copy returns AS I fades in, then a copy of I → ↙
  f I common    common-uses, lengths 12–20
  g I heatmap   heatmaps
  h I ngram     add the n-gram view
  i I common2   common-uses — blank word + a crimson missed E, lengths 7–11
  j A intro+cu  A's turn, then common-uses lengths 1–4 (combined beat)
  k A heat+ng   heatmaps, then add the n-gram view (combined beat)
  l A common2   common-uses — words ending in E (E revealed), lengths 5–9
  m close       fade everything out — ends blank

The two common2 beats (i, l) show DEEPER game states (I_AFTER_E / A_ENDS_E), each
VERIFIED against letter_analysis's guesses_of_letter at optimal/uniform.

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every run_time below.

Render:  render 07a --fast  (…07m)  /  render 07 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.tier_letter_scene import TierLetterScene

# each top-tier letter and the best-first-guess length range it owns (partitions 1–20)
TOP = [("e", range(5, 12)), ("i", range(12, 21)), ("a", range(1, 5))]

# The two "return to common-uses" beats (script beats i, l) show DEEPER game states —
# each a (length, board, missed) spec fed to show_common. Both are the level-1
# (2nd-guess) states VERIFIED against letter_analysis's guesses_of_letter table at
# STRATEGY=optimal / WEIGHTING=uniform (10/10 present; see scene-07 provenance):
#   I after E misses on mid-length words -> blank board + a crimson missed E, lengths 7–11
I_AFTER_E = [(L, "_" * L, ["e"]) for L in (7, 8, 9, 10, 11)]
#   A as a good 2nd vowel in words ending in E -> E revealed at the last slot, no miss, 5–9
A_ENDS_E  = [(L, "_" * (L - 1) + "e", []) for L in (5, 6, 7, 8, 9)]


class Scene07(TierLetterScene):
    """Top tier E/I/A, continuing scene 06. See module docstring for the beat map."""

    TIER_IDX = 0
    LETTERS  = [ch for ch, _ in TOP]                # e, i, a (revealed one per beat)
    FILLED   = []                                   # top tier IS the current tier

    def setup_scene(self):
        self.build_board(on_screen=True)            # continuation of 06 (centred)

    # ── E ───────────────────────────────────────────────────────────────────────
    # a : fill E, tuck the list ↖, send a copy of E ↙
    @subscene
    def e_intro(self):
        self.intro_letter(0, 1.2)

    # b : common-uses — blank first-guess words, lengths 5–11
    @subscene
    def e_common(self):
        self.show_common(TOP[0][1], 0.9)

    # c : swap common-uses out for the heatmaps
    @subscene
    def e_heat(self):
        self.show_heat("e", 1.0)

    # d : add the n-gram view
    @subscene
    def e_ngram(self):
        self.add_ngram("e", 0.8)

    # ── I ───────────────────────────────────────────────────────────────────────
    # e : E's copy returns AS I fades in, then a copy of I → ↙
    @subscene
    def i_intro(self):
        self.advance_letter(1, 0.9, 1.0)

    # f : common-uses, lengths 12–20
    @subscene
    def i_common(self):
        self.show_common(TOP[1][1], 0.9)

    # g : swap to the heatmaps
    @subscene
    def i_heat(self):
        self.show_heat("i", 1.0)

    # h : add the n-gram view
    @subscene
    def i_ngram(self):
        self.add_ngram("i", 0.8)

    # i : return to common-uses — blank word + a crimson missed E, lengths 7–11
    #     (I is the top guess on mid-length words AFTER the E misses)
    @subscene
    def i_common2(self):
        self.show_common(I_AFTER_E, 0.9)

    # ── A ───────────────────────────────────────────────────────────────────────
    # j : A's turn, then common-uses lengths 1–4
    @subscene
    def a_intro(self):
        self.advance_letter(2, 0.9, 1.0)
        self.show_common(TOP[2][1], 0.9)

    # k : swap to the heatmaps, then add the n-gram view
    @subscene
    def a_heat(self):
        self.show_heat("a", 1.0)
        self.add_ngram("a", 0.8)

    # l : return to common-uses — words ending in E (E revealed, no misses), lengths 5–9
    #     (A is a good second vowel in words ending in E)
    @subscene
    def a_common2(self):
        self.show_common(A_ENDS_E, 0.9)

    # m : clear the whole screen for the next scene (ends blank)
    @subscene
    def close(self):
        self.close_all(0.8)
