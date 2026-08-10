"""SCENE 10 — the HIGH↓ tier (T, N, O), letter by letter.

Back-to-back continuation of scene 09: opens on the named tier list CENTRED (top tier
E/I/A + HIGH↑ S/R already filled, as 09 left it), then works the HIGH↓ tier
(TIER_LETTERS[2] = "TNO"). Like the test scene 96 / scene 09, each letter shows only
the position-frequency (heatmap) + n-gram views — no common-uses view. The tier list
returns to CENTRE at the end for the next tier scene.

Per letter, exactly as 07/09: the letter fills into its tier, the list tucks ×0.7 to
the top-left, and a COPY of the letter moves ↙ recolouring white→brand blue; the next
letter removes the views, sends the corner copy back AS it fades into the tier, then
sends its own copy down.

Beats a–j:
  a T intro     fill T into HIGH↓; tier list → top-left; copy of T → ↙
  b T heatmap   position-frequency heatmaps (Location Frequencies)
  c T ngram     add the n-gram view (Top N-grams)
  d N intro     remove T's views, T's copy returns AS N fades in, copy of N → ↙
  e N heatmap   heatmaps for N
  f N ngram     add the n-gram view for N
  g O intro     remove N's views, N's copy returns AS O fades in, copy of O → ↙
  h O heatmap   heatmaps for O
  i O ngram     add the n-gram view for O
  j recenter    clear views + big letter; tier list returns to CENTRE (for next scene)

Heatmap/ngram numbers come from the committed caches (letter_heat_data /
letter_ngram_data), as in 96.

NOTE (extraction candidate): 07/09/10 now share almost all of their machinery (the
tier-list letter mechanic + rise-in view helpers + recenter). This is well past the
"second scene" trigger — the shared parts belong in a TierLetterScene base the
remaining tier scenes subclass. ASK before extracting (shared change).

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every fade / move /
view run_time.

Render:  render 10a --fast  (…10j)  /  render 10 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets import tier_list as tl
from assets.letter_heatmaps import letter_heatmaps
from assets.letter_ngrams import letter_ngrams

TIER_IDX = 2                                       # HIGH↓ tier
LETTERS  = ["t", "n", "o"]                         # = TIER_LETTERS[2] = "TNO"

# tier-list tuck + big-letter geometry (identical to 07/09)
TL_SHRINK   = 0.7
TL_TOP_BUFF = 0.5
BIG_GROW    = 5.5
BIG_COLOR   = ACCENT_FILL

# view region (right of the tucked tier list)
HEAT_CENTER = np.array([1.6, -0.4, 0.0])
NG_X        = 6.0
TITLE_Y     = 3.2


class Scene10(HangmanScene):
    """HIGH↓ tier T/N/O. See module docstring for the beat map."""

    def setup_scene(self):
        # continuation of 09: named tier list centred on screen, TOP + HIGH↑ filled.
        # HIGH↓ tiles (T,N,O) pre-placed invisible, revealed one per intro beat.
        self.tl = tl.get_tier_list("name")
        tl.fill_tier(self.tl, 0, "EIA")            # top tier   (from scene 07)
        tl.fill_tier(self.tl, 1, "SR")             # HIGH↑ tier (from scene 09)
        self.tier_tiles = tl.fill_tier(self.tl, TIER_IDX, "".join(LETTERS).upper())
        for t in self.tier_tiles:
            t.set_opacity(0)
        self.add(self.tl)
        self._tl_full_h = self.tl.height
        self._tl_full_w = self.tl.width
        self._big_h = crisp_text("A", font_size=48).height * BIG_GROW
        self.corner = self.corner_home = None                  # the big ↙ copy
        self.heat = self.loc_title = None
        self.ngram = self.ng_title = None

    # ── letter mechanic (mirror of 07/09; extraction candidate) ─────────────────
    def _corner_target(self, tile):
        fx, fy = config.frame_x_radius, config.frame_y_radius
        tier_cx = -fx + TL_TOP_BUFF + (self._tl_full_w * TL_SHRINK) / 2
        final_bottom = (fy - TL_TOP_BUFF) - self._tl_full_h * TL_SHRINK
        cy = (final_bottom + -fy) / 2
        return [tier_cx, cy, 0]

    def _send_copy_down(self, tile, run_time):
        copy = tile.copy()
        self.add(copy)
        self.play(copy.animate.scale_to_fit_height(self._big_h)
                  .move_to(self._corner_target(copy)).set_color(BIG_COLOR),
                  run_time=run_time)
        self.corner, self.corner_home = copy, tile

    def _return_next(self, i, run_time):
        """One play: the corner copy returns to its tier slot (recolouring white)
        WHILE the next tile fades into the tier; then the copy is dropped."""
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

    # ── view management (heatmap + ngram, 96-style row-by-row rise) ──────────────
    def _title(self, l1, l2, x):
        return crisp_paragraph(l1, l2, font_size=30, color=BLACK,
                               alignment="center").move_to([x, TITLE_Y, 0])

    def _rise(self, parent, rows, *, lag_ratio=0.14, shift=0.28):
        for row in rows:
            row.shift(DOWN * shift).set_opacity(0)
        self.add(parent)
        return LaggedStart(*[row.animate.shift(UP * shift).set_opacity(1)
                             for row in rows], lag_ratio=lag_ratio)

    def _heat_rows(self, heat):
        return [VGroup(lab, hm) for lab, hm in zip(heat.labels, heat.heatmaps)]

    def _show_heat(self, ch, run_time):
        self.heat = letter_heatmaps(ch, center=HEAT_CENTER)
        self.loc_title = self._title("Location", "Frequencies", HEAT_CENTER[0])
        self.play(FadeIn(self.loc_title),
                  self._rise(self.heat, self._heat_rows(self.heat)), run_time=run_time)

    def _add_ngram(self, ch, run_time):
        top_y = self.heat.heatmaps[0].get_top()[1]
        bot_y = self.heat.heatmaps[-1].get_bottom()[1]
        self.ngram = letter_ngrams(ch, center_x=NG_X, top_y=top_y, bottom_y=bot_y)
        self.ng_title = self._title("Top", "N-grams", NG_X)
        self.play(FadeIn(self.ng_title),
                  self._rise(self.ngram, self.ngram.rows), run_time=run_time)

    def _clear_views(self, run_time=0.6):
        """Fade the heatmap + n-gram (and titles) out — removed before the next letter."""
        outs = [FadeOut(v) for v in (self.heat, self.loc_title, self.ngram,
                                     self.ng_title) if v]
        if outs:
            self.play(*outs, run_time=run_time)
        self.heat = self.loc_title = self.ngram = self.ng_title = None

    def _intro(self, i, run_time):
        """Fill tile `i` into its tier and tuck the list ↖ + send a copy ↙ — beat a's
        opening (used only for the FIRST letter, when the list is still centred)."""
        self.play(self.tier_tiles[i].animate.set_opacity(1), run_time=0.6)
        copy = self.tier_tiles[i].copy()
        self.add(copy)
        self.play(self.tl.animate.scale(TL_SHRINK).to_corner(UL, buff=TL_TOP_BUFF),
                  copy.animate.scale_to_fit_height(self._big_h)
                  .move_to(self._corner_target(copy)).set_color(BIG_COLOR),
                  run_time=run_time)
        self.corner, self.corner_home = copy, self.tier_tiles[i]

    def _advance(self, i, run_time_return, run_time_down):
        """Remove the current views, then return the corner copy AS tile `i` fades in,
        and send tile `i`'s copy ↙ — the per-letter switch for letters after the first."""
        self._clear_views()
        self._return_next(i, run_time_return)
        self._send_copy_down(self.tier_tiles[i], run_time_down)

    # ── T ─────────────────────────────────────────────────────────────────────
    # a : fill T into HIGH↓, tuck the list ↖, send a copy of T ↙
    @subscene
    def t_intro(self):
        self._intro(0, 1.2)

    # b : position-frequency heatmaps
    @subscene
    def t_heat(self):
        self._show_heat("t", 1.0)

    # c : add the n-gram view
    @subscene
    def t_ngram(self):
        self._add_ngram("t", 0.8)

    # ── N ─────────────────────────────────────────────────────────────────────
    # d : remove T's views, T's copy returns AS N fades in, then a copy of N ↙
    @subscene
    def n_intro(self):
        self._advance(1, 0.9, 1.0)

    # e : heatmaps for N
    @subscene
    def n_heat(self):
        self._show_heat("n", 1.0)

    # f : add the n-gram view for N
    @subscene
    def n_ngram(self):
        self._add_ngram("n", 0.8)

    # ── O ─────────────────────────────────────────────────────────────────────
    # g : remove N's views, N's copy returns AS O fades in, then a copy of O ↙
    @subscene
    def o_intro(self):
        self._advance(2, 0.9, 1.0)

    # h : heatmaps for O
    @subscene
    def o_heat(self):
        self._show_heat("o", 1.0)

    # i : add the n-gram view for O
    @subscene
    def o_ngram(self):
        self._add_ngram("o", 0.8)

    # j : clear views + big letter; tier list returns to CENTRE (for the next scene)
    @subscene
    def recenter(self):
        outs = [v for v in (self.corner, self.heat, self.loc_title, self.ngram,
                            self.ng_title) if v]
        self.play(*[FadeOut(m) for m in outs],
                  self.tl.animate.scale(1 / TL_SHRINK).move_to(ORIGIN), run_time=1.0)
        self.corner = self.corner_home = None
