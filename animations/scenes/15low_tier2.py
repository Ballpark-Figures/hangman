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

Beats a–e: X establishes the views via the merged `intro_letter_views` (heatmap + n-gram
rise in BEHIND the tuck, like scene 13's P), then Z/J/Q are each a single RAPID crossfade
switch (`rapid_letter` — heatmap morphs, n-gram crossfades, big letters cross), then
recenter. (Scene 15's Script.md animation column is blank, so the beat split is a
convention choice; using the rapid "quick change" machinery from scenes 13/14 throughout.)
  a x_intro   — X fills in, tuck ↖ + copy ↙, views rise behind (`intro_letter_views`)
  b z_rapid · c j_rapid · d q_rapid — rapid crossfade switches
  e recenter  — clear views + big letter; tier list returns to CENTRE (list now COMPLETE)

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every run_time below.

Render:  render 15a --fast  (…15e)  /  render 15 sub  for the whole scene
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
                (4, "PUGMBH"), (5, "FYVWK")]         # from scenes 07–14

    def setup_scene(self):
        self.build_board(on_screen=True)            # continuation of 14 (centred)

    # ── X — establishes the views the rapid trio morphs through ──────────────────
    # a : fill X into LOW↓, tuck the list ↖ + send a copy of X ↙, with X's heatmap +
    #     n-gram RISING IN BEHIND that leftward motion (like scene 13's P)
    @subscene
    def x_intro(self):
        self.intro_letter_views(0, "x", 0.6, 1.2)

    # ── Z, J, Q : rapid crossfade switches (heatmap morphs, n-gram crossfades, letters cross) ──
    # b : rapid crossfade-switch to Z
    @subscene
    def z_rapid(self):
        self.rapid_letter(1, "z", 0.6)

    # c : rapid crossfade-switch to J
    @subscene
    def j_rapid(self):
        self.rapid_letter(2, "j", 0.6)

    # d : rapid crossfade-switch to Q
    @subscene
    def q_rapid(self):
        self.rapid_letter(3, "q", 0.6)

    # e : clear views + big letter; tier list returns to CENTRE (list now COMPLETE)
    @subscene
    def recenter(self):
        self.recenter_board(1.0)
