"""SCENE 12 — the MID↑ tier (L, D, C), letter by letter.

Built on the shared `TierLetterScene` base (assets/tier_letter_scene.py). Like the
test scene 96, the script (row 12) names no common-uses beats, so each letter shows
ONLY the heatmap + n-gram views. First scene of the MID group (after scene 11's
end-of-high-tier summary): STARTS on a blank screen — the named tier list (TOP + HIGH
already filled) fades in centred — works the MID↑ tier (TIER_LETTERS[3] = "LDC"), and
ENDS with the tier list back at CENTRE for scene 13 (MID↓).

START-MODE ASSUMPTION (flag): blank start + fade-in, mirroring 09 (the first HIGH
scene). If scene 11 leaves the tier list on screen centred, flip to a continuation:
`build_board(on_screen=True)` and delete the `establish` beat.

Beats a–k:
  a establish   named tier list (TOP + HIGH filled) fades in, centred
  b L intro     fill L into MID↑; tier list → top-left; copy of L → ↙
  c L heatmap   position-frequency heatmaps
  d L ngram     add the n-gram view
  e D intro     remove L's views, L's copy returns AS D fades in, copy of D → ↙
  f D heatmap   heatmaps for D
  g D ngram     add the n-gram view for D
  h C intro     remove D's views, D's copy returns AS C fades in, copy of C → ↙
  i C heatmap   heatmaps for C
  j C ngram     add the n-gram view for C
  k recenter    clear views + big letter; tier list returns to CENTRE (for scene 13)

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every run_time below.

Render:  render 12a --fast  (…12k)  /  render 12 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.tier_letter_scene import TierLetterScene


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

    # ── C ───────────────────────────────────────────────────────────────────────
    # h : remove D's views, D's copy returns AS C fades in, then a copy of C ↙
    @subscene
    def c_intro(self):
        self.advance_letter(2, 0.9, 1.0)

    # i : heatmaps for C
    @subscene
    def c_heat(self):
        self.show_heat("c", 1.0)

    # j : add the n-gram view for C
    @subscene
    def c_ngram(self):
        self.add_ngram("c", 0.8)

    # k : clear views + big letter; tier list returns to CENTRE (for scene 13)
    @subscene
    def recenter(self):
        self.recenter_board(1.0)
