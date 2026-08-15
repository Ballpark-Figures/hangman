"""SCENE 14 — the LOW↑ tier (F, Y, V, W, K), letter by letter.

Built on the shared `TierLetterScene` base (assets/tier_letter_scene.py). Back-to-back
continuation of scene 13: opens on the named tier list CENTRED (TOP…MID↓ filled), works
the LOW↑ tier (TIER_LETTERS[5] = "FYVWK") with heatmap + n-gram views per letter (no
common-uses, like 96), and recenters at the end for scene 15.

Presented in straight tier order F, Y, V, W, K (matches the row-21 narration; the tier
lists W above K, so no out-of-order reveal).

START-MODE ASSUMPTION (flag): continuation of 13 (centred). If a talking head / the
row-20 "bottom-tier shoutout" clears the screen before this, flip to a blank start:
`build_board(on_screen=False)` + an `establish` beat (`self.enter_centered(0.8)`).

F/V/W each run intro → heatmap → n-gram. The Y section is expanded: after Y's big-letter
intro come three example-word beats (e/f/g) and a common-uses beat (j) closing the section;
K then gets a SPECIAL staged position-frequency reveal (the Tversky-Kahneman availability-
heuristic bit) instead of a single heatmap beat, then its n-gram + recenter.
  a f_intro · b f_heat · c f_ngram
  d y_intro        — Y fills in, big copy ↙
  e y_words_blue   — YESTERYEAR (large, Ys BLUE) fades in rising
  f y_words_crimson— SLYLY (large, Ys CRIMSON) fades in rising below it
  g y_words_out    — both example words fade out
  h y_heat · i y_ngram
  j y_common       — "Example Uses" — Y's top 4 table cases (optimal/uniform)
  k v_intro · l v_heat · m v_ngram · n w_intro · o w_heat · p w_ngram
  q k_intro        — K fills in, copy ↙ (unchanged advance)
  r k_heat_gray    — position-frequency view enters with ALL boxes GREY (no data yet)
  s k_flash_cols   — flash column 1, then column 3 (yahtzee row-highlight style)
  t k_reveal_c1    — colour position 1 only; vmax = that column's max (full range on it)
  u k_reveal_c3    — colour positions 1-3; vmax = cols-1-3 max (col 1 washes out)
  v k_reveal_all   — colour every position; final vmax = data max (position 4 dominates)
  w k_ngram        — add the n-gram view (C/N/L/R)
  x recenter       — hand off to scene 15
The staged vmax rescaling IS the payoff: col 1 looks saturated at p, then washes out as
positions 3 then 4 reveal a higher max. Hue stays BLUE (K's consonant convention) at
every stage; `k_reveal_all` reproduces the standard `show_heat("k")` state exactly, so
`add_ngram` reads `self.heat` unchanged.

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every run_time below.

Render:  render 14a --fast  (…14x)  /  render 14 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets import tier_list as tl
from assets import letter_heat_data as lhd
from assets.letter_heatmaps import letter_heatmaps
from assets.tier_letter_scene import TierLetterScene, HEAT_CENTER

# ── Y example-word beats (inserted after Y's big-letter intro) ────────────────
# Two large hero words showing Y in different roles, stacked in the empty view
# region (centre-right). Ys recoloured to CONTRAST: YESTERYEAR blue, SLYLY crimson;
# the other letters stay the title ink (BLACK). Each fades in while rising (UP*RISE).
WORD_FS   = 90                                    # large display font
WORD_BUFF = 0.06                                  # per-letter spacing
WORD_INK  = BLACK                                 # non-Y letters (matches the titles)
WORD1_CTR = np.array([1.6, 1.1, 0.0])             # YESTERYEAR centre
WORD2_CTR = np.array([1.6, -1.2, 0.0])            # SLYLY centre (below it)
WORD_RISE = 0.6                                    # fade-in upward travel

# Y's common-uses ("Example Uses") states — the TOP 4 rows of
# guesses_of_letter_all_lengths('y') [optimal/uniform], n_words DESC. SOURCED +
# reproducible via math/common_uses_scene14.py (prints these exact rows).
# Each spec is (length, board, missed).
Y_COMMON = [
    (5, "_a___",  ["e", "r", "s", "t"]),
    (5, "_u___",  ["a", "c", "e", "i", "o", "s"]),
    (5, "_i___",  ["a", "e", "o", "s", "t"]),
    (6, "_o____", ["a", "e", "n", "s"]),
]


class Scene14(TierLetterScene):
    """LOW↑ tier F/Y/V/W/K, continuing scene 13. See docstring for the beat map."""

    TIER_IDX = 5
    LETTERS  = ["f", "y", "v", "w", "k"]             # = TIER_LETTERS[5]
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

    # example-word helper: one large word with its Y's recoloured, built at `center`
    def _word_row(self, word, ys, color, center):
        row = VGroup(*[crisp_text(ch, font_size=WORD_FS, color=WORD_INK)
                       for ch in word])
        row.arrange(RIGHT, buff=WORD_BUFF, aligned_edge=DOWN)   # caps → shared baseline
        for i in ys:
            row[i].set_color(color)
        return row.move_to(center)

    def _setup_yword1(self):
        # YESTERYEAR — Ys (indices 0, 6) in blue
        self.yword1 = self._word_row("YESTERYEAR", [0, 6], ACCENT_FILL, WORD1_CTR)

    def _setup_yword2(self):
        # SLYLY — Ys (indices 2, 4) in crimson
        self.yword2 = self._word_row("SLYLY", [2, 4], CRIMSON, WORD2_CTR)

    # e : YESTERYEAR (Ys blue) fades in while rising
    @subscene
    def y_words_blue(self):
        self._setup_yword1()
        self.play(FadeIn(self.yword1, shift=UP * WORD_RISE), run_time=0.9)

    # f : SLYLY (Ys crimson) fades in while rising, below it
    @subscene
    def y_words_crimson(self):
        self._setup_yword2()
        self.play(FadeIn(self.yword2, shift=UP * WORD_RISE), run_time=0.9)

    # g : both example words fade out
    @subscene
    def y_words_out(self):
        self.play(FadeOut(self.yword1), FadeOut(self.yword2), run_time=0.7)
        self.yword1 = self.yword2 = None

    # h : heatmaps for Y
    @subscene
    def y_heat(self):
        self.show_heat("y", 1.0)

    # i : add the n-gram view for Y
    @subscene
    def y_ngram(self):
        self.add_ngram("y", 0.8)

    # j : common-uses — Y's top 4 table cases (swaps in over the heat + n-gram)
    @subscene
    def y_common(self):
        self.show_common(Y_COMMON, 0.9)

    # ── V ───────────────────────────────────────────────────────────────────────
    # k : V's turn
    @subscene
    def v_intro(self):
        self.advance_letter(2, 0.9, 1.0)

    # l : heatmaps for V
    @subscene
    def v_heat(self):
        self.show_heat("v", 1.0)

    # m : add the n-gram view for V
    @subscene
    def v_ngram(self):
        self.add_ngram("v", 0.8)

    # ── W ───────────────────────────────────────────────────────────────────────
    # n : W's turn
    @subscene
    def w_intro(self):
        self.advance_letter(3, 0.9, 1.0)

    # o : heatmaps for W
    @subscene
    def w_heat(self):
        self.show_heat("w", 1.0)

    # p : add the n-gram view for W
    @subscene
    def w_ngram(self):
        self.add_ngram("w", 0.8)

    # ── K — the staged position-frequency reveal (availability heuristic) ────────
    # K's heatmap builds in gray, flashes cols 1 & 3, then reveals position-by-position
    # with the colour scale rescaling each step (see docstring). Helpers below drive it.

    def _k_gray_view(self):
        """Build K's position-frequency view (same geometry as `show_heat("k")`) but
        with every cell GREY — no data revealed yet. Sets self.heat / self.loc_title so
        the base's add_ngram / recenter work unchanged."""
        self.heat = letter_heatmaps("k", center=HEAT_CENTER, high_color=tl.heat_color("k"))
        for hm in self.heat.heatmaps:
            for sq in hm.cells[0]:
                sq.set_fill(MUTED_GREY, opacity=1.0)
        self.loc_title = self._title1("Position Frequencies", HEAT_CENTER[0])

    def _vmax_over(self, cols):
        """Max K-share over the given position columns (0-indexed), across every length
        that HAS that column — the top of the white→blue scale for a partial reveal."""
        data = lhd.get("k")
        vals = [data["rows"][L][c] for L in data["lengths"]
                for c in cols if c < len(data["rows"][L])]
        return max(vals) if vals else 0.0

    def _recolor_cols(self, cols, vmax, run_time):
        """Colour the cells in `cols` white→blue by K-share against `vmax` (cells not in
        `cols` stay whatever they are — grey until revealed). ALL cells transition to
        their next colour AT ONCE (one simultaneous play), so an already-coloured column
        eases from its old scale to the new one as freshly-revealed columns come off grey.
        `vmax = data['vmax']` over ALL columns reproduces `letter_heatmaps`."""
        data = lhd.get("k")
        hi = tl.heat_color("k")
        anims = []
        for i, L in enumerate(data["lengths"]):
            shares = data["rows"][L]
            for c in cols:
                if c >= len(shares):
                    continue
                alpha = min(shares[c] / vmax, 1.0) if vmax > 0 else 0.0
                col = interpolate_color(WHITE, hi, alpha)
                anims.append(self.heat.heatmaps[i].cells[0][c]
                             .animate.set_fill(col, opacity=1.0))
        self.play(*anims, run_time=run_time)

    def _flash_column(self, c, run_time):
        """Flash position-column `c` yahtzee-style: a soft ACCENT_GOLD fill + thick black
        border over the column strip, fade in → hold → fade out. `run_time` scales the
        WHOLE flash (default split 0.25 in · 0.8 hold · 0.25 out)."""
        data = lhd.get("k")
        cells = [self.heat.heatmaps[i].cells[0][c]
                 for i, L in enumerate(data["lengths"]) if c < len(data["rows"][L])]
        top = max(sq.get_top()[1] for sq in cells)
        bot = min(sq.get_bottom()[1] for sq in cells)
        x, w = cells[0].get_center()[0], cells[0].width
        center = [x, (top + bot) / 2, 0]
        fill = Rectangle(width=w, height=top - bot, stroke_width=0,
                         fill_color=ACCENT_GOLD, fill_opacity=0.45).move_to(center)
        border = Rectangle(width=w, height=top - bot, fill_opacity=0,
                           stroke_color=BLACK, stroke_width=3.0).move_to(center)
        r = run_time / 1.3
        self.play(FadeIn(fill), FadeIn(border), run_time=0.25 * r)
        self.wait(0.8 * r)
        self.play(FadeOut(fill), FadeOut(border), run_time=0.25 * r)
        self.remove(fill, border)

    # q : K's turn — fill in, copy ↙
    @subscene
    def k_intro(self):
        self.advance_letter(4, 0.9, 1.0)

    # r : position-frequency view enters, every box GREY (no data yet)
    @subscene
    def k_heat_gray(self):
        self._k_gray_view()
        self.play(FadeIn(self.loc_title),
                  self._rise(self.heat, self._heat_rows(self.heat)), run_time=1.0)

    # s : flash the 1st column, then the 3rd column (availability-heuristic setup)
    @subscene
    def k_flash_cols(self):
        self._flash_column(0, 1.3)          # position 1
        self._flash_column(2, 1.3)          # position 3

    # t : reveal position 1 only — scale so the full white→blue range covers just it
    @subscene
    def k_reveal_c1(self):
        self._recolor_cols([0], self._vmax_over([0]), 1.0)

    # u : reveal positions 1-3 — rescale so the range now covers cols 1-3 (col 1 washes out)
    @subscene
    def k_reveal_c3(self):
        self._recolor_cols([0, 1, 2], self._vmax_over([0, 1, 2]), 1.0)

    # v : reveal the rest — final scale (data vmax); position 4 dominates
    @subscene
    def k_reveal_all(self):
        data = lhd.get("k")
        ncols = max(len(data["rows"][L]) for L in data["lengths"])
        self._recolor_cols(list(range(ncols)), data["vmax"], 1.0)

    # w : add the n-gram view for K
    @subscene
    def k_ngram(self):
        self.add_ngram("k", 0.8)

    # x : clear views + big letter; tier list returns to CENTRE (for scene 15)
    @subscene
    def recenter(self):
        self.recenter_board(1.0)
