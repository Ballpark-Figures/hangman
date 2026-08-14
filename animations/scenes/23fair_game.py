"""SCENE 23 — FAIR GAME: how many misses SHOULD hangman allow?

NB the Script.md row 23 is UNFINISHED (later voiceover has ``___``/``…`` blanks); this
builds the 4 beats that ARE specified (a–d), covering the length-1 case only. The table
+ CDF are structured to extend to more lengths once the script fills in.

On the brand BG_COLOR (HangmanScene). Opens by recalling scene 19's by-length double bar
chart (a), marks the current "6 misses" limit as too high (b), then splits the frame: a
CHALKBOARD table on the LEFT (Word Length | Fair # of Misses | a gallows column) and, on
the RIGHT, the survival CDF for the current length — "Chance of Surviving" vs "# of
Misses" (c) — before filling the length-1 row (d).

Script row 23 splits on '—' → 4 beats, one @subscene each (a–d).

SOURCED DATA
  • the survival CDF = `assets/scene23_data.py` (committed `scene23_cache.json`): per
    length, P(surviving within k misses) for the WINPROB (survival-optimal) guesser vs
    the BEST_OPENER word-choice distribution. Exact points come straight from the
    committed winprob solves `math/data/shared/winprob/lenNN_best_opener_nNN.json`; the
    tail past the top solved budget (lengths 3–7 only) is greedy-completed and flagged
    `exact=False` (drawn crimson + a "values not exact" note). Length 1 is fully exact
    (0.5 at 0 misses → the 50-50 the voiceover cites → 1.0 at 1 miss).
  • beat-a double chart = the SAME numbers as scene 19 (`short_words_data.by_length`,
    optimal avg misses per length, uniform vs better choosing).

REUSE MAP (element → shared source)
  • double bar chart (a)        → bpkfigures.bar_graph.grouped_bar_chart + grow_bars,
                                  short_words_data.by_length — scene 19's `_double_chart`.
  • y=6 / 50% reference lines    → DashedLine at chart.y_of(6) / the CDF chart base+0.5·h.
  • chalkboard + chalk table (c) → assets.chalkboard (chalkboard / chalk_phrase /
                                  chalk_number) — the same slate + written font as 22/94.
  • survival CDF bars (c)        → bpkfigures.bar_graph.get_bar_chart (blue ACCENT_FILL;
                                  `highlight={label: CRIMSON}` for inexact tail bars) +
                                  grow_bars entrance.
  • gallows + purple oval (d)    → mini gallows (chalk lines) + one tall Ellipse tinted by
                                  `_miss_color(1)` = LIGHT_PALETTE purple (the intro tree's
                                  1-miss colour).

FLAGS (owned by a human — tune/decide later)
  • The y=6 line (b) and the 50% line (c) are drawn CRIMSON / BLACK dashed; recolour to
    taste. "6" = the usual full-gallows limit the voiceover calls too high.
  • Fair # of Misses = 1 for length 1 is the SCRIPT's value (the 50-50-at-one-miss
    argument), not a computed fairness rule — no fairness metric is defined yet.
  • all geometry (chalkboard box, table columns, graph box) + run_times = guesses.

BEAT MAP
  a double_plot  — recall scene 19's by-length double bar chart (uniform vs better choosing)
  b line_at_6    — dashed reference line at y=6 misses across that chart
  c fair_setup   — chart out; LEFT chalkboard + empty table, RIGHT "1-Letter Words" survival
                   CDF (# of Misses vs Chance of Surviving) + a dashed 50% line
  d fill_row_1   — fill the length-1 row (1 | 1) + draw a gallows with a tall purple oval

Render:  render 23a --fast   (…23d)   /   render 23 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from bpkfigures.bar_graph import grouped_bar_chart, get_bar_chart, grow_bars
from assets import short_words_data
from assets import scene23_data
from assets.word_tables_scene import UNIFORM_COLOR, BESTOP_COLOR, INK
from assets.chalkboard import chalkboard, chalk_phrase, chalk_number, CHALK

# ── beat b : the "too high" reference line ────────────────────────────────────
LIMIT_MISSES = 6

# ── beat c : chalkboard table (LEFT) ──────────────────────────────────────────
CB_CX, CB_W, CB_H = -4.15, 7.5, 7.7          # chalkboard prop, left half
COL_LEN_X, COL_FAIR_X, COL_GAL_X = -6.5, -4.35, -2.05   # 3 column centres
HEADER_Y = 2.85                              # header baseline band
RULE_Y = 2.15                                # underline below headers
ROW_Y0, ROW_DY = 1.35, -1.05                 # first data row, per-row step (future rows)

# ── beat c : survival CDF (RIGHT) ─────────────────────────────────────────────
GRAPH_CX, GRAPH_CY, GRAPH_W, GRAPH_H = 4.2, -0.35, 5.2, 3.9


def _miss_color(n):
    """The intro tree's per-miss-count colour (1→purple … 6→red)."""
    return LIGHT_PALETTE[len(LIGHT_PALETTE) - n]


