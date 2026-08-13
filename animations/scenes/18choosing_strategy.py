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
  c strategy     — "Average Misses: N" (counter, top); LEFT = the most common real
                   4-letter words (by zipf), RIGHT = the most common letter-combos in the
                   wordlist, each a MULTI-ROW block of bars (scene-17 style, bold labels).
                   Starts UNIFORM (every bar equal). SOURCED scene18_data.
  d try_keep     — one combo bar rises → the WORDS exhibiting it rise too → the avg
                   counts UP; we KEEP it. Rising bars flash GREEN.
  e try_undo     — a DIFFERENT change → the avg counts DOWN (a failure) → undo → reset
                   the whole thing back to the uniform start. Falling bars flash CRIMSON.
  f replay       — replay the optimization uniform→final in N_BUCKETS steps: each step
                   morphs the combo bars, then the word bars, then the avg (grow = green,
                   shrink = crimson).

REUSE MAP (styling sources):
  - bars    : bpkfigures.bar_graph get_bar_chart / grow_bars (scene-17 word-frequency bars)
  - text    : crisp_text (non-chalkboard world), ink BLACK, bold bar labels
  - counter : a ValueTracker + become() so the avg number never moves or resizes
  - colours : ACCENT_FILL bars; grow = ACCENT_GREEN, shrink = CRIMSON; blue words

FLAGS (owned by a human — tune/decide in the timing+polish pass):
  - beat b background: the tree world is navy (scenes 01/05); roughed on a navy card.
  - TRACK_N / PER_ROW / row geometry / BAR_LABEL_FS / all run_times = guesses.
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets import scene18_data
from assets.chalkboard import BOARD_NAVY, CHALK
from bpkfigures.bar_graph import get_bar_chart, grow_bars

INK = BLACK                       # dark labels on the brand light-blue bg (scene-17 convention)
WORD_BLUE = ACCENT_FILL           # the blue words in the beat-a table + the resting bars
GROW_GREEN = ACCENT_GREEN         # a bar flashes green while it GROWS
SHRINK_CRIMSON = CRIMSON          # a bar flashes crimson while it SHRINKS
TITLE_Y = 3.7                     # beat-a table title

# ── beat-c/d/e/f bar composition (length 2 → 2 rows of 8) ─────────────────────
WORD_CX, COMBO_CX = -4.0, 4.0     # left = words, right = combos
ROW_W = 6.8                       # each side's row width
PER_ROW = 8                       # bars per row
ROW_H = 1.0                       # bar height at y_max
BASE_YS = [0.3, -1.9]             # the 2 row BASELINES (bars grow up)
BAR_LABEL_FS = 20                 # bold, scene-17-word-bar sized

# ── the mini best-opener greedy TREE (whole tree, no letters) on a navy card ───
TREE_C = (-4.2, 2.9)              # card centre (top-left, LEFT of the avg readout)
TREE_W, TREE_H = 6.2, 2.4         # the plotting box inside the card
AVG_C = (3.4, 2.9)               # "Average Misses: N" — to the RIGHT of the tree
TREE_DOT_R = 0.03
TREE_EDGE_W = 1.3
TREE_MISS_COL = CRIMSON           # miss edges (the deep "spine")
TREE_HIT_COL = CHALK              # hit edges + nodes (off-white)


