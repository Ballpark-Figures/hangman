"""SCENE 07 — the TOP TIER of the tier list, letter by letter (E, I, A).

Scene 96's layout (a reference letter tucked at a corner + a big letter copy at
bottom-left + swappable data views), but the letter GRID is replaced by the TIER
LIST (top-left) and a new COMMON-USES view leads each letter ahead of the existing
position-frequency (heatmap) + n-gram views. Brand light-blue world, NOT chalk.

Script row 13, split on '—' -> 10 beats a–j (voiceover ↔ animation zip 1:1):
  a E intro     fill E into the top tier; move the tier list to top-left; big E ↙
  b E common    common-uses view — blank first-guess words, lengths 5–11
  c E heatmap   swap common-uses out for the position-frequency heatmaps
  d E ngram     add the n-gram view
  e I intro     send E back; fill I into the top tier; big I ↙
  f I common    common-uses view — blank first-guess words, lengths 12–20
  g I heatmap   swap to the heatmaps
  h I ngram     add the n-gram view
  i A intro+cu  send I back; fill A into the top tier; big A ↙; common-uses 1–4
  j A heat+ng   heatmaps, then add the n-gram view

The common-uses content is BLANK first-guess boards (E len 5–11, I len 12–20,
A len 1–4 — the sourced best-first-guess length ranges); a blank board of length N
is just N underscores, so no per-word data is needed (see hangman CLAUDE.md
"Common uses view"). Heatmap/n-gram numbers come from the committed caches as in 96.

SEAM ASSUMPTION (flag): scene 07 opens on the NAMED, EMPTY tier list centred (as
06 leaves it, minus 06g's preview fill); E/I/A fill in here one at a time.

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every fade / move /
view-swap run_time.

Render:  render 07a --fast  (…07j)  /  render 07 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets import tier_list as tl
from assets.common_uses import common_uses
from assets.letter_heatmaps import letter_heatmaps
from assets.letter_ngrams import letter_ngrams

# top-tier letters, in order, and the best-first-guess length ranges they own
TOP = [("e", range(5, 12)), ("i", range(12, 21)), ("a", range(1, 5))]

TL_SCALE   = 0.5                                   # tier list shrink when tucked UL
TL_CORNER  = np.array([-5.6, 2.3, 0])              # tier-list centre once tucked
BIG_POS    = np.array([-6.2, -2.7, 0])             # big current-letter copy ↙
BIG_H      = 1.9

# view region (right of the tucked tier list) — heatmap/ngram reuse 96's anchors
HEAT_CENTER = np.array([1.4, -0.4, 0.0])
NG_X        = 6.2
CU_CENTER   = np.array([2.4, 0.0, 0.0])            # common-uses block centre


class Scene07(HangmanScene):
    """Top tier E/I/A. See module docstring for the beat map."""

    def setup_scene(self):
        # opens on the named, empty tier list centred (carried from scene 06)
        self.tl = tl.get_tier_list("name")
        # pre-place E,I,A into the top tier (children of the group so they travel
        # with it when it tucks); revealed one per letter-intro beat
        self.tier_tiles = tl.fill_tier(self.tl, 0, "EIA")
        for t in self.tier_tiles:
            t.set_opacity(0)
        self.big = None
        self.common = self.heat = self.ngram = None

    # ── helpers ───────────────────────────────────────────────────────────────
    def _big_letter(self, ch):
        return crisp_text(ch.upper(), font_size=FONT_SIZE_LG, color=ACCENT_FILL,
                          weight=BOLD).set_height(BIG_H).move_to(BIG_POS)

    def _cu(self, length_range):
        return common_uses([L for L in length_range], center=CU_CENTER)

    def _heat(self, ch):
        return letter_heatmaps(ch, center=HEAT_CENTER)

    def _ngram(self, ch):
        h = self.heat
        top_y = h.heatmaps[0].get_top()[1]
        bot_y = h.heatmaps[-1].get_bottom()[1]
        return letter_ngrams(ch, center_x=NG_X, top_y=top_y, bottom_y=bot_y)

    def _intro_letter(self, i):
        """Reveal top-tier tile i, and swap the big bottom-left copy to it."""
        ch = TOP[i][0]
        big = self._big_letter(ch)
        anims = [self.tier_tiles[i].animate.set_opacity(1), FadeIn(big)]
        if self.big is not None:
            anims.append(FadeOut(self.big))
        self.play(*anims, run_time=1.0)
        self.big = big

    def _clear_views(self):
        outs = [FadeOut(v) for v in (self.common, self.heat, self.ngram) if v]
        if outs:
            self.play(*outs, run_time=0.6)
        self.common = self.heat = self.ngram = None

    # ── E ─────────────────────────────────────────────────────────────────────
    # a : fill E in the top tier, tuck the list to UL, drop a big E ↙
    @subscene
    def e_intro(self):
        self.play(self.tier_tiles[0].animate.set_opacity(1), run_time=0.7)
        big = self._big_letter("e")
        self.play(self.tl.animate.scale(TL_SCALE).move_to(TL_CORNER),
                  FadeIn(big), run_time=1.2)
        self.big = big

    # b : common-uses view — blank first-guess words, lengths 5–11
    @subscene
    def e_common(self):
        self.common = self._cu(TOP[0][1])
        self.play(FadeIn(self.common), run_time=0.9)

    # c : swap common-uses out for the heatmaps
    @subscene
    def e_heat(self):
        self.heat = self._heat("e")
        self.play(FadeOut(self.common), FadeIn(self.heat), run_time=1.0)
        self.common = None

    # d : add the n-gram view
    @subscene
    def e_ngram(self):
        self.ngram = self._ngram("e")
        self.play(FadeIn(self.ngram), run_time=0.8)

    # ── I ─────────────────────────────────────────────────────────────────────
    # e : send E back, fill I in the top tier, big I ↙
    @subscene
    def i_intro(self):
        self._clear_views()
        self._intro_letter(1)

    # f : common-uses view — blank first-guess words, lengths 12–20
    @subscene
    def i_common(self):
        self.common = self._cu(TOP[1][1])
        self.play(FadeIn(self.common), run_time=0.9)

    # g : swap to the heatmaps
    @subscene
    def i_heat(self):
        self.heat = self._heat("i")
        self.play(FadeOut(self.common), FadeIn(self.heat), run_time=1.0)
        self.common = None

    # h : add the n-gram view
    @subscene
    def i_ngram(self):
        self.ngram = self._ngram("i")
        self.play(FadeIn(self.ngram), run_time=0.8)

    # ── A ─────────────────────────────────────────────────────────────────────
    # i : send I back, fill A in the top tier, big A ↙, then common-uses 1–4
    @subscene
    def a_intro(self):
        self._clear_views()
        self._intro_letter(2)
        self.common = self._cu(TOP[2][1])
        self.play(FadeIn(self.common), run_time=0.9)

    # j : swap to the heatmaps, then add the n-gram view
    @subscene
    def a_heat(self):
        self.heat = self._heat("a")
        self.play(FadeOut(self.common), FadeIn(self.heat), run_time=1.0)
        self.common = None
        self.ngram = self._ngram("a")
        self.play(FadeIn(self.ngram), run_time=0.8)
