"""SCENE 15 — the LOW↓ tier (X, Z, J, Q), letter by letter.

Built on the shared `TierLetterScene` base (assets/tier_letter_scene.py). Back-to-back
continuation of scene 14 and the LAST tier: opens on the named tier list CENTRED (all
tiers down through LOW↑ filled), works the LOW↓ tier (TIER_LETTERS[6] = "XZJQ") with
heatmap + n-gram views per letter (no common-uses, like 96). The row-22 voiceover walks
them X, Z, J, Q — which IS the tier order. Recenters at the end, leaving the COMPLETE
tier list centred for the "how to use it" scene that follows.

START-MODE ASSUMPTION (flag): continuation of 14 (centred). Flip to a blank start
(`build_board(on_screen=False)` + an `establish` beat) if something clears the screen
between 14 and 15.

Beats a–m: X/Z/J/Q each as intro → heatmap → n-gram, then recenter.

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every run_time below.

Render:  render 15a --fast  (…15m)  /  render 15 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.tier_letter_scene import TierLetterScene


class Scene15(TierLetterScene):
    """LOW↓ tier X/Z/J/Q, continuing scene 14. See docstring for the beat map."""

    TIER_IDX = 6
    LETTERS  = ["x", "z", "j", "q"]                  # = TIER_LETTERS[6]
    FILLED   = [(0, "EIA"), (1, "SR"), (2, "TNO"), (3, "LDC"),
                (4, "PUGMBH"), (5, "FYVKW")]         # from scenes 07–14

    def setup_scene(self):
        self.build_board(on_screen=True)            # continuation of 14 (centred)

    # ── X ───────────────────────────────────────────────────────────────────────
    # a : fill X into LOW↓, tuck the list ↖, send a copy of X ↙
    @subscene
    def x_intro(self):
        self.intro_letter(0, 1.2)

    # b : position-frequency heatmaps
    @subscene
    def x_heat(self):
        self.show_heat("x", 1.0)

    # c : add the n-gram view
    @subscene
    def x_ngram(self):
        self.add_ngram("x", 0.8)

    # ── Z ───────────────────────────────────────────────────────────────────────
    # d : Z's turn
    @subscene
    def z_intro(self):
        self.advance_letter(1, 0.9, 1.0)

    # e : heatmaps for Z
    @subscene
    def z_heat(self):
        self.show_heat("z", 1.0)

    # f : add the n-gram view for Z
    @subscene
    def z_ngram(self):
        self.add_ngram("z", 0.8)

    # ── J ───────────────────────────────────────────────────────────────────────
    # g : J's turn
    @subscene
    def j_intro(self):
        self.advance_letter(2, 0.9, 1.0)

    # h : heatmaps for J
    @subscene
    def j_heat(self):
        self.show_heat("j", 1.0)

    # i : add the n-gram view for J
    @subscene
    def j_ngram(self):
        self.add_ngram("j", 0.8)

    # ── Q ───────────────────────────────────────────────────────────────────────
    # j : Q's turn
    @subscene
    def q_intro(self):
        self.advance_letter(3, 0.9, 1.0)

    # k : heatmaps for Q
    @subscene
    def q_heat(self):
        self.show_heat("q", 1.0)

    # l : add the n-gram view for Q
    @subscene
    def q_ngram(self):
        self.add_ngram("q", 0.8)

    # m : clear views + big letter; tier list returns to CENTRE (list now COMPLETE)
    @subscene
    def recenter(self):
        self.recenter_board(1.0)