class Scene18(HangmanScene):
    """The choosing strategy. See the module docstring for the beat map + flags."""

    def setup_scene(self):
        self.data = scene18_data.get()
        opt = self.data["optimization"]
        self.combos = opt["tracked_combos"]
        self.words = opt["tracked_words"]
        # per-side fixed y_max so every state's bars share one scale
        self.combo_ymax = max(max(b["combo_mult"]) for b in opt["buckets"])
        self.word_ymax = max(max(b["word_freq"]) for b in opt["buckets"])
        self.avg_tracker = ValueTracker(0.0)     # bare tracker pickles fine (updater added in body)
        # carried mobjects / state
        self.table = None
        self.tree_card = None                    # beat-b placeholder card
        self.mini_card = self.tree_mob = None    # beat-c+ mini greedy tree (+ its navy card)
        self.avg_label = self.avg_num = None
        self.word_charts = self.combo_charts = None
        self.word_bars = self.combo_bars = None
        self.word_base = self.combo_base = None
        self.word_vals = self.combo_vals = None

    # ── text helpers ──────────────────────────────────────────────────────────
    def _fit_text(self, text, width, **kw):
        # long crisp_text wraps at the 240pt supersample; build small, scale to width
        return crisp_text(text, font_size=10, **kw).scale_to_fit_width(width)

    def _number_text(self, value):
        """The avg number at a FIXED height + left edge, so counting never moves/resizes it."""
        return (crisp_text(f"{value:.2f}", font_size=10, color=INK, weight=BOLD)
                .scale_to_fit_height(self.num_h)
                .move_to([self.num_left, self.num_y, 0], aligned_edge=LEFT))

    def _setup_avg(self, value):
        # label + number built at the SAME base size and scaled together → same size
        label = crisp_text("Average Misses:", font_size=10, color=INK, weight=BOLD)
        num = crisp_text(f"{value:.2f}", font_size=10, color=INK, weight=BOLD)
        num.next_to(label, RIGHT, buff=0.12)
        VGroup(label, num).scale_to_fit_width(6.0).move_to([AVG_C[0], AVG_C[1], 0])
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

    def _count_and_tree(self, state, run_time):
        """Count the avg AND crossfade the mini tree to ``state``'s tree, together — the
        tree updates every time the avg does."""
        new_tree = self._tree_mob(state["tree"])
        self.avg_num.add_updater(
            lambda m: m.become(self._number_text(self.avg_tracker.get_value())))
        self.play(FadeOut(self.tree_mob), FadeIn(new_tree),
                  self.avg_tracker.animate.set_value(state["avg_misses"]), run_time=run_time)
        self.avg_num.clear_updaters()
        self.tree_mob = new_tree

    # ── mini tree (whole best-opener greedy tree, no letters) ─────────────────
    def _tree_mob(self, tree):
        """Draw the WHOLE tree as dots + hit/miss edges, fit into the TREE box. Layout:
        leaves spread left→right in order, an internal node sits above its children,
        depth increases downward. Miss edges (the spine) are crimson, hits off-white."""
        pos, leaf = {}, [0]

        def layout(node, depth):
            if node.get("leaf"):
                x = leaf[0]; leaf[0] += 1
            else:
                xs = [layout(k["sub"], depth + 1) for k in node["kids"]]
                x = sum(xs) / len(xs)
            pos[id(node)] = (x, depth)
            return x
        layout(tree, 0)

        xs = [p[0] for p in pos.values()]
        x0, x1 = min(xs), max(xs)
        dmax = max(p[1] for p in pos.values())
        sx = TREE_W / (x1 - x0 or 1)
        sy = TREE_H / (dmax or 1)

        def place(node):
            x, d = pos[id(node)]
            return [TREE_C[0] + (x - (x0 + x1) / 2) * sx, TREE_C[1] + TREE_H / 2 - d * sy, 0]

        edges, dots = VGroup(), VGroup()

        def draw(node):
            c = place(node)
            dots.add(Dot(c, radius=TREE_DOT_R, color=TREE_HIT_COL))
            if not node.get("leaf"):
                for k in node["kids"]:
                    edges.add(Line(c, place(k["sub"]), stroke_width=TREE_EDGE_W,
                                   color=(TREE_MISS_COL if k["miss"] else TREE_HIT_COL)))
                    draw(k["sub"])
        draw(tree)
        return VGroup(edges, dots)              # edges behind dots

    def _tree_card(self):
        return RoundedRectangle(width=TREE_W + 0.7, height=TREE_H + 0.7, corner_radius=0.15,
                                fill_color=BOARD_NAVY, fill_opacity=1.0,
                                stroke_color=WHITE, stroke_width=2).move_to([*TREE_C, 0])

    # ── bar helpers ───────────────────────────────────────────────────────────
    def _build_side(self, cx, labels, values, y_max):
        """A side's bars as ROWS get_bar_charts; return (charts, flat bars, flat baselines).
        Labels are re-aligned to one line per row (get_bar_chart top-aligns bbox tops, so
        ascender/descender words otherwise sit at different heights)."""
        charts, bars, base = [], [], []
        for r, base_y in enumerate(BASE_YS):
            sl = slice(r * PER_ROW, (r + 1) * PER_ROW)
            items = list(zip(labels[sl], values[sl]))
            chart = get_bar_chart(
                items, center=[cx, base_y + ROW_H / 2, 0], width=ROW_W, height=ROW_H,
                y_max=y_max, n_slots=PER_ROW, bar_color=WORD_BLUE, ink_color=INK,
                baseline_labels=True,                      # sit labels on one baseline
                label_factory=lambda s: crisp_text(s, font_size=BAR_LABEL_FS, color=INK,
                                                   weight=BOLD))
            charts.append(chart)
            bars += list(chart.bars)
            base += [base_y] * len(chart.bars)
        return charts, bars, base

    def _grow_anim(self, bar, base_y, h0, h1, flash=None):
        """One bar height h0→h1, flashing a colour while it changes then settling to blue.
        flash=None → direction (grow GREEN / shrink CRIMSON); flash=<colour> → force that
        colour for a changing bar (e.g. CRIMSON for a failed change, or WORD_BLUE = no flash)."""
        eps = 1e-6
        changed = abs(h1 - h0) > eps
        if flash is not None:
            dcol = flash if changed else WORD_BLUE
        else:
            dcol = GROW_GREEN if h1 > h0 + eps else SHRINK_CRIMSON if changed else WORD_BLUE

        def upd(m, a):
            m.stretch_to_fit_height(max(interpolate(h0, h1, a), 1e-3), about_edge=DOWN)
            m.set_y(base_y + m.height / 2)                    # keep the base pinned
            t = 0.0 if a < 0.72 else (a - 0.72) / 0.28        # hold flash colour, then ease to blue
            m.set_color(interpolate_color(dcol, WORD_BLUE, t))
        return UpdateFromAlphaFunc(bar, upd)

    def _morph_bars(self, bars, base, cur_vals, new_vals, y_max, run_time, flash=None):
        anims = [self._grow_anim(b, by, ROW_H * v0 / y_max, ROW_H * v1 / y_max, flash)
                 for b, by, v0, v1 in zip(bars, base, cur_vals, new_vals)]
        self.play(*anims, run_time=run_time)
        cur_vals[:] = list(new_vals)

    def _apply_state(self, state, combo_rt, word_rt, flash=None):
        """Morph combos, THEN words, to a {combo_mult, word_freq} state (script order)."""
        self._morph_bars(self.combo_bars, self.combo_base, self.combo_vals,
                         state["combo_mult"], self.combo_ymax, combo_rt, flash)
        self._morph_bars(self.word_bars, self.word_base, self.word_vals,
                         state["word_freq"], self.word_ymax, word_rt, flash)

    def _apply_state_at_once(self, state, run_time, flash=None):
        """Morph combos, words AND the avg counter to a state ALL in one play (used for
        the reset — cleanup, not a deliberate combo→word→avg step)."""
        anims = [self._grow_anim(b, by, ROW_H * v0 / self.combo_ymax,
                                 ROW_H * v1 / self.combo_ymax, flash)
                 for b, by, v0, v1 in zip(self.combo_bars, self.combo_base,
                                          self.combo_vals, state["combo_mult"])]
        anims += [self._grow_anim(b, by, ROW_H * v0 / self.word_ymax,
                                  ROW_H * v1 / self.word_ymax, flash)
                  for b, by, v0, v1 in zip(self.word_bars, self.word_base,
                                           self.word_vals, state["word_freq"])]
        new_tree = self._tree_mob(state["tree"])
        self.avg_num.add_updater(
            lambda m: m.become(self._number_text(self.avg_tracker.get_value())))
        self.play(*anims, FadeOut(self.tree_mob), FadeIn(new_tree),
                  self.avg_tracker.animate.set_value(state["avg_misses"]), run_time=run_time)
        self.avg_num.clear_updaters()
        self.tree_mob = new_tree
        self.combo_vals[:] = list(state["combo_mult"])
        self.word_vals[:] = list(state["word_freq"])

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
    #     the mini best-opener greedy TREE sits (on a navy card) left of the avg readout
    @subscene
    def strategy(self):
        self.play(FadeOut(self.tree_card), run_time=0.5)
        self.tree_card = None

        uni = self.data["optimization"]["buckets"][0]          # bucket 0 = uniform
        self._setup_avg(uni["avg_misses"])
        self.mini_card = self._tree_card()
        self.tree_mob = self._tree_mob(uni["tree"])
        self.word_charts, self.word_bars, self.word_base = self._build_side(
            WORD_CX, self.words, uni["word_freq"], self.word_ymax)
        self.combo_charts, self.combo_bars, self.combo_base = self._build_side(
            COMBO_CX, self.combos, uni["combo_mult"], self.combo_ymax)
        self.word_vals = list(uni["word_freq"])
        self.combo_vals = list(uni["combo_mult"])

        self.play(FadeIn(self.avg_label), FadeIn(self.avg_num),
                  FadeIn(self.mini_card), FadeIn(self.tree_mob), run_time=0.6)
        all_bars, label_fades = [], []
        for chart in (*self.word_charts, *self.combo_charts):
            self.add(chart)
            chart.labels.set_opacity(0)
            all_bars += list(chart.bars)
            label_fades.append(chart.labels.animate.set_opacity(1))
        grow_bars(self, all_bars, 1.3, lag=0.02, extra=label_fades)

    # ── d : a combo rises → its words rise → avg + tree update → keep ──────────
    @subscene
    def try_keep(self):
        after = self.data["example_keep"]["after"]
        self._apply_state(after, combo_rt=0.9, word_rt=0.9)    # combo bar (green), then its word bars
        self._count_and_tree(after, 0.8)                       # avg ticks UP + tree updates (kept)

    # ── e : a different change → avg counts DOWN (failure) → undo → reset ──────
    @subscene
    def try_undo(self):
        undo = self.data["example_undo"]
        # try the failing change: RAISE the e combo → GREEN (direction rule); avg drops
        self._apply_state(undo["worse"], combo_rt=0.9, word_rt=0.9)
        self._count_and_tree(undo["worse"], 0.8)               # DOWN = failure (+ tree)
        # undo it: LOWER the e combo back → CRIMSON (direction rule)
        self._apply_state(undo["base"], combo_rt=0.7, word_rt=0.7)
        self._count_and_tree(undo["base"], 0.6)
        # reset the kept beat-d change (lower u) — JUST resetting: bars + avg + tree
        # together in ONE play, kept BLUE
        self._apply_state_at_once(undo["reset"], run_time=0.9, flash=WORD_BLUE)

    # ── f : replay the optimization uniform→final, one step per change ─────────
    @subscene
    def replay(self):
        buckets = self.data["optimization"]["buckets"]         # 0 (uniform) .. final
        step = 0.45                   # lockstep montage (identical steps) — one knob
        for b in buckets[1:]:
            self._apply_state(b, combo_rt=step, word_rt=step)
            self._count_and_tree(b, step * 0.9)                # avg + tree update together
