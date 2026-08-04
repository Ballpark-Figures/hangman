"""TEST — the whole win-probability strategy tree for length 3, on a plain navy
background (intro visual), with a camera that dives down one path.

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

Colour — each edge and its BOTTOM node are coloured by the misses accumulated there:
0 = white, then 1→light-purple, 2→blue, 3→green, 4→yellow, 5→orange, 6→light-red
(bpkfigures LIGHT_PALETTE, reverse-indexed). The all-blank branch is the miss.

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
from assets.chalkboard import CHALK, BOARD_NAVY
from assets.hangman_board import merge_pattern, hangman_drawing

# ── sourced data: winprob tree, len-3 uniform, budget n=5 ─────────────────────
TREE_PATH = (Path(__file__).resolve().parents[2]
             / "math/data/shared/winprob/len03_uniform_n05.json")
WORD = "yes"          # featured deepest-row (depth-8) word — the camera's target
                      # ("yes" is WON at depth 8: the dive spells it out to a won leaf)

# ── layered layout (frame 16×9 → x-radius 8.0, y-radius 4.5) ──────────────────
TOP_Y   = 3.5         # row 0 (the opening guess) sits here
ROWGAP0 = 2.6         # gap row-0→row-1; each next gap ×SHRINK (rows bunch downward)
SHRINK  = 0.65        # THE per-level scale factor: rows bunch, the camera ZOOMS, and
                      # the nodes/gallows/blanks all shrink by this each level down, so
                      # the dive is self-similar (everything holds its on-screen size)
HALF_W  = 7.0         # leaves spread across ±HALF_W

EDGE_SW_ROOT  = 4.0   # trunk stroke; tapers by SHRINK too (constant on-screen)
EDGE_SW_TAPER = SHRINK
EDGE_SW_MIN   = 0.05  # low floor so the stroke keeps shrinking with the deep zoom

DOT_R_ROOT  = 0.09    # node-dot radius at the root; tapers by SHRINK (constant on-screen)
DOT_R_TAPER = SHRINK
DOT_R_MIN   = 0.001   # low floor so deep nodes stay at the SHRINK scale (don't clamp big)
DOT_APPEAR  = 0.9    # a node's dot stays hidden until this fraction of its row's draw
NODE_LETTER_H = 1.3   # guess-letter height as a multiple of the node radius

# ── board-state annotations (blanks + gallows) — sizes/offsets are fractions of the
#    camera width at the relevant depth, so they stay a constant ON-SCREEN size (the
#    zoom already keeps the local scale constant, like the nodes). ─────────────────
BLK_H   = 0.05        # blank rule/letter height  (fraction of the camera width)
GAL_H   = 0.10        # gallows height            (fraction of the camera width)
ANN_CLR = 0.06        # clearance between the near (edge-facing) blank and the edge line
ANN_UP  = 0.06        # how far ABOVE the root node the unit sits (must fit above it)
EDGE_FRAC = 0.25      # edge labels sit this fraction UP the edge (lower = further DOWN);
                      # 1-EDGE_FRAC is also when they appear (as the edge tip passes them)
LEAF_GAP = 0.04       # stack gap (gallows→word) and node→unit gap
ANN_SW_FRAC = 0.32    # blanks/gallows line thickness (fraction of the sizing scale)
ANN_WINDOW = 0.12     # an edge label fades in over this fraction of the row, once the
                      # growing edge tip passes its spot


def _appear_at_end(t):
    """Rate-func: hold at 0 until DOT_APPEAR (the edge has ~reached the node), then
    ramp to 1 — so a node's dot only appears once its incoming edge arrives."""
    return 0.0 if t < DOT_APPEAR else (t - DOT_APPEAR) / (1 - DOT_APPEAR)


def _appear_from(trigger, window=1.0):
    """Rate-func factory: hold at 0 until `trigger`, then ramp to 1 over `window`."""
    return lambda t: 0.0 if t <= trigger else min(1.0, (t - trigger) / window)

