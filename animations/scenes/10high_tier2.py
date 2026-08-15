"""SCENE 10 — the HIGH↓ tier (T, N, O), letter by letter.

Built on the shared `TierLetterScene` base (assets/tier_letter_scene.py). Back-to-back
continuation of scene 09: opens on the named tier list CENTRED (top tier E/I/A + HIGH↑
S/R already filled, as 09 left it), works the HIGH↓ tier (TIER_LETTERS[2] = "TNO") with
heatmap + n-gram views per letter (no common-uses, like 96), returns the tier list to
CENTRE, then CLEARS it — scene 11 is the (animated) intermission, NOT a talking head, so
10 must end blank (like 07 before the 08 interlude), not hand a centred list forward.

Beats a–k:
  a T intro     fill T into HIGH↓; tier list → top-left; copy of T → ↙
  b T heatmap   position-frequency heatmaps
  c T ngram     add the n-gram view
  d N intro     remove T's views, T's copy returns AS N fades in, copy of N → ↙
  e N heatmap   heatmaps for N
  f N ngram     add the n-gram view for N
  g O intro     remove N's views, N's copy returns AS O fades in, copy of O → ↙
  h O heatmap   heatmaps for O
  i O ngram     add the n-gram view for O
  j recenter    clear views + big letter; tier list returns to CENTRE (completed HIGH tier)
  k clear_list  TRANSITION: fade the tier list out → blank, for the intermission (11)

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every run_time below.

Render:  render 10a --fast  (…10k)  /  render 10 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.tier_letter_scene import TierLetterScene


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

    # ── O ───────────────────────────────────────────────────────────────────────
    # g : remove N's views, N's copy returns AS O fades in, then a copy of O ↙
    @subscene
    def o_intro(self):
        self.advance_letter(2, 0.9, 1.0)

    # h : heatmaps for O
    @subscene
    def o_heat(self):
        self.show_heat("o", 1.0)

    # i : add the n-gram view for O
    @subscene
    def o_ngram(self):
        self.add_ngram("o", 0.8)

    # j : clear views + big letter; tier list returns to CENTRE (the completed HIGH tier)
    @subscene
    def recenter(self):
        self.recenter_board(1.0)

    # k : TRANSITION to scene 11 — fade the completed tier list off, ending BLANK.
    #     Scene 11 (the intermission) opens on a navy interlude with no tier list, so
    #     10 must not leave the list on screen (cf. 07, which close_all's before 08).
    @subscene
    def clear_list(self):
        self.play(FadeOut(self.tl), run_time=0.8)
