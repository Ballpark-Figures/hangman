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
                           black box (censored) so it's never shown.

Formatting conventions (routed through single helpers so they hold everywhere):
  - every number is 2 SIGNIFICANT FIGURES (`_sig2`) — multipliers AND word %.
  - a pattern (blanked word) / a word is BOLD and MONOSPACED (`_mono`) — each letter on a
    fixed slot so they form little COLUMNS down the table.
  - pattern tables show only multiplier != 1 (Common = boosted, Rare = reduced).

REUSE MAP (styling sources):
  - table machinery : assets.word_tables_scene.WordTablesScene — the SHARED base holding
                      `_table`/`_reveal`/`_mono`/`_sig2`/`_scene_title`/`_censor` + the
                      layout constants; also the base for scene 20 (longer_words).
  - double chart    : bpkfigures.bar_graph.grouped_bar_chart + grow_bars — the SHARED grouped
                      bar chart (axes, x/y labels, title, legend), also used by scene 17's
                      optimal-vs-zipf plot. Just pass the two series + labels here.
  - text/colour     : crisp_text, INK = BLACK; bars ACCENT_FILL (uniform) / CRIMSON (best_opener).

FLAGS (owned by a human — tune/decide in the timing+polish pass):
  - table TITLES ("Common Letter Patterns" …) are rendered as captions; drop/reword if undesired.
  - "Blur PIMP" is done as a transparent black CENSOR box over the word (per the user); swap for
    a real blur in post if preferred.
  - all geometry (columns, CHAR_W, row spacing, stack anchors, chart box) + run_times = guesses.

Render:  render 19a --fast (…19h)  /  render 19 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets import short_words_data
from assets.word_tables_scene import (
    WordTablesScene, INK, UNIFORM_COLOR, BESTOP_COLOR, LEFT_X, RIGHT_X)
from bpkfigures.bar_graph import grouped_bar_chart, grow_bars

STACK_TOP = 2.85                   # len-2: top (Common) table's title y
STACK_BOTTOM_TITLE = -0.55         # len-2: bottom (Rare) table's title y — the two Rare tables
                                   # share this y so their titles ALIGN (regardless of row count)
LEN34_TOP = 2.85                   # len-3/4: the single table's title y


class Scene19(WordTablesScene):
    """Short words — the choosing strategy for lengths 2/3/4. See docstring for beats."""

    def setup_scene(self):
        self.tables = short_words_data.get()["tables"]
        self.chart = None
        self.title = None
        self.left_tables = self.right_tables = None

    # ── the by-length double bar chart (shared bpkfigures.grouped_bar_chart) ──
    def _double_chart(self):
        data = short_words_data.get()["by_length"]
        lengths = sorted(int(L) for L in data["uniform"])
        uni = [data["uniform"][str(L)]["avg"] for L in lengths]
        best = [data["best_opener"][str(L)]["avg"] for L in lengths]
        return grouped_bar_chart(
            lengths, [("Uniform", UNIFORM_COLOR, uni), ("Better Choosing", BESTOP_COLOR, best)],
            title="Optimal Misses per Word", x_title="Word Length", ink_color=INK)

    # a : double bar chart — optimal avg misses per length, UNIFORM vs BETTER CHOOSING
    @subscene
    def double_plot(self):
        self.chart = self._double_chart()
        self.chart.rest.set_opacity(0)                      # axes/labels/title/legend fade in with bars
        self.add(self.chart)
        grow_bars(self, self.chart.bars, 1.2, lag=0.02,
                  extra=[self.chart.rest.animate.set_opacity(1)])

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
                             self._word_rows(t2["common_words"]), top_y=STACK_TOP, cx=RIGHT_X,
                             mono=False)
        self._reveal(common, 1.0)
        rare = self._table("Rare Words", ("Word", "Frequency"),
                           self._word_rows(t2["rare_words"]), top_y=STACK_BOTTOM_TITLE, cx=RIGHT_X,
                           mono=False)
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
                             self._word_rows(t3["common_words"]), top_y=LEN34_TOP, cx=RIGHT_X,
                             mono=False)
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
                             mono=False, censor={"PIMP"})
        self._reveal(common, 1.6)
        self.right_tables = VGroup(common)
