"""SCENE 09 — the HIGH↑ tier (S, R), letter by letter.

Built on the shared `TierLetterScene` base (assets/tier_letter_scene.py). Unlike the
other high/mid/low tier scenes, the HIGH↑ tier HAS common-uses beats (script row 09):
each of S and R closes on a common-uses view of real game states pulled from the table.
STARTS on a blank screen (the named tier list, top tier E/I/A already filled, fades in
centred), then works the HIGH↑ tier (TIER_LETTERS[1] = "SR"), and ENDS with the tier
list back at CENTRE — scene 10 continues from that state (back-to-back scenes).

Script row 09, split on '—' → 9 beats a–i (voiceover ↔ animation zip 1:1) + recenter:
  a establish   named tier list (E/I/A filled) fades in, centred
  b S intro     fill S into HIGH↑; tier list → top-left; copy of S → ↙
  c S heatmap   position-frequency heatmaps
  d S ngram     add the n-gram view
  e S common    common-uses — first 8 table examples with NO missed R (S_COMMON)
  f R intro     remove S's views, S's copy returns AS R fades in, copy of R → ↙
  g R heatmap   heatmaps for R
  h R ngram     add the n-gram view
  i R common    common-uses — first 8 table examples with NO missed T (R_COMMON)
  j recenter    clear views + big letter; tier list returns to CENTRE (for scene 10)

The two common-uses beats (e, i) show real (level ≥ 1) game states — the FIRST scenes
to exercise common_uses' partial-board / red-misses path with real data. Each state is
SOURCED from letter_analysis.ipynb's `guesses_of_letter_all_lengths(<letter>)` at
STRATEGY=optimal / WEIGHTING=uniform (the notebook's n_words-descending display sort);
reproduced by `math/common_uses_scene09.py`, which prints these exact rows.

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every run_time below.

Render:  render 09a --fast  (…09j)  /  render 09 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.tier_letter_scene import TierLetterScene

# The two common-uses beats pull states straight from letter_analysis.ipynb's
# guesses_of_letter_all_lengths(<letter>) at STRATEGY=optimal / WEIGHTING=uniform,
# sorted by n_words DESCENDING (the notebook's display sort). "first N examples" =
# .head(N). SOURCED + reproducible via math/common_uses_scene09.py (prints these rows).
# Each spec is (length, board, missed).
#   S — the table's first 8 rows whose `missed` has NO R (the two missed-R rows of
#   the raw top-10 dropped: S rarely follows a missed R, a strong opener).
S_COMMON = [
    (7, "_____e_",   []),
    (8, "______e_",  []),
    (7, "____e__",   []),
    (4, "_a__",      []),
    (8, "_____e__",  []),
    (6, "___e__",    []),
    (5, "__a__",     ["e"]),
    (9, "______e__", []),
]
#   R — the table's first 8 rows whose `missed` has NO T ("don't have a missing T").
R_COMMON = [
    (6, "____e_",    []),
    (5, "___e_",     []),
    (7, "_____e_",   ["s"]),
    (6, "_e____",    []),
    (8, "______e_",  ["s"]),
    (6, "_e__e_",    []),
    (4, "__a_",      []),
    (8, "_e____e_",  []),
]


class Scene09(TierLetterScene):
    """HIGH↑ tier S/R. See module docstring for the beat map."""

    TIER_IDX = 1
    LETTERS  = ["s", "r"]                           # = TIER_LETTERS[1]
    FILLED   = [(0, "EIA")]                          # top tier, from scene 07

    def setup_scene(self):
        self.build_board(on_screen=False)           # blank start; establish fades in

    # a : the named tier list (E/I/A filled) fades in, centred
    @subscene
    def establish(self):
        self.enter_centered(0.8)

    # ── S ───────────────────────────────────────────────────────────────────────
    # b : fill S into the HIGH↑ tier, tuck the list ↖, send a copy of S ↙
    @subscene
    def s_intro(self):
        self.intro_letter(0, 1.2)

    # c : position-frequency heatmaps
    @subscene
    def s_heat(self):
        self.show_heat("s", 1.0)

    # d : add the n-gram view
    @subscene
    def s_ngram(self):
        self.add_ngram("s", 0.8)

    # e : common-uses — first 8 table examples with no missed R
    @subscene
    def s_common(self):
        self.show_common(S_COMMON, 0.9)

    # ── R ───────────────────────────────────────────────────────────────────────
    # f : remove S's views, S's copy returns AS R fades in, then a copy of R ↙
    @subscene
    def r_intro(self):
        self.advance_letter(1, 0.9, 1.0)

    # g : heatmaps for R
    @subscene
    def r_heat(self):
        self.show_heat("r", 1.0)

    # h : add the n-gram view for R
    @subscene
    def r_ngram(self):
        self.add_ngram("r", 0.8)

    # i : common-uses — first 8 table examples with no missed T
    @subscene
    def r_common(self):
        self.show_common(R_COMMON, 0.9)

    # j : clear views + big letter; tier list returns to CENTRE (for scene 10)
    @subscene
    def recenter(self):
        self.recenter_board(1.0)
