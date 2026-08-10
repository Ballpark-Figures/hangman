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

TREE CONVENTIONS (this scene):
  - MISS edge/node = RED, HIT edge/node (and a guess node) = WHITE. Binary — NOT the
    intro's graduated per-miss-count palette (`_miss_color`).
  - A node's blanks (partially-filled word + a red missed letter under the miss child)
    are a LEAF annotation: only the current frontier nodes carry them. EXPANDING a node
    REMOVES that node's blanks (it's no longer a leaf) and ADDS blanks under its new
    children; the node's un-expanded SIBLINGS keep theirs.

Script row 05, split on '—' (voiceover ↔ animation zip 1:1). BEAT MAP:
  a greedy_chart  — recap: greedy avg misses by word length (the scene-04 chart)
  b root_node     — one decision node appears centre (the top of the tree)
  c cycle_letters — cycle every letter A–Z through the node (which opener is best?)
  d grid_spread   — 20 openers into a 4×5 grid; each sprouts its next level (blanks + miss)
  --- next sections (not yet built) ---
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


def _miss_color(miss):
    """Binary tree colour for scene 05: a MISS edge/node is RED, a HIT edge/node (and
    the guess node itself) is white. Simpler than the intro's graduated per-miss-count
    palette — for this scene, miss = red, hit = white. ``miss`` is truthy for the
    absent (miss) branch."""
    return LIGHT_RED if miss else CHALK


# ── beat d : the 4×5 grid of (splitting) openers, each sprouting its next level.
#    The 6 letters absent from every 2-letter word (c/j/k/q/v/z — a single miss
#    child) are dropped, leaving 20. ─────────────────────────────────────────────
GRID_ROWS, GRID_COLS = 4, 5
GRID_NODE_R      = 0.16   # parent-node radius (natural; the whole grid is scaled to fit)
GRID_CHILD_RF    = 0.68   # child radius as a fraction of the parent radius
GRID_CHILD_DY    = 0.55   # parent → child vertical drop (natural units)
GRID_CHILD_SPR   = 0.72   # child horizontal half-spread (blanks sit under each child)
GRID_BLANK_H     = 0.13   # blank-row height under a child (rule + revealed letter)
GRID_BLANK_DROP  = 0.36   # child centre → blank RULE baseline (fixed → rules line up AND
                          # the written letter above the rule clears the child dot)
GRID_MISS_H      = GRID_BLANK_H    # missed letter (red) — SAME size as the blank letters
GRID_W, GRID_H   = 15.6, 8.0       # the cells tile this box (full width, small top/bottom margin)
GRID_CENTER      = [0, 0, 0]


