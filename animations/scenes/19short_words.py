"""SCENE 19 — SHORT WORDS (the choosing strategy for lengths 2, 3, 4).

On the BRAND light-blue background (HangmanScene → BG_COLOR), crisp_text + filled
shapes — NOT chalk, NOT navy. Opens with the by-length double plot, then walks the
per-length adversarial (best-opener-tuned) frequency search results as TABLES:
LEFT = letter-combo patterns + their multipliers, RIGHT = the chosen words + their
frequency share.

BEAT MAP (Script.md scene 19; --- delimited, 8 beats a-h):
  a double_plot          — double bar chart: the OPTIMAL strategy's avg misses per word
                           length, EQUAL (uniform) vs BEST_OPENER (adversarial) weighting;
                           same style as scene 17's optimal-vs-zipf chart. SOURCED
                           short_words_data.by_length (exact where converged, avg of
                           lower/upper bounds where not).
  b two_letter_patterns  — title "2-Letter Words"; LEFT Most Common Letter Patterns, then
                           below it Least Common Letter Patterns (cols Pattern / Multiplier).
  c two_letter_words     — RIGHT Most Common Words, then below it Least Common Words (cols
                           Word / Frequency, as a % to 1 dp).
  d three_letter_patterns— title → "3-Letter Words"; clear the len-2 tables; LEFT Most
                           Common Letter Patterns (top 12).
  e three_letter_words   — RIGHT Most Common Words (top 12; top word HAJ).
  f four_letter_title    — title → "4-Letter Words"; clear the len-3 tables (title swap only).
  g four_letter_patterns — LEFT Most Common Letter Patterns (top 12; duplicated-letter combos).
  h four_letter_words    — RIGHT Most Common Words (top 12); then BLUR the PIMP row.

REUSE MAP (styling sources):
  - double chart : bpkfigures.bar_graph get_bar_chart / grow_bars — an INLINED adapt of
                   scene 17's `_strategy_chart`/`_legend` (best_opener swaps in for zipf).
                   >>> FLAG: duplicates scene 17's private chart builder (2nd use) — should
                   be PROMOTED to a shared "double bar chart by length" helper (ask first).
  - tables       : scene 18's beat-a table — crisp_text title + column headers + rows on a
                   shared BASELINE (baseline_at), rows rise in with a lagged upward cascade.
  - text/colour  : crisp_text, INK = BLACK; bars ACCENT_FILL (uniform) / CRIMSON (best_opener).

FLAGS (owned by a human — tune/decide in the timing+polish pass):
  - table TITLES ("Most Common Letter Patterns" …) are rendered as captions per the script's
    "table of …" naming; drop/reword if undesired.
  - "Blur PIMP" is roughed as a stacked-offset SMEAR (manim has no native blur); a true blur
    is a post/compositing effect if preferred.
  - all geometry (column x, row spacing, table tops, chart box) + run_times = guesses.

Render:  render 19a --fast (…19h)  /  render 19 sub  for the whole scene
"""
from pathlib import Path
import sys
import math

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets import short_words_data
from bpkfigures.bar_graph import get_bar_chart, grow_bars

INK = BLACK                        # dark labels on the brand light-blue bg (scene 17/18 convention)
UNIFORM_COLOR = ACCENT_FILL        # equal-weighted bars (the double plot)
BESTOP_COLOR = CRIMSON             # best-opener (adversarial) weighted bars

TITLE_Y = 3.95                     # the scene title ("N-Letter Words")

# ── table layout (LEFT = patterns, RIGHT = words) ─────────────────────────────
LEFT_X, RIGHT_X = -3.7, 3.7        # each side's centre
LABEL_DX, VALUE_DX = -1.25, 1.15   # column x offsets from a side centre (label left, value right)
TABLE_TITLE_W = 5.4                # a wide table title scales down to this
SCENE_TITLE_H = 0.52               # scene-title glyph height (built small, scaled up)
TABLE_TITLE_H = 0.30               # table-title glyph height
HDR_FS = 22
ROW_FS = 22
TITLE_GAP = 0.6                    # table title → header
HDR_GAP = 0.42                     # header → first row
ROW_DY = 0.44                      # row → row
LEN2_TOPS = (3.05, 0.07)           # len-2: two stacked tables per side (Most, then Least) — title ys
LEN34_TOP = 2.95                   # len-3/4: one 12-row table per side — title y


