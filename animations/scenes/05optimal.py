"""SCENE 05 — the OPTIMAL strategy, taught as a SEARCH on the length-2 tree.

Greedy does well, but the word set is small enough to do better: we can solve the
game exactly. This scene walks the exact solver's search on the smallest non-trivial
game — the 49 length-2 words — try every first letter, expand every situation,
recurse to the bottom, count the average misses, then back the values up the tree.
It closes with a greedy-vs-optimal comparison across all word lengths.

Runs on the NAVY chalkboard background (scene 04 ends by expanding the board to
navy). Decision nodes are the shared `tree_view` graph nodes (blue `ACCENT_FILL`
circle + white letter); board text is the chalk (written) font.

All numbers are SOURCED from `assets/tree2_data.py` (committed `tree2_cache.json`,
the annotated length-2 optimal tree from `optimal.annotated_tree`) and, for the
recap chart, `assets/greedy_data.py`. The render reads only the caches.

Script row 05, split on '—' (voiceover ↔ animation zip 1:1). BEAT MAP:
  a greedy_chart  — recap: greedy avg misses by word length (the scene-04 chart)
  b root_node     — one decision node appears centre (the top of the tree)
  c cycle_letters — cycle every letter A–Z through the node (which opener is best?)
  --- next sections (not yet built) ---
  d grid_spread   — 28 nodes into a 4×7 grid; each sprouts its next level (try every opener)
  e … the A-case dive, back-up/solve, dedup + prune, paired greedy-vs-optimal chart

Render:  render 05a --fast  (…05c)   /   render 05 sub  for the whole scene

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every fade/grow
run_time; the letter-cycle per-step run_time (0.09).
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from bpkfigures.bar_graph import get_bar_chart
from assets.chalkboard import CHALK, BOARD_NAVY, chalk_letter
from assets import tree_view as tv
from assets import tree2_data
from assets import greedy_data

DATA = tree2_data.get()
GDATA = greedy_data.get()

# ── recap chart (beat a) — light bars on navy, chalk labels ───────────────────
CHART_COLOR = LIGHT_BLUE

# ── decision node (beats b–c) ─────────────────────────────────────────────────
NODE_R_ROOT = 0.9         # radius of the lone root node at centre
LETTER_HFRAC = 0.8        # letter height as a fraction of node radius (matches tree_view)


# NOTE: `_chalk_num` / `_chalk_phrase` mirror scene 04's chart helpers so beat a
# renders identically to scene 04's avg chart. The chart itself DUPLICATES scene
# 04's `_avg_chart`; it will be unified into a shared helper when Part C builds the
# paired greedy-vs-optimal chart (which extends the same `bar_graph` asset).
def _chalk_phrase(text, *, height=0.4, stroke_width=3.2, buff=0.10, space=0.34,
                  color=CHALK):
    grp = VGroup()
    x = 0.0
    for ch in text.upper():
        if ch == " ":
            x += space
            continue
        L = chalk_letter(ch, height=height, stroke_width=stroke_width, color=color)
        L.move_to([x + L.width / 2, 0, 0])
        grp.add(L)
        x += L.width + buff
    grp.move_to(ORIGIN)
    return grp


def _chalk_num(n, *, height, stroke_width=2.6, color=CHALK):
    return _chalk_phrase(str(n), height=height, stroke_width=stroke_width,
                         buff=0.06, color=color)


class Scene05(HangmanScene):
    """Optimal strategy as a search on the length-2 tree.

    BEAT MAP (built so far):
      greedy_chart  — a: recap greedy avg-misses-by-length chart
      root_node     — b: the root decision node appears at centre
      cycle_letters — c: cycle every letter A–Z through the node
    """

    def setup_scene(self):
        # navy from frame 0 (scene 04 handed off on navy); nothing else on screen
        self.camera.background_color = BOARD_NAVY

    # ── shared node builder ───────────────────────────────────────────────────
    def _node_circle(self, center, r=NODE_R_ROOT):
        return Circle(radius=r, color=ACCENT_FILL, fill_opacity=1.0,
                      stroke_width=2.5).move_to(center)

    def _node_letter(self, ch, circ):
        lab = crisp_text(ch.upper(), color=WHITE, weight=BOLD)
        lab.scale_to_fit_height(circ.radius * LETTER_HFRAC).move_to(circ)
        return lab

    # ── a : recap the greedy avg-misses-by-length chart (from scene 04) ────────
    @subscene
    def greedy_chart(self):
        self.chart = self._greedy_chart()
        self.play(FadeIn(self.chart.axes), FadeIn(self.chart.labels),
                  FadeIn(self.chart.yticks), FadeIn(self.chart.title),
                  *[Create(b) for b in self.chart.bars], run_time=1.8)

    # ── b : the root decision node appears centre (the top of the tree) ────────
    @subscene
    def root_node(self):
        self.play(FadeOut(self.chart), run_time=0.6)
        self.chart = None
        self.node = self._node_circle(ORIGIN)
        self.node_letter = self._node_letter("a", self.node)
        self.play(GrowFromCenter(self.node), run_time=0.7)
        self.play(FadeIn(self.node_letter), run_time=0.3)

    # ── c : cycle every letter A–Z through the node (which opener is best?) ─────
    @subscene
    def cycle_letters(self):
        # lockstep cycle (one continuous VO) — settle back on A
        for ch in "bcdefghijklmnopqrstuvwxyza":
            self.play(Transform(self.node_letter, self._node_letter(ch, self.node)),
                      run_time=0.09)

    # ── components ─────────────────────────────────────────────────────────────
    def _greedy_chart(self):
        """Greedy avg misses by word length, on the SHARED `get_bar_chart` (chalk
        labels, y_max=7). DUPLICATES scene 04's `_avg_chart` — see module note."""
        data = GDATA["avg_misses_by_length"]
        lengths = sorted(int(k) for k in data)
        items = [(L, data[str(L)]["avg_misses"]) for L in lengths]
        chart = get_bar_chart(
            items, center=[0, 0, 0], width=12.0, height=4.2, y_max=7,
            bar_color=CHART_COLOR, ink_color=CHALK, bar_ratio=0.75,
            bar_stroke_width=4, bar_outline="open",
            label_factory=lambda L: _chalk_num(L, height=0.24), label_buff=0.20,
            x_axis=True, y_axis=True,
            y_ticks=range(0, 8, 2),
            y_tick_factory=lambda t: _chalk_num(t, height=0.22),
            title_mobject=_chalk_phrase("Average Misses by Word Length", height=0.38),
            title_buff=0.5,
        )
        chart.shift([0, -chart.get_center()[1], 0])
        chart.axes = VGroup(chart.x_axis, chart.y_axis)
        return chart
