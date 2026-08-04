"""TEST — the whole win-probability strategy tree for length 3, chalked onto the
scene-94 chalkboard (intro visual), with a camera that dives down one path.

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
  • horizontal x is the standard non-crossing assignment: leaves spread evenly
    left→right and every parent is centred over its children, so edges never cross.
  • children order alternates the heavy side per row (even rows lean the most-words
    branch right, odd rows left) so the dominant spine zig-zags and the canopy hangs
    balanced. (The root centres over its children, so it sits at a small x offset.)

Camera (this is a MovingCameraScene):
  a grow  — every guess-row draws SIMULTANEOUSLY at a constant (linear) rate, each
            row in the SAME time (ROW_TIME). The camera starts zoomed on the root and
            dives down the featured word's path, zooming in one step per row, arriving
            at the leaf exactly as the last row (and that leaf) draws.
  b zoom_out — pull back out to the whole tree.

The snapshot cache doesn't pickle camera state, so `grow` stashes the per-row camera
poses on `self` (they DO get pickled) and `zoom_out` re-establishes the leaf pose
before pulling back — so rendering `92b` alone still starts from the zoomed-in leaf.

Render:  render 92a --fast   /   render 92b --fast
"""
from pathlib import Path
import sys
import json

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from manim import MovingCameraScene
from assets.chalkboard import chalkboard, CHALK

# ── sourced data: winprob tree, len-3 uniform, budget n=5 ─────────────────────
TREE_PATH = (Path(__file__).resolve().parents[2]
             / "math/data/shared/winprob/len03_uniform_n05.json")
WORD = "six"          # featured deepest-row (depth-8) word — the camera's target
                      # ("six" is a LOST word: its path ends on the fatal 6th miss)

# ── board (matches scene 94) ──────────────────────────────────────────────────
BOARD_W, BOARD_H = 15.2, 8.4
NAVY_HX = BOARD_W / 2 - 0.34    # writable navy half-extents (frame inset 0.34) —
NAVY_HY = BOARD_H / 2 - 0.34    # the camera frame is clamped inside these

# ── layered layout (frame 16×9 → x-radius 8.0, y-radius 4.5) ──────────────────
TOP_Y   = 3.5         # row 0 (the opening guess) sits here
ROWGAP0 = 2.6         # gap row-0→row-1; each next gap ×SHRINK (rows bunch downward)
SHRINK  = 0.65        # row gap ×0.65 each level down
HALF_W  = 7.0         # leaves spread across ±HALF_W

EDGE_SW_ROOT  = 4.0   # trunk stroke; taper toward the twigs
EDGE_SW_TAPER = 0.72
EDGE_SW_MIN   = 0.9

DOT_R_ROOT  = 0.09    # node-dot radius at the root; tapers with depth
DOT_R_TAPER = 0.8
DOT_R_MIN   = 0.012
DOT_APPEAR  = 0.82    # a node's dot stays hidden until this fraction of its row's draw


def _appear_at_end(t):
    """Rate-func: hold at 0 until DOT_APPEAR (the edge has ~reached the node), then
    ramp to 1 — so a node's dot only appears once its incoming edge arrives."""
    return 0.0 if t < DOT_APPEAR else (t - DOT_APPEAR) / (1 - DOT_APPEAR)

# ── camera dive ───────────────────────────────────────────────────────────────
ROW_TIME    = 1.3     # every guess-row grows in the SAME time, at a linear rate
CAM_W_START = 6.0     # camera frame width at the root (zoomed-in start)
CAM_W_END   = 1.0     # camera frame width at the leaf (tight close-up)
CAM_FULL_W  = 16.0    # full-frame width for the zoom-out beat
ZOOM_OUT_RT = 3.2