# ── camera dive ───────────────────────────────────────────────────────────────
ROW_TIME    = 2.0     # base time for the first guess-row
ROW_SLOW    = 1.15    # each row down takes this factor LONGER (slows as we descend)
ROOT_PAUSE  = 1.0     # hold after the opening letter appears, before the dive starts
CAM_W_START = 3.0     # camera frame width at the root; each level zooms by SHRINK
CAM_FULL_W  = 16.0    # full-frame width for the zoom-out beat
ZOOM_OUT_RT = 5.0


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
        self.camera.background_color = BOARD_NAVY
        self._setup_tree()                 # layout + edges/dots/camera keyframes
        # On screen from frame 0 (the leading 1s hold sits on this): the root DOT (its
        # guess letter is faded in as grow's first beat), the 3 empty blanks up-and-
        # left, and the empty gallows up-and-right.
        rpos = self._node_pos(self.tree)
        w0 = self._cam_width[0]
        self.root_dot = Dot(rpos, radius=DOT_R_ROOT, color=self._miss_color(0),
                            z_index=2)
        self.root_letter = crisp_text(self._guess[id(self.tree)].upper(),
                                      color=BOARD_NAVY, weight=BOLD)
        self.root_letter.scale_to_fit_height(NODE_LETTER_H * DOT_R_ROOT)
        self.root_letter.move_to(rpos).set_z_index(3)          # added later (fade-in)
        # the stacked gallows+word unit, placed ABOVE the root node
        self.root_ann = self._annotation("_" * len(WORD), 0, w0)
        self.root_ann.next_to(rpos, UP, buff=ANN_UP * w0)
        self.add(self.root_dot, self.root_ann)
        self.camera.frame.move_to(self._cam_center[0]).set(width=self._cam_width[0])

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

    # ── miss-count colour: 0 stays white, then 1→purple … 6→red (reverse rainbow) ─
    def _miss_color(self, misses):
        if misses <= 0:
            return CHALK
        return LIGHT_PALETTE[len(LIGHT_PALETTE) - misses]   # 1→last(purple), 6→first(red)

    # ── a node marker: dot (coloured by misses) with the guess letter inside for a
    #    decision node (leaves get a bare dot) — VGroup(dot[, letter]) ───────────
    def _node_marker(self, idn, pos, r):
        dot = Dot(pos, radius=r, color=self._miss_color(self._misses[idn]), z_index=2)
        g = self._guess[idn]
        if g is None:                                   # a leaf: no guess to show
            return VGroup(dot)
        lab = crisp_text(g.upper(), color=BOARD_NAVY, weight=BOLD)
        lab.scale_to_fit_height(NODE_LETTER_H * r).move_to(pos).set_z_index(3)
        return VGroup(dot, lab)

    # ── board-state builders (CHALK; cap-height h, line thickness sw). No missed
    #    letters. Callers pass sw ∝ the camera width so the on-screen line thickness
    #    stays constant as the diagrams shrink and the camera zooms in. ────────────
    def _blanks(self, pattern, h, sw):
        """A row of underscore rules with any revealed HIT letters above them."""
        slot, gap = h * 0.85, h * 0.55
        row = VGroup()
        for ch in pattern:
            rule = Line(LEFT * slot / 2, RIGHT * slot / 2, color=CHALK,
                        stroke_width=sw)
            cell = VGroup(rule)
            if ch != "_":
                t = crisp_text(ch.upper(), color=CHALK, weight=BOLD)
                t.scale_to_fit_height(h).next_to(rule, UP, buff=h * 0.22)
                cell.add(t)
            row.add(cell)
        row.arrange(RIGHT, buff=gap, aligned_edge=DOWN)
        return row

    def _gallows(self, misses, h, sw):
        """The gallows with `misses` body parts, scaled to height h."""
        g = hangman_drawing(misses, color=CHALK).scale_to_fit_height(h)
        g.set_stroke(width=sw)
        return g

    def _annotation(self, pattern, misses, s):
        """A stacked board-state label — the gallows with the WORD (blanks) BELOW it,
        sized by scale `s`. The underscores sit a FIXED distance below the gallows
        (the letter space above them is reserved), so the blanks are the same distance
        from the gallows whether or not letters are present."""
        gal = self._gallows(misses, GAL_H * s, ANN_SW_FRAC * s)
        blk = self._blanks(pattern, BLK_H * s, ANN_SW_FRAC * s)
        reserve = (LEAF_GAP + 1.22 * BLK_H) * s          # gallows-bottom → underscores
        blk.set_x(gal.get_center()[0])
        blk.shift([0, (gal.get_bottom()[1] - reserve) - blk.get_bottom()[1], 0])
        return VGroup(gal, blk)

    # ── edge geometry helper (for keeping the edge labels clear of the line) ──
    def _edge_x_at(self, a, b, y):
        """x of the line a→b at height y (a.x if the edge is horizontal)."""
        if abs(a[1] - b[1]) < 1e-6:
            return a[0]
        return a[0] + (b[0] - a[0]) * (a[1] - y) / (a[1] - b[1])

    # ── assign a raw leaf-index x to every node (parent centred over children);
    #    also track the misses accumulated at each node (the all-blank branch is
    #    the miss) so edges/dots can be coloured by their bottom node ────────────
    def _assign(self, node, depth, misses, pattern, parent):
        self._depth[id(node)] = depth
        self._misses[id(node)] = misses
        self._guess[id(node)] = node.get("guess")   # None for a leaf
        self._pattern[id(node)] = pattern           # revealed (hit) letters so far
        self._parent[id(node)] = parent             # parent id (None for the root)
        if "branches" not in node:
            x = self._next_leaf
            self._next_leaf += 1
        else:
            allblank = "_" * len(next(iter(node["branches"])))   # the miss branch key
            # order children by word-count, alternating the heavy side per row:
            # even depth → most words on the RIGHT, odd depth → on the LEFT
            items = sorted(node["branches"].items(),
                           key=lambda kv: self._words(kv[1]), reverse=(depth % 2 == 1))
            xs = []
            for key, child in items:
                m = misses + (1 if key == allblank else 0)
                pat = merge_pattern(pattern, key)
                xs.append(self._assign(child, depth + 1, m, pat, id(node)))
                self._edges.append((id(node), id(child)))
            x = (xs[0] + xs[-1]) / 2                 # centre over child extent
        self._x[id(node)] = x
        return x

    # ── scene position of a node (by object or by id) ─────────────────────────
    def _pos_of(self, idn):
        return np.array([(self._x[idn] - (self._n - 1) / 2) * self._scale,
                         self._row_y(self._depth[idn]), 0.0])

    def _node_pos(self, node):
        return self._pos_of(id(node))

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
        self._x, self._depth, self._edges, self._misses = {}, {}, [], {}
        self._guess, self._pattern, self._parent = {}, {}, {}
        self._rows, self._next_leaf = [TOP_Y], 0
        self._assign(self.tree, 0, 0, "_" * len(WORD), None)

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
            self._by_depth.setdefault(d, VGroup()).add(          # colour by bottom node;
                Line(a, b, color=self._miss_color(self._misses[cid]),  # edges UNDER nodes
                     stroke_width=sw, z_index=1))

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
                self._node_marker(idn, pos, r))

        # camera pose per path node (depth 0…8): centre EXACTLY on the node so the
        # growing frontier stays at the vertical centre throughout (navy fills the
        # frame, so there's no board edge to avoid). Width zooms by SHRINK per level —
        # the SAME factor the rows bunch — so the local edge (and everything sized off
        # the camera width) holds a constant on-screen size all the way down.
        path = self._path_to(WORD)
        dmax = len(path) - 1
        self._path, self._dmax = path, dmax
        self._cam_center, self._cam_width = [], []
        for k, node in enumerate(path):
            w = CAM_W_START * SHRINK ** k
            self._cam_center.append(self._node_pos(node))
            self._cam_width.append(w)

        # blanks + gallows annotation for EVERY node beyond the root, grouped by depth
        # and by kind. A DECISION node's label sits along its incoming edge (on the
        # edge's "above" side, held clear of the line) and appears as the edge tip
        # passes it; a LEAF's label is stacked below the node and appears WITH the node.
        # Sized off the camera width at that depth (constant on-screen). No missed
        # letters are ever written — misses only add a gallows part.
        self._ann_edge_by_depth = {}     # decision-node labels (appear as the edge passes)
        self._ann_leaf_by_depth = {}     # leaf labels (appear with the node)
        for idn, d in self._depth.items():
            if d == 0:                                   # root label placed in setup_scene
                continue
            s = self._cam_width[d]
            unit = self._annotation(self._pattern[idn], self._misses[idn], s)
            cpos = self._pos_of(idn)
            if self._guess[idn] is None:                 # LEAF → stacked below the node
                unit.next_to(cpos, DOWN, buff=LEAF_GAP * s)
                self._ann_leaf_by_depth.setdefault(d, VGroup()).add(unit)
            else:                                        # DECISION → along its edge
                a = self._pos_of(self._parent[idn])      # parent node
                unit.set_y((cpos + (a - cpos) * EDGE_FRAC)[1])
                blk = unit[1]                            # keep the NEAR blank clear of it
                ex = self._edge_x_at(a, cpos, blk.get_bottom()[1])
                if cpos[0] < a[0]:                       # down-left → unit LEFT of line
                    unit.shift([(ex - ANN_CLR * s) - blk.get_right()[0], 0, 0])
                else:                                    # down-right → unit RIGHT of line
                    unit.shift([(ex + ANN_CLR * s) - blk.get_left()[0], 0, 0])
                self._ann_edge_by_depth.setdefault(d, VGroup()).add(unit)

    # a : draw the tree row by row (each row at once, linear, equal time) while the
    #     camera dives down WORD's path, zooming in a step per row to the leaf
    @subscene
    def grow(self):
        # first beat: fade the opening guess letter into the root node, then hold
        self.play(FadeIn(self.root_letter), run_time=0.8)
        self.wait(ROOT_PAUSE)
        last = len(self._cam_center) - 1
        for d in sorted(self._by_depth):
            k = min(d + 1, last)                     # camera holds at the leaf once reached
            rf = rush_into if d == 0 else linear     # ease INTO the very first step only
            rt = ROW_TIME * ROW_SLOW ** d            # slow down as we descend
            anims = [
                Create(self._by_depth[d], lag_ratio=0.0, rate_func=rf),
                self.camera.frame.animate(rate_func=rf)
                    .move_to(self._cam_center[k]).set(width=self._cam_width[k]),
            ]
            if (d + 1) in self._dots_by_depth:       # dots pop only as the edges reach them
                anims.append(FadeIn(self._dots_by_depth[d + 1],
                                    rate_func=_appear_at_end))
            if (d + 1) in self._ann_edge_by_depth:   # decision labels: as the edge passes
                anims.append(FadeIn(self._ann_edge_by_depth[d + 1],
                                    rate_func=_appear_from(1 - EDGE_FRAC, ANN_WINDOW)))
            if (d + 1) in self._ann_leaf_by_depth:   # leaf labels: with the node
                anims.append(FadeIn(self._ann_leaf_by_depth[d + 1],
                                    rate_func=_appear_at_end))
            self.play(*anims, run_time=rt)

    # b : pull the camera back out to the whole tree
    @subscene
    def zoom_out(self):
        # snapshot cache saves neither camera state nor the bg colour → re-set both
        self.camera.background_color = BOARD_NAVY
        self.camera.frame.move_to(self._cam_center[-1]).set(width=self._cam_width[-1])
        self.play(self.camera.frame.animate.move_to(ORIGIN).set(width=CAM_FULL_W),
                  run_time=ZOOM_OUT_RT, rate_func=smooth)
