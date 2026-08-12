"""SCENE 18 — the CHOOSING strategy (best-opener word choice, length 4).

The chooser's half of the game: how to pick words that are HARD to guess. We start
by naively picking the hardest single words, reject that, then hill-climb a per-word
frequency distribution (via letter-combo multipliers) that maximises the best-opener
guesser's average misses — starting from a UNIFORM (every word equally likely) game.

BEAT MAP (Script.md scene 18; --- delimited, 6 beats a-f):
  a most_misses  — table "Words with Most Misses" (cols Words / # Misses), the words
                   the OPTIMAL guesser misses most. Words in BLUE; rows rise in with a
                   lagged upward cascade; only the top (14-miss) words are listed.
                   SOURCED scene18_data.most_misses (greedy-completed upper bound at the
                   unconverged short lengths — a NEAR-OPTIMAL number, per the user).
  b opt_tree     — the optimal length-2 tree + "*See blog post for more information".
                   >>> PLACEHOLDER: meant to be the SAME tree as the END of scene 05
                   (tree2_data.py), not built yet. Roughed as a labelled card.
  c strategy     — "Average Misses: N" (counter, top); LEFT = top len-4 words, RIGHT =
                   top letter-combos, each a MULTI-ROW block of bars (scene-17 style).
                   Starts UNIFORM (every bar equal). SOURCED scene18_data.
  d try_keep     — one combo bar rises → the WORDS exhibiting it rise too → the avg
                   counts UP; we KEEP it.
  e try_undo     — a DIFFERENT change → the avg counts DOWN (a failure) → undo → reset
                   the whole thing back to the uniform start.
  f replay       — replay the optimization uniform→final in N_BUCKETS steps: each step
                   morphs the combo bars, then the word bars, then the avg.

REUSE MAP (styling sources):
  - bars    : bpkfigures.bar_graph get_bar_chart / morph_bar_chart / grow_bars (scene 17)
  - text    : crisp_text (non-chalkboard world), ink BLACK on the brand bg
  - counter : a ValueTracker + become() so the avg number never moves or resizes
  - colours : ACCENT_FILL bars + blue words; numbers ALL from assets/scene18_data cache

FLAGS (owned by a human — tune/decide in the timing+polish pass):
  - beat b background: the tree world is navy (scenes 01/05); roughed on a navy card.
  - TRACK_N / PER_ROW / row geometry / all run_times = guesses. The uniform bars start
    SHORT (final products are up to ~19× the uniform 1) — the honest scene-17 linear
    scale; if that reads too flat, say so and we can start them at an equal DISPLAY
    height instead.

Render:  render 18a --fast (…18f)  /  render 18 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets import scene18_data
from assets.chalkboard import BOARD_NAVY
from bpkfigures.bar_graph import get_bar_chart, morph_bar_chart, grow_bars

INK = BLACK                       # dark labels on the brand light-blue bg (scene-17 convention)
WORD_BLUE = ACCENT_FILL           # the blue words in the beat-a table + the bars
TITLE_Y = 3.7

# ── beat-c/d/e/f multi-row bar composition ────────────────────────────────────
WORD_CX, COMBO_CX = -4.0, 4.0     # left = words, right = combos
ROW_W = 6.8                       # each side's row width
PER_ROW = 8                       # bars per row (TRACK_N // ROWS)
ROW_H = 1.1                       # bar height at y_max
BASE_YS = [1.4, -0.3, -2.0]       # the 3 row BASELINES (bars grow up; ROWS = len(BASE_YS))
BAR_LABEL_FS = 13


class Scene18(HangmanScene):
    """The choosing strategy. See the module docstring for the beat map + flags."""

    def setup_scene(self):
        self.data = scene18_data.get()
        opt = self.data["optimization"]
        self.combos = opt["tracked_combos"]
        self.words = opt["tracked_words"]
        # per-side fixed y_max so every state's bars share one scale (morph pairs them)
        self.combo_ymax = max(max(b["combo_mult"]) for b in opt["buckets"])
        self.word_ymax = max(max(b["word_freq"]) for b in opt["buckets"])
        self.avg_tracker = ValueTracker(0.0)     # bare tracker pickles fine (updater added in body)
        # carried mobjects
        self.table = None
        self.tree_card = None
        self.avg_label = self.avg_num = None
        self.word_rows = self.combo_rows = None

    # ── text helpers ──────────────────────────────────────────────────────────
    def _fit_text(self, text, width, **kw):
        # long crisp_text wraps at the 240pt supersample; build small, scale to width
        return crisp_text(text, font_size=10, **kw).scale_to_fit_width(width)

    def _number_text(self, value):
        """The avg number at a FIXED height + left edge, so counting never moves/resizes it."""
        t = crisp_text(f"{value:.2f}", font_size=48, color=INK, weight=BOLD)
        t.scale_to_fit_height(self.num_h).move_to([self.num_left, self.num_y, 0], aligned_edge=LEFT)
        return t

    def _setup_avg(self, value):
        label = self._fit_text("Average Misses:", 3.8, color=INK, weight=BOLD)
        num = crisp_text(f"{value:.2f}", font_size=48, color=INK, weight=BOLD)
        num.scale_to_fit_height(label.height).next_to(label, RIGHT, buff=0.22)
        VGroup(label, num).move_to([0, TITLE_Y, 0])
        self.num_h = num.height
        self.num_left, self.num_y = num.get_left()[0], num.get_center()[1]
        self.avg_label, self.avg_num = label, num
        self.avg_tracker.set_value(value)

    def _count_to(self, value, run_time):
        """Animate the avg number to ``value`` with a counter (become() from the tracker)."""
        self.avg_num.add_updater(
            lambda m: m.become(self._number_text(self.avg_tracker.get_value())))
        self.play(self.avg_tracker.animate.set_value(value), run_time=run_time)
        self.avg_num.clear_updaters()

    # ── bar helpers ───────────────────────────────────────────────────────────
    def _side_rows(self, cx, labels, values, y_max):
        """A side's bars as ROWS get_bar_charts (PER_ROW bars each), heights = values."""
        rows = []
        for r, base_y in enumerate(BASE_YS):
            sl = slice(r * PER_ROW, (r + 1) * PER_ROW)
            items = list(zip(labels[sl], values[sl]))
            rows.append(get_bar_chart(
                items, center=[cx, base_y + ROW_H / 2, 0], width=ROW_W, height=ROW_H,
                y_max=y_max, n_slots=PER_ROW, bar_color=WORD_BLUE, ink_color=INK,
                label_factory=lambda s: crisp_text(s, font_size=BAR_LABEL_FS, color=INK)))
        return rows

    def _remorph(self, old_rows, cx, labels, values, y_max, run_time):
        """Morph a side's row-charts to new ``values``; return the new live row-charts."""
        new_rows = self._side_rows(cx, labels, values, y_max)
        anims = []
        for o, n in zip(old_rows, new_rows):
            anims += morph_bar_chart(o, n)
        self.play(*anims, run_time=run_time)
        return new_rows

    def _apply_state(self, state, combo_rt, word_rt):
        """Morph combos, THEN words, to a {combo_mult, word_freq} state (script order)."""
        self.combo_rows = self._remorph(self.combo_rows, COMBO_CX, self.combos,
                                        state["combo_mult"], self.combo_ymax, combo_rt)
        self.word_rows = self._remorph(self.word_rows, WORD_CX, self.words,
                                       state["word_freq"], self.word_ymax, word_rt)

    # ── a : "Words with Most Misses" — blue words, lagged upward rise, 14-miss set ──
    @subscene
    def most_misses(self):
        mm = self.data["most_misses"]
        top = [r for r in mm["table"] if r["misses"] == mm["max_misses"]]   # only the 14-miss words

        title = self._fit_text("Words with Most Misses", 7.0, color=INK,
                               weight=BOLD).move_to([0, TITLE_Y, 0])
        hdr = VGroup(crisp_text("Words", font_size=30, color=INK, weight=BOLD).move_to([-1.9, 2.5, 0]),
                     self._fit_text("# Misses", 1.8, color=INK, weight=BOLD).move_to([1.9, 2.5, 0]))
        rows = VGroup()
        for r, row in enumerate(top):
            y = 1.85 - r * 0.5
            rows.add(VGroup(
                crisp_text(row["word"], font_size=26, color=WORD_BLUE).move_to([-1.9, y, 0]),
                crisp_text(str(row["misses"]), font_size=26, color=INK).move_to([1.9, y, 0])))
        for row in rows:
            row.shift(DOWN * 0.4).set_opacity(0)          # start below + hidden → rise in

        self.table = VGroup(title, hdr, rows)
        self.play(FadeIn(title), FadeIn(hdr), run_time=0.6)
        self.play(LaggedStart(*[row.animate.shift(UP * 0.4).set_opacity(1) for row in rows],
                              lag_ratio=0.18), run_time=1.4)

    # ── b : optimal length-2 tree (PLACEHOLDER — mirrors the end of scene 05) ──
    @subscene
    def opt_tree(self):
        self.play(FadeOut(self.table), run_time=0.5)
        self.table = None

        card = RoundedRectangle(width=9.0, height=4.6, corner_radius=0.2,
                                fill_color=BOARD_NAVY, fill_opacity=1.0,
                                stroke_color=WHITE, stroke_width=2).move_to([0, 0.5, 0])
        note = VGroup(crisp_text("Optimal length-2 tree", font_size=30, color=WHITE),
                      crisp_text("(mirrors the end of scene 05)", font_size=24, color=WHITE))
        note.arrange(DOWN, buff=0.3).move_to(card.get_center())
        foot = self._fit_text("*See blog post for more information", 6.0,
                              color=INK).move_to([0, -3.2, 0])
        self.tree_card = VGroup(card, note, foot)
        self.play(FadeIn(self.tree_card), run_time=0.8)

    # ── c : the choosing strategy composition — starts UNIFORM (every bar equal) ──
    @subscene
    def strategy(self):
        self.play(FadeOut(self.tree_card), run_time=0.5)
        self.tree_card = None

        uni = self.data["optimization"]["buckets"][0]          # bucket 0 = uniform
        self._setup_avg(uni["avg_misses"])
        self.word_rows = self._side_rows(WORD_CX, self.words, uni["word_freq"], self.word_ymax)
        self.combo_rows = self._side_rows(COMBO_CX, self.combos, uni["combo_mult"], self.combo_ymax)

        self.play(FadeIn(self.avg_label), FadeIn(self.avg_num), run_time=0.6)
        all_bars, label_fades = [], []
        for chart in (*self.word_rows, *self.combo_rows):
            self.add(chart)
            chart.labels.set_opacity(0)
            all_bars += list(chart.bars)
            label_fades.append(chart.labels.animate.set_opacity(1))
        grow_bars(self, all_bars, 1.3, lag=0.02, extra=label_fades)

    # ── d : a combo rises → its words rise → avg counts UP → keep ──────────────
    @subscene
    def try_keep(self):
        after = self.data["example_keep"]["after"]
        self._apply_state(after, combo_rt=0.9, word_rt=0.9)    # combo bar, then its word bars
        self._count_to(after["avg_misses"], 0.8)               # avg ticks UP (kept)

    # ── e : a different change → avg counts DOWN (failure) → undo → reset ──────
    @subscene
    def try_undo(self):
        undo = self.data["example_undo"]
        # try the failing change: bars move, avg drops
        self._apply_state(undo["worse"], combo_rt=0.9, word_rt=0.9)
        self._count_to(undo["worse"]["avg_misses"], 0.8)       # DOWN = failure
        # undo it: back to the kept (beat-d) state
        self._apply_state(undo["base"], combo_rt=0.7, word_rt=0.7)
        self._count_to(undo["base"]["avg_misses"], 0.6)
        # reset the whole thing back to the uniform start
        self._apply_state(undo["reset"], combo_rt=0.9, word_rt=0.9)
        self._count_to(undo["reset"]["avg_misses"], 0.8)

    # ── f : replay the optimization uniform→final in N_BUCKETS steps ───────────
    @subscene
    def replay(self):
        buckets = self.data["optimization"]["buckets"]         # 0 (uniform) .. N (final)
        step = 0.3                    # lockstep montage (identical bucket steps) — one knob
        for b in buckets[1:]:
            self.combo_rows = self._remorph(self.combo_rows, COMBO_CX, self.combos,
                                            b["combo_mult"], self.combo_ymax, step)
            self.word_rows = self._remorph(self.word_rows, WORD_CX, self.words,
                                           b["word_freq"], self.word_ymax, step)
            self._count_to(b["avg_misses"], step * 0.7)
