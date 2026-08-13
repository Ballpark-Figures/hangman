"""SCENE 19 — SHORT WORDS (the choosing strategy for lengths 2, 3, 4).

On the BRAND light-blue background (HangmanScene → BG_COLOR), crisp_text + filled
shapes — NOT chalk, NOT navy. Opens with the by-length double plot, then walks the
per-length adversarial (best-opener-tuned) frequency search results as TABLES:
LEFT = letter-combo patterns + their multipliers, RIGHT = the chosen words + their
frequency share.

BEAT MAP (Script.md scene 19; --- delimited, 8 beats a-h):
  a double_plot          — double bar chart (WITH axes): the OPTIMAL strategy's avg misses
                           per word length, EQUAL (uniform) vs BEST_OPENER (adversarial)
                           weighting; scene-17 style. SOURCED short_words_data.by_length.
  b two_letter_patterns  — title "2-Letter Words"; LEFT Common Letter Patterns (mult > 1),
                           then Rare Letter Patterns (mult < 1) anchored to the bottom.
  c two_letter_words     — RIGHT Common Words, then Rare Words (frequency as % — 2 sig figs).
  d three_letter_patterns— title → "3-Letter Words"; clear len-2 tables; LEFT Common Patterns.
  e three_letter_words   — RIGHT Common Words (top word HAJ).
  f four_letter_title    — title → "4-Letter Words"; clear the len-3 tables (title swap only).
  g four_letter_patterns — LEFT Common Letter Patterns (duplicated-letter combos).
  h four_letter_words    — RIGHT Common Words; the PIMP word is replaced by a transparent
                           gray box (censored) so it's never shown.

Formatting conventions (routed through single helpers so they hold everywhere):
  - every number is 2 SIGNIFICANT FIGURES (`_sig2`) — multipliers AND word %.
  - a pattern (blanked word) / a word is BOLD and MONOSPACED (`_mono`) — each letter on a
    fixed slot so they form little COLUMNS down the table.
  - pattern tables show only multiplier != 1 (Common = boosted, Rare = reduced).

REUSE MAP (styling sources):
  - double chart : bpkfigures.bar_graph get_bar_chart (x_axis/y_axis/y_ticks) + grow_bars —
                   an INLINED adapt of scene 17's `_strategy_chart`/`_legend` (best_opener
                   swaps in for zipf, axes added).
                   >>> FLAG: still duplicates scene 17's private chart builder — a shared
                   "double bar chart by length" helper is now clearly warranted (ask).
  - tables       : scene 18's beat-a table — crisp_text title + column headers + rows on a
                   shared BASELINE (baseline_at), rows rise in (FadeIn + shift up).
  - text/colour  : crisp_text, INK = BLACK; bars ACCENT_FILL (uniform) / CRIMSON (best_opener).

FLAGS (owned by a human — tune/decide in the timing+polish pass):
  - table TITLES ("Common Letter Patterns" …) are rendered as captions; drop/reword if undesired.
  - "Blur PIMP" is done as a transparent gray CENSOR box over the word (per the user); swap for
    a real blur in post if preferred.
  - all geometry (columns, CHAR_W, row spacing, stack anchors, chart box) + run_times = guesses.

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

TITLE_Y = 3.6                      # the scene title ("N-Letter Words")

# ── table layout (LEFT = patterns, RIGHT = words) ─────────────────────────────
LEFT_X, RIGHT_X = -3.7, 3.7        # each side's centre
LABEL_DX, VALUE_DX = -1.25, 1.15   # column x offsets from a side centre (label left, value right)
CHAR_W = 0.28                      # monospaced letter slot (letters line up into columns)
TABLE_TITLE_W = 5.4                # a wide table title scales down to this
SCENE_TITLE_H = 0.52               # scene-title glyph height (built small, scaled up)
TABLE_TITLE_H = 0.30               # table-title glyph height
HDR_FS = 22
ROW_FS = 22
TITLE_GAP = 0.6                    # table title → header
HDR_GAP = 0.44                     # header → first row
ROW_DY = 0.48                      # row → row
STACK_TOP = 2.85                   # len-2: top (Common) table's title y
STACK_BOTTOM_TITLE = -0.55         # len-2: bottom (Rare) table's title y — the two Rare tables
                                   # share this y so their titles ALIGN (regardless of row count)
LEN34_TOP = 2.85                   # len-3/4: the single table's title y


class Scene19(HangmanScene):
    """Short words — the choosing strategy for lengths 2/3/4. See docstring for beats."""

    def setup_scene(self):
        self.tables = short_words_data.get()["tables"]
        self.chart = None
        self.title = None
        self.left_tables = self.right_tables = None

    # ── number / cell formatting (one source of truth) ────────────────────────
    def _sig2(self, x):
        """2 significant figures."""
        if x == 0:
            return "0"
        d = 1 - math.floor(math.log10(abs(x)))
        return f"{x:.{max(d, 0)}f}"

    def _pat_rows(self, rows):
        return [(r["pattern"], self._sig2(r["multiplier"])) for r in rows]

    def _word_rows(self, rows):
        return [(r["word"], self._sig2(r["pct"]) + "%") for r in rows]

    def _mono(self, s, cx, y, color=INK):
        """A bold, MONOSPACED string: each char on a fixed CHAR_W slot centred on cx, so
        equal-length strings line their letters up into columns down the table."""
        n = len(s)
        g = VGroup()
        for i, ch in enumerate(s):
            x = cx + (i - (n - 1) / 2) * CHAR_W
            g.add(crisp_text(ch, font_size=ROW_FS, color=color, weight=BOLD, baseline_at=(x, y)))
        return g

    # ── censor: replace a word entirely with a transparent gray box ───────────
    def _censor(self, mob):
        return RoundedRectangle(width=mob.width + 0.14, height=mob.height + 0.12,
                                corner_radius=0.05, fill_color=MUTED_GREY, fill_opacity=0.55,
                                stroke_width=0).move_to(mob)

    # ── title helpers (build small + scale so long titles don't wrap) ─────────
    def _fit(self, text, height, **kw):
        return crisp_text(text, font_size=10, **kw).scale_to_fit_height(height)

    def _scene_title(self, text):
        return self._fit(text, SCENE_TITLE_H, color=INK, weight=BOLD).move_to([0, TITLE_Y, 0])

    def _table_title(self, text, maxw):
        t = self._fit(text, TABLE_TITLE_H, color=INK, weight=BOLD)
        if t.width > maxw:
            t.scale_to_fit_width(maxw)
        return t

    # ── one titled table (title + column headers + baseline/mono rows) ────────
    def _table(self, title, headers, rows, *, top_y, cx, censor=()):
        lx, vx = cx + LABEL_DX, cx + VALUE_DX
        ttl = self._table_title(title, TABLE_TITLE_W).move_to([cx, top_y, 0])
        hy = top_y - TITLE_GAP
        hdr = VGroup(
            crisp_text(headers[0], font_size=HDR_FS, color=INK, weight=BOLD, baseline_at=(lx, hy)),
            crisp_text(headers[1], font_size=HDR_FS, color=INK, weight=BOLD, baseline_at=(vx, hy)))
        row_group = VGroup()
        for r, (lab, val) in enumerate(rows):
            ry = hy - HDR_GAP - r * ROW_DY
            label_mob = self._mono(lab, lx, ry)
            if lab in censor:
                label_mob = self._censor(label_mob)      # word replaced → never shown
            val_mob = crisp_text(val, font_size=ROW_FS, color=INK, baseline_at=(vx, ry))
            row_group.add(VGroup(label_mob, val_mob))
        tab = VGroup(ttl, hdr, row_group)
        tab.title, tab.header, tab.rows = ttl, hdr, row_group
        return tab

    def _reveal(self, tab, rows_run_time):
        """Fade the title+header in, then rise the rows up (FadeIn+shift keeps each cell's
        own opacity — so a censored cell keeps its transparency)."""
        self.play(FadeIn(tab.title), FadeIn(tab.header), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(row, shift=UP * 0.3) for row in tab.rows],
                              lag_ratio=0.12), run_time=rows_run_time)

    # ── the by-length double bar chart (adapt of scene 17's _strategy_chart) ──
    def _legend(self, entries, pos):
        g = VGroup()
        for name, color in entries:
            sq = Square(side_length=0.28, fill_color=color, fill_opacity=1.0, stroke_width=0)
            g.add(VGroup(sq, crisp_text(name, font_size=22, color=INK)).arrange(RIGHT, buff=0.18))
        return g.arrange(DOWN, buff=0.22, aligned_edge=LEFT).move_to(pos)

    def _axes(self, cx, base_y, W, H, ymax, ticks):
        xa = Line([cx - W / 2, base_y, 0], [cx + W / 2, base_y, 0], color=INK, stroke_width=3)
        ya = Line([cx - W / 2, base_y, 0], [cx - W / 2, base_y + H, 0], color=INK, stroke_width=3)
        g = VGroup(xa, ya)
        for t in ticks:
            yy = base_y + t / ymax * H
            tick = Line([cx - W / 2 - 0.12, yy, 0], [cx - W / 2, yy, 0], color=INK, stroke_width=2)
            lab = crisp_text(str(t), font_size=18, color=INK).next_to(tick, LEFT, buff=0.12)
            g.add(tick, lab)
        return g

    def _double_chart(self):
        data = short_words_data.get()["by_length"]
        lengths = sorted(int(L) for L in data["uniform"])
        ymax = max(data[w][str(L)]["avg"] for w in ("uniform", "best_opener") for L in lengths)
        W, cy, H = 12.6, -0.25, 3.8         # raised (cy) + bigger title gap → fills the top
        N, slot = len(lengths), 12.6 / len(lengths)
        dx = slot / 4.2                                     # half-gap between the paired bars
        base_y = cy - H / 2

        def series(w, color, off):
            items = [(str(L), data[w][str(L)]["avg"]) for L in lengths]
            return get_bar_chart(items, center=[off, cy, 0], width=W, height=H, y_max=ymax,
                                 n_slots=N, bar_color=color, bar_ratio=0.42, show_labels=False)

        uni, best = series("uniform", UNIFORM_COLOR, -dx), series("best_opener", BESTOP_COLOR, dx)
        axes = self._axes(0, base_y, W, H, ymax, [0, 2, 4, 6])
        xlabels = VGroup(*[crisp_text(str(L), font_size=20, color=INK).move_to(
                              [-W / 2 + (i + 0.5) * slot, base_y - 0.28, 0])
                           for i, L in enumerate(lengths)])
        xtitle = crisp_text("Word Length", font_size=24, color=INK).move_to([0, base_y - 0.78, 0])
        title = crisp_text("Optimal Misses per Word", font_size=34, color=INK,
                           weight=BOLD).move_to([0, cy + H / 2 + 1.15, 0])
        legend = self._legend([("Equal", UNIFORM_COLOR), ("Best Opener", BESTOP_COLOR)],
                              [4.6, cy + H / 2 - 0.2, 0])
        g = VGroup(uni, best, axes, xlabels, xtitle, title, legend)
        g.uni, g.best = uni, best
        g.rest = VGroup(axes, xlabels, xtitle, title, legend)
        return g

    # a : double bar chart — optimal avg misses per length, EQUAL vs BEST_OPENER
    @subscene
    def double_plot(self):
        self.chart = self._double_chart()
        self.chart.rest.set_opacity(0)                      # axes/labels/title/legend fade in with bars
        self.add(self.chart)
        bars = [*self.chart.uni.bars, *self.chart.best.bars]
        grow_bars(self, bars, 1.2, lag=0.02, extra=[self.chart.rest.animate.set_opacity(1)])

    # b : "2-Letter Words"; LEFT Common Patterns (top), Rare Patterns (bottom-anchored)
    @subscene
    def two_letter_patterns(self):
        self.play(FadeOut(self.chart), run_time=0.5)
        self.chart = None
        self.title = self._scene_title("2-Letter Words")
        self.play(FadeIn(self.title), run_time=0.5)

        t2 = self.tables["2"]
        common = self._table("Common Letter Patterns", ("Pattern", "Multiplier"),
                             self._pat_rows(t2["common_patterns"]), top_y=STACK_TOP, cx=LEFT_X)
        self._reveal(common, 1.0)
        rare = self._table("Rare Letter Patterns", ("Pattern", "Multiplier"),
                           self._pat_rows(t2["rare_patterns"]), top_y=STACK_BOTTOM_TITLE, cx=LEFT_X)
        self._reveal(rare, 1.0)
        self.left_tables = VGroup(common, rare)

    # c : RIGHT Common Words (top), Rare Words (bottom-anchored)
    @subscene
    def two_letter_words(self):
        t2 = self.tables["2"]
        common = self._table("Common Words", ("Word", "Frequency"),
                             self._word_rows(t2["common_words"]), top_y=STACK_TOP, cx=RIGHT_X)
        self._reveal(common, 1.0)
        rare = self._table("Rare Words", ("Word", "Frequency"),
                           self._word_rows(t2["rare_words"]), top_y=STACK_BOTTOM_TITLE, cx=RIGHT_X)
        self._reveal(rare, 1.0)
        self.right_tables = VGroup(common, rare)

    # d : title → "3-Letter Words"; clear len-2 tables; LEFT Common Patterns (12)
    @subscene
    def three_letter_patterns(self):
        new = self._scene_title("3-Letter Words")
        self.play(Transform(self.title, new), FadeOut(self.left_tables),
                  FadeOut(self.right_tables), run_time=0.6)
        self.left_tables = self.right_tables = None

        t3 = self.tables["3"]
        common = self._table("Common Letter Patterns", ("Pattern", "Multiplier"),
                             self._pat_rows(t3["common_patterns"]), top_y=LEN34_TOP, cx=LEFT_X)
        self._reveal(common, 1.6)
        self.left_tables = VGroup(common)

    # e : RIGHT Common Words (12; top word HAJ)
    @subscene
    def three_letter_words(self):
        t3 = self.tables["3"]
        common = self._table("Common Words", ("Word", "Frequency"),
                             self._word_rows(t3["common_words"]), top_y=LEN34_TOP, cx=RIGHT_X)
        self._reveal(common, 1.6)
        self.right_tables = VGroup(common)

    # f : title → "4-Letter Words"; clear the len-3 tables (title swap only)
    @subscene
    def four_letter_title(self):
        new = self._scene_title("4-Letter Words")
        self.play(Transform(self.title, new), FadeOut(self.left_tables),
                  FadeOut(self.right_tables), run_time=0.6)
        self.left_tables = self.right_tables = None

    # g : LEFT Common Patterns (12; duplicated-letter combos)
    @subscene
    def four_letter_patterns(self):
        t4 = self.tables["4"]
        common = self._table("Common Letter Patterns", ("Pattern", "Multiplier"),
                             self._pat_rows(t4["common_patterns"]), top_y=LEN34_TOP, cx=LEFT_X)
        self._reveal(common, 1.6)
        self.left_tables = VGroup(common)

    # h : RIGHT Common Words (12); the PIMP word is replaced by a transparent gray box
    @subscene
    def four_letter_words(self):
        t4 = self.tables["4"]
        common = self._table("Common Words", ("Word", "Frequency"),
                             self._word_rows(t4["common_words"]), top_y=LEN34_TOP, cx=RIGHT_X,
                             censor={"PIMP"})
        self._reveal(common, 1.6)
        self.right_tables = VGroup(common)
