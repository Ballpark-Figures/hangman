"""SCENE 07 — the TOP TIER of the tier list, letter by letter (E, I, A).

A CONTINUATION of scene 06: the named tier list is already on screen (centred, top
tier empty). Modelled on scene 96's layout (the reference tucked at a corner + a big
letter copy at bottom-left + swappable data views), but the letter GRID is the TIER
LIST, and a COMMON-USES view leads each letter ahead of the position-frequency
(heatmap) + n-gram views. Brand light-blue world, NOT chalk.

The letter mechanic mirrors 96's `LetterGrid.choose`/`swap`: the tier list shrinks
×0.8 up to the top-left corner while a COPY of the letter detaches from the tier and
MOVES down to the bottom-left, recolouring white→brand-blue as it goes; the next
letter sends the corner copy back, appears in the tier, and sends its own copy down.

Script row 13, split on '—' -> 10 beats a–j (voiceover ↔ animation zip 1:1):
  a E intro     fill E into the top tier; tier list → top-left; copy of E → ↙
  b E common    common-uses view — blank first-guess words, lengths 5–11
  c E heatmap   swap common-uses out for the position-frequency heatmaps
  d E ngram     add the n-gram view
  e I intro     send E's copy back; I appears in the tier; copy of I → ↙
  f I common    common-uses view — blank first-guess words, lengths 12–20
  g I heatmap   swap to the heatmaps
  h I ngram     add the n-gram view
  i A intro+cu  send I's copy back; A appears; copy of A → ↙; common-uses 1–4
  j A heat+ng   heatmaps, then add the n-gram view

Each view carries a two-line title in 96's style (Common/Uses · Location/Frequencies
· Top/N-grams). Common-uses content is BLANK first-guess boards (the sourced best-
first-guess length ranges — see hangman CLAUDE.md "Common uses view"); heatmap/ngram
numbers come from the committed caches as in 96.

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

# tier-list tuck + big-letter geometry (matches 96's LetterGrid.choose)
TL_SHRINK   = 0.8
TL_TOP_BUFF = 0.5
CORNER_BUFF = 1.0
BIG_GROW    = 5.5                                  # big letter = grid-base × 5.5
BIG_COLOR   = ACCENT_FILL                          # tier white → brand blue on the move

# view region (right of the tucked tier list)
HEAT_CENTER = np.array([1.6, -0.4, 0.0])
NG_X        = 6.0
CU_LEFT     = 0.3                                  # common-uses board left edge
CU_Y        = 0.0
TITLE_Y     = 3.2


class Scene07(HangmanScene):
    """Top tier E/I/A, continuing scene 06. See module docstring for the beat map."""

    def setup_scene(self):
        # continuation of 06: the named tier list is already centred on screen,
        # top tier empty. Pre-place E,I,A into the top tier (children of the group,
        # so they travel with it when it tucks) and reveal them one per intro beat.
        self.tl = tl.get_tier_list("name")
        self.tier_tiles = tl.fill_tier(self.tl, 0, "EIA")
        for t in self.tier_tiles:
            t.set_opacity(0)
        self.add(self.tl)
        self._tl_full_h = self.tl.height
        self._big_h = crisp_text("A", font_size=48).height * BIG_GROW
        self.corner = self.corner_home = None                  # the big ↙ copy
        self.common = self.cu_title = None
        self.heat = self.loc_title = None
        self.ngram = self.ng_title = None

    # ── letter mechanic (copy detaches from the tier and moves ↙, recolouring) ──
    def _corner_target(self, tile):
        """The bottom-left rest pose for the big letter copy — 96's `choose` math:
        left-anchored, vertically centred in the gap below the tucked tier list."""
        fx, fy = config.frame_x_radius, config.frame_y_radius
        tw = tile.width * self._big_h / tile.height
        final_bottom = (fy - TL_TOP_BUFF) - self._tl_full_h * TL_SHRINK
        cy = (final_bottom + -fy) / 2
        return [(-fx + CORNER_BUFF) + tw / 2, cy, 0]

    def _send_copy_down(self, tile, run_time):
        """A COPY of `tile` detaches and moves ↙, growing + recolouring to brand blue.
        The original tile stays in the tier."""
        copy = tile.copy()
        self.add(copy)
        self.play(copy.animate.scale_to_fit_height(self._big_h)
                  .move_to(self._corner_target(copy)).set_color(BIG_COLOR),
                  run_time=run_time)
        self.corner, self.corner_home = copy, tile

    def _send_corner_back(self, run_time):
        """Move the current big ↙ copy back onto its tier slot (recolouring white),
        then drop it — the original tier tile remains."""
        if self.corner is None:
            return
        c, tile = self.corner, self.corner_home
        self.play(c.animate.scale_to_fit_height(tile.height)
                  .move_to(tile.get_center()).set_color(tl.LETTER_COLOR),
                  run_time=run_time)
        self.remove(c)
        self.corner = self.corner_home = None

    # ── view management (each view carries its own two-line title) ──────────────
    def _title(self, l1, l2, x):
        return crisp_paragraph(l1, l2, font_size=30, color=BLACK,
                               alignment="center").move_to([x, TITLE_Y, 0])

    def _show_common(self, length_range, run_time):
        self.common = common_uses([L for L in length_range], board_left_x=CU_LEFT,
                                  center_y=CU_Y)
        self.cu_title = self._title("Common", "Uses", self.common.get_center()[0])
        self.play(FadeIn(self.common), FadeIn(self.cu_title), run_time=run_time)

    def _swap_common_to_heat(self, ch, run_time):
        self.heat = letter_heatmaps(ch, center=HEAT_CENTER)
        self.loc_title = self._title("Location", "Frequencies", HEAT_CENTER[0])
        self.play(FadeOut(self.common), FadeOut(self.cu_title),
                  FadeIn(self.heat), FadeIn(self.loc_title), run_time=run_time)
        self.common = self.cu_title = None

    def _add_ngram(self, ch, run_time):
        top_y = self.heat.heatmaps[0].get_top()[1]
        bot_y = self.heat.heatmaps[-1].get_bottom()[1]
        self.ngram = letter_ngrams(ch, center_x=NG_X, top_y=top_y, bottom_y=bot_y)
        self.ng_title = self._title("Top", "N-grams", NG_X)
        self.play(FadeIn(self.ngram), FadeIn(self.ng_title), run_time=run_time)

    def _clear_views(self, run_time=0.6):
        outs = [FadeOut(v) for v in (self.common, self.cu_title, self.heat,
                                     self.loc_title, self.ngram, self.ng_title) if v]
        if outs:
            self.play(*outs, run_time=run_time)
        self.common = self.cu_title = None
        self.heat = self.loc_title = None
        self.ngram = self.ng_title = None

    # ── E ─────────────────────────────────────────────────────────────────────
    # a : fill E in the top tier, tuck the list ↖, send a copy of E ↙
    @subscene
    def e_intro(self):
        self.play(self.tier_tiles[0].animate.set_opacity(1), run_time=0.6)
        copy = self.tier_tiles[0].copy()
        self.add(copy)
        self.play(self.tl.animate.scale(TL_SHRINK).to_corner(UL, buff=TL_TOP_BUFF),
                  copy.animate.scale_to_fit_height(self._big_h)
                  .move_to(self._corner_target(copy)).set_color(BIG_COLOR),
                  run_time=1.2)
        self.corner, self.corner_home = copy, self.tier_tiles[0]

    # b : common-uses view — blank first-guess words, lengths 5–11
    @subscene
    def e_common(self):
        self._show_common(TOP[0][1], 0.9)

    # c : swap common-uses out for the heatmaps
    @subscene
    def e_heat(self):
        self._swap_common_to_heat("e", 1.0)

    # d : add the n-gram view
    @subscene
    def e_ngram(self):
        self._add_ngram("e", 0.8)

    # ── I ─────────────────────────────────────────────────────────────────────
    # e : send E's copy back, I appears in the tier, send a copy of I ↙
    @subscene
    def i_intro(self):
        self._clear_views()
        self._send_corner_back(0.8)
        self.play(self.tier_tiles[1].animate.set_opacity(1), run_time=0.6)
        self._send_copy_down(self.tier_tiles[1], 1.0)

    # f : common-uses view — blank first-guess words, lengths 12–20
    @subscene
    def i_common(self):
        self._show_common(TOP[1][1], 0.9)

    # g : swap to the heatmaps
    @subscene
    def i_heat(self):
        self._swap_common_to_heat("i", 1.0)

    # h : add the n-gram view
    @subscene
    def i_ngram(self):
        self._add_ngram("i", 0.8)

    # ── A ─────────────────────────────────────────────────────────────────────
    # i : send I's copy back, A appears, send a copy of A ↙, then common-uses 1–4
    @subscene
    def a_intro(self):
        self._clear_views()
        self._send_corner_back(0.8)
        self.play(self.tier_tiles[2].animate.set_opacity(1), run_time=0.6)
        self._send_copy_down(self.tier_tiles[2], 1.0)
        self._show_common(TOP[2][1], 0.9)

    # j : swap to the heatmaps, then add the n-gram view
    @subscene
    def a_heat(self):
        self._swap_common_to_heat("a", 1.0)
        self._add_ngram("a", 0.8)