class Scene19(HangmanScene):
    """Short words — the choosing strategy for lengths 2/3/4. See docstring for beats."""

    def setup_scene(self):
        self.tables = short_words_data.get()["tables"]
        self.chart = None
        self.title = None
        self.left_tables = self.right_tables = None

    # ── data → (label, value_str) rows ────────────────────────────────────────
    def _pat_rows(self, rows):
        return [(r["pattern"], f"{r['multiplier']:g}") for r in rows]   # full decimal multiplier

    def _word_rows(self, rows):
        return [(r["word"], f"{r['pct']:.1f}%") for r in rows]          # frequency share, 1 dp

    # ── title helpers ─────────────────────────────────────────────────────────
    # long crisp_text wraps at the 240pt supersample; build small + scale to a FIXED
    # HEIGHT (consistent size across titles of different lengths), then clamp width.
    def _fit(self, text, height, **kw):
        return crisp_text(text, font_size=10, **kw).scale_to_fit_height(height)

    def _scene_title(self, text):
        return self._fit(text, SCENE_TITLE_H, color=INK, weight=BOLD).move_to([0, TITLE_Y, 0])

    def _table_title(self, text, maxw):
        t = self._fit(text, TABLE_TITLE_H, color=INK, weight=BOLD)
        if t.width > maxw:
            t.scale_to_fit_width(maxw)
        return t

    # ── one titled table (title + column headers + baseline-aligned rows) ─────
    def _table(self, title, headers, rows, *, top_y, cx):
        lx, vx = cx + LABEL_DX, cx + VALUE_DX
        ttl = self._table_title(title, TABLE_TITLE_W).move_to([cx, top_y, 0])
        hy = top_y - TITLE_GAP
        hdr = VGroup(
            crisp_text(headers[0], font_size=HDR_FS, color=INK, weight=BOLD, baseline_at=(lx, hy)),
            crisp_text(headers[1], font_size=HDR_FS, color=INK, weight=BOLD, baseline_at=(vx, hy)))
        row_group, cells = VGroup(), {}
        for r, (lab, val) in enumerate(rows):
            ry = hy - HDR_GAP - r * ROW_DY
            lm = crisp_text(lab, font_size=ROW_FS, color=INK, baseline_at=(lx, ry))
            vm = crisp_text(val, font_size=ROW_FS, color=INK, baseline_at=(vx, ry))
            row_group.add(VGroup(lm, vm))
            cells[lab] = (lm, vm)
        tab = VGroup(ttl, hdr, row_group)
        tab.title, tab.header, tab.rows, tab.cells = ttl, hdr, row_group, cells
        return tab

    def _reveal(self, tab, rows_run_time):
        """Fade the title+header in, then rise the rows up with a lagged cascade."""
        for row in tab.rows:
            row.shift(DOWN * 0.35).set_opacity(0)
        self.play(FadeIn(tab.title), FadeIn(tab.header), run_time=0.4)
        self.play(LaggedStart(*[row.animate.shift(UP * 0.35).set_opacity(1) for row in tab.rows],
                              lag_ratio=0.12), run_time=rows_run_time)

    # ── the by-length double bar chart (adapt of scene 17's _strategy_chart) ──
    def _legend(self, entries, pos):
        g = VGroup()
        for name, color in entries:
            sq = Square(side_length=0.28, fill_color=color, fill_opacity=1.0, stroke_width=0)
            g.add(VGroup(sq, crisp_text(name, font_size=22, color=INK)).arrange(RIGHT, buff=0.18))
        return g.arrange(DOWN, buff=0.22, aligned_edge=LEFT).move_to(pos)

    def _double_chart(self):
        data = short_words_data.get()["by_length"]
        lengths = sorted(int(L) for L in data["uniform"])
        ymax = max(data[w][str(L)]["avg"] for w in ("uniform", "best_opener") for L in lengths)
        W, cy, H = 12.6, -0.55, 3.8
        N, slot = len(lengths), 12.6 / len(lengths)
        dx = slot / 4.2                                     # half-gap between the paired bars

        def series(w, color, off):
            items = [(str(L), data[w][str(L)]["avg"]) for L in lengths]
            return get_bar_chart(items, center=[off, cy, 0], width=W, height=H, y_max=ymax,
                                 n_slots=N, bar_color=color, bar_ratio=0.42, show_labels=False)

        uni, best = series("uniform", UNIFORM_COLOR, -dx), series("best_opener", BESTOP_COLOR, dx)
        base_y = cy - H / 2
        xlabels = VGroup(*[crisp_text(str(L), font_size=20, color=INK).move_to(
                              [-W / 2 + (i + 0.5) * slot, base_y - 0.28, 0])
                           for i, L in enumerate(lengths)])
        xtitle = crisp_text("word length", font_size=24, color=INK).move_to([0, base_y - 0.78, 0])
        title = crisp_text("Optimal Misses per Word", font_size=34, color=INK,
                           weight=BOLD).move_to([0, cy + H / 2 + 0.7, 0])
        legend = self._legend([("Equal", UNIFORM_COLOR), ("Best Opener", BESTOP_COLOR)],
                              [4.6, cy + H / 2 - 0.2, 0])
        g = VGroup(uni, best, xlabels, xtitle, title, legend)
        g.uni, g.best, g.rest = uni, best, VGroup(xlabels, xtitle, title, legend)
        return g

    # ── poor-man blur (manim has no native blur): a stacked low-opacity smear ─
    def _blur(self, mob, *, layers=10, spread=0.05):
        g = VGroup()
        for k in range(layers):
            ang = 2 * math.pi * k / layers
            g.add(mob.copy().shift([spread * math.cos(ang), spread * math.sin(ang), 0])
                  .set_opacity(0.18))
        return g.move_to(mob)

    # a : double bar chart — optimal avg misses per length, EQUAL vs BEST_OPENER
    @subscene
    def double_plot(self):
        self.chart = self._double_chart()
        self.chart.rest.set_opacity(0)                      # axis labels/title/legend fade in with bars
        self.add(self.chart)
        bars = [*self.chart.uni.bars, *self.chart.best.bars]
        grow_bars(self, bars, 1.2, lag=0.02, extra=[self.chart.rest.animate.set_opacity(1)])

    # b : "2-Letter Words"; LEFT Most Common Patterns, then Least Common Patterns
    @subscene
    def two_letter_patterns(self):
        self.play(FadeOut(self.chart), run_time=0.5)
        self.chart = None
        self.title = self._scene_title("2-Letter Words")
        self.play(FadeIn(self.title), run_time=0.5)

        t2 = self.tables["2"]
        most = self._table("Most Common Letter Patterns", ("Pattern", "Multiplier"),
                           self._pat_rows(t2["most_patterns"]), top_y=LEN2_TOPS[0], cx=LEFT_X)
        self._reveal(most, 1.2)
        least = self._table("Least Common Letter Patterns", ("Pattern", "Multiplier"),
                            self._pat_rows(t2["least_patterns"]), top_y=LEN2_TOPS[1], cx=LEFT_X)
        self._reveal(least, 1.2)
        self.left_tables = VGroup(most, least)

    # c : RIGHT Most Common Words, then Least Common Words (frequency as %)
    @subscene
    def two_letter_words(self):
        t2 = self.tables["2"]
        most = self._table("Most Common Words", ("Word", "Frequency"),
                           self._word_rows(t2["most_words"]), top_y=LEN2_TOPS[0], cx=RIGHT_X)
        self._reveal(most, 1.2)
        least = self._table("Least Common Words", ("Word", "Frequency"),
                            self._word_rows(t2["least_words"]), top_y=LEN2_TOPS[1], cx=RIGHT_X)
        self._reveal(least, 1.2)
        self.right_tables = VGroup(most, least)

    # d : title → "3-Letter Words"; clear len-2 tables; LEFT Most Common Patterns (12)
    @subscene
    def three_letter_patterns(self):
        new = self._scene_title("3-Letter Words")
        self.play(Transform(self.title, new), FadeOut(self.left_tables),
                  FadeOut(self.right_tables), run_time=0.6)
        self.left_tables = self.right_tables = None

        t3 = self.tables["3"]
        most = self._table("Most Common Letter Patterns", ("Pattern", "Multiplier"),
                           self._pat_rows(t3["most_patterns"]), top_y=LEN34_TOP, cx=LEFT_X)
        self._reveal(most, 1.6)
        self.left_tables = VGroup(most)

    # e : RIGHT Most Common Words (12; top word HAJ)
    @subscene
    def three_letter_words(self):
        t3 = self.tables["3"]
        most = self._table("Most Common Words", ("Word", "Frequency"),
                           self._word_rows(t3["most_words"]), top_y=LEN34_TOP, cx=RIGHT_X)
        self._reveal(most, 1.6)
        self.right_tables = VGroup(most)

    # f : title → "4-Letter Words"; clear the len-3 tables (title swap only)
    @subscene
    def four_letter_title(self):
        new = self._scene_title("4-Letter Words")
        self.play(Transform(self.title, new), FadeOut(self.left_tables),
                  FadeOut(self.right_tables), run_time=0.6)
        self.left_tables = self.right_tables = None

    # g : LEFT Most Common Patterns (12; duplicated-letter combos)
    @subscene
    def four_letter_patterns(self):
        t4 = self.tables["4"]
        most = self._table("Most Common Letter Patterns", ("Pattern", "Multiplier"),
                           self._pat_rows(t4["most_patterns"]), top_y=LEN34_TOP, cx=LEFT_X)
        self._reveal(most, 1.6)
        self.left_tables = VGroup(most)

    # h : RIGHT Most Common Words (12); then blur the PIMP row
    @subscene
    def four_letter_words(self):
        t4 = self.tables["4"]
        most = self._table("Most Common Words", ("Word", "Frequency"),
                           self._word_rows(t4["most_words"]), top_y=LEN34_TOP, cx=RIGHT_X)
        self._reveal(most, 1.6)
        self.right_tables = VGroup(most)

        pimp_lab, _ = most.cells["PIMP"]
        blur = self._blur(pimp_lab)
        self.play(FadeOut(pimp_lab), FadeIn(blur), run_time=0.6)
