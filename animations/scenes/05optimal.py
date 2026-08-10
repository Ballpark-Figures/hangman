"""SCENE 05 — the OPTIMAL strategy, taught as a SEARCH on the length-2 tree.

Greedy does well, but the word set is small enough to do better: we can solve the
game exactly. This scene walks the exact solver's search on the smallest non-trivial
game — the 49 length-2 words — try every first letter, expand every situation,
recurse to the bottom, count the average misses, then back the values up the tree.
It closes with a greedy-vs-optimal comparison across all word lengths.

Runs on the NAVY background (scene 04 ends by expanding the board to navy). This is
NOT the chalkboard, so text is `crisp_text` and charts are FILLED (no chalk font, no
line-outline bars — see hangman CLAUDE.md). Decision nodes use the INTRO tree styling
(a `Dot` coloured by miss-count with the guess letter knocked out in `BOARD_NAVY` —
mirrors `92wintree_test._node_marker`), NOT `tree_view`'s solid-circle nodes.

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
from assets.chalkboard import CHALK, BOARD_NAVY
from assets import tree2_data
from assets import greedy_data

DATA = tree2_data.get()
GDATA = greedy_data.get()

# ── recap chart (beat a) — crisp labels + FILLED bars on navy (NOT chalk / not
#    line-outline: navy is not the chalkboard — see hangman CLAUDE.md) ───────────
CHART_COLOR = LIGHT_BLUE

# ── decision nodes (intro tree styling: a Dot coloured by miss-count with the
#    guess letter knocked out in navy; mirrors 92wintree_test._node_marker) ──────
NODE_R_ROOT   = 0.5       # lone root node at full frame (≈ the intro's on-screen root:
                          # DOT_R_ROOT/CAM_W_START × frame width ≈ 0.09/3 × 16)
NODE_LETTER_H = 1.3       # guess-letter height as a multiple of node radius (intro)


def _miss_color(misses):
    """Node/edge colour by miss-count: 0 = CHALK (white), then 1→purple … 6→red
    (LIGHT_PALETTE reversed). Mirrors 92wintree_test._miss_color."""
    if misses <= 0:
        return CHALK
    return LIGHT_PALETTE[len(LIGHT_PALETTE) - misses]


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

    # ── shared node builder (intro styling) ───────────────────────────────────
    def _node_dot(self, center, r=NODE_R_ROOT, *, misses=0):
        return Dot(center, radius=r, color=_miss_color(misses), z_index=2)

    def _node_letter(self, ch, node):
        lab = crisp_text(ch.upper(), color=BOARD_NAVY, weight=BOLD)
        lab.scale_to_fit_height(NODE_LETTER_H * node.radius).move_to(node)
        lab.set_z_index(3)
        return lab

    def _grow_up(self, bars, *extra, run_time=1.0):
        """Height-only grow: each bar rises from the axis (x fixed). ``extra`` plays
        alongside. The normal filled-bar reveal (mirrors yahtzee 07's `_grow_up`)."""
        for b in bars:
            b.save_state()
            b.stretch(1e-3, dim=1, about_edge=DOWN)
        self.play(*[Restore(b) for b in bars], *extra, run_time=run_time)

    # ── a : recap the greedy avg-misses-by-length chart (from scene 04) ────────
    @subscene
    def greedy_chart(self):
        self.chart = self._greedy_chart()
        # title kept to ONE line: crisp_text supersamples to a 240pt cap, at which a
        # long string wraps in pango — so build it small (low underlying pt) and
        # scale up to the on-screen width.
        self.chart_title = crisp_text("Average Misses by Word Length",
                                      font_size=10, color=WHITE, weight=BOLD)
        self.chart_title.scale_to_fit_width(6.5).next_to(self.chart, UP, buff=0.4)
        rest = VGroup(self.chart.axes, self.chart.labels, self.chart.yticks,
                      self.chart_title)
        # the normal filled-bar reveal: bars grow UP from the axis (not the chalk
        # line-trace) while the axes/labels/title fade in
        self._grow_up(self.chart.bars, FadeIn(rest), run_time=1.6)

    # ── b : the root decision node appears centre (the top of the tree) ────────
    @subscene
    def root_node(self):
        self.play(FadeOut(self.chart), FadeOut(self.chart_title), run_time=0.6)
        self.chart = self.chart_title = None
        self.node = self._node_dot(ORIGIN)
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
        """Greedy avg misses by word length. Non-chalkboard scene → crisp labels +
        FILLED bars (see hangman CLAUDE.md: chalk font / line-outline graphs are
        chalkboard-only). Same shared `get_bar_chart`, light ink for the navy bg.
        (Part C will fold this into the paired greedy-vs-optimal chart.)"""
        data = GDATA["avg_misses_by_length"]
        lengths = sorted(int(k) for k in data)
        items = [(L, data[str(L)]["avg_misses"]) for L in lengths]
        chart = get_bar_chart(
            items, center=[0, 0, 0], width=12.0, height=4.2, y_max=7,
            bar_color=CHART_COLOR, ink_color=WHITE, bar_ratio=0.75,
            x_axis=True, y_axis=True,
            y_ticks=range(0, 8, 2),
        )   # no title — not called for by the script (and get_bar_chart's title
            # wraps here; revisit when Part C builds the paired chart)
        chart.shift([0, -chart.get_center()[1], 0])
        chart.axes = VGroup(chart.x_axis, chart.y_axis)
        return chart
