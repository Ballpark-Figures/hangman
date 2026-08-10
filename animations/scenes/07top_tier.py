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
  e I intro     E's copy returns AS I fades in (together), then a copy of I → ↙
  f I common    common-uses view — blank first-guess words, lengths 12–20
  g I heatmap   swap to the heatmaps
  h I ngram     add the n-gram view
  i A intro+cu  I's copy returns AS A fades in, then a copy of A → ↙; common-uses 1–4
  j A heat+ng   heatmaps, then add the n-gram view
  k close       fade everything out — ends on a blank screen for the next scene

Each view carries a title (single-line "Common Uses"; two-line "Location/Frequencies"
and "Top/N-grams", 96's style) and enters with 96's row-by-row upward rise. Common-
uses content is BLANK first-guess boards (the sourced best-first-guess length ranges
— see hangman CLAUDE.md "Common uses view"); heatmap/ngram numbers come from the
committed caches as in 96.

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

# tier-list tuck + big-letter geometry (mirrors 96's LetterGrid.choose; a touch
# smaller than 96's 0.8 to leave more room above the big letter)
TL_SHRINK   = 0.7
TL_TOP_BUFF = 0.5
BIG_GROW    = 5.5                                  # big letter = grid-base × 5.5
BIG_COLOR   = ACCENT_FILL                          # tier white → brand blue on the move

# view region (right of the tucked tier list)
HEAT_CENTER = np.array([1.6, -0.4, 0.0])
NG_X        = 6.0
CU_CENTER_X = 3.0                                  # common-uses list centred here (so
                                                   # the wide len-20 I list isn't
                                                   # crunched against the right edge)
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
        self._tl_full_w = self.tl.width
        self._big_h = crisp_text("A", font_size=48).height * BIG_GROW
        self.corner = self.corner_home = None                  # the big ↙ copy
        self.common = self.cu_title = None
        self.heat = self.loc_title = None
        self.ngram = self.ng_title = None

    # ── letter mechanic (copy detaches from the tier and moves ↙, recolouring) ──
    def _corner_target(self, tile):
        """The bottom-left rest pose for the big letter copy: horizontally CENTRED
        under the tucked tier list, and vertically centred in the gap below it."""
        fx, fy = config.frame_x_radius, config.frame_y_radius
        tier_cx = -fx + TL_TOP_BUFF + (self._tl_full_w * TL_SHRINK) / 2
        final_bottom = (fy - TL_TOP_BUFF) - self._tl_full_h * TL_SHRINK
        cy = (final_bottom + -fy) / 2
        return [tier_cx, cy, 0]

    def _send_copy_down(self, tile, run_time):
        """A COPY of `tile` detaches and moves ↙, growing + recolouring to brand blue.
        The original tile stays in the tier."""
        copy = tile.copy()
        self.add(copy)
        self.play(copy.animate.scale_to_fit_height(self._big_h)
                  .move_to(self._corner_target(copy)).set_color(BIG_COLOR),
                  run_time=run_time)
        self.corner, self.corner_home = copy, tile

    def _return_next(self, i, run_time):
        """One play: the current big ↙ copy moves back onto its tier slot (recolouring
        white) WHILE the next letter (tile `i`) fades into the tier — then the copy is
        dropped (the original tier tile remains). Followed by `_send_copy_down`."""
        reveal = self.tier_tiles[i].animate.set_opacity(1)
        if self.corner is None:
            self.play(reveal, run_time=run_time)
            return
        c, tile = self.corner, self.corner_home
        self.play(c.animate.scale_to_fit_height(tile.height)
                  .move_to(tile.get_center()).set_color(tl.LETTER_COLOR),
                  reveal, run_time=run_time)
        self.remove(c)
        self.corner = self.corner_home = None

    # ── view management (each view carries its own title + 96's row-by-row rise) ─
    def _title(self, l1, l2, x):
        """A two-line view title (Location/Frequencies · Top/N-grams), 96's style."""
        return crisp_paragraph(l1, l2, font_size=30, color=BLACK,
                               alignment="center").move_to([x, TITLE_Y, 0])

    def _title1(self, text, x):
        """A single-line view title (Common Uses)."""
        return crisp_text(text, font_size=30, color=BLACK).move_to([x, TITLE_Y, 0])

    def _rise(self, parent, rows, *, lag_ratio=0.14, shift=0.28):
        """96's entrance: reveal `parent`'s `rows` one at a time with overlapping
        upward fades. Add the whole group, preset each row a touch low + transparent,
        then lag each up into place. Returns the LaggedStart (self.play sets run_time)."""
        for row in rows:
            row.shift(DOWN * shift).set_opacity(0)
        self.add(parent)
        return LaggedStart(*[row.animate.shift(UP * shift).set_opacity(1)
                             for row in rows], lag_ratio=lag_ratio)

    def _heat_rows(self, heat):
        return [VGroup(lab, hm) for lab, hm in zip(heat.labels, heat.heatmaps)]

    def _cu_rows(self, cu):
        return [VGroup(lab, row) for lab, row in zip(cu.labels, cu.rows)]

    def _show_common(self, length_range, run_time):
        self.common = common_uses([L for L in length_range])
        self.common.set_x(CU_CENTER_X)             # centre each list (widths vary)
        self.cu_title = self._title1("Common Uses", CU_CENTER_X)
        # vertically centre the list between the title and the bottom of the screen
        self.common.set_y((self.cu_title.get_bottom()[1] + -config.frame_y_radius) / 2)
        self.play(FadeIn(self.cu_title),
                  self._rise(self.common, self._cu_rows(self.common)), run_time=run_time)

    def _swap_common_to_heat(self, ch, run_time):
        self.heat = letter_heatmaps(ch, center=HEAT_CENTER)
        self.loc_title = self._title("Location", "Frequencies", HEAT_CENTER[0])
        self.play(FadeOut(self.common), FadeOut(self.cu_title), FadeIn(self.loc_title),
                  self._rise(self.heat, self._heat_rows(self.heat)), run_time=run_time)
        self.common = self.cu_title = None

    def _add_ngram(self, ch, run_time):
        top_y = self.heat.heatmaps[0].get_top()[1]
        bot_y = self.heat.heatmaps[-1].get_bottom()[1]
        self.ngram = letter_ngrams(ch, center_x=NG_X, top_y=top_y, bottom_y=bot_y)
        self.ng_title = self._title("Top", "N-grams", NG_X)
        self.play(FadeIn(self.ng_title),
                  self._rise(self.ngram, self.ngram.rows), run_time=run_time)

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
    # e : E's copy returns AS I fades in (together), then a copy of I moves ↙
    @subscene
    def i_intro(self):
        self._clear_views()
        self._return_next(1, 0.9)
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
    # i : I's copy returns AS A fades in (together), a copy of A moves ↙, then CU 1–4
    @subscene
    def a_intro(self):
        self._clear_views()
        self._return_next(2, 0.9)
        self._send_copy_down(self.tier_tiles[2], 1.0)
        self._show_common(TOP[2][1], 0.9)

    # j : swap to the heatmaps, then add the n-gram view
    @subscene
    def a_heat(self):
        self._swap_common_to_heat("a", 1.0)
        self._add_ngram("a", 0.8)

    # k : clear the whole screen for the next scene (ends blank)
    @subscene
    def close(self):
        outs = [self.tl] + [v for v in (self.corner, self.heat, self.loc_title,
                                        self.ngram, self.ng_title) if v]
        self.play(*[FadeOut(m) for m in outs], run_time=0.8)
