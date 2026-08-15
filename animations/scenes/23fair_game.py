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
    tail past the top solved budget (lengths 3–7 only) is the MAX of two achievable
    strategies (winprob-continuation + optimal), flagged `exact=False` (drawn crimson +
    a "*values not exact" note). Length 1 is fully exact (0.5 at 0 misses → the 50-50 the
    voiceover cites → 1.0 at 1 miss).
  • beat-a double chart = the SAME numbers as scene 19 (`short_words_data.by_length`,
    optimal avg misses per length, uniform vs better choosing).

REUSE MAP (element → shared source)
  • double bar chart (a)        → bpkfigures.bar_graph.grouped_bar_chart + grow_bars,
                                  short_words_data.by_length — scene 19's `_double_chart`.
  • y=6 / 50% reference lines    → DashedLine at chart.y_of(6) / the CDF chart base+0.5·h.
  • chalkboard + chalk table (c) → bpkfigures.chalkboard (chalkboard / chalk_phrase /
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
                   CDF (Misses before Losing vs Chance of Surviving) + a dashed 50% line
  d fill_row_1   — fill the length-1 row (1 | 1) + gallows with a tall purple-oval head
  e switch_to_2  — switch to 2-letter words: morph the CDF 1->2 letters (title crossfades)
                   and write ONLY the "2" in the Word Length column (row 2, nothing else)
  f fill_row_2   — length-2 fair number (4) + the colour-coded gallows (head purple, body
                   blue, arms green, legs yellow — each part = the intro tree's miss colour)
  g switch_to_3  — switch to 3-letter words: morph the CDF 2->3; the first INEXACT (estimated-
                   tail) bars appear crimson (50% line turns blue over them) + caption; write "3"
  h fill_row_3   — length-3 fair number (8) + DRAWING: split gallows (base purple + rest
                   blue) then a standard 6-part hangman, through all 8 colours
  i switch_to_4  — switch to 4-letter words: morph the CDF 3->4; write "4" (nothing else)
  j fill_row_4   — length-4 fair number (7) + DRAWING: the whole gallows as ONE stroke
                   (no bottom-left stub) then a standard hangman (7 elements)
  k switch_to_5  — switch to 5-letter words: morph the CDF 4->5; write "5" (nothing else)
  l fill_row_5   — length-5 fair number (5) + DRAWING: chalk gallows + head/torso/arm-line/
                   two legs (5 elements)
  m switch_to_6  — morph to 6-letter; write the "6" of the centred "6-7" AS the graph morphs
  n fill_row_6   — length-6 fair number (4 — bar 4 is nearest 50%) + the fair-4 drawing
  o switch_to_7  — length 7 shares fair 4: write the "-7" of "6-7" as the 7-graph appears
  p switch_to_8  — switch to 8-letter words; write "8" (crimson caption clears — len 8+ exact)
  q fill_row_8   — length-8 fair number (3) + a 3-circle SNOWMAN on the gallows (top->bottom)
  r switch_to_9  — switch to 9-letter words; write "9"
  s fill_row_9   — length-9 fair number (2) + a 2-circle SNOWMAN on the gallows
  t switch_to_10plus — morph to 10-letter; write the "10" of the centred "10+"
  u plus_11      — morph to 11-letter; write the "+" (completes "10+")
  v march_to_16  — keep morphing 12..16 (all still fair 1); the fair "1" (12), gallows (13)
                   and oval (14) are drawn DURING this march, not after

Word-length labels are written AS the CDF morphs to that length (via _morph_cdf's
`extra_move`), not after. Every DRAWING is coloured to END at red (see _draw_colors) — an
N-element drawing uses the last N of [deep-red, deep-purple, purple, blue, green, yellow,
orange, red]; snowmen are yellow/orange/red top->bottom. Drawings are STAGGERED — odd word
lengths on the left of the Drawing column, even on the right.

NB beats e–v run AHEAD of Script.md's animation column (still 4 segments); they animate the
length-2..16 part of beat-d's voiceover ("With 2 letters, the closest we can get is …").
The dashed 50%/y=6 reference lines are z-indexed ABOVE the bars and turn BLUE where they
pass over crimson bars; a CDF morph moves the shared bars first, then GROWS the brand-new
bars up from the axis (not a simultaneous fade-in).

Render:  render 23a --fast   (…23v)   /   render 23 sub  for the whole scene
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
from bpkfigures.chalkboard import chalkboard, chalk_phrase, chalk_number, CHALK

# ── beat b : the "too high" reference line ────────────────────────────────────
LIMIT_MISSES = 6

# ── beat c : layout ───────────────────────────────────────────────────────────
# ONE equal gap separates frame-left | board | graph | frame-right, AND is the
# board's left/top/bottom margin — so the board's width + the graph's placement are
# DERIVED from this margin + the measured graph width (see fair_setup).
MARGIN = 0.6
COL_DX = (-2.2, 0.0, 2.2)                     # table column x-offsets from board centre
DRAW_DX = 0.55                                # stagger: odd lengths LEFT, even lengths RIGHT
DRAW_SCALE = 0.85                             # shrink drawings so 9 rows fit the board
HEADER_Y = 2.85                              # header baseline band
RULE_Y = 2.15                                # underline below headers
ROW_Y0, ROW_DY = 1.6, -0.58                  # first data row, per-row step (fits 9 rows)

# ── beat c : survival CDF (RIGHT) — nominal box; placed by fair_setup ──────────
GRAPH_CX, GRAPH_CY, GRAPH_W, GRAPH_H = 4.2, -0.35, 5.2, 3.9


def _miss_color(n):
    """The intro tree's per-miss-count colour (1→purple … 6→red)."""
    return LIGHT_PALETTE[len(LIGHT_PALETTE) - n]


# Drawing colours: a drawing ALWAYS ENDS at red. FULL_COLORS is the full 8-long ramp
# ending at red — two DEEPER shades, then the rainbow (purple→red). An N-element drawing
# uses the LAST N of these (n<=6 = a rainbow suffix; 7 prepends deep purple; 8 deep red too).
DEEP_RED = interpolate_color(LIGHT_RED, BLACK, 0.4)
DEEP_PURPLE = interpolate_color(LIGHT_PURPLE, BLACK, 0.4)
FULL_COLORS = [DEEP_RED, DEEP_PURPLE] + [_miss_color(k) for k in range(1, 7)]


def _draw_colors(n):
    """The n drawing colours in draw order, always ending at red (LIGHT_RED)."""
    return FULL_COLORS[-n:]


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
        self.col_x = None            # the 3 table column x's (set when the board is placed)
        self.cdf = None              # the right-side survival-CDF chart group (current length)
        self.cdf_extra = None        # its axis titles
        self.fifty = None            # the dashed 50% line
        self.row1 = None
        self.len2 = None             # length-2 row label (e)
        self.fair2 = self.gal2 = None    # length-2 fair number + gallows (f)
        self.len3 = None             # length-3 row label (g)
        self.asterisk = None         # "values not exact" crimson-tail caption (g)
        self.fair3 = self.draw3 = None   # length-3 fair number + drawing (h)
        self.len4 = None             # length-4 row label (i)
        self.fair4 = self.draw4 = None   # length-4 fair number + drawing (j)
        self.len5 = None             # length-5 row label (k)
        self.fair5 = self.draw5 = None   # length-5 fair number + drawing (l)
        self.len67 = None            # the centred "6-7" label (6 at m, -7 at o)
        self.fair6 = self.gal6 = None    # length-6 fair number + drawing (n)
        self.len8 = self.fair8 = self.snow8 = None    # length-8 row (p/q)
        self.len9 = self.fair9 = self.snow9 = None    # length-9 row (r/s)
        self.len10p = self.fair10 = self.draw10 = None  # length-10+ row (t..w)

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
        # blue where the line passes over a crimson (best_opener) bar tall enough to reach it
        crimson_bars = self.chart.series[1].bars
        blue = [(b.get_left()[0], b.get_right()[0]) for b in crimson_bars
                if b.get_top()[1] >= y - 1e-3]
        self.line6 = self._split_dashed(y, -g["width"] / 2, g["width"] / 2, blue,
                                        stroke_width=4, dash_length=0.16)

    @subscene
    def line_at_6(self):
        self._setup_line_at_6()
        self.play(Create(self.line6), run_time=0.8)

    # ── chalkboard table (LEFT) ───────────────────────────────────────────────
    def _setup_board(self, cx, w, h):
        self.cb = chalkboard(w, h, center=[cx, 0, 0])
        self.cb.set_z_index(-10)
        self.col_x = [cx + dx for dx in COL_DX]
        # two-line chalk headers so each fits its narrow column
        def header(lines, x):
            g = VGroup(*[chalk_phrase(t, height=0.24, stroke_width=2.8, space=0.18)
                         for t in lines])
            g.arrange(DOWN, buff=0.10).move_to([x, HEADER_Y, 0])
            return g
        h_len = header(["WORD", "LENGTH"], self.col_x[0])
        h_fair = header(["FAIR # OF", "MISSES"], self.col_x[1])
        h_draw = header(["DRAWING"], self.col_x[2])
        half = w / 2 - 0.5
        rule = Line([cx - half, RULE_Y, 0], [cx + half, RULE_Y, 0],
                    color=CHALK, stroke_width=3)
        self.table = VGroup(h_len, h_fair, h_draw, rule)

    # ── survival CDF (RIGHT) ──────────────────────────────────────────────────
    def _cdf_chart(self, length):
        pts = scene23_data.get()["cdf"][str(length)]
        # x-axis = "misses before losing" = miss budget + 1 (a game that ENDS at m
        # misses lets the guesser survive within m-1), so budget 0 -> label 1, etc.
        items = [(str(p["misses"] + 1), p["p_win"]) for p in pts]
        # inexact (estimated tail) bars go crimson; exact bars stay blue
        highlight = {str(p["misses"] + 1): CRIMSON for p in pts if not p["exact"]}
        title = crisp_text(f"{length}-Letter Words", font_size=28, color=INK, weight=BOLD)
        chart = get_bar_chart(
            items, center=[GRAPH_CX, GRAPH_CY, 0], width=GRAPH_W, height=GRAPH_H,
            y_min=0.0, y_max=1.0, bar_color=ACCENT_FILL, ink_color=INK,
            highlight=highlight, bar_ratio=1.0,
            label_factory=lambda s: crisp_text(s, font_size=20, color=INK),
            label_buff=0.14, x_axis=True, y_axis=True, y_ticks=[0.0, 0.5, 1.0],
            y_tick_factory=lambda t: crisp_text(f"{int(t * 100)}%", font_size=18,
                                                color=INK),
            y_tick_buff=0.12, title_mobject=title, title_buff=0.3)
        return chart

    def _cdf_axis_titles(self, chart):
        g = chart.chart_geom
        xt = crisp_text("Misses before Losing", font_size=20, color=INK)
        xt.next_to(chart.labels, DOWN, buff=0.22).set_x(GRAPH_CX)
        yt = crisp_text("Chance of Surviving", font_size=20, color=INK).rotate(PI / 2)
        yt.next_to(chart.yticks, LEFT, buff=0.2).set_y(GRAPH_CY)
        return VGroup(xt, yt)

    def _split_dashed(self, y, x_left, x_right, blue_intervals, *, stroke_width=3,
                      dash_length=0.14):
        """A dashed horizontal line at height ``y`` from ``x_left`` to ``x_right``, drawn
        BLUE (ACCENT_FILL) across the given ``blue_intervals`` (x-ranges over crimson bars)
        and CRIMSON elsewhere. z-indexed above the bars."""
        def dash(a, b, col):
            return DashedLine([a, y, 0], [b, y, 0], color=col, stroke_width=stroke_width,
                              dash_length=dash_length)
        ivs = sorted((max(a, x_left), min(b, x_right))
                     for a, b in blue_intervals if min(b, x_right) > max(a, x_left))
        seg = VGroup()
        x = x_left
        for a, b in ivs:
            if b <= x:
                continue
            a = max(a, x)
            if a > x:
                seg.add(dash(x, a, CRIMSON))
            seg.add(dash(a, b, ACCENT_FILL))
            x = b
        if x < x_right:
            seg.add(dash(x, x_right, CRIMSON))
        seg.set_z_index(10)
        return seg

    def _fifty_line(self, length, chart=None):
        """Dashed 50% reference line across the positioned CDF chart; blue over the
        crimson (inexact) bars, crimson elsewhere. Reads geometry off ``chart`` (defaults
        to the current self.cdf) so it can be built for the INCOMING chart mid-morph."""
        chart = chart if chart is not None else self.cdf
        xa = chart.x_axis
        left, right = xa.get_left()[0], xa.get_right()[0]
        y = xa.get_center()[1] + 0.5 * GRAPH_H            # y_min 0, y_max 1 → 50% halfway
        crim = [i for i, p in enumerate(scene23_data.get()["cdf"][str(length)])
                if not p["exact"]]
        blue = [(chart.bars[crim[0]].get_left()[0], right)] if crim else []
        return self._split_dashed(y, left, right, blue)

    # ── c : chart out; chalkboard + empty table, "1-Letter Words" CDF + 50% line
    @subscene
    def fair_setup(self):
        self.play(FadeOut(self.chart), FadeOut(self.line6), run_time=0.6)
        self.chart = self.line6 = None

        m = MARGIN
        # build the graph, MEASURE it, then derive the board width + graph placement so
        # frame-left|board|graph|frame-right are separated by equal gaps m and the
        # board's left/top/bottom margins are all m too (board vertically centred).
        self.cdf = self._cdf_chart(1)
        self.cdf_extra = self._cdf_axis_titles(self.cdf)
        graph = VGroup(self.cdf, self.cdf_extra)
        cb_w, cb_h = 16 - 3 * m - graph.width, 9 - 2 * m
        board_cx = -8 + m + cb_w / 2
        graph.shift(RIGHT * ((-8 + 2 * m + cb_w) - graph.get_left()[0]))   # left edge = board_right + m
        self.fifty = self._fifty_line(1)                  # 50% line (built after positioning)

        self._setup_board(board_cx, cb_w, cb_h)
        self.play(FadeIn(self.cb), run_time=0.6)
        h_len, h_fair, h_draw, rule = self.table
        self.play(LaggedStartMap(Create, _strokes(*h_len, *h_fair, *h_draw),
                                 lag_ratio=0.5), run_time=1.6)
        self.play(Create(rule), run_time=0.5)

        rest = VGroup(self.cdf.labels, self.cdf.x_axis, self.cdf.y_axis,
                      self.cdf.yticks, self.cdf.title, self.cdf_extra)
        rest.set_opacity(0)
        self.add(self.cdf, self.cdf_extra)      # fifty is added by its Create below
        grow_bars(self, self.cdf.bars, 1.2, lag=0.08,
                  extra=[rest.animate.set_opacity(1)])
        self.play(Create(self.fifty), run_time=0.7)

    def _row_y(self, i):
        """Baseline y of table row i (row 0 = length 1, row 1 = length 2, …)."""
        return ROW_Y0 + i * ROW_DY

    def _draw_x(self, i):
        """Staggered x for row i's drawing: odd word lengths (even row index) go LEFT,
        even lengths go RIGHT — so consecutive drawings don't collide vertically."""
        return self.col_x[2] + (-DRAW_DX if i % 2 == 0 else DRAW_DX)

    def _write(self, *chalk_mobs):
        """A LaggedStart Create of the given chalk mobjects' strokes — used as a
        _morph_cdf `extra_move` so a word-length label writes AS the graph morphs."""
        return LaggedStartMap(Create, _strokes(*chalk_mobs), lag_ratio=0.5)

    def _chalk_frame(self, sw=3.0):
        """The white (chalk) gallows frame: base, post, beam, rope."""
        return VGroup(
            Line([-0.34, -0.46, 0], [0.06, -0.46, 0], color=CHALK, stroke_width=sw),
            Line([-0.30, -0.46, 0], [-0.30, 0.46, 0], color=CHALK, stroke_width=sw),
            Line([-0.30, 0.46, 0], [0.12, 0.46, 0], color=CHALK, stroke_width=sw),
            Line([0.12, 0.46, 0], [0.12, 0.30, 0], color=CHALK, stroke_width=sw))

    # ── mini gallows: chalk frame + the first n body parts, colour-coded by miss ──
    def _mini_gallows(self, n):
        """A small CHALK gallows frame hanging ``n`` coloured body parts (coloured to END
        at red via _draw_colors). n==1 is the tall outlined oval; n>=2 is a round head +
        torso + one arm-line + one leg-line. Handles: ``.frame`` (chalk gallows),
        ``.parts`` (the n drawn parts, in order)."""
        sw = 3.0
        frame = self._chalk_frame(sw)
        if n == 1:
            parts = [Ellipse(width=0.26, height=0.58, fill_opacity=0.0,
                             stroke_width=sw).move_to([0.12, 0.01, 0])]
        else:
            head = Circle(radius=0.11, fill_opacity=0.0,
                          stroke_width=sw).move_to([0.12, 0.19, 0])
            body = Line([0.12, 0.08, 0], [0.12, -0.28, 0], stroke_width=sw)
            arms = Line([-0.06, -0.06, 0], [0.30, -0.06, 0], stroke_width=sw)
            legs = Line([-0.04, -0.28, 0], [0.28, -0.28, 0], stroke_width=sw)
            parts = [head, body, arms, legs][:n]
        for p, col in zip(parts, _draw_colors(len(parts))):  # colour to end at red
            p.set_color(col)
        g = VGroup(frame, *parts)
        g.frame, g.parts = frame, parts
        return g.scale(DRAW_SCALE)

    # ── morph the current CDF into a new-length one, then GROW the brand-new bars ──
    def _morph_cdf(self, new, length, move_rt, grow_rt, *, extra_move=()):
        """Align ``new`` onto the current CDF (self.cdf) and morph in two phases: the
        SHARED bars move/reshape while the framing (x-labels, ticks, axes, title)
        crossfades; THEN the brand-new bars grow up from the axis (labels fading in
        with them, and the 50% line recolouring blue over any new crimson bars) — so
        the new bars grow only AFTER the old ones finish moving. ``extra_move`` plays
        ALONGSIDE the first (move) phase — used to write the word-length label AS the
        graph animation starts."""
        old = self.cdf
        new.shift(old.y_axis.get_center() - new.y_axis.get_center())
        k = min(len(old.bars), len(new.bars))
        move = [ReplacementTransform(old.bars[i], new.bars[i]) for i in range(k)]
        move += [FadeOut(old.bars[i]) for i in range(k, len(old.bars))]
        lk = min(len(old.labels), len(new.labels))
        move += [FadeTransform(old.labels[i], new.labels[i]) for i in range(lk)]
        move += [FadeOut(old.labels[i]) for i in range(len(new.labels), len(old.labels))]
        for attr in ("x_axis", "y_axis", "yticks", "title"):
            o, nw = getattr(old, attr, None), getattr(new, attr, None)
            if o is not None and nw is not None:
                move.append(FadeTransform(o, nw))
        # recolour the 50% line (blue over the NEW crimson region) IN THE SAME play as the
        # bars morph, so the line's colour change and the crimson width change are simultaneous
        new_fifty = self._fifty_line(length, new)
        self.play(*move, *extra_move, FadeTransform(self.fifty, new_fifty), run_time=move_rt)
        self.fifty = new_fifty
        self.cdf = new
        # "*values not exact" caption: present iff this length has crimson (inexact) bars
        extra = []
        note = self._asterisk_note(length)
        if note is not None and self.asterisk is None:
            self.asterisk = note
            extra.append(FadeIn(note))
        elif note is None and self.asterisk is not None:
            extra.append(FadeOut(self.asterisk))
            self.asterisk = None
        tail = list(new.bars[k:])
        if tail:
            elabels = VGroup(*new.labels[k:])
            elabels.set_opacity(0)
            extra.append(elabels.animate.set_opacity(1))
            grow_bars(self, tail, grow_rt, lag=0.05, extra=extra)
        elif extra:
            self.play(*extra, run_time=grow_rt)

    def _asterisk_note(self, length):
        """A crimson '*values not exact' caption under the inexact (estimated-tail) bars,
        or None if this length is fully exact."""
        pts = scene23_data.get()["cdf"][str(length)]
        if all(p["exact"] for p in pts):
            return None
        note = crisp_text("*values not exact", font_size=16, color=CRIMSON)
        note.next_to(self.cdf_extra[0], DOWN, buff=0.18)   # below the x-axis title
        note.align_to(self.cdf.x_axis, RIGHT)              # right edge at the plot edge
        return note

    # ── d : fill the length-1 row (1 | 1) + gallows with a tall oval (now red) ───
    def _setup_row1(self):
        cx_len, cx_fair, _ = self.col_x
        y = self._row_y(0)
        n_len = chalk_number(1, height=0.42, stroke_width=3.2).move_to([cx_len, y, 0])
        n_fair = chalk_number(1, height=0.42, stroke_width=3.2).move_to([cx_fair, y, 0])
        gal = self._mini_gallows(1).move_to([self._draw_x(0), y, 0])
        self.row1 = VGroup(n_len, n_fair, gal)

    @subscene
    def fill_row_1(self):
        self._setup_row1()
        n_len, n_fair, gal = self.row1
        self.play(LaggedStartMap(Create, _strokes(n_len), lag_ratio=0.5), run_time=0.6)
        self.play(LaggedStartMap(Create, _strokes(n_fair), lag_ratio=0.5), run_time=0.6)
        self.play(LaggedStartMap(Create, gal.frame, lag_ratio=0.8), run_time=1.0)
        for p in gal.parts:                            # just the head (purple) at len 1
            self.play(Create(p), run_time=0.5)

    # ── e : switch to 2-letter words — morph the CDF, write only the length-2 row ─
    def _setup_switch_2(self):
        self.len2 = chalk_number(2, height=0.42, stroke_width=3.2).move_to(
            [self.col_x[0], self._row_y(1), 0])        # Word Length column, row 2

    @subscene
    def switch_to_2(self):
        self._setup_switch_2()
        self._morph_cdf(self._cdf_chart(2), 2, 1.2, 1.0,  # 1- -> 2-Letter (title crossfades)
                        extra_move=[self._write(self.len2)])

    # ── f : length-2 fair number (4) + the colour-coded gallows (4 parts) ─────────
    def _setup_row2_fill(self):
        y = self._row_y(1)
        self.fair2 = chalk_number(4, height=0.42, stroke_width=3.2).move_to(
            [self.col_x[1], y, 0])
        self.gal2 = self._mini_gallows(4).move_to([self._draw_x(1), y, 0])

    @subscene
    def fill_row_2(self):
        self._setup_row2_fill()
        self.play(LaggedStartMap(Create, _strokes(self.fair2), lag_ratio=0.5),
                  run_time=0.6)
        self.play(LaggedStartMap(Create, self.gal2.frame, lag_ratio=0.8), run_time=1.0)
        for p in self.gal2.parts:                      # head, body, arms, legs (coloured)
            self.play(Create(p), run_time=0.45)

    # ── g : switch to 3-letter words — morph the CDF (first inexact/crimson tail) ──
    def _setup_switch_3(self):
        self.len3 = chalk_number(3, height=0.42, stroke_width=3.2).move_to(
            [self.col_x[0], self._row_y(2), 0])        # Word Length column, row 3

    @subscene
    def switch_to_3(self):
        self._setup_switch_3()
        self._morph_cdf(self._cdf_chart(3), 3, 1.2, 1.0,  # 2- -> 3-Letter (crimson tail + caption)
                        extra_move=[self._write(self.len3)])

    # ── the table "Drawing": a standard hangman coloured element-by-element via
    #    _draw_colors (always ending at red). gallows="split" = base + rest as two elements
    #    (8 total); gallows="single" = the WHOLE gallows as ONE stroke, ignoring the
    #    bottom-left stub (7 total). Body = the 6 standard parts: head, torso, 2 arms,
    #    2 legs. ─────────────────────────────────────────────────────────────────────
    def _hangman_drawing(self, gallows):
        sw = 3.0
        if gallows == "split":
            base = Line([-0.34, -0.46, 0], [0.06, -0.46, 0], stroke_width=sw)
            rest = VGroup(                                    # post + beam + rope
                Line([-0.30, -0.46, 0], [-0.30, 0.46, 0], stroke_width=sw),
                Line([-0.30, 0.46, 0], [0.12, 0.46, 0], stroke_width=sw),
                Line([0.12, 0.46, 0], [0.12, 0.30, 0], stroke_width=sw))
            gall = [base, rest]
        else:                                                 # single stroke, no stub
            stroke = VMobject(stroke_width=sw)
            stroke.set_points_as_corners([[0.06, -0.46, 0], [-0.30, -0.46, 0],
                                          [-0.30, 0.46, 0], [0.12, 0.46, 0],
                                          [0.12, 0.30, 0]])
            gall = [stroke]
        head = Circle(radius=0.10, fill_opacity=0.0, stroke_width=sw).move_to([0.12, 0.20, 0])
        torso = Line([0.12, 0.10, 0], [0.12, -0.15, 0], stroke_width=sw)
        arm1 = Line([0.12, 0.03, 0], [-0.03, -0.09, 0], stroke_width=sw)
        arm2 = Line([0.12, 0.03, 0], [0.27, -0.09, 0], stroke_width=sw)
        leg1 = Line([0.12, -0.15, 0], [0.00, -0.32, 0], stroke_width=sw)
        leg2 = Line([0.12, -0.15, 0], [0.24, -0.32, 0], stroke_width=sw)
        parts = gall + [head, torso, arm1, arm2, leg1, leg2]
        for p, col in zip(parts, _draw_colors(len(parts))):  # colour to end at red
            p.set_color(col)
        g = VGroup(*parts)
        g.parts = parts
        return g.scale(DRAW_SCALE)

    # ── length-5 "Drawing": CHALK gallows + head, torso, one arm-line, two legs (5) ──
    def _body_drawing(self):
        sw = 3.0
        frame = self._chalk_frame(sw)
        head = Circle(radius=0.10, fill_opacity=0.0, stroke_width=sw).move_to([0.12, 0.20, 0])
        torso = Line([0.12, 0.10, 0], [0.12, -0.15, 0], stroke_width=sw)
        arms = Line([-0.04, -0.02, 0], [0.28, -0.02, 0], stroke_width=sw)   # one arm-line
        leg1 = Line([0.12, -0.15, 0], [0.00, -0.32, 0], stroke_width=sw)
        leg2 = Line([0.12, -0.15, 0], [0.24, -0.32, 0], stroke_width=sw)
        parts = [head, torso, arms, leg1, leg2]
        for p, col in zip(parts, _draw_colors(len(parts))):  # colour to end at red
            p.set_color(col)
        g = VGroup(frame, *parts)
        g.frame, g.parts = frame, parts
        return g.scale(DRAW_SCALE)

    # ── snowman "Drawing" (lengths 8/9): CHALK gallows + a stack of n circles hanging
    #    from the rope, head (small) at top → base (big) at bottom, drawn TOP to BOTTOM
    #    starting with YELLOW. ───────────────────────────────────────────────────────
    def _snowman(self, n):
        sw = 3.0
        frame = self._chalk_frame(sw)
        radii = [0.09, 0.11, 0.14][-n:]                  # top(head, small) -> bottom(big)
        circles, cy, prev = [], 0.30, 0.0                # top edge at the rope end (0.30)
        for i, r in enumerate(radii):
            cy = (0.30 - r) if i == 0 else cy - prev - r  # stack touching, downward
            circles.append(Circle(radius=r, fill_opacity=0.0,
                                   stroke_width=sw).move_to([0.12, cy, 0]))
            prev = r
        for c, col in zip(circles, _draw_colors(n)):     # top -> bottom, ending at red
            c.set_color(col)                             # 3: yellow/orange/red · 2: orange/red
        g = VGroup(frame, *circles)
        g.frame, g.parts = frame, circles                # parts already top->bottom order
        return g.scale(DRAW_SCALE)

    # ── h : length-3 fair number (8) + split-gallows standard hangman (8 elements) ──
    def _setup_row3_fill(self):
        y = self._row_y(2)
        self.fair3 = chalk_number(8, height=0.42, stroke_width=3.2).move_to(
            [self.col_x[1], y, 0])
        self.draw3 = self._hangman_drawing("split").move_to([self._draw_x(2), y, 0])

    @subscene
    def fill_row_3(self):
        self._setup_row3_fill()
        self.play(LaggedStartMap(Create, _strokes(self.fair3), lag_ratio=0.5),
                  run_time=0.6)
        for p in self.draw3.parts:                            # 8 elements, one per miss
            self.play(Create(p), run_time=0.4)

    # ── i : switch to 4-letter words — morph the CDF, write only the length-4 row ──
    def _setup_switch_4(self):
        self.len4 = chalk_number(4, height=0.42, stroke_width=3.2).move_to(
            [self.col_x[0], self._row_y(3), 0])        # Word Length column, row 4

    @subscene
    def switch_to_4(self):
        self._setup_switch_4()
        self._morph_cdf(self._cdf_chart(4), 4, 1.2, 1.0,  # 3- -> 4-Letter
                        extra_move=[self._write(self.len4)])

    # ── j : length-4 fair number (7) + single-stroke-gallows hangman (7 elements) ──
    def _setup_row4_fill(self):
        y = self._row_y(3)
        self.fair4 = chalk_number(7, height=0.42, stroke_width=3.2).move_to(
            [self.col_x[1], y, 0])
        self.draw4 = self._hangman_drawing("single").move_to([self._draw_x(3), y, 0])

    @subscene
    def fill_row_4(self):
        self._setup_row4_fill()
        self.play(LaggedStartMap(Create, _strokes(self.fair4), lag_ratio=0.5),
                  run_time=0.6)
        for p in self.draw4.parts:                            # 7 elements, one per miss
            self.play(Create(p), run_time=0.4)

    # ── k : switch to 5-letter words — morph the CDF, write only the length-5 row ──
    def _setup_switch_5(self):
        self.len5 = chalk_number(5, height=0.42, stroke_width=3.2).move_to(
            [self.col_x[0], self._row_y(4), 0])        # Word Length column, row 5

    @subscene
    def switch_to_5(self):
        self._setup_switch_5()
        self._morph_cdf(self._cdf_chart(5), 5, 1.2, 1.0,  # 4- -> 5-Letter
                        extra_move=[self._write(self.len5)])

    # ── l : length-5 fair number (5) + body-only drawing (head/torso/arm-line/2 legs) ─
    def _setup_row5_fill(self):
        y = self._row_y(4)
        self.fair5 = chalk_number(5, height=0.42, stroke_width=3.2).move_to(
            [self.col_x[1], y, 0])
        self.draw5 = self._body_drawing().move_to([self._draw_x(4), y, 0])

    @subscene
    def fill_row_5(self):
        self._setup_row5_fill()
        self.play(LaggedStartMap(Create, _strokes(self.fair5), lag_ratio=0.5),
                  run_time=0.6)
        self.play(LaggedStartMap(Create, self.draw5.frame, lag_ratio=0.8), run_time=1.0)
        for p in self.draw5.parts:                            # 5 elements, one per miss
            self.play(Create(p), run_time=0.4)

    # ── m : switch to 6-letter words — draw the "6" of the CENTRED "6-7" as 6 appears ─
    def _setup_switch_6(self):
        # lay out the whole "6-7" now (centred like every other label); the "6" is drawn
        # here, the "-7" when the 7-graph appears — so the merged label stays centred.
        self.len67 = chalk_phrase("6-7", height=0.42, stroke_width=3.2, buff=0.06).move_to(
            [self.col_x[0], self._row_y(5), 0])

    @subscene
    def switch_to_6(self):
        self._setup_switch_6()
        self._morph_cdf(self._cdf_chart(6), 6, 1.2, 1.0,  # 5- -> 6-Letter; write the "6"
                        extra_move=[self._write(VGroup(self.len67[0]))])

    # ── n : length-6 fair number (4, = bar 4 nearest 50%) + fair-4 drawing ─────────
    def _setup_row6_fill(self):
        y = self._row_y(5)
        self.fair6 = chalk_number(4, height=0.42, stroke_width=3.2).move_to(
            [self.col_x[1], y, 0])
        self.gal6 = self._mini_gallows(4).move_to([self._draw_x(5), y, 0])

    @subscene
    def fill_row_6(self):
        self._setup_row6_fill()
        self.play(LaggedStartMap(Create, _strokes(self.fair6), lag_ratio=0.5),
                  run_time=0.6)
        self.play(LaggedStartMap(Create, self.gal6.frame, lag_ratio=0.8), run_time=1.0)
        for p in self.gal6.parts:                             # head, body, arm-line, leg-line
            self.play(Create(p), run_time=0.45)

    # ── o : switch to 7-letter words — same fair # (4): draw the "-7" of "6-7" as 7 appears
    @subscene
    def switch_to_7(self):
        self._morph_cdf(self._cdf_chart(7), 7, 1.2, 1.0,  # 6- -> 7-Letter (completes "6-7")
                        extra_move=[self._write(VGroup(*self.len67[1:]))])

    # ── p : switch to 8-letter words — morph the CDF, write only the length-8 row ──
    def _setup_switch_8(self):
        self.len8 = chalk_number(8, height=0.42, stroke_width=3.2).move_to(
            [self.col_x[0], self._row_y(6), 0])        # Word Length column, row for len 8

    @subscene
    def switch_to_8(self):
        self._setup_switch_8()
        self._morph_cdf(self._cdf_chart(8), 8, 1.2, 1.0,  # 7- -> 8-Letter (caption clears)
                        extra_move=[self._write(self.len8)])

    # ── q : length-8 fair number (3) + a little 3-circle SNOWMAN (no gallows) ──────
    def _setup_row8_fill(self):
        y = self._row_y(6)
        self.fair8 = chalk_number(3, height=0.42, stroke_width=3.2).move_to(
            [self.col_x[1], y, 0])
        self.snow8 = self._snowman(3).move_to([self._draw_x(6), y, 0])

    @subscene
    def fill_row_8(self):
        self._setup_row8_fill()
        self.play(LaggedStartMap(Create, _strokes(self.fair8), lag_ratio=0.5),
                  run_time=0.6)
        self.play(LaggedStartMap(Create, self.snow8.frame, lag_ratio=0.8), run_time=1.0)
        for c in self.snow8.parts:                            # 3 circles, top -> bottom
            self.play(Create(c), run_time=0.4)

    # ── r : switch to 9-letter words — morph the CDF, write only the length-9 row ──
    def _setup_switch_9(self):
        self.len9 = chalk_number(9, height=0.42, stroke_width=3.2).move_to(
            [self.col_x[0], self._row_y(7), 0])

    @subscene
    def switch_to_9(self):
        self._setup_switch_9()
        self._morph_cdf(self._cdf_chart(9), 9, 1.2, 1.0,  # 8- -> 9-Letter
                        extra_move=[self._write(self.len9)])

    # ── s : length-9 fair number (2) + a 2-circle SNOWMAN ─────────────────────────
    def _setup_row9_fill(self):
        y = self._row_y(7)
        self.fair9 = chalk_number(2, height=0.42, stroke_width=3.2).move_to(
            [self.col_x[1], y, 0])
        self.snow9 = self._snowman(2).move_to([self._draw_x(7), y, 0])

    @subscene
    def fill_row_9(self):
        self._setup_row9_fill()
        self.play(LaggedStartMap(Create, _strokes(self.fair9), lag_ratio=0.5),
                  run_time=0.6)
        self.play(LaggedStartMap(Create, self.snow9.frame, lag_ratio=0.8), run_time=1.0)
        for c in self.snow9.parts:                            # 2 circles, top -> bottom
            self.play(Create(c), run_time=0.4)

    # ── t : morph to 10-letter words; write the "10" of the CENTRED "10+" as 10 appears.
    #    The "10+" row's fair "1" + oval are BUILT here but drawn later, DURING the march.
    def _setup_switch_10(self):
        y = self._row_y(8)
        self.len10p = chalk_phrase("10+", height=0.42, stroke_width=3.2, buff=0.06).move_to(
            [self.col_x[0], y, 0])
        self.fair10 = chalk_number(1, height=0.42, stroke_width=3.2).move_to(
            [self.col_x[1], y, 0])
        self.draw10 = self._mini_gallows(1).move_to([self._draw_x(8), y, 0])   # gallows + oval

    @subscene
    def switch_to_10plus(self):
        self._setup_switch_10()
        self._morph_cdf(self._cdf_chart(10), 10, 1.2, 1.0,  # 9- -> 10-Letter; write "10"
                        extra_move=[self._write(VGroup(*self.len10p[0:2]))])

    # ── u : morph to 11-letter words; write the "+" (completing "10+") as 11 appears ──
    @subscene
    def plus_11(self):
        self._morph_cdf(self._cdf_chart(11), 11, 1.2, 1.0,  # 10- -> 11-Letter; write the "+"
                        extra_move=[self._write(VGroup(self.len10p[2]))])

    # ── v : keep morphing the CDF through 12..16 (all still fair 1); the fair "1", the
    #    gallows, and the oval are drawn DURING this march (not after it) ─────────────
    @subscene
    def march_to_16(self):
        self._morph_cdf(self._cdf_chart(12), 12, 1.0, 0.8,   # 12: write the fair "1"
                        extra_move=[self._write(self.fair10)])
        self._morph_cdf(self._cdf_chart(13), 13, 1.0, 0.8,   # 13: draw the gallows
                        extra_move=[LaggedStartMap(Create, self.draw10.frame, lag_ratio=0.8)])
        self._morph_cdf(self._cdf_chart(14), 14, 1.0, 0.8,   # 14: draw the oval
                        extra_move=[Create(self.draw10.parts[0])])
        self._morph_cdf(self._cdf_chart(15), 15, 1.0, 0.8)   # 15, 16: just keep marching
        self._morph_cdf(self._cdf_chart(16), 16, 1.0, 0.8)
