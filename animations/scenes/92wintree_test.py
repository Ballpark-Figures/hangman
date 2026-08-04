"""TEST — the whole win-probability strategy tree for length 3, chalked onto the
scene-94 chalkboard (intro visual). JUST the tree structure for now (no letters,
counts, or boards).

Sourced tree: winprob, uniform weighting, miss budget n=5 — every word is either
WON within 5 misses or LOST on the 6th. So each root-to-tip path is drawn down to
(and including) the edge into that fatal 6th miss (a `lost` leaf), but NO further.
306 decision nodes, 261 win leaves, 56 loss leaves, depth 8 — a big sprawling tree
whose SHAPE is the point (individual nodes aren't meant to be read).

Layout — a LAYERED tree (one ROW per guess-count), rooted at the TOP, growing DOWN:
  • row 0 = the opening guess; row d = the state after d guesses. Each node sits on
    its depth's row (y only depends on depth).
  • ROW SPACING shrinks ×SHRINK (0.65) each level, so the rows bunch closer together
    as you go down — "shorter edges lower down."
  • horizontal x is the standard non-crossing assignment: leaves are spread evenly
    left→right and every parent is centred over its children, so edges never cross.
  • children are ordered left→right by word-count, but the heavy side ALTERNATES by
    row: even rows lean the most-words branch RIGHT, odd rows lean it LEFT — so the
    dominant spine zig-zags down the tree instead of hugging one side.

KNOBS: TOP_Y / ROWGAP0 / SHRINK set the vertical rows; HALF_W the horizontal spread.

Render:  render 92a --fast
"""
from pathlib import Path
import sys
import json

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.chalkboard import chalkboard, CHALK

# ── sourced data: winprob tree, len-3 uniform, budget n=5 ─────────────────────
TREE_PATH = (Path(__file__).resolve().parents[2]
             / "math/data/shared/winprob/len03_uniform_n05.json")

# ── board (matches scene 94) ──────────────────────────────────────────────────
BOARD_W, BOARD_H = 15.2, 8.4

# ── layered layout (frame 16×9 → x-radius 8.0, y-radius 4.5) ──────────────────
TOP_Y   = 3.9         # row 0 (the opening guess) sits here
ROWGAP0 = 2.6         # gap row-0→row-1; each next gap ×SHRINK (rows bunch downward)
SHRINK  = 0.65        # row gap ×0.65 each level down
HALF_W  = 7.0         # leaves spread across ±HALF_W

EDGE_SW_ROOT  = 4.0   # trunk stroke; taper toward the twigs
EDGE_SW_TAPER = 0.72
EDGE_SW_MIN   = 0.9


class WinTree(HangmanScene):
    """Grow the len-3 winprob(n=5) tree on the chalkboard, one guess-row at a time.

    Layered layout is built once in _setup_tree (pure geometry from the solver
    JSON); subscene a chalks the edges on, row by row from the top.
    """

    # the chalkboard is the backdrop — on screen from frame 0
    def setup_scene(self):
        self.tree = json.loads(TREE_PATH.read_text())["tree"]
        self.cb = chalkboard(BOARD_W, BOARD_H)
        self.cb.set_z_index(-10)
        self.add(self.cb)

    # ── word-count a child represents (sort key + horizontal ordering) ────────
    def _words(self, node):
        if "branches" in node:      # decision node: words still consistent
            return node["n"]
        if "word" in node:          # a solved (won) word
            return 1
        return len(node["lost"])    # a lost leaf: the words given up on

    # ── row y for a given depth (gaps shrink ×SHRINK each level) ──────────────
    def _row_y(self, depth):
        while len(self._rows) <= depth:
            d = len(self._rows)
            self._rows.append(self._rows[-1] - ROWGAP0 * SHRINK ** (d - 1))
        return self._rows[depth]

    # ── assign a raw leaf-index x to every node (parent centred over children) ─
    def _assign(self, node, depth):
        self._depth[id(node)] = depth
        if "branches" not in node:
            x = self._next_leaf
            self._next_leaf += 1
        else:
            # order children by word-count, alternating the heavy side per row:
            # even depth → most words on the RIGHT, odd depth → on the LEFT
            children = sorted(node["branches"].values(), key=self._words,
                              reverse=(depth % 2 == 1))
            xs = [self._assign(c, depth + 1) for c in children]
            x = (xs[0] + xs[-1]) / 2                 # centre over child extent
            for c in children:
                self._edges.append((id(node), id(c)))
        self._x[id(node)] = x
        return x

    # ── build the chalk edges (grouped by depth for a row-by-row grow) ────────
    def _setup_tree(self):
        self._x, self._depth, self._edges = {}, {}, []
        self._rows, self._next_leaf = [TOP_Y], 0
        self._assign(self.tree, 0)

        n = self._next_leaf
        scale = 2 * HALF_W / max(1, n - 1)           # leaf indices → board width
        def px(idn, depth):
            return np.array([(self._x[idn] - (n - 1) / 2) * scale,
                             self._row_y(depth), 0.0])

        self._by_depth = {}
        for pid, cid in self._edges:
            d = self._depth[pid]
            sw = max(EDGE_SW_MIN, EDGE_SW_ROOT * EDGE_SW_TAPER ** d)
            edge = Line(px(pid, d), px(cid, d + 1), color=CHALK, stroke_width=sw)
            self._by_depth.setdefault(d, VGroup()).add(edge)
        self.edges = VGroup(*[e for d in sorted(self._by_depth)
                              for e in self._by_depth[d]])

    # a : chalk the tree on one guess-row at a time from the top down — every edge
    #     in a row draws simultaneously, and each row finishes before the next
    @subscene
    def grow(self):
        self._setup_tree()
        row_rt = [0.7, 0.8, 0.9, 1.0, 1.0, 0.9, 0.8, 0.7]   # one per edge-row
        for d in sorted(self._by_depth):
            self.play(Create(self._by_depth[d]),
                      run_time=row_rt[d] if d < len(row_rt) else row_rt[-1])