class WinTree(MovingCameraScene, HangmanScene):
    """Grow the len-3 winprob(n=5) tree on the chalkboard while the camera dives
    down WORD's path; then pull back out.

    MovingCameraScene supplies self.camera.frame (BpkScene is a plain Scene). The
    layered layout + camera keyframes are built once in _setup_tree (pure geometry
    from the solver JSON).
    """

    # the chalkboard is the backdrop; start the camera zoomed on the root (x=0)
    def setup_scene(self):
        self.tree = json.loads(TREE_PATH.read_text())["tree"]
        self.cb = chalkboard(BOARD_W, BOARD_H)
        self.cb.set_z_index(-10)
        self.add(self.cb)
        self._setup_tree()                 # layout + edges/dots/camera keyframes
        # the initial node at the ACTUAL root position, on screen from frame 0 so the
        # leading 1s hold sits on it; the camera starts centred on it too
        self.root_dot = Dot(self._node_pos(self.tree), radius=DOT_R_ROOT, color=CHALK)
        self.add(self.root_dot)
        self.camera.frame.move_to(self._cam_center[0]).set(width=self._cam_width[0])

    # ── keep a frame of the given width fully inside the navy board ────────────
    def _clamp_center(self, c, w):
        hw, hh = w / 2, w * 9 / 16 / 2
        return np.array([min(max(c[0], -NAVY_HX + hw), NAVY_HX - hw),
                         min(max(c[1], -NAVY_HY + hh), NAVY_HY - hh), 0.0])

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

    # ── scene position of a node from its stored raw-x and depth ──────────────
    def _node_pos(self, node):
        idn = id(node)
        return np.array([(self._x[idn] - (self._n - 1) / 2) * self._scale,
                         self._row_y(self._depth[idn]), 0.0])

    # ── the root→leaf node chain for `word` (follows the revealed patterns) ────
    def _path_to(self, word):
        node, nodes = self.tree, [self.tree]
        while "branches" in node:
            g = node["guess"]
            key = "".join(g if word[p] == g else "_" for p in range(len(word)))
            node = node["branches"][key]
            nodes.append(node)
        return nodes                                 # root … leaf(word)

    # ── build the chalk edges (grouped by depth) + the camera keyframes ───────
    def _setup_tree(self):
        self._x, self._depth, self._edges = {}, {}, []
        self._rows, self._next_leaf = [TOP_Y], 0
        self._assign(self.tree, 0)

        self._n = self._next_leaf
        self._scale = 2 * HALF_W / max(1, self._n - 1)   # leaf indices → board width

        self._by_depth = {}
        for pid, cid in self._edges:
            d = self._depth[pid]
            a = np.array([(self._x[pid] - (self._n - 1) / 2) * self._scale,
                          self._row_y(d), 0.0])
            b = np.array([(self._x[cid] - (self._n - 1) / 2) * self._scale,
                          self._row_y(d + 1), 0.0])
            sw = max(EDGE_SW_MIN, EDGE_SW_ROOT * EDGE_SW_TAPER ** d)
            self._by_depth.setdefault(d, VGroup()).add(
                Line(a, b, color=CHALK, stroke_width=sw))

        # a chalk dot at every node (radius tapers with depth); the root dot is
        # already on screen from setup_scene, so build depth ≥ 1 here.
        self._dots_by_depth = {}
        for idn, d in self._depth.items():
            if d == 0:
                continue
            pos = np.array([(self._x[idn] - (self._n - 1) / 2) * self._scale,
                            self._row_y(d), 0.0])
            r = max(DOT_R_MIN, DOT_R_ROOT * DOT_R_TAPER ** d)
            self._dots_by_depth.setdefault(d, VGroup()).add(
                Dot(pos, radius=r, color=CHALK))

        # camera pose per path node (depth 0…8): centre on the node (clamped inside
        # the board), width shrinking GEOMETRICALLY (constant ratio per row) from
        # CAM_W_START to CAM_W_END — so it keeps pace with the ×SHRINK row bunching
        # and each layer zooms in by the same factor, all the way to the leaf.
        path = self._path_to(WORD)
        dmax = len(path) - 1
        self._cam_center, self._cam_width = [], []
        for k, node in enumerate(path):
            w = CAM_W_START * (CAM_W_END / CAM_W_START) ** (k / dmax)
            self._cam_center.append(self._clamp_center(self._node_pos(node), w))
            self._cam_width.append(w)

    # a : draw the tree row by row (each row at once, linear, equal time) while the
    #     camera dives down WORD's path, zooming in a step per row to the leaf
    @subscene
    def grow(self):
        last = len(self._cam_center) - 1
        for d in sorted(self._by_depth):
            k = min(d + 1, last)                     # camera holds at the leaf once reached
            anims = [
                Create(self._by_depth[d], lag_ratio=0.0, rate_func=linear),
                self.camera.frame.animate(rate_func=linear)
                    .move_to(self._cam_center[k]).set(width=self._cam_width[k]),
            ]
            if (d + 1) in self._dots_by_depth:       # dots pop only as the edges reach them
                anims.append(FadeIn(self._dots_by_depth[d + 1],
                                    rate_func=_appear_at_end))
            self.play(*anims, run_time=ROW_TIME)

    # b : pull the camera back out to the whole tree
    @subscene
    def zoom_out(self):
        # snapshot cache doesn't save camera state → re-establish the leaf pose first
        self.camera.frame.move_to(self._cam_center[-1]).set(width=self._cam_width[-1])
        self.play(self.camera.frame.animate.move_to(ORIGIN).set(width=CAM_FULL_W),
                  run_time=ZOOM_OUT_RT, rate_func=smooth)