def _strokes(*chalk_mobs):
    """Flatten chalk phrases/numbers to their individual STROKES (phrase→glyph→
    stroke) so `LaggedStartMap(Create, …)` writes them one stroke at a time — Create
    over a whole multi-stroke glyph inside a LaggedStart throws."""
    out = VGroup()
    for m in chalk_mobs:
        for glyph in m:
            for stroke in glyph:
                out.add(stroke)
    return out


class Scene23(HangmanScene):
    """Fair game — how many misses hangman should allow. See docstring for beats."""

    def setup_scene(self):
        self.chart = None
        self.line6 = None
        self.cb = None
        self.table = None            # headers + rule (built in c)
        self.cdf = None              # the right-side survival-CDF chart group
        self.cdf_extra = None        # its axis titles + 50% line + chart title
        self.row1 = None

    # ── a : recall scene 19's by-length double bar chart ──────────────────────
    def _double_chart(self):
        data = short_words_data.get()["by_length"]
        lengths = sorted(int(L) for L in data["uniform"])
        uni = [data["uniform"][str(L)]["avg"] for L in lengths]
        best = [data["best_opener"][str(L)]["avg"] for L in lengths]
        return grouped_bar_chart(
            lengths, [("Uniform", UNIFORM_COLOR, uni),
                      ("Better Choosing", BESTOP_COLOR, best)],
            title="Optimal Misses per Word", x_title="Word Length", ink_color=INK)

    @subscene
    def double_plot(self):
        self.chart = self._double_chart()
        self.chart.rest.set_opacity(0)
        self.add(self.chart)
        grow_bars(self, self.chart.bars, 1.2, lag=0.02,
                  extra=[self.chart.rest.animate.set_opacity(1)])

    # ── b : dashed reference line at y=6 misses ───────────────────────────────
    def _setup_line_at_6(self):
        g = self.chart.chart_geom
        y = g["base_y"] + LIMIT_MISSES / g["ymax"] * g["height"]
        self.line6 = DashedLine([-g["width"] / 2, y, 0], [g["width"] / 2, y, 0],
                                color=CRIMSON, stroke_width=4, dash_length=0.16)

    @subscene
    def line_at_6(self):
        self._setup_line_at_6()
        self.play(Create(self.line6), run_time=0.8)

    # ── chalkboard table (LEFT) ───────────────────────────────────────────────
    def _setup_board(self):
        self.cb = chalkboard(CB_W, CB_H, center=[CB_CX, 0, 0])
        self.cb.set_z_index(-10)
        # two-line chalk headers so each fits its narrow column
        def header(lines, x):
            g = VGroup(*[chalk_phrase(t, height=0.24, stroke_width=2.8) for t in lines])
            g.arrange(DOWN, buff=0.10).move_to([x, HEADER_Y, 0])
            return g
        h_len = header(["WORD", "LENGTH"], COL_LEN_X)
        h_fair = header(["FAIR # OF", "MISSES"], COL_FAIR_X)
        rule = Line([COL_LEN_X - 0.95, RULE_Y, 0], [COL_GAL_X + 0.95, RULE_Y, 0],
                    color=CHALK, stroke_width=3)
        self.table = VGroup(h_len, h_fair, rule)

    # ── survival CDF (RIGHT) ──────────────────────────────────────────────────
    def _cdf_chart(self, length):
        pts = scene23_data.get()["cdf"][str(length)]
        items = [(str(p["misses"]), p["p_win"]) for p in pts]
        # inexact (greedy-tail) bars go crimson; exact bars stay blue
        highlight = {str(p["misses"]): CRIMSON for p in pts if not p["exact"]}
        title = crisp_text(f"{length}-Letter Words", font_size=28, color=INK, weight=BOLD)
        chart = get_bar_chart(
            items, center=[GRAPH_CX, GRAPH_CY, 0], width=GRAPH_W, height=GRAPH_H,
            y_min=0.0, y_max=1.0, bar_color=ACCENT_FILL, ink_color=INK,
            highlight=highlight, bar_ratio=0.55,
            label_factory=lambda s: crisp_text(s, font_size=20, color=INK),
            label_buff=0.14, x_axis=True, y_axis=True, y_ticks=[0.0, 0.5, 1.0],
            y_tick_factory=lambda t: crisp_text(f"{int(t * 100)}%", font_size=18,
                                                color=INK),
            y_tick_buff=0.12, title_mobject=title, title_buff=0.3)
        return chart

    def _cdf_axis_titles(self, chart):
        g = chart.chart_geom
        xt = crisp_text("# of Misses", font_size=20, color=INK)
        xt.next_to(chart.labels, DOWN, buff=0.22).set_x(GRAPH_CX)
        yt = crisp_text("Chance of Surviving", font_size=20, color=INK).rotate(PI / 2)
        yt.next_to(chart.yticks, LEFT, buff=0.2).set_y(GRAPH_CY)
        return VGroup(xt, yt)

    def _fifty_line(self):
        base = GRAPH_CY - GRAPH_H / 2                      # y=0 axis
        y50 = base + 0.5 * GRAPH_H                         # y_max=1 → 50% at cy
        return DashedLine([GRAPH_CX - GRAPH_W / 2, y50, 0],
                          [GRAPH_CX + GRAPH_W / 2, y50, 0],
                          color=INK, stroke_width=3, dash_length=0.14)

    # ── c : chart out; chalkboard + empty table, "1-Letter Words" CDF + 50% line
    @subscene
    def fair_setup(self):
        self.play(FadeOut(self.chart), FadeOut(self.line6), run_time=0.6)
        self.chart = self.line6 = None

        self._setup_board()
        self.play(FadeIn(self.cb), run_time=0.6)
        h_len, h_fair, rule = self.table
        self.play(LaggedStartMap(Create, _strokes(*h_len, *h_fair), lag_ratio=0.5),
                  run_time=1.4)
        self.play(Create(rule), run_time=0.5)

        self.cdf = self._cdf_chart(1)
        self.cdf_extra = self._cdf_axis_titles(self.cdf)
        rest = VGroup(self.cdf.labels, self.cdf.x_axis, self.cdf.y_axis,
                      self.cdf.yticks, self.cdf.title, self.cdf_extra)
        rest.set_opacity(0)
        self.add(self.cdf, self.cdf_extra)
        grow_bars(self, self.cdf.bars, 1.2, lag=0.08,
                  extra=[rest.animate.set_opacity(1)])
        self.fifty = self._fifty_line()
        self.play(Create(self.fifty), run_time=0.7)

    # ── mini gallows with one tall body oval, for the table's gallows column ──
    def _mini_gallows(self, color):
        sw = 3.0
        base = Line([-0.34, -0.46, 0], [0.06, -0.46, 0], color=CHALK, stroke_width=sw)
        post = Line([-0.30, -0.46, 0], [-0.30, 0.46, 0], color=CHALK, stroke_width=sw)
        beam = Line([-0.30, 0.46, 0], [0.12, 0.46, 0], color=CHALK, stroke_width=sw)
        rope = Line([0.12, 0.46, 0], [0.12, 0.30, 0], color=CHALK, stroke_width=sw)
        oval = Ellipse(width=0.17, height=0.36, color=color, fill_color=color,
                       fill_opacity=1.0, stroke_width=2).move_to([0.12, 0.11, 0])
        g = VGroup(base, post, beam, rope, oval)
        g.frame, g.oval = VGroup(base, post, beam, rope), oval
        return g

    # ── d : fill the length-1 row (1 | 1) + gallows with a tall purple oval ───
    def _setup_row1(self):
        n_len = chalk_number(1, height=0.42, stroke_width=3.2).move_to(
            [COL_LEN_X, ROW_Y0, 0])
        n_fair = chalk_number(1, height=0.42, stroke_width=3.2).move_to(
            [COL_FAIR_X, ROW_Y0, 0])
        gal = self._mini_gallows(_miss_color(1)).move_to([COL_GAL_X, ROW_Y0, 0])
        self.row1 = VGroup(n_len, n_fair, gal)

    @subscene
    def fill_row_1(self):
        self._setup_row1()
        n_len, n_fair, gal = self.row1
        self.play(LaggedStartMap(Create, _strokes(n_len), lag_ratio=0.5), run_time=0.6)
        self.play(LaggedStartMap(Create, _strokes(n_fair), lag_ratio=0.5), run_time=0.6)
        self.play(LaggedStartMap(Create, gal.frame, lag_ratio=0.8), run_time=1.0)
        self.play(GrowFromCenter(gal.oval), run_time=0.5)
