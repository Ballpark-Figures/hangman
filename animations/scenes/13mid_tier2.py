"""SCENE 13 — the MID↓ tier (P, U, G, M, B, H), letter by letter.

Built on the shared `TierLetterScene` base (assets/tier_letter_scene.py). Back-to-back
continuation of scene 12: opens on the named tier list CENTRED (TOP + HIGH + MID↑
filled), works the MID↓ tier, and recenters at the end. The U and G sections each carry
a common-uses beat (per the user's request); the rest are heatmap + n-gram only (like 96).

TWO twists from the usual tier scene:
  • PRESENTATION order is P, M, B (a shared "common at the start, rare at the end"
    profile — script row 13) shown in RAPID SUCCESSION, THEN U, G, H as normal. The
    tier list still LISTS them in slot order PUGMBH, so P/M/B fill slots 0/3/4 and
    U/G/H fill the gaps 1/2/5 afterwards.
  • The rapid trio CROSSFADES its views: the heatmap morphs + the n-gram crossfades
    to the next letter in place (`rapid_letter`), instead of the usual remove-and-rise.

Beats:
  a P intro     fill P into MID↓; tier list → top-left + copy of P → ↙, with P's heatmap
                + n-gram RISING IN BEHIND that leftward motion (establishes the views the
                rapid trio morphs through) — `intro_letter_views`
  b M rapid     crossfade-switch to M (heatmap morphs, n-gram crossfades)
  c B rapid     crossfade-switch to B
  d U intro     as normal: remove B's views, B's copy returns AS U fades in, copy → ↙
  e U heatmap · f U ngram · g U common (top 6 table cases for U, U_COMMON)
  h G intro (normal) · i G heatmap · j G ngram · k G common (top 6 "in_" cases, G_COMMON)
  l H intro (normal) · m H heatmap · n H ngram
  o recenter    clear views + big letter; tier list returns to CENTRE (for next scene)

The two common-uses beats (g, k) show real (level ≥ 1) game states SOURCED from
letter_analysis.ipynb's `guesses_of_letter_all_lengths(<letter>)` at STRATEGY=optimal /
WEIGHTING=uniform, n_words descending; reproduced by `math/common_uses_scene13.py`. U is
our 4th/5th vowel choice, so every U state already has the other vowels (a/e/i/o) in its
missed tally; G is restricted to boards ending in "in_" (the G completes an ING at the
word's end — G's signature use), the TOP 6 after that filter.

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every run_time below;
the merged intro-with-views (a) and the rapid-trio switches (b/c) especially.

Render:  render 13a --fast  (…13o)  /  render 13 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.tier_letter_scene import TierLetterScene

# U's common-uses beat pulls states straight from letter_analysis.ipynb's
# guesses_of_letter_all_lengths('u') at STRATEGY=optimal / WEIGHTING=uniform, sorted
# by n_words DESCENDING (the notebook's display sort). "top 6 cases" = .head(6).
# SOURCED + reproducible via math/common_uses_scene13.py (prints these rows).
# Each spec is (length, board, missed) — U is our 4th/5th vowel choice, so every
# state already has the other vowels (a/e/i/o) missed (hence the tallies).
U_COMMON = [
    (5, "_____",  ["a", "e", "i", "o"]),
    (4, "____",   ["a", "e", "i", "o"]),
    (6, "_____e", ["a", "i"]),
    (6, "______", ["a", "e", "i", "o"]),
    (3, "___",    ["a", "e", "i", "o"]),
    (6, "___i__", ["a", "e", "o"]),
]

# G's common-uses beat, same pipeline, RESTRICTED to states whose board ENDS IN "in_"
# (the guessed G completes an ING at the word's end) — G's signature use, per the
# voiceover. top 6 by n_words after that filter; reproduced by common_uses_scene13.py
# (dump("g", 6, board_suffix="in_")).
G_COMMON = [
    (7, "____in_",   ["e"]),
    (8, "_____in_",  ["e"]),
    (9, "______in_", ["e"]),
    (7, "_e__in_",   []),
    (7, "_i__in_",   ["e"]),
    (8, "__e__in_",  []),
]


class Scene13(TierLetterScene):
    """MID↓ tier PUGMBH, presented P/M/B (rapid) then U/G/H. See docstring for beats."""

    TIER_IDX = 4
    LETTERS  = ["p", "u", "g", "m", "b", "h"]        # tier/slot order = TIER_LETTERS[4]
    FILLED   = [(0, "EIA"), (1, "SR"), (2, "TNO"), (3, "LDC")]   # from scenes 07–12

    def setup_scene(self):
        self.build_board(on_screen=True)            # continuation of 12 (centred)

    # ── P, M, B : rapid succession (crossfade views) ─────────────────────────────
    # a : fill P (slot 0) into MID↓, tuck the list ↖ + send a copy of P ↙, with P's
    #     heatmap + n-gram RISING IN BEHIND that leftward motion (establishes the views
    #     the rapid trio morphs through)
    @subscene
    def p_intro(self):
        self.intro_letter_views(0, "p", 0.6, 1.2)

    # b : rapid crossfade-switch to M (slot 3) — heatmap morphs, n-gram crossfades;
    #     M slides down AS P returns up (incoming/outgoing move together)
    @subscene
    def m_rapid(self):
        self.rapid_letter(3, "m", 0.6)

    # c : rapid crossfade-switch to B (slot 4)
    @subscene
    def b_rapid(self):
        self.rapid_letter(4, "b", 0.6)

    # ── U, G, H : as normal ──────────────────────────────────────────────────────
    # d : remove B's views, B's copy returns AS U (slot 1) fades in, then a copy of U ↙
    @subscene
    def u_intro(self):
        self.advance_letter(1, 0.9, 1.0)

    # e : heatmaps for U
    @subscene
    def u_heat(self):
        self.show_heat("u", 1.0)

    # f : add the n-gram view for U
    @subscene
    def u_ngram(self):
        self.add_ngram("u", 0.8)

    # g : common-uses — top 6 table cases for U
    @subscene
    def u_common(self):
        self.show_common(U_COMMON, 0.9)

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

    # k : common-uses — top 6 table cases for G (boards ending in "in_")
    @subscene
    def g_common(self):
        self.show_common(G_COMMON, 0.9)

    # l : H's turn (slot 5), as normal
    @subscene
    def h_intro(self):
        self.advance_letter(5, 0.9, 1.0)

    # m : heatmaps for H
    @subscene
    def h_heat(self):
        self.show_heat("h", 1.0)

    # n : add the n-gram view for H
    @subscene
    def h_ngram(self):
        self.add_ngram("h", 0.8)

    # o : clear views + big letter; tier list returns to CENTRE (for the next scene)
    @subscene
    def recenter(self):
        self.recenter_board(1.0)
