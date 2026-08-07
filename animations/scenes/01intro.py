"""SCENE 01 — the cold open: a chalk game of WIN, then the whole len-3 decision
tree grows while the camera dives down one path.

Combines the two test scenes:
  • the CHALK GAME (`94chalkgame`) — WORD retargeted to WIN, guessed I·N·W (all
    hits, no misses), played on the wooden chalkboard.
  • the WIN-TREE (`92wintree_test`) — the winprob len-3 uniform n=5 tree, grown
    row-by-row while a MovingCamera dives down WORD ("yes")'s path, then zoom out.

The two live in different frames — the chalk game reads at the FULL 16×9 frame,
the tree is camera-zoomed (width 3 at the root, ×SHRINK per level). Beat `c` is
the bridge: it dissolves the board frame into the (already-navy) background, fades
the WIN letters, MORPHS the chalk gallows+blanks up into the tree's root-flank
annotation, fades in the root node, and zooms the camera onto the root — handing
off to `grow` at the exact root pose.

Script beat ↔ subscene (Script.md row 01, split on '—'):
  a board    — "Is it possible to play the perfect game…"  fade in gallows + 3 blanks
  b play_win — "Well no, not really…"                      guess I, N, W (all hits)
  c to_tree  — "But here's the next best thing."           board→navy; morph to tree root
  d grow     — "This is a decision tree…"                  grow the tree; camera dives "yes"
  e zoom_out — "We absolutely can… like this."             pull back to the whole tree

BEAT MAP
  board    — draw the 3 word blanks + the gallows
  play_win — bubble I → n → w, each written into its blank (WIN, no misses)
  to_tree  — bridge: dissolve board, morph gallows/blanks → root, zoom to root
  grow     — draw the tree row by row; camera dives down "yes"'s path to its leaf
  zoom_out — pull the camera back out to the whole tree

Source: math/data/shared/winprob/len03_uniform_n05.json (winprob, uniform, n=5).

Render:  render 01a --fast … 01e   /   render 01 sub  for the whole scene

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every run_time in
play_win's guesses, the to_tree bridge (2.5s morph+zoom), and ROW_TIME/ZOOM_OUT_RT
carried over from the test scenes.
"""
from pathlib import Path
import sys
import json

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from manim import MovingCameraScene
from bpkfigures.speech_bubble import speech_bubble
from assets.chalkboard import chalkboard, chalk_letter, CHALK, BOARD_NAVY
from assets.hangman_board import merge_pattern, hangman_drawing

# ── the chalk game (beats a–b): WIN, guessed I·N·W (all hits, no misses) ───────
GAME_WORD = "win"
GUESSES   = ["i", "n", "w"]

# ── sourced tree (beats d–e): winprob len-3 uniform n=5 ───────────────────────
TREE_PATH = (Path(__file__).resolve().parents[2]
             / "math/data/shared/winprob/len03_uniform_n05.json")
WORD = "yes"          # featured deepest-row (depth-8) word — the camera's target

# ── chalk-game layout (frame 16×9 → x-radius 8.0, y-radius 4.5) ───────────────
BOARD_W, BOARD_H = 15.2, 8.4

BLANK_SLOT   = 0.85     # width of one underscore rule
BLANK_GAP    = 0.36     # gap between blanks
BLANK_CX     = -3.0     # blank-row centre x (left side of the board)
BLANK_Y      = -0.2     # blank-row baseline y
BLANK_SW     = 7.0      # chalk stroke width for the rules
LETTER_H     = 1.05     # cap height of a revealed letter (drawn as strokes)
LETTER_SW    = 5.5      # chalk stroke width for a revealed letter
LETTER_BUFF  = 0.20

HANG_SCALE   = 1.2                      # gallows on the RIGHT
HANG_POS     = np.array([4.3, 0.5, 0])
HANG_SW      = 6.0

# the guesser is off the LEFT edge: the tail TIP sits at the screen edge and the
# bubble grows from there (anchored by the tip, NOT move_to — see 94chalkgame).
BUBBLE_TIP   = np.array([-7.9, 2.4, 0])
BUBBLE_FS    = 56
BUBBLE_TAIL  = 1.5

