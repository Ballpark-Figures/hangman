"""SCENE 09 — the HIGH↑ tier (S, R), letter by letter.

Built on the shared `TierLetterScene` base (assets/tier_letter_scene.py). Like the
test scene 96, the script (row 14) names no common-uses beats, so each letter shows
ONLY the heatmap + n-gram views. STARTS on a blank screen (the named tier list, top
tier E/I/A already filled, fades in centred), then works the HIGH↑ tier
(TIER_LETTERS[1] = "SR"), and ENDS with the tier list back at CENTRE — scene 10
continues from that state (back-to-back scenes).

Beats a–h:
  a establish   named tier list (E/I/A filled) fades in, centred
  b S intro     fill S into HIGH↑; tier list → top-left; copy of S → ↙
  c S heatmap   position-frequency heatmaps
  d S ngram     add the n-gram view
  e R intro     remove S's views, S's copy returns AS R fades in, copy of R → ↙
  f R heatmap   heatmaps for R
  g R ngram     add the n-gram view for R
  h recenter    clear views + big letter; tier list returns to CENTRE (for scene 10)

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every run_time below.

Render:  render 09a --fast  (…09h)  /  render 09 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.tier_letter_scene import TierLetterScene


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

    # e : remove S's views, S's copy returns AS R fades in, then a copy of R ↙
    @subscene
    def r_intro(self):
        self.advance_letter(1, 0.9, 1.0)

    # f : heatmaps for R
    @subscene
    def r_heat(self):
        self.show_heat("r", 1.0)

    # g : add the n-gram view for R
    @subscene
    def r_ngram(self):
        self.add_ngram("r", 0.8)

    # h : clear views + big letter; tier list returns to CENTRE (for scene 10)
    @subscene
    def recenter(self):
        self.recenter_board(1.0)