class Scene05(HangmanScene):
    """Optimal strategy as a search on the length-2 tree.

    BEAT MAP (built so far):
      greedy_chart  — a: recap greedy avg-misses-by-length chart
      root_node     — b: the root decision node appears at centre
      cycle_letters — c: cycle every letter A–Z through the node
      grid_spread   — d: 28 → 4×7 grid; each opener sprouts its next level
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

    # ── grid of openers (beat d) ──────────────────────────────────────────────
    def _blanks(self, pattern, h=GRID_BLANK_H):
        """A row of blanks (white rules) for a length-N pattern, each revealed HIT
        letter written above its slot. Mirrors 92wintree_test._blanks."""
        slot, gap = h * 0.9, h * 0.5
        row = VGroup()
        for ch in pattern:
            rule = Line([-slot / 2, 0, 0], [slot / 2, 0, 0], color=CHALK,
                        stroke_width=2.0)
            cell = VGroup(rule)
            if ch != "_":
                t = crisp_text(ch.upper(), color=CHALK, weight=BOLD)
                t.scale_to_fit_height(h).next_to(rule, UP, buff=h * 0.22)
                cell.add(t)
            row.add(cell)
        row.arrange(RIGHT, buff=gap, aligned_edge=DOWN)
        return row

    def _mini_tree(self, option):
        """One opener's mini-tree: the parent node (its letter) + a downward fan of
        child nodes, one per situation the guess produces (its partition). Under each
        child sit the partially-filled blanks; the absent ('____') branch is a miss
        → the missed opener letter goes in RED below its blanks. Returns
        VGroup(parent, fan) with `.parent` / `.fan` handles."""
        r = GRID_NODE_R
        dot = Dot(ORIGIN, radius=r, color=_miss_color(0))
        lab = crisp_text(option["letter"].upper(), color=BOARD_NAVY, weight=BOLD)
        lab.scale_to_fit_height(NODE_LETTER_H * r).move_to(dot)
        parent = VGroup(dot, lab)
        fan = VGroup()
        pats = list(option["subtree"]["branches"].keys())
        xs = np.linspace(-GRID_CHILD_SPR, GRID_CHILD_SPR, len(pats)) if len(pats) > 1 \
            else [0.0]
        cr = r * GRID_CHILD_RF
        for pat, x in zip(pats, xs):
            miss = 1 if set(pat) == {"_"} else 0        # all-blank branch = a miss
            cpos = np.array([x, -GRID_CHILD_DY, 0.0])
            cdot = Dot(cpos, radius=cr, color=_miss_color(miss))
            d = normalize(cpos - dot.get_center())
            fan.add(Line(dot.get_center() + d * r, cpos - d * cr,
                         color=_miss_color(miss), stroke_width=2.0), cdot)
            # align by the RULE baseline (blanks' bottom), so filled and empty blanks
            # sit at the SAME height whether or not a letter is written above them
            blanks = self._blanks(pat).set_x(cpos[0])
            blanks.shift([0, (cpos[1] - GRID_BLANK_DROP) - blanks.get_bottom()[1], 0])
            fan.add(blanks)
            if miss:                                     # the missed opener letter, in red
                ml = crisp_text(option["letter"].upper(), color=LIGHT_RED, weight=BOLD)
                ml.scale_to_fit_height(GRID_MISS_H).next_to(blanks, DOWN, buff=0.09)
                fan.add(ml)
        mt = VGroup(parent, fan)
        mt.parent, mt.fan = parent, fan
        return mt

    def _setup_grid(self):
        # only the letters that actually SPLIT (appear in some 2-letter word); the 6
        # always-miss letters (c/j/k/q/v/z) are dropped → 20 openers, a clean 4×5.
        opts = sorted((o for o in DATA["tree"]["options"] if o["splits"]),
                      key=lambda o: o["letter"])
        cells = [self._mini_tree(o) for o in opts]
        # tile the cells across the full frame: one uniform scale (so every node is the
        # same size), then drop each mini-tree at its cell centre (row-major).
        cw, ch = GRID_W / GRID_COLS, GRID_H / GRID_ROWS
        scale = min(cw * 0.92 / max(c.width for c in cells),
                    ch * 0.88 / max(c.height for c in cells))
        for idx, mt in enumerate(cells):
            r_i, c_i = divmod(idx, GRID_COLS)
            mt.scale(scale)
            mt.move_to([GRID_CENTER[0] - GRID_W / 2 + (c_i + 0.5) * cw,
                        GRID_CENTER[1] + GRID_H / 2 - (r_i + 0.5) * ch, 0])
        self.grid = VGroup(*cells)

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

    # ── d : spread 28 copies into a 4×7 grid, then each opener sprouts its next
    #        level (try every first letter, see every situation) ─────────────────
    @subscene
    def grid_spread(self):
        self._setup_grid()
        parents = [mt.parent for mt in self.grid]        # 'A'..'Z' at their grid cells
        # phase 1 (like yahtzee's one_die): every opener starts stacked at the centre
        # at the big root-node size, then ALL fan out SIMULTANEOUSLY, shrinking to the
        # grid — the lone centre node becomes the grid, nothing lingers in the middle.
        for p in parents:
            p.save_state()                               # remember its grid pose
            p.scale((2 * NODE_R_ROOT) / p[0].width).move_to(ORIGIN)
        self.remove(self.node, self.node_letter)         # swap the identical big 'A' in
        self.node = self.node_letter = None
        self.add(*parents[1:], parents[0])               # 'A' on top of the stack
        self.play(*[Restore(p) for p in parents], run_time=1.5)
        # phase 2: every opener sprouts its next level at once (its partition)
        self.play(*[GrowFromPoint(mt.fan, mt.parent.get_center()) for mt in self.grid],
                  run_time=1.4)

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
