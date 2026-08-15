"""SCENE 12 — the MID↑ tier (L, D, C), letter by letter.

Built on the shared `TierLetterScene` base (assets/tier_letter_scene.py). First scene
of the MID group (after scene 11's end-of-high-tier summary): STARTS on a blank screen
— the named tier list (TOP + HIGH already filled) fades in centred — works the MID↑
tier (TIER_LETTERS[3] = "LDC"), and ENDS with the tier list back at CENTRE for scene
13 (MID↓). Only the D section carries a common-uses beat (per the user's request); L
and C show heatmap + n-gram only, like test scene 96.

START-MODE ASSUMPTION (flag): blank start + fade-in, mirroring 09 (the first HIGH
scene). If scene 11 leaves the tier list on screen centred, flip to a continuation:
`build_board(on_screen=True)` and delete the `establish` beat.

Beats a–l:
  a establish   named tier list (TOP + HIGH filled) fades in, centred
  b L intro     fill L into MID↑; tier list → top-left; copy of L → ↙
  c L heatmap   position-frequency heatmaps
  d L ngram     add the n-gram view
  e D intro     remove L's views, L's copy returns AS D fades in, copy of D → ↙
  f D heatmap   heatmaps for D
  g D ngram     add the n-gram view for D
  h D common    common-uses — top 8 table cases for D (D_COMMON)
  i C intro     remove D's views, D's copy returns AS C fades in, copy of C → ↙
  j C heatmap   heatmaps for C
  k C ngram     add the n-gram view for C
  l recenter    clear views + big letter; tier list returns to CENTRE (for scene 13)

The D common-uses beat (h) shows real (level ≥ 1 and level-1 fresh-edge) game states
SOURCED from letter_analysis.ipynb's `guesses_of_letter_all_lengths('d')` at
STRATEGY=optimal / WEIGHTING=uniform, n_words descending — the TOP 8 rows; reproduced
by `math/common_uses_scene12.py`, which prints these exact rows.

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every run_time below.

Render:  render 12a --fast  (…12l)  /  render 12 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.tier_letter_scene import TierLetterScene

# D's common-uses beat pulls states straight from letter_analysis.ipynb's
# guesses_of_letter_all_lengths('d') at STRATEGY=optimal / WEIGHTING=uniform, sorted
# by n_words DESCENDING (the notebook's display sort). "top 8 cases" = .head(8).
# SOURCED + reproducible via math/common_uses_scene12.py (prints these rows).
# Each spec is (length, board, missed) — D thrives near word EDGES beside an E, often
# after R/S have already missed (hence the (R S) tallies).
D_COMMON = [
    (6, "____e_",    ["r", "s"]),
    (7, "_____e_",   ["r", "s"]),
    (5, "___e_",     ["r", "s"]),
    (7, "_e___e_",   []),
    (8, "______e_",  ["r", "s"]),
    (9, "_e_____e_", []),
    (6, "_e__e_",    ["r"]),
    (6, "_e___e",    []),
]


class Scene12(TierLetterScene):
    """MID↑ tier L/D/C. See module docstring for the beat map."""

    TIER_IDX = 3
    LETTERS  = ["l", "d", "c"]                       # = TIER_LETTERS[3]
    FILLED   = [(0, "EIA"), (1, "SR"), (2, "TNO")]   # TOP + HIGH, from scenes 07/09/10

    def setup_scene(self):
        self.build_board(on_screen=False)           # blank start; establish fades in

    # a : the named tier list (TOP + HIGH filled) fades in, centred
    @subscene
    def establish(self):
        self.enter_centered(0.8)

    # ── L ───────────────────────────────────────────────────────────────────────
    # b : fill L into the MID↑ tier, tuck the list ↖, send a copy of L ↙
    @subscene
    def l_intro(self):
        self.intro_letter(0, 1.2)

    # c : position-frequency heatmaps
    @subscene
    def l_heat(self):
        self.show_heat("l", 1.0)

    # d : add the n-gram view
    @subscene
    def l_ngram(self):
        self.add_ngram("l", 0.8)

    # ── D ───────────────────────────────────────────────────────────────────────
    # e : remove L's views, L's copy returns AS D fades in, then a copy of D ↙
    @subscene
    def d_intro(self):
        self.advance_letter(1, 0.9, 1.0)

    # f : heatmaps for D
    @subscene
    def d_heat(self):
        self.show_heat("d", 1.0)

    # g : add the n-gram view for D
    @subscene
    def d_ngram(self):
        self.add_ngram("d", 0.8)

    # h : common-uses — top 8 table cases for D
    @subscene
    def d_common(self):
        self.show_common(D_COMMON, 0.9)

    # ── C ───────────────────────────────────────────────────────────────────────
    # i : remove D's views, D's copy returns AS C fades in, then a copy of C ↙
    @subscene
    def c_intro(self):
        self.advance_letter(2, 0.9, 1.0)

    # j : heatmaps for C
    @subscene
    def c_heat(self):
        self.show_heat("c", 1.0)

    # k : add the n-gram view for C
    @subscene
    def c_ngram(self):
        self.add_ngram("c", 0.8)

    # l : clear views + big letter; tier list returns to CENTRE (for scene 13)
    @subscene
    def recenter(self):
        self.recenter_board(1.0)