# ── layered tree layout (verbatim from 92wintree_test) ────────────────────────
TOP_Y   = 3.5         # row 0 (the opening guess) sits here
ROWGAP0 = 2.6         # gap row-0→row-1; each next gap ×SHRINK (rows bunch downward)
SHRINK  = 0.65        # per-level scale: rows bunch, camera ZOOMS, nodes/annos shrink
HALF_W  = 7.0         # leaves spread across ±HALF_W

EDGE_SW_ROOT  = 4.0
EDGE_SW_TAPER = SHRINK
EDGE_SW_MIN   = 0.05

DOT_R_ROOT  = 0.09
DOT_R_TAPER = SHRINK
DOT_R_MIN   = 0.001
DOT_APPEAR  = 0.9
NODE_LETTER_H = 1.3

BLK_H   = 0.05        # blank rule/letter height  (fraction of the camera width)
GAL_H   = 0.10        # gallows height            (fraction of the camera width)
ANN_CLR = 0.06
ANN_CLR_STEPS = 6
ANN_CLR_STEP  = 0.9
ANN_SIDE = 0.28       # root: horizontal offset of the blanks (LEFT) / gallows (RIGHT)
SIDE_OVERRIDE = {("_e_", 1): -1}
EDGE_FRAC = 0.50
LEAF_GAP = 0.04
ANN_SW_FRAC = 0.32
ANN_WINDOW = 0.12

ROW_TIME    = 3.0     # every guess-row takes the SAME time (constant-rate growth)
EASE_FRAC   = 0.4     # first step only: fraction of its time spent ramping to speed
ROOT_PAUSE  = 1.0     # hold after the opening letter fades onto the root, before diving
CAM_W_START = 3.0     # camera frame width at the root; each level zooms by SHRINK
CAM_FULL_W  = 16.0
ZOOM_OUT_RT = 5.0


def _appear_at_end(t):
    """Hold at 0 until DOT_APPEAR (edge has ~reached the node), then ramp to 1."""
    return 0.0 if t < DOT_APPEAR else (t - DOT_APPEAR) / (1 - DOT_APPEAR)


def _appear_from(trigger, window=1.0):
    """Rate-func factory: hold at 0 until `trigger`, then ramp to 1 over `window`."""
    return lambda t: 0.0 if t <= trigger else min(1.0, (t - trigger) / window)


def _ease_then_linear(t):
    """First step: ramp velocity from 0 over the first EASE_FRAC, then hold constant
    — ending at the linear rows' speed so it hands off seamlessly."""
    s = EASE_FRAC
    vfull = 1.0 / (1.0 - s / 2.0)
    if t <= s:
        return 0.5 * vfull * t * t / s
    return 0.5 * vfull * s + vfull * (t - s)


