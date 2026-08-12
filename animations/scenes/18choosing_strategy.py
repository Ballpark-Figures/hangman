"""SCENE 18 — the CHOOSING strategy (best-opener word choice, length 4).

The chooser's half of the game: how to pick words that are HARD to guess. We start
by naively picking the hardest single words, reject that, then hill-climb a per-word
frequency distribution (via letter-combo multipliers) that maximises the best-opener
guesser's average misses.

BEAT MAP (Script.md scene 18; --- delimited, 6 beats a-f):
  a most_misses    — table "Words with Most Misses" (cols Words / # Misses), the top
                     words under OPTIMAL play. SOURCED scene18_data.most_misses
                     (greedy-completed upper bound at the unconverged short lengths —
                     a NEAR-OPTIMAL number, per the user's call). FadeIn (a reference
                     list, not gameplay drawing).
  b opt_tree       — the optimal length-2 tree + "*See blog post for more information".
                     >>> PLACEHOLDER: this is meant to be the SAME tree as the END of
                     scene 05 (tree2_data.py), which isn't built yet. Roughed as a
                     labelled card; wire in scene 05's tree builder once it exists.
  c strategy       — "Average Misses: 6.80" (top); LEFT = top len-4 words by frequency
                     as bars, RIGHT = top letter-combos by adjustment factor as bars,
                     in the style of scene 17's word-frequency bars. This is the FINAL
                     (bucket-10) state. SOURCED scene18_data.choosing / .optimization.
  d try_keep       — one combo bar change that RAISES misses → keep it.
  e try_undo       — one change that LOWERS misses → undo → reset the whole thing to
                     the uniform start.
  f replay         — replay the whole optimization start→final in 10 equal buckets:
                     each bucket morphs the combo bars, the word bars, then the avg.

REUSE MAP (styling sources):
  - bars            : bpkfigures.bar_graph get_bar_chart / morph_bar_chart / grow_bars
                      (same as scene 17's "Word Frequency" bars)
  - text            : crisp_text (non-chalkboard world), ink BLACK on the brand bg
  - colours         : ACCENT_FILL bars, ACCENT_GOLD for the highlighted change
  - numbers         : ALL from assets/scene18_data (committed cache); render never
                      touches math/

FLAGS (owned by a human — tune/decide in the timing+polish pass):
  - beats d/e reset to the START before demonstrating: a change can only RAISE misses
    away from the converged optimum, so the "increase → keep" demo (beat d) is truthful
    only from the uniform start. This RE-ORDERS the script's reset (script resets in
    beat e). >>> CONFIRM how you want 3→4→5 sequenced.
  - WORD_N / COMBO_N bars shown, chart sizes/positions, all run_times = guesses.
  - beat b background: the tree world is navy (scenes 01/05); roughed on the brand bg.

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

INK = BLACK                      # dark labels on the brand light-blue bg (scene-17 convention)
TITLE_Y = 3.7

# ── beat-a table ──────────────────────────────────────────────────────────────
TABLE_ROWS = 10                  # rows shown (data may carry a few more for ties)

# ── beats c-f bar composition ─────────────────────────────────────────────────
WORD_CX, COMBO_CX = -3.9, 3.9    # left = words, right = combos
HALF_W = 6.6                     # each half's chart width
BARS_H = 3.4                     # chart height
BARS_CY = -1.7                   # baseline row centre (bars grow up)
BAR_LABEL_FS = 14


class Scene18(HangmanScene):
    """The choosing strategy. See the module docstring for the beat map + flags."""

    def setup_scene(self):
        self.data = scene18_data.get()
        # per-side fixed y_max so every bucket's bars share one scale (morph pairs them)
        opt = self.data["optimization"]
        self.combo_ymax = max(max(b["combo_mult"]) for b in opt["buckets"])
        self.word_ymax = max(max(b["word_freq"]) for b in opt["buckets"])
        # carried mobjects
        self.table = None
        self.tree_card = None
        self.avg_title = None
        self.word_chart = self.combo_chart = None

    # ── helpers ───────────────────────────────────────────────────────────────
    def _bucket(self, i):
        return self.data["optimization"]["buckets"][i]

    def _word_chart(self, values):
        opt = self.data["optimization"]
        items = list(zip(opt["tracked_words"], values))
        return get_bar_chart(items, center=[WORD_CX, BARS_CY, 0], width=HALF_W,
                             height=BARS_H, y_max=self.word_ymax, bar_color=ACCENT_FILL,
                             ink_color=INK, label_factory=lambda s: crisp_text(
                                 s, font_size=BAR_LABEL_FS, color=INK))

    def _combo_chart(self, values):
        opt = self.data["optimization"]
        items = list(zip(opt["tracked_combos"], values))
        return get_bar_chart(items, center=[COMBO_CX, BARS_CY, 0], width=HALF_W,
                             height=BARS_H, y_max=self.combo_ymax, bar_color=ACCENT_FILL,
                             ink_color=INK, label_factory=lambda s: crisp_text(
                                 s, font_size=BAR_LABEL_FS, color=INK))

    def _fit_text(self, text, width, **kw):
        # long crisp_text wraps at the 240pt supersample; build small, scale to width
        return crisp_text(text, font_size=10, **kw).scale_to_fit_width(width)

    def _avg_label(self, value):
        return self._fit_text(f"Average Misses: {value:.2f}", 5.5, color=INK,
                              weight=BOLD).move_to([0, TITLE_Y, 0])

    # ── a : "Words with Most Misses" table (top words under OPTIMAL play) ──────
    @subscene
    def most_misses(self):
        mm = self.data["most_misses"]
        rows = mm["table"][:max(TABLE_ROWS, len(mm["tied_at_max"]))]

        title = self._fit_text("Words with Most Misses", 7.0, color=INK,
                               weight=BOLD).move_to([0, TITLE_Y, 0])
        hdr_w = crisp_text("Words", font_size=30, color=INK, weight=BOLD)
        hdr_m = self._fit_text("# Misses", 1.8, color=INK, weight=BOLD)
        col_w, col_m = -1.9, 1.9
        header = VGroup(hdr_w.move_to([col_w, 2.5, 0]), hdr_m.move_to([col_m, 2.5, 0]))

        body = VGroup()
        for r, row in enumerate(rows):
            y = 1.9 - r * 0.52
            body.add(crisp_text(row["word"], font_size=26, color=INK).move_to([col_w, y, 0]))
            body.add(crisp_text(str(row["misses"]), font_size=26, color=INK).move_to([col_m, y, 0]))
        self.table = VGroup(title, header, body)
        self.play(FadeIn(self.table), run_time=0.8)

    # ── b : optimal length-2 tree (PLACEHOLDER — mirrors the end of scene 05) ──
    @subscene
    def opt_tree(self):
        self.play(FadeOut(self.table), run_time=0.5)
        self.table = None

        card = RoundedRectangle(width=9.0, height=5.0, corner_radius=0.2,
                                fill_color=BOARD_NAVY, fill_opacity=1.0,
                                stroke_color=WHITE, stroke_width=2).move_to([0, 0.3, 0])
        note = crisp_text("Optimal length-2 tree\n(mirrors the end of scene 05)",
                          font_size=30, color=WHITE).move_to(card.get_center())
        foot = crisp_text("*See blog post for more information", font_size=22,
                          color=INK).move_to([0, -3.3, 0])
        self.tree_card = VGroup(card, note, foot)
        self.play(FadeIn(self.tree_card), run_time=0.8)

    # ── c : the final choosing strategy — avg misses + word bars + combo bars ──
    @subscene
    def strategy(self):
        self.play(FadeOut(self.tree_card), run_time=0.5)
        self.tree_card = None

        final = self._bucket(len(self.data["optimization"]["buckets"]) - 1)
        self.avg_title = self._avg_label(final["avg_misses"])
        self.word_chart = self._word_chart(final["word_freq"])
        self.combo_chart = self._combo_chart(final["combo_mult"])

        self.play(FadeIn(self.avg_title), run_time=0.6)
        for chart in (self.word_chart, self.combo_chart):
            self.add(chart)
            chart.labels.set_opacity(0)          # grow_bars restores bars; fade labels in via extra
        grow_bars(self, [*self.word_chart.bars, *self.combo_chart.bars], 1.3, lag=0.03,
                  extra=[self.word_chart.labels.animate.set_opacity(1),
                         self.combo_chart.labels.animate.set_opacity(1)])

    # ── d : a change that RAISES misses → keep (demoed from the uniform start) ─
    @subscene
    def try_keep(self):
        # reset the composition to the uniform START so a change can truthfully RAISE
        # misses (see the FLAG in the docstring re: 3→4→5 ordering).
        start = self._bucket(0)
        new_w, new_c = self._word_chart(start["word_freq"]), self._combo_chart(start["combo_mult"])
        new_avg = self._avg_label(start["avg_misses"])
        self.play(*morph_bar_chart(self.word_chart, new_w),
                  *morph_bar_chart(self.combo_chart, new_c),
                  Transform(self.avg_title, new_avg), run_time=1.0)

        keep = self.data["example_keep"]
        # grow one combo bar (illustrative) and tick the avg UP; keep it.
        pat = keep["pattern"]
        bar = self.combo_chart.bar_of.get(pat) or self.combo_chart.bars[0]
        raised = self._avg_label(keep["after_avg"])
        self.play(bar.animate.set_color(ACCENT_GOLD).stretch_to_fit_height(
            bar.get_height() * 1.6, about_edge=DOWN),
            Transform(self.avg_title, raised), run_time=1.0)
        self.play(bar.animate.set_color(ACCENT_FILL), run_time=0.4)   # accepted → back to fill

    # ── e : a change that LOWERS misses → undo → reset to the start ────────────
    @subscene
    def try_undo(self):
        undo = self.data["example_undo"]
        pat = undo["pattern"]
        bar = self.combo_chart.bar_of.get(pat) or self.combo_chart.bars[0]
        h0 = bar.get_height()
        worse = self._avg_label(undo["worse_avg"])
        # try it: bar changes, avg drops (worse for the adversary)
        self.play(bar.animate.set_color(ACCENT_GOLD).stretch_to_fit_height(
            h0 * 1.6, about_edge=DOWN), Transform(self.avg_title, worse), run_time=1.0)
        # undo: back to where it was
        start = self._bucket(0)
        back = self._avg_label(start["avg_misses"])
        self.play(bar.animate.set_color(ACCENT_FILL).stretch_to_fit_height(h0, about_edge=DOWN),
                  Transform(self.avg_title, back), run_time=0.8)

    # ── f : replay the optimization start→final in 10 equal buckets ────────────
    @subscene
    def replay(self):
        buckets = self.data["optimization"]["buckets"]
        step = 0.7                    # lockstep montage (10 identical bucket steps) — one knob
        for i in range(1, len(buckets)):
            b = buckets[i]
            new_c = self._combo_chart(b["combo_mult"])
            new_w = self._word_chart(b["word_freq"])
            new_avg = self._avg_label(b["avg_misses"])
            self.play(*morph_bar_chart(self.combo_chart, new_c), run_time=step)
            self.play(*morph_bar_chart(self.word_chart, new_w), run_time=step)
            self.play(Transform(self.avg_title, new_avg), run_time=step * 0.6)
