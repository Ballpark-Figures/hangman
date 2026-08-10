"""SCENE 14 — the LOW↑ tier (F, Y, V, K, W), letter by letter.

Built on the shared `TierLetterScene` base (assets/tier_letter_scene.py). Back-to-back
continuation of scene 13: opens on the named tier list CENTRED (TOP…MID↓ filled), works
the LOW↑ tier (TIER_LETTERS[5] = "FYVKW") with heatmap + n-gram views per letter (no
common-uses, like 96), and recenters at the end for scene 15.

PRESENTATION ORDER = F, Y, V, W, K — following the row-21 narration (which discusses W
alongside V, before K), NOT the tier/slot order FYVKW. So W (slot 4) is revealed before
K (slot 3): the row reads "F Y V _ W" until K fills the gap (cf. scene 13's PUGMBH).

START-MODE ASSUMPTION (flag): continuation of 13 (centred). If a talking head / the
row-20 "bottom-tier shoutout" clears the screen before this, flip to a blank start:
`build_board(on_screen=False)` + an `establish` beat (`self.enter_centered(0.8)`).

Beats a–p: F/Y/V/W/K each as intro → heatmap → n-gram, then recenter.

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every run_time below.

Render:  render 14a --fast  (…14p)  /  render 14 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.tier_letter_scene import TierLetterScene


class Scene14(TierLetterScene):
    """LOW↑ tier F/Y/V/K/W, continuing scene 13. See docstring for the beat map."""

    TIER_IDX = 5
    LETTERS  = ["f", "y", "v", "k", "w"]             # = TIER_LETTERS[5]
    FILLED   = [(0, "EIA"), (1, "SR"), (2, "TNO"),
                (3, "LDC"), (4, "PUGMBH")]           # from scenes 07–13

    def setup_scene(self):
        self.build_board(on_screen=True)            # continuation of 13 (centred)

    # ── F ───────────────────────────────────────────────────────────────────────
    # a : fill F into LOW↑, tuck the list ↖, send a copy of F ↙
    @subscene
    def f_intro(self):
        self.intro_letter(0, 1.2)

    # b : position-frequency heatmaps
    @subscene
    def f_heat(self):
        self.show_heat("f", 1.0)

    # c : add the n-gram view
    @subscene
    def f_ngram(self):
        self.add_ngram("f", 0.8)

    # ── Y ───────────────────────────────────────────────────────────────────────
    # d : Y's turn
    @subscene
    def y_intro(self):
        self.advance_letter(1, 0.9, 1.0)

    # e : heatmaps for Y
    @subscene
    def y_heat(self):
        self.show_heat("y", 1.0)

    # f : add the n-gram view for Y
    @subscene
    def y_ngram(self):
        self.add_ngram("y", 0.8)

    # ── V ───────────────────────────────────────────────────────────────────────
    # g : V's turn
    @subscene
    def v_intro(self):
        self.advance_letter(2, 0.9, 1.0)

    # h : heatmaps for V
    @subscene
    def v_heat(self):
        self.show_heat("v", 1.0)

    # i : add the n-gram view for V
    @subscene
    def v_ngram(self):
        self.add_ngram("v", 0.8)

    # ── W ───────────────────────────────────────────────────────────────────────
    # j : W's turn (slot 4 — revealed before K, following the narration; leaves a
    #     one-slot gap at K's slot 3, which K fills next)
    @subscene
    def w_intro(self):
        self.advance_letter(4, 0.9, 1.0)

    # k : heatmaps for W
    @subscene
    def w_heat(self):
        self.show_heat("w", 1.0)

    # l : add the n-gram view for W
    @subscene
    def w_ngram(self):
        self.add_ngram("w", 0.8)

    # ── K ───────────────────────────────────────────────────────────────────────
    # m : K's turn (slot 3 — fills the gap left after W)
    @subscene
    def k_intro(self):
        self.advance_letter(3, 0.9, 1.0)

    # n : heatmaps for K
    @subscene
    def k_heat(self):
        self.show_heat("k", 1.0)

    # o : add the n-gram view for K
    @subscene
    def k_ngram(self):
        self.add_ngram("k", 0.8)

    # p : clear views + big letter; tier list returns to CENTRE (for scene 15)
    @subscene
    def recenter(self):
        self.recenter_board(1.0)