class Scene01(MovingCameraScene, HangmanScene):
    """Chalk game of WIN → grow the len-3 winprob(n=5) tree with a camera dive.

    MovingCameraScene supplies self.camera.frame. The chalk game plays at the full
    16×9 frame; _setup_tree (verbatim from 92) precomputes the layered layout +
    camera keyframes so the bridge (to_tree) and dive (grow) can hand off cleanly.
    """

    # the wooden chalkboard sits on the light-blue BG_COLOR surround (set by
    # HangmanScene.construct); in to_tree the navy board EXPANDS to fill the frame.
    def setup_scene(self):
        self.tree = json.loads(TREE_PATH.read_text())["tree"]
        self._setup_tree()                 # layout + edges/dots/annos/camera keyframes
        self.cb = chalkboard(BOARD_W, BOARD_H)
        self.cb.set_z_index(-10)
        self.add(self.cb)
        self.revealed = VGroup()           # revealed WIN letters (faded out in to_tree)

    # ══════════════════════════════════════════════════════════════════════════
    #  CHALK GAME builders (from 94chalkgame)
    # ══════════════════════════════════════════════════════════════════════════
    def _reveal_letter(self, ch, rule):
        L = chalk_letter(ch, height=LETTER_H, stroke_width=LETTER_SW, color=CHALK)
        L.next_to(rule, UP, buff=LETTER_BUFF)
        L.set_x(rule.get_center()[0])
        return L

    def _bubble(self, ch):
        b = speech_bubble(ch.upper(), font_size=BUBBLE_FS, tail="left",
                          tail_len=BUBBLE_TAIL)
        b.shift(BUBBLE_TIP - b.tip_dot.get_center())   # anchor the tail tip
        return b

    def _play_guess(self, i, *, rt_bubble, rt_write, rt_out):
        """One guess: pop the bubble, write the hit letter(s) into the blank(s),
        dismiss the bubble. WIN has no misses, so this is hit-only."""
        g = GUESSES[i]
        positions = [p for p, c in enumerate(GAME_WORD) if c == g]
        bub = self._bubble(g)
        self.play(GrowFromPoint(bub, bub.tip_dot.get_center()), run_time=rt_bubble)
        for p in positions:                            # LEFT→RIGHT, stroke-by-stroke
            L = self._reveal_letter(g, self.rules[p])
            self.revealed.add(L)
            self.play(LaggedStartMap(Create, L, lag_ratio=0.5), run_time=rt_write)
        self.play(FadeOut(bub), run_time=rt_out)

    def _setup_blanks(self):
        n = len(GAME_WORD)
        total = n * BLANK_SLOT + (n - 1) * BLANK_GAP
        x0 = BLANK_CX - total / 2 + BLANK_SLOT / 2
        self.rules = VGroup()
        for k in range(n):
            x = x0 + k * (BLANK_SLOT + BLANK_GAP)
            self.rules.add(Line([x - BLANK_SLOT / 2, BLANK_Y, 0],
                                [x + BLANK_SLOT / 2, BLANK_Y, 0],
                                color=CHALK, stroke_width=BLANK_SW))

    def _setup_gallows(self):
        # build the full gallows just to place it, then keep only the gallows frame
        # (WIN has no misses, so no body parts are ever drawn).
        full = hangman_drawing(6, color=CHALK, stroke_width=HANG_SW)
        full.scale(HANG_SCALE).move_to(HANG_POS)
        for p in list(full.parts):
            full.remove(p)
        self.hang = full

    # ══════════════════════════════════════════════════════════════════════════
    #  TREE machinery (verbatim from 92wintree_test)
    # ══════════════════════════════════════════════════════════════════════════
    def _words(self, node):
        if "branches" in node:
            return node["n"]
        if "word" in node:
            return 1
        return len(node["lost"])

    def _row_y(self, depth):
        while len(self._rows) <= depth:
            d = len(self._rows)
            self._rows.append(self._rows[-1] - ROWGAP0 * SHRINK ** (d - 1))
        return self._rows[depth]

    def _miss_color(self, misses):
        if misses <= 0:
            return CHALK
        return LIGHT_PALETTE[len(LIGHT_PALETTE) - misses]

    def _node_marker(self, idn, pos, r):
        dot = Dot(pos, radius=r, color=self._miss_color(self._misses[idn]), z_index=2)
        g = self._guess[idn]
        if g is None:
            return VGroup(dot)
        lab = crisp_text(g.upper(), color=BOARD_NAVY, weight=BOLD)
        lab.scale_to_fit_height(NODE_LETTER_H * r).move_to(pos).set_z_index(3)
        return VGroup(dot, lab)

    def _blanks(self, pattern, h, sw):
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
        g = hangman_drawing(misses, color=CHALK).scale_to_fit_height(h)
        g.set_stroke(width=sw)
        return g

    def _annotation(self, pattern, misses, s):
        gal = self._gallows(misses, GAL_H * s, ANN_SW_FRAC * s)
        blk = self._blanks(pattern, BLK_H * s, ANN_SW_FRAC * s)
        reserve = (LEAF_GAP + 1.22 * BLK_H) * s
        blk.set_x(gal.get_center()[0])
        blk.shift([0, (gal.get_bottom()[1] - reserve) - blk.get_bottom()[1], 0])
        return VGroup(gal, blk)

    def _edge_x_at(self, a, b, y):
        if abs(a[1] - b[1]) < 1e-6:
            return a[0]
        return a[0] + (b[0] - a[0]) * (a[1] - y) / (a[1] - b[1])

    def _seg_hits_box(self, p0, p1, lo, hi):
        d = p1 - p0
        t0, t1 = 0.0, 1.0
        for i in (0, 1):
            if abs(d[i]) < 1e-9:
                if p0[i] < lo[i] or p0[i] > hi[i]:
                    return False
            else:
                a, b = (lo[i] - p0[i]) / d[i], (hi[i] - p0[i]) / d[i]
                if a > b:
                    a, b = b, a
                t0, t1 = max(t0, a), min(t1, b)
                if t0 > t1:
                    return False
        return True

    def _ann_hits(self, lo, hi, depth):
        n = 0
        for pd in (depth - 3, depth - 2, depth - 1, depth):
            for pid, cid in self._edges_by_pdepth.get(pd, ()):
                p0, p1 = self._pos_of(pid)[:2], self._pos_of(cid)[:2]
                if (max(p0[0], p1[0]) < lo[0] or min(p0[0], p1[0]) > hi[0] or
                        max(p0[1], p1[1]) < lo[1] or min(p0[1], p1[1]) > hi[1]):
                    continue
                if self._seg_hits_box(p0, p1, lo, hi):
                    n += 1
        return n

    def _assign(self, node, depth, misses, pattern, parent):
        self._depth[id(node)] = depth
        self._misses[id(node)] = misses
        self._guess[id(node)] = node.get("guess")
        self._pattern[id(node)] = pattern
        self._parent[id(node)] = parent
        if "branches" not in node:
            x = self._next_leaf
            self._next_leaf += 1
        else:
            allblank = "_" * len(next(iter(node["branches"])))
            items = sorted(node["branches"].items(),
                           key=lambda kv: self._words(kv[1]), reverse=(depth % 2 == 1))
            xs = []
            for key, child in items:
                m = misses + (1 if key == allblank else 0)
                pat = merge_pattern(pattern, key)
                xs.append(self._assign(child, depth + 1, m, pat, id(node)))
                self._edges.append((id(node), id(child)))
            x = (xs[0] + xs[-1]) / 2
        self._x[id(node)] = x
        return x

    def _pos_of(self, idn):
        return np.array([(self._x[idn] - (self._n - 1) / 2) * self._scale,
                         self._row_y(self._depth[idn]), 0.0])

    def _node_pos(self, node):
        return self._pos_of(id(node))

    def _path_to(self, word):
        node, nodes = self.tree, [self.tree]
        while "branches" in node:
            g = node["guess"]
            key = "".join(g if word[p] == g else "_" for p in range(len(word)))
            node = node["branches"][key]
            nodes.append(node)
        return nodes

    def _setup_tree(self):
        self._x, self._depth, self._edges, self._misses = {}, {}, [], {}
        self._guess, self._pattern, self._parent = {}, {}, {}
        self._rows, self._next_leaf = [TOP_Y], 0
        self._assign(self.tree, 0, 0, "_" * len(WORD), None)

        self._n = self._next_leaf
        self._scale = 2 * HALF_W / max(1, self._n - 1)
        self._edges_by_pdepth = {}
        for pid, cid in self._edges:
            self._edges_by_pdepth.setdefault(self._depth[pid], []).append((pid, cid))

        self._by_depth = {}
        for pid, cid in self._edges:
            d = self._depth[pid]
            a = np.array([(self._x[pid] - (self._n - 1) / 2) * self._scale,
                          self._row_y(d), 0.0])
            b = np.array([(self._x[cid] - (self._n - 1) / 2) * self._scale,
                          self._row_y(d + 1), 0.0])
            sw = max(EDGE_SW_MIN, EDGE_SW_ROOT * EDGE_SW_TAPER ** d)
            self._by_depth.setdefault(d, VGroup()).add(
                Line(a, b, color=self._miss_color(self._misses[cid]),
                     stroke_width=sw, z_index=1))

        self._dots_by_depth = {}
        for idn, d in self._depth.items():
            if d == 0:
                continue
            pos = np.array([(self._x[idn] - (self._n - 1) / 2) * self._scale,
                            self._row_y(d), 0.0])
            r = max(DOT_R_MIN, DOT_R_ROOT * DOT_R_TAPER ** d)
            self._dots_by_depth.setdefault(d, VGroup()).add(
                self._node_marker(idn, pos, r))

        path = self._path_to(WORD)
        dmax = len(path) - 1
        self._path, self._dmax = path, dmax
        self._cam_center, self._cam_width = [], []
        for k, node in enumerate(path):
            w = CAM_W_START * SHRINK ** k
            self._cam_center.append(self._node_pos(node))
            self._cam_width.append(w)

        self._ann_edge_by_depth = {}
        self._ann_leaf_by_depth = {}
        for idn, d in self._depth.items():
            if d == 0:
                continue
            s = self._cam_width[d]
            unit = self._annotation(self._pattern[idn], self._misses[idn], s)
            cpos = self._pos_of(idn)
            if self._guess[idn] is None:
                unit.next_to(cpos, DOWN, buff=LEAF_GAP * s)
                self._ann_leaf_by_depth.setdefault(d, VGroup()).add(unit)
            else:
                a = self._pos_of(self._parent[idn])
                unit.set_y((cpos + (a - cpos) * EDGE_FRAC)[1])
                blk = unit[1]
                ex = self._edge_x_at(a, cpos, blk.get_bottom()[1])
                bl, br = unit.get_left()[0], unit.get_right()[0]
                bb, bt = unit.get_bottom()[1], unit.get_top()[1]
                default_left = cpos[0] < a[0]
                override = SIDE_OVERRIDE.get((self._pattern[idn], self._misses[idn]))
                sides = (override,) if override is not None else (-1, 1)
                best = None
                for sign in sides:
                    for m in range(ANN_CLR_STEPS):
                        clr = ANN_CLR * (1 + m * ANN_CLR_STEP) * s
                        dx = (ex - clr - br) if sign < 0 else (ex + clr - bl)
                        hits = self._ann_hits(np.array([bl + dx, bb]),
                                              np.array([br + dx, bt]), d)
                        key = (hits, m, 0 if (sign < 0) == default_left else 1)
                        if best is None or key < best[0]:
                            best = (key, dx)
                        if hits == 0:
                            break
                unit.shift([best[1], 0, 0])
                self._ann_edge_by_depth.setdefault(d, VGroup()).add(unit)

        # the tree's ROOT node + its flanking annotation (blanks LEFT, gallows RIGHT),
        # built HERE (ids valid during setup_scene — a snapshot reload gives self.tree a
        # new id, so runtime id-lookups would KeyError). Kept OFF screen until to_tree.
        rpos = self._node_pos(self.tree)
        w0 = self._cam_width[0]
        self.root_dot = Dot(rpos, radius=DOT_R_ROOT, color=self._miss_color(0),
                            z_index=2)
        self.root_letter = crisp_text(self._guess[id(self.tree)].upper(),
                                      color=BOARD_NAVY, weight=BOLD)
        self.root_letter.scale_to_fit_height(NODE_LETTER_H * DOT_R_ROOT)
        self.root_letter.move_to(rpos).set_z_index(3)
        base_y = rpos[1] - DOT_R_ROOT
        self.root_blanks = self._blanks("_" * len(WORD), BLK_H * w0, ANN_SW_FRAC * w0)
        self.root_blanks.set_x(rpos[0] - ANN_SIDE * w0)
        self.root_blanks.shift([0, base_y - self.root_blanks.get_bottom()[1], 0])
        self.root_gallows = self._gallows(0, GAL_H * w0, ANN_SW_FRAC * w0)
        self.root_gallows.set_x(rpos[0] + ANN_SIDE * w0)
        self.root_gallows.shift([0, base_y - self.root_gallows.get_bottom()[1], 0])

    # ══════════════════════════════════════════════════════════════════════════
    #  SUBSCENES
    # ══════════════════════════════════════════════════════════════════════════

    # a : fade in the gallows and the 3 word blanks
    @subscene
    def board(self):
        self._setup_blanks()
        self._setup_gallows()
        self.play(FadeIn(self.rules), FadeIn(self.hang), run_time=1.2)

    # b : guess I, N, W — all hits, the word WIN fills in with no misses
    @subscene
    def play_win(self):
        self._play_guess(0, rt_bubble=0.7, rt_write=0.9, rt_out=0.4)   # I
        self._play_guess(1, rt_bubble=0.7, rt_write=0.9, rt_out=0.4)   # N
        self._play_guess(2, rt_bubble=0.7, rt_write=0.9, rt_out=0.4)   # W

    # c : the bridge — the navy board EXPANDS to fill the frame (navy stays navy;
    #     the light-blue surround is covered), the WIN letters fade OUT, the gallows
    #     + blanks MORPH into the tree's root annotation, the root node (no letter
    #     yet) FADES in, and the camera zooms onto the root.
    @subscene
    def to_tree(self):
        self.play(
            self.cb.board.animate.scale(6),                   # navy expands to fill frame
            FadeOut(self.cb.frame),                           # wooden frame dissolves
            FadeOut(self.revealed),                           # WIN letters fade out
            ReplacementTransform(self.rules, self.root_blanks),
            ReplacementTransform(self.hang, self.root_gallows),
            FadeIn(self.root_dot),                            # node fades in (no letter yet)
            self.camera.frame.animate.move_to(self._cam_center[0])
                .set(width=self._cam_width[0]),
            run_time=2.5, rate_func=smooth,
        )
        # the expanded board is now the navy backdrop for the tree; also set the camera
        # bg navy so the snapshot carries it forward (framework restores both).
        self.camera.background_color = BOARD_NAVY
        self.rules = self.hang = self.revealed = None         # drop consumed carry-overs

    # d : draw the tree row by row (each row at once, linear, equal time) while the
    #     camera dives down WORD's path, zooming a step per row to the leaf. The
    #     root node + annotation are already on screen (from to_tree).
    @subscene
    def grow(self):
        # the framework restores the incoming root pose + navy bg from to_tree's
        # snapshot. First beat: fade the opening guess letter onto the root node.
        self.play(FadeIn(self.root_letter), run_time=0.8)
        self.wait(ROOT_PAUSE)                                 # hold on the root before diving
        last = len(self._cam_center) - 1
        for d in sorted(self._by_depth):
            k = min(d + 1, last)
            if d == 0:
                rf = _ease_then_linear
                rt = ROW_TIME / (1 - EASE_FRAC / 2)
            else:
                rf, rt = linear, ROW_TIME
            anims = [
                Create(self._by_depth[d], lag_ratio=0.0, rate_func=rf),
                self.camera.frame.animate(rate_func=rf)
                    .move_to(self._cam_center[k]).set(width=self._cam_width[k]),
            ]
            if (d + 1) in self._dots_by_depth:
                anims.append(FadeIn(self._dots_by_depth[d + 1],
                                    rate_func=_appear_at_end))
            if (d + 1) in self._ann_edge_by_depth:
                anims.append(FadeIn(self._ann_edge_by_depth[d + 1],
                                    rate_func=_appear_from(1 - EDGE_FRAC, ANN_WINDOW)))
            if (d + 1) in self._ann_leaf_by_depth:
                anims.append(FadeIn(self._ann_leaf_by_depth[d + 1],
                                    rate_func=_appear_at_end))
            self.play(*anims, run_time=rt)

    # e : pull the camera back out to the whole tree
    @subscene
    def zoom_out(self):
        # framework restores the incoming leaf pose + navy bg from grow's snapshot.
        edge_ann = VGroup(*self._ann_edge_by_depth.values())
        self.play(FadeOut(edge_ann), run_time=1.0)
        self.play(self.camera.frame.animate.move_to(ORIGIN).set(width=CAM_FULL_W),
                  run_time=ZOOM_OUT_RT, rate_func=smooth)
