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
  e a_dive        — bring A to centre; walk-highlight children (gold); grid A-miss's options
  f f_drill       — breadcrumb the optimal (O), drill its all-miss leaf into the next option grid
  --- next sections (not yet built) ---
  g … recurse to 'Avg misses: 0'; back up the solved values (green); dedup + prune; paired chart

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


def _n_of(node):
    return node.get("n", 1 if "word" in node else 0)


def _greedy_score(option):
    """Greedy's selection metric for an option: how many remaining words CONTAIN its
    letter (= the sum of its HIT-branch word counts). Sorting options by this DESC gives
    the greedy order — greedy's own pick lands first (top-left)."""
    return sum(_n_of(ch) for pat, ch in option["subtree"]["branches"].items()
               if set(pat) != {"_"})


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
PATH_SCALE       = 0.5     # the drilled-past path (A→O→…) is shrunk vs the active subtree


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

    def _miss_row(self, letters):
        """A row of RED missed letters (the running wrong-guess tally)."""
        row = VGroup(*[crisp_text(c, color=LIGHT_RED, weight=BOLD)
                       .scale_to_fit_height(GRID_MISS_H) for c in letters])
        row.arrange(RIGHT, buff=GRID_MISS_H * 0.45)
        return row

    def _mini_tree(self, option, *, parent_miss=0, missed=None):
        """One guess's mini-tree: the parent node (its letter) + a downward fan of
        child nodes, one per situation the guess produces (its partition). Under each
        child sit the partially-filled blanks; the absent ('____') branch is a miss →
        the running missed-letter tally (``missed`` so far + this letter) goes in RED
        below its blanks. ``parent_miss`` colours the PARENT node (0 = white guess node;
        1 = red, i.e. reached via an earlier miss). Returns VGroup(parent, fan)."""
        r = GRID_NODE_R
        dot = Dot(ORIGIN, radius=r, color=_miss_color(parent_miss))
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
            edge = Line(dot.get_center() + d * r, cpos - d * cr,
                        color=_miss_color(miss), stroke_width=2.0)
            # align by the RULE baseline (blanks' bottom), so filled and empty blanks
            # sit at the SAME height whether or not a letter is written above them
            blanks = self._blanks(pat).set_x(cpos[0])
            blanks.shift([0, (cpos[1] - GRID_BLANK_DROP) - blanks.get_bottom()[1], 0])
            # each child is a BRANCH sub-group [0]=edge [1]=dot [2]=blanks [3]=miss letter,
            # so a later beat can recolour / drop a single branch by index
            branch = VGroup(edge, cdot, blanks)
            # the running missed-letter tally (red) under EVERY blank below a miss: the
            # path misses so far (e.g. A), plus this letter if THIS branch also missed
            tally = (missed or []) + ([option["letter"].upper()] if miss else [])
            if tally:
                row = self._miss_row(tally)
                row.next_to(blanks, DOWN, buff=0.09).set_x(blanks.get_x())
                branch.add(row)
            branch.edge, branch.dot, branch.blanks = edge, cdot, blanks
            fan.add(branch)
        mt = VGroup(parent, fan)
        mt.parent, mt.fan = parent, fan
        return mt

    def _tile(self, cells, *, rows=None, cols=None, w=GRID_W, h=GRID_H, center=None):
        """Tile PRE-BUILT cells across a ``w``×``h`` box at ONE uniform scale (every
        node the same size), row-major. Default cols is aspect-aware."""
        center = GRID_CENTER if center is None else center
        maxw = max(c.width for c in cells)
        maxh = max(c.height for c in cells)
        if cols is None:
            cols = max(1, int(round((len(cells) * (w / h) / (maxw / maxh)) ** 0.5)))
        if rows is None:
            rows = (len(cells) + cols - 1) // cols
        cw, ch = w / cols, h / rows
        scale = min(cw * 0.92 / maxw, ch * 0.88 / maxh)
        for idx, mt in enumerate(cells):
            r_i, c_i = divmod(idx, cols)
            mt.scale(scale)
            mt.move_to([center[0] - w / 2 + (c_i + 0.5) * cw,
                        center[1] + h / 2 - (r_i + 0.5) * ch, 0])
        return VGroup(*cells)

    def _grid_of(self, options, **kw):
        return self._tile([self._mini_tree(o) for o in options], **kw)

    # ── path-rooted cells (the shrunk A→…→ miss-path top + one grafted option) ──
    def _n_miss_node(self, depth):
        """The node reached by ``depth`` all-miss guesses down the optimal path
        (depth 1 = A-miss, 2 = A-miss→O-miss, …)."""
        node = DATA["tree"]
        for _ in range(depth):
            node = node["children"]["__"]
        return node

    def _path_diag(self, depth):
        """The SHRUNK drilled-past path A→O→… for ``depth`` guesses, as a diagonal going
        down-LEFT (the miss branch is the left child). Each guess node keeps its HIT
        siblings as bare dots (NO blanks — the non-active nodes are decluttered).
        Returns (group, anchor, last_dot): where the active subtree attaches, and the
        deepest guess node it hangs from."""
        r = GRID_NODE_R
        node = DATA["tree"]
        grp = VGroup()
        A_pos = pos = np.array([0.0, 0.0, 0.0])
        prev_dot = last_dot = None
        for i in range(depth):
            dot = Dot(pos, radius=r, color=_miss_color(0 if i == 0 else 1))
            lab = crisp_text(node["optimal_letter"].upper(), color=BOARD_NAVY, weight=BOLD)
            lab.scale_to_fit_height(NODE_LETTER_H * r).move_to(dot)
            grp.add(dot, lab)
            if prev_dot is not None:
                dn = normalize(pos - prev_dot.get_center())
                grp.add(Line(prev_dot.get_center() + dn * r, pos - dn * r,
                             color=LIGHT_RED, stroke_width=2.0))
            hits = [p for p in node["children"] if set(p) != {"_"}]   # hit siblings, no blanks
            for j, _ in enumerate(hits):
                hpos = pos + np.array([GRID_CHILD_SPR * (j + 1), -GRID_CHILD_DY, 0.0])
                hdot = Dot(hpos, radius=r * GRID_CHILD_RF, color=_miss_color(0))
                dn = normalize(hpos - pos)
                grp.add(Line(pos + dn * r, hpos - dn * r * GRID_CHILD_RF,
                             color=CHALK, stroke_width=2.0), hdot)
            prev_dot = last_dot = dot
            pos = pos + np.array([-GRID_CHILD_SPR, -GRID_CHILD_DY, 0.0])   # miss → down-left
            node = node["children"]["__"]
        anchor = A_pos + (pos - A_pos) * PATH_SCALE
        grp.scale(PATH_SCALE, about_point=A_pos)
        return grp, anchor, last_dot

    def _diag_cell(self, depth, option):
        """A grid cell: the SHRUNK diagonal path A→…→ (down-left, root off-centre) plus
        the active option subtree at FULL size grafted on the deepest miss branch. The
        red missed-letter tally at the subtree's bottom accumulates the whole path."""
        path_letters, n = [], DATA["tree"]
        for _ in range(depth):
            path_letters.append(n["optimal_letter"].upper())
            n = n["children"]["__"]
        sub = self._mini_tree(option, parent_miss=1, missed=path_letters)
        path, anchor, last_dot = self._path_diag(depth)
        sub.shift(anchor - sub[0][0].get_center())        # option root → the miss anchor
        dn = normalize(anchor - last_dot.get_center())
        edge = Line(last_dot.get_center() + dn * (GRID_NODE_R * PATH_SCALE),
                    sub[0][0].get_center() - dn * GRID_NODE_R,
                    color=LIGHT_RED, stroke_width=2.0)
        return VGroup(path, edge, sub)

    def _setup_grid(self):
        # only the letters that actually SPLIT (appear in some 2-letter word); the 6
        # always-miss letters (c/j/k/q/v/z) are dropped → 20 openers, a clean 4×5,
        # in GREEDY order (most words containing the letter first).
        opts = sorted((o for o in DATA["tree"]["options"] if o["splits"]),
                      key=lambda o: (-_greedy_score(o), o["letter"]))
        self.grid = self._grid_of(opts, rows=GRID_ROWS, cols=GRID_COLS)

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

    # ── e : bring the A case to centre, walk-highlight its children (node + incoming
    #        edge → gold), then settle on the leftmost (the A-miss situation) ────────
    @subscene
    def a_dive(self):
        self._e_isolate_a(1.2)
        self._e_walk_children(2.4)      # total for the walk (split across the children)
        self._e_focus_leftmost(0.6)
        self._e_option_grid(2.6)        # grid of every next-letter option from A-miss

    def _e_isolate_a(self, run_time):
        a = self.grid[0]                                 # 'A' — sorted first, top-left cell
        self.play(FadeOut(VGroup(*self.grid[1:])),
                  a.animate.scale_to_fit_height(4.2).move_to(ORIGIN),
                  run_time=run_time)
        self.a_tree = a
        self.grid = None

    def _e_walk_children(self, run_time):
        # highlight each child (its dot + incoming edge → gold), one at a time, restoring
        # to its own colour before moving on. fan = a[1]; branch = [edge, dot, ...].
        fan = self.a_tree[1]
        per = run_time / len(fan)
        for br in fan:
            edge, dot = br[0], br[1]
            oe, od = edge.get_color(), dot.get_color()
            self.play(edge.animate.set_color(ACCENT_GOLD),
                      dot.animate.set_color(ACCENT_GOLD), run_time=per * 0.35)
            self.wait(per * 0.30)
            self.play(edge.animate.set_color(oe), dot.animate.set_color(od),
                      run_time=per * 0.35)

    def _e_focus_leftmost(self, run_time):
        # go back to the leftmost child (the A-miss node) and LEAVE it gold
        br = self.a_tree[1][0]
        self.play(br[0].animate.set_color(ACCENT_GOLD),
                  br[1].animate.set_color(ACCENT_GOLD), run_time=run_time)

    def _e_option_grid(self, run_time):
        # "make a grid of every option for letters to continue from that node": from the
        # A-miss state, try every next letter → a grid of A-ROOTED trees (each = the A
        # tree, top shrunk, with that option grafted on the miss branch), in GREEDY order
        # (most words containing the letter first → greedy's pick top-left), same column
        # count as beat d.
        opts = sorted((o for o in self._n_miss_node(1)["options"] if o["splits"]),
                      key=lambda o: (-_greedy_score(o), o["letter"]))
        cells = [self._diag_cell(1, o) for o in opts]
        grid = self._tile(cells, cols=GRID_COLS)
        # fade the old A tree out FIRST, then grow the adjusted trees into their slots
        self.play(FadeOut(self.a_tree), run_time=run_time * 0.35)
        self.a_tree = None
        self.play(*[GrowFromCenter(c) for c in grid], run_time=run_time * 0.65)
        self.grid = grid

    # ── f : keep drilling — expand the top-left (greedy pick O) tree's all-miss leaf
    #        into the next grid, each cell now rooted along the path A→O (depth 2),
    #        greedy-sorted, drilling the top-left again. ───────────────────────────────
    @subscene
    def f_drill(self):
        opts = sorted((o for o in self._n_miss_node(2)["options"] if o["splits"]),
                      key=lambda o: (-_greedy_score(o), o["letter"]))
        cells = [self._diag_cell(2, o) for o in opts]
        grid = self._tile(cells, cols=GRID_COLS)
        # fade e's grid out FIRST, then grow the deeper trees into their slots
        self.play(FadeOut(self.grid), run_time=0.7)
        self.play(*[GrowFromCenter(c) for c in grid], run_time=1.4)
        self.grid = grid

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
