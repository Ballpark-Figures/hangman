"""SCENE 09 — the HIGH↑ tier (S, R), letter by letter.

The same machinery as scene 07, but for the second tier (TIER_LETTERS[1] = "SR")
and treated like the test scene 96: the script (row 14) names no common-uses beats,
so each letter shows ONLY the position-frequency (heatmap) + n-gram views — no
common-uses view. Starts AND ends on a blank screen.

The named tier list (top tier already showing E/I/A from scene 07) enters CENTRED,
then — exactly as in 07 — the first letter fills into its tier, the list tucks ×0.7
to the top-left corner, and a COPY of the letter moves ↙ recolouring white→brand
blue. The next letter sends the corner copy back, appears in the tier, and sends its
own copy down.

Beats a–h (no script animation column for row 14 → mirrors 07 minus common-uses):
  a establish   named tier list (E/I/A filled) fades in, centred
  b S intro     fill S into HIGH↑; tier list → top-left; copy of S → ↙
  c S heatmap   position-frequency heatmaps (Location Frequencies)
  d S ngram     add the n-gram view (Top N-grams)
  e R intro     S's copy returns AS R fades in, then a copy of R → ↙ (views persist)
  f R heatmap   MORPH the heatmap S→R in place (96-style), fade old n-gram out
  g R ngram     rise R's n-gram content under the persistent title
  h close       fade everything out — ends blank

Heatmap/ngram numbers come from the committed caches (letter_heat_data /
letter_ngram_data), as in 96.

NOTE (extraction candidate): this shares almost all of its machinery with 07 (the
tier-list letter mechanic + the rise-in view helpers). Once 09's shape is settled,
those belong in a shared TierLetterScene base — ASK before extracting (shared change).

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every fade / move /
view run_time.

Render:  render 09a --fast  (…09h)  /  render 09 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets import tier_list as tl
from assets.letter_heatmaps import letter_heatmaps
from assets.letter_ngrams import letter_ngrams

TIER_IDX = 1                                       # HIGH↑ tier
LETTERS  = ["s", "r"]                              # = TIER_LETTERS[1] = "SR"

# tier-list tuck + big-letter geometry (identical to 07)
TL_SHRINK   = 0.7
TL_TOP_BUFF = 0.5
BIG_GROW    = 5.5
BIG_COLOR   = ACCENT_FILL

# view region (right of the tucked tier list)
HEAT_CENTER = np.array([1.6, -0.4, 0.0])
NG_X        = 6.0
TITLE_Y     = 3.2


class Scene09(HangmanScene):
    """HIGH↑ tier S/R. See module docstring for the beat map."""

    def setup_scene(self):
        # blank start: build the named tier list (top tier E/I/A already filled from
        # scene 07) but do NOT add it — beat `establish` fades it in centred. Tier-1
        # tiles (S,R) are pre-placed invisible and revealed one per intro beat.
        self.tl = tl.get_tier_list("name")
        tl.fill_tier(self.tl, 0, "EIA")            # top tier, visible (from scene 07)
        self.tier_tiles = tl.fill_tier(self.tl, TIER_IDX, "".join(LETTERS).upper())
        for t in self.tier_tiles:
            t.set_opacity(0)
        self._tl_full_h = self.tl.height
        self._tl_full_w = self.tl.width
        self._big_h = crisp_text("A", font_size=48).height * BIG_GROW
        self.corner = self.corner_home = None                  # the big ↙ copy
        self.heat = self.loc_title = None
        self.ngram = self.ng_title = None

    # ── letter mechanic (mirror of 07; extraction candidate) ────────────────────
    def _corner_target(self, tile):
        """Bottom-left rest pose for the big letter copy: centred under the tucked
        tier list, vertically centred in the gap below it."""
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

    def _morph_heat(self, ch, run_time):
        """96's letter switch: MORPH the current heatmap into `ch`'s in place
        (ReplacementTransform — the cells recolour, they don't disappear + come back)
        and fade the old n-gram content out. Both titles persist."""
        new = letter_heatmaps(ch, center=HEAT_CENTER)
        anims = [ReplacementTransform(self.heat, new)]
        if self.ngram is not None:
            anims.append(FadeOut(self.ngram))
        self.play(*anims, run_time=run_time)
        self.heat, self.ngram = new, None

    def _rise_ngram(self, ch, run_time):
        """Rise `ch`'s n-gram content in under the (persistent) Top N-grams title —
        the n-grams cross-fade letter to letter (their structure differs), as in 96."""
        top_y = self.heat.heatmaps[0].get_top()[1]
        bot_y = self.heat.heatmaps[-1].get_bottom()[1]
        new = letter_ngrams(ch, center_x=NG_X, top_y=top_y, bottom_y=bot_y)
        self.play(self._rise(new, new.rows), run_time=run_time)
        self.ngram = new

    # ── beats ───────────────────────────────────────────────────────────────────
    # a : the named tier list (E/I/A filled) fades in, centred
    @subscene
    def establish(self):
        self.play(FadeIn(self.tl), run_time=0.8)

    # b : fill S into the HIGH↑ tier, tuck the list ↖, send a copy of S ↙
    @subscene
    def s_intro(self):
        self.play(self.tier_tiles[0].animate.set_opacity(1), run_time=0.6)
        copy = self.tier_tiles[0].copy()
        self.add(copy)
        self.play(self.tl.animate.scale(TL_SHRINK).to_corner(UL, buff=TL_TOP_BUFF),
                  copy.animate.scale_to_fit_height(self._big_h)
                  .move_to(self._corner_target(copy)).set_color(BIG_COLOR),
                  run_time=1.2)
        self.corner, self.corner_home = copy, self.tier_tiles[0]

    # c : position-frequency heatmaps
    @subscene
    def s_heat(self):
        self._show_heat("s", 1.0)

    # d : add the n-gram view
    @subscene
    def s_ngram(self):
        self._add_ngram("s", 0.8)

    # e : S's copy returns AS R fades in (together), then a copy of R moves ↙
    #     (the heatmap + n-gram STAY on screen — they morph/cross-fade next)
    @subscene
    def r_intro(self):
        self._return_next(1, 0.9)
        self._send_copy_down(self.tier_tiles[1], 1.0)

    # f : morph the Location Frequencies heatmap S→R (cells recolour in place),
    #     fading the old n-gram out
    @subscene
    def r_heat(self):
        self._morph_heat("r", 1.0)

    # g : rise R's n-gram content in under the persistent Top N-grams title
    @subscene
    def r_ngram(self):
        self._rise_ngram("r", 0.8)

    # h : clear the whole screen for the next scene (ends blank)
    @subscene
    def close(self):
        outs = [self.tl] + [v for v in (self.corner, self.heat, self.loc_title,
                                        self.ngram, self.ng_title) if v]
        self.play(*[FadeOut(m) for m in outs], run_time=0.8)
