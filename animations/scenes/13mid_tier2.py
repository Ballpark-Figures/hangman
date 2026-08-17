"""SCENE 13 — the MID↓ tier (P, U, G, M, B, H), letter by letter.

Built on the shared `TierLetterScene` base (assets/tier_letter_scene.py). Back-to-back
continuation of scene 12: opens on the named tier list CENTRED (TOP + HIGH + MID↑
filled), works the MID↓ tier, and recenters at the end. No common-uses (like 96).

TWO twists from the usual tier scene:
  • PRESENTATION order is P, M, B (a shared "common at the start, rare at the end"
    profile — script row 13) shown in RAPID SUCCESSION, THEN U, G, H as normal. The
    tier list still LISTS them in slot order PUGMBH, so P/M/B fill slots 0/3/4 and
    U/G/H fill the gaps 1/2/5 afterwards.
  • The rapid trio CROSSFADES its views: the heatmap morphs + the n-gram crossfades
    to the next letter in place (`rapid_letter`), instead of the usual remove-and-rise.

Beats:
  a P intro     fill P into MID↓; tier list → top-left; copy of P → ↙
  b P views     P's heatmap + n-gram (establishes the views the rapid trio morphs)
  c M rapid     crossfade-switch to M (heatmap morphs, n-gram crossfades)
  d B rapid     crossfade-switch to B
  e U intro     as normal: remove B's views, B's copy returns AS U fades in, copy → ↙
  f U heatmap · g U ngram
  h G intro (normal) · i G heatmap · j G ngram
  k H intro (normal) · l H heatmap · m H ngram
  n recenter    clear views + big letter; tier list returns to CENTRE (for next scene)

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every run_time below;
the rapid-trio ones (c/d, and P's quick views in b) especially.

Render:  render 13a --fast  (…13n)  /  render 13 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.tier_letter_scene import TierLetterScene


class Scene13(TierLetterScene):
    """MID↓ tier PUGMBH, presented P/M/B (rapid) then U/G/H. See docstring for beats."""

    TIER_IDX = 4
    LETTERS  = ["p", "u", "g", "m", "b", "h"]        # tier/slot order = TIER_LETTERS[4]
    FILLED   = [(0, "EIA"), (1, "SR"), (2, "TNO"), (3, "LDC")]   # from scenes 07–12

    def setup_scene(self):
        self.build_board(on_screen=True)            # continuation of 12 (centred)

    # ── P, M, B : rapid succession (crossfade views) ─────────────────────────────
    # a : fill P (slot 0) into MID↓, tuck the list ↖, send a copy of P ↙
    @subscene
    def p_intro(self):
        self.intro_letter(0, 1.2)

    # b : P's heatmap + n-gram — establishes the views the rapid trio morphs through
    @subscene
    def p_views(self):
        self.show_heat("p", 0.9)
        self.add_ngram("p", 0.7)

    # c : rapid crossfade-switch to M (slot 3) — heatmap morphs, n-gram crossfades
    @subscene
    def m_rapid(self):
        self.rapid_letter(3, "m", 0.7, 0.6)

    # d : rapid crossfade-switch to B (slot 4)
    @subscene
    def b_rapid(self):
        self.rapid_letter(4, "b", 0.7, 0.6)

    # ── U, G, H : as normal ──────────────────────────────────────────────────────
    # e : remove B's views, B's copy returns AS U (slot 1) fades in, then a copy of U ↙
    @subscene
    def u_intro(self):
        self.advance_letter(1, 0.9, 1.0)

    # f : heatmaps for U
    @subscene
    def u_heat(self):
        self.show_heat("u", 1.0)

    # g : add the n-gram view for U
    @subscene
    def u_ngram(self):
        self.add_ngram("u", 0.8)

    # h : G's turn (slot 2), as normal
    @subscene
    def g_intro(self):
        self.advance_letter(2, 0.9, 1.0)

    # i : heatmaps for G
    @subscene
    def g_heat(self):
        self.show_heat("g", 1.0)

    # j : add the n-gram view for G
    @subscene
    def g_ngram(self):
        self.add_ngram("g", 0.8)

    # k : H's turn (slot 5), as normal
    @subscene
    def h_intro(self):
        self.advance_letter(5, 0.9, 1.0)

    # l : heatmaps for H
    @subscene
    def h_heat(self):
        self.show_heat("h", 1.0)

    # m : add the n-gram view for H
    @subscene
    def h_ngram(self):
        self.add_ngram("h", 0.8)

    # n : clear views + big letter; tier list returns to CENTRE (for the next scene)
    @subscene
    def recenter(self):
        self.recenter_board(1.0)
