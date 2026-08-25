"""SCENE 10 — the HIGH↓ tier (T, N, O), letter by letter.

Built on the shared `TierLetterScene` base (assets/tier_letter_scene.py). Back-to-back
continuation of scene 09: opens on the named tier list CENTRED (top tier E/I/A + HIGH↑
S/R already filled, as 09 left it), works the HIGH↓ tier (TIER_LETTERS[2] = "TNO") with
heatmap + n-gram views per letter (no common-uses, like 96), then FADES EVERYTHING out —
scene 11 is the (animated) intermission, NOT a talking head, so 10 must end blank (like
07 before the 08 interlude), not hand a centred list forward.

Unlike scene 09's HIGH↑ tier, only N and O carry common-uses beats here (script row
10) — T is heatmap + n-gram only. Each common-uses state is SOURCED from
letter_analysis.ipynb's `guesses_of_letter_all_lengths(<letter>)` at STRATEGY=optimal /
WEIGHTING=uniform, sorted by n_words descending; "first 6 examples" = .head(6).
Reproduced by `math/common_uses_scene10.py`, which prints these exact rows.

Beats a–l:
  a T intro     fill T into HIGH↓; tier list → top-left; copy of T → ↙
  b T heatmap   position-frequency heatmaps
  c T ngram     add the n-gram view
  d N intro     remove T's views, T's copy returns AS N fades in, copy of N → ↙
  e N heatmap   heatmaps for N
  f N ngram     add the n-gram view for N
  g N common    common-uses — first 6 examples from the table (N_COMMON)
  h O intro     remove N's views, N's copy returns AS O fades in, copy of O → ↙
  i O heatmap   heatmaps for O
  j O ngram     add the n-gram view for O
  k O common    common-uses — first 6 examples from the table (O_COMMON)
  l close_out   fade EVERYTHING (O view, big O, tier list) out → blank, for the intermission (11)

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every run_time below.

Render:  render 10a --fast  (…10l)  /  render 10 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.tier_letter_scene import TierLetterScene

# N and O common-uses states pull straight from letter_analysis.ipynb's
# guesses_of_letter_all_lengths(<letter>) at STRATEGY=optimal / WEIGHTING=uniform,
# sorted by n_words DESCENDING. "first 6 examples" = .head(6). SOURCED + reproducible
# via math/common_uses_scene10.py (prints these exact rows). Each spec is
# (length, board, missed).
#   N — the table's first 6 rows.
N_COMMON = [
    (7, "____i__",   ["e"]),
    (8, "_____i__",  ["e"]),
    (7, "_e_____",   []),
    (9, "______i__", ["e"]),
    (6, "_a____",    ["e"]),
    (8, "___e____",  []),
]
#   O — the table's first 6 rows.
O_COMMON = [
    (5, "_____",     ["a", "e"]),
    (6, "______",    ["a", "e"]),
    (4, "____",      ["a", "e"]),
    (3, "___",       ["a", "e"]),
    (5, "____e",     ["a"]),
    (7, "_______",   ["a", "e", "i"]),
]


class Scene10(TierLetterScene):
    """HIGH↓ tier T/N/O, continuing scene 09. See module docstring for the beat map."""

    TIER_IDX = 2
    LETTERS  = ["t", "n", "o"]                       # = TIER_LETTERS[2]
    FILLED   = [(0, "EIA"), (1, "SR")]               # top + HIGH↑, from scenes 07/09

    def setup_scene(self):
        self.build_board(on_screen=True)            # continuation of 09 (centred)

    # ── T ───────────────────────────────────────────────────────────────────────
    # a : fill T into HIGH↓, tuck the list ↖, send a copy of T ↙
    @subscene
    def t_intro(self):
        self.intro_letter(0, 1.2)

    # b : position-frequency heatmaps
    @subscene
    def t_heat(self):
        self.show_heat("t", 1.0)

    # c : add the n-gram view
    @subscene
    def t_ngram(self):
        self.add_ngram("t", 0.8)

    # ── N ───────────────────────────────────────────────────────────────────────
    # d : remove T's views, T's copy returns AS N fades in, then a copy of N ↙
    @subscene
    def n_intro(self):
        self.advance_letter(1, 0.9, 1.0)

    # e : heatmaps for N
    @subscene
    def n_heat(self):
        self.show_heat("n", 1.0)

    # f : add the n-gram view for N
    @subscene
    def n_ngram(self):
        self.add_ngram("n", 0.8)

    # g : common-uses — first 6 examples from the table
    @subscene
    def n_common(self):
        self.show_common(N_COMMON, 0.9)

    # ── O ───────────────────────────────────────────────────────────────────────
    # h : remove N's views, N's copy returns AS O fades in, then a copy of O ↙
    @subscene
    def o_intro(self):
        self.advance_letter(2, 0.9, 1.0)

    # i : heatmaps for O
    @subscene
    def o_heat(self):
        self.show_heat("o", 1.0)

    # j : add the n-gram view for O
    @subscene
    def o_ngram(self):
        self.add_ngram("o", 0.8)

    # k : common-uses — first 6 examples from the table
    @subscene
    def o_common(self):
        self.show_common(O_COMMON, 0.9)

    # l : end the HIGH tier — fade EVERYTHING (O view, big O, tier list) out to blank.
    #     No recenter flourish: scene 11 (the intermission) opens on a navy interlude
    #     with no tier list, so 10 just fades the final O view + list off (cf. 07, which
    #     close_all's before 08).
    @subscene
    def close_out(self):
        self.close_all(1.0)
