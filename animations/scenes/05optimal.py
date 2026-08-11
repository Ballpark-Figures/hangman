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
  f drill         — breadcrumb the optimal (O), drill its all-miss leaf into the 4×4 option grid
  g resolve       — keep drilling (3×4 → 2×3 grids) to the {by,my} base case; Y-first spine +
                    'Avg misses: 0' on the forced M
  h solve_base    — we've solved that position: green ONLY the computed part (M→MY, avg 0) and
                    drop its miss tally; the rest greens as we back the value up
  i backup_b      — back up the B node: try B/M candidates (complete green subtrees), choose B,
                    'Avg misses: 0.5'
  j backup_y      — back up the Y node: fade B's value, cycle Y/B/M candidate subtrees, choose Y
  k backup_u      — start backing up U: solve its OTHER child {up,us} (shrink Y-subtree, grow it)
  l solve_ups     — solve {up,us}: cycle P/S candidate subtrees, choose P (0.5)
  m choose_u      — back up U: cycle U/Y/B/M/P/S candidate subtrees w/ a rolling avg counter,
                    choose U (1.0) and lock its node + edges + value green
  --- next sections (not yet built) ---
  … back the values up the diagonal (E→A) level by level; dedup + prune; paired chart

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
# the recapped hit-sibling LEAF TEXT on the shrunk diagonal (beat g's final tree)
GRID_LEAF_H      = GRID_BLANK_H * 1.22
GRID_LEAF_DROP   = 0.36            # child centre → its blank baseline
GRID_W, GRID_H   = 15.6, 8.0       # the cells tile this box (full width, small top/bottom margin)
GRID_CENTER      = [0, 0, 0]
PATH_SCALE       = 0.5     # the drilled-past path (A→O→…) is shrunk vs the active subtree
# the diagonal takes a TALLER vertical step than a normal parent→child drop, so each
# guess node has room BELOW it for its hit-siblings' recapped leaf text (avoids the packed
# rows colliding). Only the drilled-past diagonal uses this; grafted subtrees use CHILD_DY.
PATH_DY          = GRID_CHILD_DY * 1.55


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

    def _miss_row(self, letters, h=GRID_MISS_H):
        """A row of RED missed letters (the running wrong-guess tally)."""
        row = VGroup(*[crisp_text(c, color=LIGHT_RED, weight=BOLD)
                       .scale_to_fit_height(h) for c in letters])
        row.arrange(RIGHT, buff=h * 0.45)
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
        kid = {}                                          # pattern -> branch (role handles)
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
            row = None
            if tally:
                row = self._miss_row(tally)
                row.next_to(blanks, DOWN, buff=0.09).set_x(blanks.get_x())
                branch.add(row)
            branch.edge, branch.dot, branch.blanks, branch.missrow = edge, cdot, blanks, row
            branch.pat, branch.miss = pat, miss
            kid[pat] = branch
            fan.add(branch)
        mt = VGroup(parent, fan)
        mt.parent, mt.fan = parent, fan
        mt.gdot, mt.glab, mt.kid = dot, lab, kid   # role handles for the transform
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

    def _path_diag(self, depth, leaf_text=False):
        """The SHRUNK drilled-past path A→O→… for ``depth`` guesses, as a diagonal going
        down-LEFT (the miss branch is the left child). Each guess node keeps its HIT
        siblings as bare dots. During the drill they are DECLUTTERED (no blanks); pass
        ``leaf_text=True`` to also build each hit-sibling's board-state annotation (the
        revealed-letter blanks + the accumulated red miss tally), collected on
        ``grp.leaf_text`` so a caller can bring it back once the tree is centred.
        Returns (group, anchor, last_dot): where the active subtree attaches, and the
        deepest guess node it hangs from."""
        r = GRID_NODE_R
        node = DATA["tree"]
        grp = VGroup()
        levels = []                                       # role handles, one per guess
        leaf_grp = VGroup()                               # hit-sibling annotations (leaf_text)
        A_pos = pos = np.array([0.0, 0.0, 0.0])
        prev_dot = last_dot = None
        missed = []                                       # miss letters accumulated down the path
        for i in range(depth):
            # z-index the dot (2) BELOW its knocked-out letter (3): later beats recolour a
            # diagonal node (greening it as its value backs up), and recolouring re-adds the
            # dot to the front of the draw order — without the z-index that would draw the
            # green dot OVER its navy letter and hide it (bit us greening U in choose_u).
            dot = Dot(pos, radius=r, color=_miss_color(0 if i == 0 else 1), z_index=2)
            lab = crisp_text(node["optimal_letter"].upper(), color=BOARD_NAVY, weight=BOLD)
            lab.scale_to_fit_height(NODE_LETTER_H * r).move_to(dot).set_z_index(3)
            grp.add(dot, lab)
            in_edge = None
            if prev_dot is not None:
                dn = normalize(pos - prev_dot.get_center())
                in_edge = Line(prev_dot.get_center() + dn * r, pos - dn * r,
                               color=LIGHT_RED, stroke_width=2.0)
                grp.add(in_edge)
            hitpats = [p for p in node["children"] if set(p) != {"_"}]  # hit siblings
            hits = []
            for j, p in enumerate(hitpats):
                # hit siblings drop the SAME amount as the miss child (PATH_DY) → every
                # node's children sit on ONE horizontal level
                hpos = pos + np.array([GRID_CHILD_SPR * (j + 1), -PATH_DY, 0.0])
                hdot = Dot(hpos, radius=r * GRID_CHILD_RF, color=_miss_color(0))
                dn = normalize(hpos - pos)
                hedge = Line(pos + dn * r, hpos - dn * r * GRID_CHILD_RF,
                             color=CHALK, stroke_width=2.0)
                grp.add(hedge, hdot)
                hits.append((hedge, hdot))
                if leaf_text:                             # this hit branch's board state
                    # SMALLER + pulled up close under the node so it clears the row below
                    blk = self._blanks(p, h=GRID_LEAF_H).set_x(hpos[0])
                    blk.shift([0, (hpos[1] - GRID_LEAF_DROP) - blk.get_bottom()[1], 0])
                    ann = VGroup(blk)
                    if missed:
                        mr = self._miss_row(missed, h=GRID_LEAF_H)
                        mr.next_to(blk, DOWN, buff=0.05).set_x(blk.get_x())
                        ann.add(mr)
                    leaf_grp.add(ann)
            levels.append({"dot": dot, "lab": lab, "in_edge": in_edge, "hits": hits})
            prev_dot = last_dot = dot
            missed = missed + [node["optimal_letter"].upper()]   # this guess missed → down-left
            # miss child drops the SAME (PATH_DY) as the hit siblings, so all of a node's
            # children are level; PATH_DY is tall enough to keep room for the leaf text
            pos = pos + np.array([-GRID_CHILD_SPR, -PATH_DY, 0.0])
            node = node["children"]["__"]
        if leaf_text:
            grp.add(leaf_grp)                             # scale + move with the diagonal
        anchor = A_pos + (pos - A_pos) * PATH_SCALE
        grp.scale(PATH_SCALE, about_point=A_pos)
        grp.levels = levels
        grp.leaf_text = leaf_grp
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
        cell = VGroup(path, edge, sub)
        cell.path, cell.drilled_edge, cell.sub = path, edge, sub   # role handles
        return cell

    # ── piece-by-piece transform of the on-screen tree into the option grid ────────
    def _source_pieces(self, tree):
        """Pieces of the CURRENT on-screen tree, by role, for pairing: the guess levels
        it already has (A, or A→O), the FRONTIER leaf (the all-miss node that will be
        drilled), that leaf's incoming edge, and the extra text to fade (blanks/tallies).
        Handles both the `_mini_tree` A-opener (beat e's source) and a `_diag_cell`
        (beat f's source, whose drilled node becomes a path level)."""
        if hasattr(tree, "path"):                         # a _diag_cell used as source
            levels = list(tree.path.levels)
            sub, in_edge = tree.sub, tree.drilled_edge
        else:                                             # the _mini_tree A-opener
            levels, sub, in_edge = [], tree, None
        hitpats = [p for p in sub.kid if set(p) != {"_"}]
        levels = levels + [{"dot": sub.gdot, "lab": sub.glab, "in_edge": in_edge,
                            "hits": [(sub.kid[p].edge, sub.kid[p].dot) for p in hitpats]}]
        miss = sub.kid["__"]
        extra = [miss.blanks] + ([miss.missrow] if miss.missrow else []) \
            + [sub.kid[p].blanks for p in hitpats] \
            + [sub.kid[p].missrow for p in hitpats if sub.kid[p].missrow]
        return levels, miss.dot, miss.edge, extra

    def _target_pieces(self, cell):
        """Pieces of a TARGET `_diag_cell`, by role: the path levels, the edge to the
        drilled node, its dot + (new) letter, and its children (grown after the move)."""
        return (cell.path.levels, cell.drilled_edge, cell.sub.gdot, cell.sub.glab,
                cell.sub.fan)

    def _transform_move(self, source, cells, run_time, extra_anims=()):
        """PHASE 1 of the drill transform: move each node/edge of ``source`` to its
        counterpart in every ``cells`` cell (the original → the top-left one via
        ReplacementTransform, copies → the rest), fading the extra text out (moving +
        shrinking WITH the tree) during the move. Each drilled node's NEW LETTER RIDES its
        node into place (develops on top of the node as it moves, not after). Any
        ``extra_anims`` play alongside the move. Returns ``grows`` = ``[(kids, dot)]`` for
        phase 2 so the caller grows the subtree (all at once, or one level at a time)."""
        s_levels, s_fdot, s_fedge, s_extra = self._source_pieces(source)
        move, grows = [], []
        for k, cell in enumerate(cells):
            t_levels, t_dedge, t_ddot, t_dlab, t_kids = self._target_pieces(cell)
            pairs = []
            for sl, tl in zip(s_levels, t_levels):        # same length by construction
                pairs += [(sl["dot"], tl["dot"]), (sl["lab"], tl["lab"])]
                if sl["in_edge"] is not None and tl["in_edge"] is not None:
                    pairs.append((sl["in_edge"], tl["in_edge"]))
                for (se, sd), (te, td) in zip(sl["hits"], tl["hits"]):
                    pairs += [(se, te), (sd, td)]
            pairs += [(s_fedge, t_dedge), (s_fdot, t_ddot)]
            xf = ReplacementTransform if k == 0 else lambda a, b: TransformFromCopy(a, b)
            move += [xf(a, b) for a, b in pairs]
            # the new letter RIDES the node: start it small + transparent AT the source
            # frontier leaf, then Restore to its target pose so it travels ON TOP of the node
            # as the node moves into place (not waiting at the destination for the node)
            t_dlab.save_state()
            t_dlab.scale(s_fdot.width / t_ddot.width).move_to(s_fdot.get_center()).set_opacity(0)
            move.append(Restore(t_dlab))
            grows.append((t_kids, t_ddot))
        # the extra text MOVES + SHRINKS with the tree (toward the top-left cell, as if it
        # were staying) while fading — not a fade-in-place
        src_A, dst_A = s_levels[0]["dot"], cells[0].path.levels[0]["dot"]
        s, o = dst_A.width / src_A.width, src_A.get_center()
        d = dst_A.get_center() - o
        extra = []
        for x in s_extra:
            ghost = x.copy().scale(s, about_point=o).shift(d).set_opacity(0)
            extra.append(Transform(x, ghost))
        # the new letters ride their nodes into place (in `move`); extra_anims play alongside
        self.play(*move, *extra, *extra_anims, run_time=run_time)
        return grows

    def _transform_into(self, source, cells, run_time):
        """Piece-by-piece drill: move source → cells with each drilled letter fading in
        DURING the move (phase 1), then grow each drilled node's whole subtree (phase 2).
        Nothing morphs as a blob."""
        grows = self._transform_move(source, cells, run_time * 0.6)
        self.play(*[GrowFromPoint(k, d.get_center()) for k, d in grows],
                  run_time=run_time * 0.4)
        self.clear()                                      # drop the transform's stray copies…
        self.add(*cells)                                  # …and re-track clean cell groups

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
        # fade everything else out FIRST, then bring the A tree to the centre
        self.play(FadeOut(VGroup(*self.grid[1:])), run_time=run_time * 0.5)
        self.play(a.animate.scale_to_fit_height(4.2).move_to(ORIGIN),
                  run_time=run_time * 0.5)
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
        self._tile(cells, cols=GRID_COLS)
        # piece-by-piece: move each of the A tree's nodes/edges to its counterpart in
        # every cell (original → top-left, copies → the rest), fade the extra text, then
        # grow each drilled node's letter + children.
        self._transform_into(self.a_tree, cells, run_time)
        self.a_tree = None
        self.grid = VGroup(*cells)

    def _ymy_cell(self):
        """The RESOLVED base-case cell (greedy-among-optimal tiebreak): at ``{by, my}`` the
        shared letter **Y** is guessed FIRST — a guaranteed hit on both (both end in Y →
        '_Y', 0 misses) — then **B** splits them (hit finishes BY, miss → my), then **M**
        finishes MY. Expected misses are unchanged (0.5 at the position, 0 at M); this only
        chooses which equally-optimal guess ORDER to draw, so the bushy bottom becomes a
        clean spine. Intro grammar: every DECISION node is lettered; completed words are
        BARE won-leaves. Returns (cell, m_dot) — m_dot is the ``Avg misses: 0`` node (the
        forced guess right after the B-miss).

        Exposes the SAME role handles as `_diag_cell` (``.path`` with ``.levels`` and
        ``.leaf_text``, ``.drilled_edge``, ``.sub.gdot/.glab/.fan``) so `_transform_move`
        can grow it from the depth-4 top-left cell like e/f: the U-miss leaf becomes **Y**.
        Additionally exposes ``sub.fan_levels`` = [Y→B, B→(BY,M), M→MY] and ``sub.bdot`` so
        the final resolve grows the subtree ONE LEVEL AT A TIME (not the whole fan)."""
        r = GRID_NODE_R
        cr = r * GRID_CHILD_RF
        DY, SPR = GRID_CHILD_DY, GRID_CHILD_SPR
        path, anchor, last_dot = self._path_diag(5, leaf_text=True)   # + hit-sibling blanks

        # Y — the forced guaranteed hit at {by,my} (drilled node; reached via U-miss → red)
        ydot = Dot(anchor, radius=r, color=_miss_color(1), z_index=2)
        ylab = crisp_text("Y", color=BOARD_NAVY, weight=BOLD)
        ylab.scale_to_fit_height(NODE_LETTER_H * r).move_to(ydot).set_z_index(3)
        dn = normalize(anchor - last_dot.get_center())
        drilled_edge = Line(last_dot.get_center() + dn * (r * PATH_SCALE),
                            anchor - dn * r, color=_miss_color(1), stroke_width=2.0)

        def _guess(pos, letter, miss):
            dot = Dot(pos, radius=r, color=_miss_color(miss), z_index=2)
            lab = crisp_text(letter.upper(), color=BOARD_NAVY, weight=BOLD)
            lab.scale_to_fit_height(NODE_LETTER_H * r).move_to(dot).set_z_index(3)
            return dot, VGroup(dot, lab)

        def _leaf(pos, word, tally):                      # bare won-leaf + revealed word + tally
            dot = Dot(pos, radius=cr, color=CHALK, z_index=2)
            blk = self._blanks(word).set_x(pos[0])
            blk.shift([0, (pos[1] - GRID_BLANK_DROP) - blk.get_bottom()[1], 0])
            mr = self._miss_row(tally)
            mr.next_to(blk, DOWN, buff=0.09).set_x(blk.get_x())
            return dot, blk, mr, VGroup(dot, blk, mr)

        def _edge(pa, ra, pb, rb, miss):
            d = normalize(pb - pa)
            return Line(pa + d * ra, pb - d * rb, color=_miss_color(miss), stroke_width=2.0)

        bpos = anchor + np.array([0.0, -DY, 0.0])
        bdot, bgrp = _guess(bpos, "B", 0)                  # reached via Y-hit → white
        bypos = bpos + np.array([SPR, -DY, 0.0])
        byleaf, by_blk, by_mr, bygrp = _leaf(bypos, "by", ["A", "O", "I", "E", "U"])
        mpos = bpos + np.array([-SPR, -DY, 0.0])
        mdot, mgrp = _guess(mpos, "M", 1)                  # reached via B-miss → red  (avg 0)
        mypos = mpos + np.array([0.0, -DY, 0.0])
        myleaf, my_blk, my_mr, mygrp = _leaf(mypos, "my", ["A", "O", "I", "E", "U", "B"])
        # fan split into LEVELS so the final resolve grows one at a time (Y itself is NOT
        # in the fan — it arrives via the transform). l1 from Y, l2 from B, l3 from M.
        e_yb = _edge(anchor, r, bpos, r, 0)                       # Y→B  hit
        e_bby = _edge(bpos, r, bypos, cr, 0)                      # B→BY hit
        e_bm = _edge(bpos, r, mpos, r, 1)                         # B→M  miss
        e_mmy = _edge(mpos, r, mypos, cr, 0)                      # M→MY hit
        l1 = VGroup(e_yb, bgrp)
        l2 = VGroup(e_bby, bygrp, e_bm, mgrp)
        l3 = VGroup(e_mmy, mygrp)
        fan = VGroup(l1, l2, l3)
        sub = VGroup(VGroup(ydot, ylab), fan)
        sub.gdot, sub.glab, sub.fan = ydot, ylab, fan
        sub.bdot, sub.mdot, sub.fan_levels = bdot, mdot, [l1, l2, l3]
        # granular handles for the DP back-up (green one section at a time; each greened
        # section drops its red miss tally). node letters stay knocked-out navy.
        sub.discs = {"y": ydot, "b": bdot, "m": mdot}
        sub.edges = {"yb": e_yb, "bby": e_bby, "bm": e_bm, "mmy": e_mmy}
        sub.leaves = {"by": (byleaf, by_blk, by_mr), "my": (myleaf, my_blk, my_mr)}
        sub.node_letters = VGroup(ylab, bgrp[1], mgrp[1])
        cell = VGroup(path, drilled_edge, sub)
        cell.path, cell.drilled_edge, cell.sub, cell.mdot = path, drilled_edge, sub, mdot
        return cell, mdot

    def _avg_label(self, node_dot, value="0", height=0.34, direction=LEFT):
        """The 'Avg misses: <value>' annotation beside a node — its backed-up optimal value.
        ``value`` is a pre-formatted string SOURCED from the tree data (0 for a determined
        leaf; e.g. 0.5 / 1 / 2 / 3.88 for a backed-up position)."""
        # build small (crisp_text supersamples to a 240pt cap where a longer string
        # WRAPS in pango — see hangman/bpkfigures CLAUDE.md) then scale to a readable height
        lab = crisp_text(f"Avg misses: {value}", font_size=12, color=WHITE, weight=BOLD)
        lab.scale_to_fit_height(height).next_to(node_dot, direction, buff=height * 0.6)
        return lab

    # ── f : keep drilling — expand the top-left (greedy pick O) tree's all-miss leaf
    #        into the next grid, each cell now rooted along the path A→O (depth 2),
    #        greedy-sorted, drilling the top-left again. ───────────────────────────────
    @subscene
    def drill(self):
        opts = sorted((o for o in self._n_miss_node(2)["options"] if o["splits"]),
                      key=lambda o: (-_greedy_score(o), o["letter"]))
        cells = [self._diag_cell(2, o) for o in opts]
        self._tile(cells, cols=4)                         # 16 splitting options → 4×4
        src = self.grid[0]                               # the top-left (A→O) tree from e
        # fade everything else out first, then piece-by-piece transform the top-left tree
        # into the cells (O shrinks into the path, O-miss becomes each new drilled node)
        self.play(FadeOut(VGroup(*self.grid[1:])), run_time=0.6)
        self._transform_into(src, cells, 2.2)
        self.grid = VGroup(*cells)

    # ── g : keep drilling to the BASE CASE. Repeat f's expand (fade all but the top-left,
    #        transform its all-miss leaf into the next option grid) down the all-miss
    #        diagonal — depth 2 → 3 (after A,O,I) → 4 (after A,O,I,E) — until the surviving
    #        set is {BY, MY}. There we play the forced Y (guaranteed hit both) and resolve
    #        into the Y-first spine, dropping 'Avg misses: 0' on the forced M after the
    #        B-miss (the recursion base case we back up from in h). "Leaf" = the FINAL
    #        GUESS — see hangman CLAUDE.md. ─────────────────────────────────────────────
    @subscene
    def resolve(self):
        self._g_expand(3, cols=4, run_time=2.4)           # depth-3 grid: 12 options → 3×4
        self._g_expand(4, cols=3, run_time=2.4)           # depth-4 grid: 6 options → 2×3
        self._g_resolve_final(3.4)                        # depth-4 top-left → the Y-first spine

    def _g_expand(self, depth, cols, run_time):
        """Fade all but the current grid's top-left, then piece-by-piece transform its
        all-miss leaf into the greedy-sorted option grid one level deeper (same move as
        drill)."""
        opts = sorted((o for o in self._n_miss_node(depth)["options"] if o["splits"]),
                      key=lambda o: (-_greedy_score(o), o["letter"]))
        cells = [self._diag_cell(depth, o) for o in opts]
        self._tile(cells, cols=cols)
        self.play(FadeOut(VGroup(*self.grid[1:])), run_time=run_time * 0.22)
        self._transform_into(self.grid[0], cells, run_time * 0.78)
        self.grid = VGroup(*cells)

    def _g_resolve_final(self, run_time):
        """The final expand: the depth-4 top-left (U) cell moves to the centre and grows
        into the Y-first spine. Unlike the grid expands, the subtree grows ONE LEVEL AT A
        TIME (Y, then B, then BY & M, then MY), and the diagonal's decluttered hit-sibling
        LEAF TEXT is brought back as the big tree centres. Ends with 'Avg misses: 0' on M."""
        spine, _ = self._ymy_cell()
        spine.scale_to_fit_height(7.2).move_to([0.4, -0.1, 0])   # room for the left avg-0 label
        self.play(FadeOut(VGroup(*self.grid[1:])), run_time=run_time * 0.14)
        # the recapped hit-sibling leaf text RIDES the diagonal in (moving WITH the nodes):
        # start it at the source-diagonal-equivalent pose (small, where the depth-4 cell is),
        # transparent, then Restore to its target pose so it travels in with the centring.
        src_A, dst_A = self.grid[0].path.levels[0]["dot"], spine.path.levels[0]["dot"]
        o = dst_A.get_center()
        lt = spine.path.leaf_text
        lt.save_state()
        lt.scale(src_A.width / dst_A.width, about_point=o).shift(src_A.get_center() - o)
        lt.set_opacity(0)
        # phase 1: centre the diagonal + turn the U-miss leaf into Y (Y's letter rides in too)
        self._transform_move(self.grid[0], [spine], run_time * 0.44,
                             extra_anims=[Restore(lt)])
        # grow the Y-subtree ONE LEVEL AT A TIME (from Y, then B, then M)
        l1, l2, l3 = spine.sub.fan_levels
        self.play(GrowFromPoint(l1, spine.sub.gdot.get_center()), run_time=run_time * 0.11)
        self.play(GrowFromPoint(l2, spine.sub.bdot.get_center()), run_time=run_time * 0.11)
        self.play(GrowFromPoint(l3, spine.sub.mdot.get_center()), run_time=run_time * 0.10)
        # both determined leaves are done with 0 further misses: label M (left) AND BY (right)
        self.avg0 = self._avg_label(spine.mdot)
        self.avg0_by = self._avg_label(spine.sub.leaves["by"][0], direction=RIGHT)
        self.play(FadeIn(self.avg0), FadeIn(self.avg0_by), run_time=run_time * 0.10)
        self.clear()                                      # re-track clean groups (post copy-reveal)
        self.add(spine, self.avg0, self.avg0_by)
        self.grid = spine

    # ── h : we've SOLVED that position — turn the ACTUALLY-solved part GREEN. Only the
    #        M-down piece has a computed value (Avg misses: 0): the M node, the M→MY edge and
    #        the MY leaf. Green those + the '0' label; the rest of the tree (B, Y, the
    #        diagonal) stays white and greens as we back the value up in i/j. Greening a
    #        section DROPS its red miss tally. Guess-node letters stay knocked-out navy. ───
    @subscene
    def solve_base(self):
        sub = self.grid.sub
        my_dot, my_blk, my_tally = sub.leaves["my"]
        by_dot, by_blk, by_tally = sub.leaves["by"]
        # both done-with-0 leaves green (M node + M→MY edge + MY leaf; and the BY leaf), each
        # dropping its red miss tally; B, Y and the diagonal stay white until they back up
        green = VGroup(sub.discs["m"], sub.edges["mmy"], my_dot, my_blk, self.avg0,
                       by_dot, by_blk, self.avg0_by)
        self.play(green.animate.set_color(LIGHT_GREEN),
                  FadeOut(my_tally), FadeOut(by_tally), run_time=1.2)

    # ── i : back up the B node (the split guess at the {by,my} '_Y' position). Try each
    #        letter that could go there (B, M) with its optimal continuation + avg misses
    #        (both 0.5), then CHOOSE B — fill its subtree green, lock the value. Later beats
    #        do the other nodes (Y, then up the diagonal). ───────────────────────────────
    @subscene
    def backup_b(self):
        sub = self.grid.sub
        blab, mlab = sub.node_letters[1], sub.node_letters[2]
        _, by_blk, _ = sub.leaves["by"]
        _, my_blk, _ = sub.leaves["my"]
        b_val = f"{self._n_miss_node(5)['avg']:g}"        # 0.5 — sourced {by,my} position value
        # (a) back up B: label it with its value; drop the children's 'Avg misses: 0'
        self.avg_b = self._avg_label(sub.discs["b"], value=b_val, direction=LEFT)
        self.play(FadeIn(self.avg_b), FadeOut(self.avg0), FadeOut(self.avg0_by),
                  run_time=0.9)
        # (b) try the OTHER letter that could go in this node — M. Its optimal continuation
        # MIRRORS B's (M→MY hit / B→BY miss), same avg 0.5, descendants already green: swap
        # the labels in place (guess B↔M, and the BY/MY leaves swap branches).
        m_guess = mlab.copy().move_to(blab)               # "M" in the guess node
        m_miss = blab.copy().move_to(mlab)                # "B" in the miss node
        m_hit = my_blk.copy().move_to(by_blk)             # "MY" on the hit leaf (right)
        m_leaf = by_blk.copy().move_to(my_blk)            # "BY" on the miss leaf (below)
        b_parts, m_parts = VGroup(blab, mlab, by_blk, my_blk), VGroup(m_guess, m_miss, m_hit, m_leaf)
        self.play(FadeOut(b_parts), FadeIn(m_parts), run_time=0.7)
        self.wait(0.5)                                    # hold on the M option (also 0.5)
        # (c) CHOOSE B: swap back, then fill B and its subtree green, locking in the value
        self.play(FadeOut(m_parts), FadeIn(b_parts), run_time=0.7)
        self.remove(m_parts)
        green = VGroup(sub.discs["b"], sub.edges["bby"], sub.edges["bm"], self.avg_b)
        self.play(green.animate.set_color(LIGHT_GREEN), run_time=1.0)

    def _ctree(self, spec, root_miss=1):
        """A COMPLETE optimal subtree, fully played out. The SUBTREE is solved (GREEN), but
        the ROOT node and its OUTGOING edges keep their ORIGINAL colours (the candidate isn't
        chosen yet — the caller greens them on lock): root node = ``_miss_color(root_miss)``,
        its hit edge white / miss edge red. Recursive: a guess node (letter, knocked-out
        navy) with a HIT child (right) and, if it splits, a MISS child (left); a forced-hit
        guess has one child straight down; a leaf is the fully revealed word. Built at natural
        GRID sizes rooted at ORIGIN. spec = {'g', 'hit', 'miss'?} or {'leaf': word}."""
        r, cr = GRID_NODE_R, GRID_NODE_R * GRID_CHILD_RF
        DY, COL = GRID_CHILD_DY, GRID_CHILD_SPR   # COL = leaf column width
        g = VGroup()
        g.root_edges = VGroup()

        # pass 1 — TIDY layout: give every leaf its own column (miss subtree LEFT, hit RIGHT)
        # and centre each node over its children, so no two subtrees overlap however deep they
        # run. The old fixed ±SPR spread let a right subtree's left edge collide with a left
        # subtree's right edge (bit us on the Y candidate in choose_u); a per-leaf column can't.
        slot = [0]

        def kids_of(sp):
            """A node's children as [(is_miss, childspec), …], miss-first (LEFT). Accepts the
            N-ary {'g','kids':[(is_miss,spec),…]} form (a guess can hit at pos 1, pos 2, or
            both → several hit children) OR the binary {'g','hit','miss'?} form."""
            if "kids" in sp:
                return sp["kids"]
            ks = [(True, sp["miss"])] if "miss" in sp else []
            return ks + [(False, sp["hit"])]

        def layout(sp, depth):
            node = {"spec": sp, "y": -depth * DY}
            if "leaf" in sp:
                node["x"], node["kids"] = slot[0] * COL, []
                slot[0] += 1
                return node
            kids = [(is_miss, layout(cs, depth + 1)) for is_miss, cs in kids_of(sp)]
            node["kids"] = kids
            node["x"] = sum(k[1]["x"] for k in kids) / len(kids)  # centre over children
            return node

        root = layout(spec, 0)
        x0 = root["x"]                             # re-centre the whole tree on x = 0

        # pass 2 — build mobjects at the laid-out positions
        def build(node, is_root):
            pos = np.array([node["x"] - x0, node["y"], 0.0])
            sp = node["spec"]
            if "leaf" in sp:
                dot = Dot(pos, radius=cr, color=LIGHT_GREEN, z_index=2)
                blk = self._blanks(sp["leaf"]).set_x(pos[0]).set_color(LIGHT_GREEN)
                blk.shift([0, (pos[1] - GRID_BLANK_DROP) - blk.get_bottom()[1], 0])
                g.add(dot, blk)
                return dot, cr
            dot = Dot(pos, radius=r, color=_miss_color(root_miss) if is_root else LIGHT_GREEN,
                      z_index=2)
            lab = crisp_text(sp["g"].upper(), color=BOARD_NAVY, weight=BOLD)
            lab.scale_to_fit_height(NODE_LETTER_H * r).move_to(dot).set_z_index(3)
            g.add(dot, lab)
            for is_miss, child in node["kids"]:
                cdot, crad = build(child, False)
                miss = 1 if is_miss else 0
                ecolor = _miss_color(miss) if is_root else LIGHT_GREEN   # only root edges original
                dn = normalize(cdot.get_center() - pos)
                edge = Line(pos + dn * r, cdot.get_center() - dn * crad,
                            color=ecolor, stroke_width=2.0)
                g.add(edge)
                if is_root:
                    g.root_edges.add(edge)                # for the caller to green on lock
            return dot, r

        g.root = build(root, True)[0]
        return g

    def _subtree_spec(self, tree, revealed=""):
        """Convert a solver option-subtree (nested ``{guess, branches}`` / ``{word}`` from
        the tree2 cache) into a `_ctree` spec, APPENDING the forced-tail guesses that finish
        a determined word — the cache stops at determination, but a game keeps guessing every
        letter until the word is fully up (see hangman CLAUDE.md 'Game / guess-order'). So a
        `{word}` leaf becomes a chain of forced-hit guess nodes (its still-unrevealed letters,
        first-appearance order) ending in the bare won-leaf. ``revealed`` = the HIT letters
        guessed so far down this branch. Keeps every candidate subtree SOURCED (not
        hand-written). Emits the N-ary 'kids' form — a guess can split into several hit
        patterns (pos 1 / pos 2 / both) plus the '__' miss (e.g. E on {…} gives e_, _e, __)."""
        if "word" in tree:
            word = tree["word"]
            remaining = []
            for ch in word:
                if ch not in revealed and ch not in remaining:
                    remaining.append(ch)
            spec = {"leaf": word}
            for ch in reversed(remaining):
                spec = {"g": ch, "hit": spec}
            return spec
        g = tree["guess"]
        br = tree["branches"]
        # every branch becomes a child: the all-'_' branch is the MISS (letter absent → left);
        # any other pattern is a HIT (letter present). Length-2 lets a letter hit at pos 1,
        # pos 2, or both, so a node can have SEVERAL hit children — hence the N-ary 'kids' form
        # (a HIT reveals g; a miss reveals nothing). Order miss-first so it stays on the left.
        items = sorted(br.items(), key=lambda kv: 0 if set(kv[0]) == {"_"} else 1)
        kids = [(set(pat) == {"_"},
                 self._subtree_spec(child, revealed if set(pat) == {"_"} else revealed + g))
                for pat, child in items]
        return {"g": g, "kids": kids}

    def _counter_label(self, tracker, node_dot, direction=LEFT, height=0.34):
        """A live 'Avg misses: N.N' label whose number ROLLS with ``tracker`` — the
        candidate-cycle counter (stays on screen, counting as the value changes, rather than
        flashing a fresh label per candidate). Same look as `_avg_label`, animated. The whole
        string is ONE mobject rebuilt on each 1-decimal tick (constant width → re-renders
        centred in place). Numbers ROUND HALF UP (1.25 → 1.3), not Python's default
        round-half-to-even. The caller removes ``lab._upd`` before greening/locking it."""
        def fmt(v):
            return f"{int(v * 10 + 0.5) / 10:.1f}"      # round half up (values are positive)

        def mk(v, color):
            return crisp_text(f"Avg misses: {fmt(v)}", font_size=12, color=color, weight=BOLD)
        lab = mk(tracker.get_value(), WHITE)
        lab.scale_to_fit_height(height).next_to(node_dot, direction, buff=height * 0.6)
        center, h = lab.get_center(), lab.height
        st = {"s": fmt(tracker.get_value()), "color": WHITE}

        def upd(m):
            s = fmt(tracker.get_value())
            if s == st["s"]:
                return
            st["s"] = s
            m.become(mk(float(s), st["color"]).scale_to_fit_height(h).move_to(center))

        lab.add_updater(upd)
        lab._upd = upd
        return lab

    # ── j : back up the Y node (the {by,my} position). B's value fades out; a fresh WHITE
    #        value appears next to Y. The first guess then cycles Y → B → M, each shown as its
    #        COMPLETE optimal subtree (fully played out, all green) with its own avg misses;
    #        then CHOOSE Y and lock the value green. ────────────────────────────────────────
    @subscene
    def backup_y(self):
        sub = self.grid.sub
        scale = sub.gdot.width / (2 * GRID_NODE_R)        # match the (fit-scaled) spine nodes
        anchor = sub.gdot.get_center()
        by_dot, by_blk, _ = sub.leaves["by"]
        my_dot, my_blk, _ = sub.leaves["my"]
        # the Y-first spine subtree WITHOUT the leaf tallies (dropped in h) — this IS the Y
        # candidate; fade it out/in as we compare, so its handles survive for later beats
        cur = VGroup(sub.gdot, sub.glab, sub.edges["yb"],
                     sub.discs["b"], sub.node_letters[1], sub.edges["bby"], by_dot, by_blk,
                     sub.edges["bm"], sub.discs["m"], sub.node_letters[2],
                     sub.edges["mmy"], my_dot, my_blk)
        # 1) B's value goes away; a FRESH white value appears next to Y (this position, being
        #    computed — not the same as B's, just coincidentally equal)
        avg_y = self._avg_label(sub.discs["y"], value="0.5", direction=LEFT)   # white
        self.play(FadeOut(self.avg_b), run_time=0.4)
        self.play(FadeIn(avg_y), run_time=0.4)
        self.avg_b = avg_y
        # 2) cycle Y → B → M, each a COMPLETE green subtree. The avg-misses value STAYS on
        #    screen (no flashing) and will roll via a counter where candidates differ; here
        #    all three are 0.5, so it just reads 0.5 throughout.
        BY, MY = {"leaf": "by"}, {"leaf": "my"}
        specs = {
            "b": {"g": "b", "hit": {"g": "y", "hit": BY},
                  "miss": {"g": "m", "hit": {"g": "y", "hit": MY}}},
            "m": {"g": "m", "hit": {"g": "y", "hit": MY},
                  "miss": {"g": "b", "hit": {"g": "y", "hit": BY}}},
        }

        def ctree(letter):
            ct = self._ctree(specs[letter])
            ct.scale(scale, about_point=ORIGIN).shift(anchor)
            return ct

        b_ct, m_ct = ctree("b"), ctree("m")

        def swap_to(tree):                                # swap the subtree; value stays put
            self.play(FadeOut(self._active), FadeIn(tree), run_time=0.6)
            self.wait(0.3)
            self._active = tree

        self._active = cur
        swap_to(b_ct)
        swap_to(m_ct)
        swap_to(cur)                                      # settle back on Y
        self.remove(b_ct, m_ct)
        # 3) choose Y: lock it — Y node + edge + value turn green
        self.play(VGroup(sub.discs["y"], sub.edges["yb"], avg_y).animate.set_color(LIGHT_GREEN),
                  run_time=0.9)

    # ── (next) : back up the U position. FIRST solve U's OTHER child {up,us}: shrink the
    #        solved Y subtree toward U to make room while {up,us} expands into its own
    #        subtree. (Rough first pass — layout only, candidate cycle + counter to follow.)
    @subscene
    def backup_u(self):
        path = self.grid.path
        sub = self.grid.sub
        u_dot = path.levels[4]["dot"]
        uc, ur = u_dot.get_center(), u_dot.width / 2      # U centre + radius
        scale = sub.gdot.width / (2 * GRID_NODE_R)
        yr = GRID_NODE_R * scale * 0.55                   # child-root radius after the shrink
        DY_U, SPREAD = 1.0, 1.3                           # spread U's two children apart (a bit)
        y_root = uc + np.array([-SPREAD, -DY_U, 0.0])     # Y (miss) LEFT
        ups_root = uc + np.array([SPREAD, -DY_U, 0.0])    # {up,us} (hit) RIGHT
        g0 = sub.gdot.get_center()
        # {up,us} subtree (P-first): P → {UP hit, S→US miss}; reached via U-HIT → white root
        spec = {"g": "p", "hit": {"leaf": "up"}, "miss": {"g": "s", "hit": {"leaf": "us"}}}
        ups = self._ctree(spec, root_miss=0).scale(scale * 0.55, about_point=ORIGIN)
        ups.shift(ups_root)
        # new full-length edges out of U (NOT shrunk): U→Y miss (red), U→{up,us} hit (white)
        dny, dnu = normalize(y_root - uc), normalize(ups_root - uc)
        yedge = Line(uc + dny * ur, y_root - dny * yr, color=_miss_color(1), stroke_width=2.0)
        uedge = Line(uc + dnu * ur, ups_root - dnu * yr, color=_miss_color(0), stroke_width=2.0)
        by_dot, by_blk, _ = sub.leaves["by"]
        my_dot, my_blk, _ = sub.leaves["my"]
        # scale ONLY the visible spine parts — NOT the whole `sub` (which still nests the
        # hidden-in-h leaf tallies; scaling the group resurrects them). Tallies stay put,
        # hidden, and never reappear.
        y_vis = VGroup(sub.gdot, sub.glab, sub.edges["yb"], sub.discs["b"],
                       sub.node_letters[1], sub.edges["bby"], by_dot, by_blk,
                       sub.edges["bm"], sub.discs["m"], sub.node_letters[2],
                       sub.edges["mmy"], my_dot, my_blk)
        # shrink Y's subtree about ITS OWN root (edge kept full), slide Y to the spread pos,
        # redraw both edges out of U, grow {up,us}, fade the old 'U_' leaf, DROP the {by,my}
        # value on Y
        self.play(y_vis.animate.scale(0.55, about_point=g0).shift(y_root - g0),
                  FadeOut(self.avg_b),
                  Transform(self.grid.drilled_edge, yedge),          # U→Y (redrawn full)
                  Transform(path.levels[4]["hits"][0][0], uedge),    # old 'U_' edge → U→{up,us}
                  FadeOut(path.levels[4]["hits"][0][1]),             # old bare 'U_' dot
                  FadeOut(path.leaf_text[-1]),                       # old 'U_ AOIE' annotation
                  GrowFromPoint(ups, uc),
                  run_time=1.3)
        # the {up,us} value now sits on P (white — being computed)
        self.avg_p = self._avg_label(ups.root, value="0.5", direction=RIGHT)
        self.play(FadeIn(self.avg_p), run_time=0.4)
        self.ups = ups

    # ── (next) : solve U's other child {up,us} — cycle its candidates P and S (mirror
    #        complete green subtrees, both 0.5), then CHOOSE P and lock it green. ───────────
    @subscene
    def solve_ups(self):
        ups = self.ups
        s_scale = ups.root.width / (2 * GRID_NODE_R)      # match the on-screen {up,us} tree
        # the S candidate (mirror of P): S → {US hit, P→UP miss}
        spec_s = {"g": "s", "hit": {"leaf": "us"}, "miss": {"g": "p", "hit": {"leaf": "up"}}}
        s_ct = self._ctree(spec_s, root_miss=0).scale(s_scale, about_point=ORIGIN)
        s_ct.shift(ups.root.get_center())
        # cycle P (current) → S → P (the value stays put)
        self.play(FadeOut(ups), FadeIn(s_ct), run_time=0.6)
        self.wait(0.4)
        self.play(FadeOut(s_ct), FadeIn(ups), run_time=0.6)
        self.remove(s_ct)
        # choose P: green its root + outgoing edges (subtree already green) and lock the value
        self.play(VGroup(ups.root, ups.root_edges, self.avg_p).animate.set_color(LIGHT_GREEN),
                  run_time=0.9)

    # ── m : back up the U position ({by,my,up,us}) — both children are solved. The hand-built
    #        subtree first REFORMATS into the uniform tidy auto-layout (fade old→new), so the U
    #        candidate matches the alternatives; the child value goes away and a rolling 'Avg
    #        misses' COUNTER appears on U. Cycle the first-guess candidates U/Y/B/M/P/S, each a
    #        COMPLETE optimal subtree (green subtree, original-colour root — every candidate a
    #        TIDY _ctree, SOURCED from the cache): U/Y = 1.0, B/M/P/S = 1.25, the counter rolling
    #        as we pass each. Then CHOOSE U (the min) and lock its node + edges + value green. ──
    @subscene
    def choose_u(self):
        path, sub, ups = self.grid.path, self.grid.sub, self.ups
        u_dot, u_lab = path.levels[4]["dot"], path.levels[4]["lab"]
        uc = u_dot.get_center()
        yedge = self.grid.drilled_edge            # U→Y   (miss, red)
        uedge = path.levels[4]["hits"][0][0]      # U→{up,us} (hit, white)
        by_dot, by_blk, _ = sub.leaves["by"]
        my_dot, my_blk, _ = sub.leaves["my"]
        y_sub = VGroup(sub.gdot, sub.glab, sub.edges["yb"], sub.discs["b"],
                       sub.node_letters[1], sub.edges["bby"], by_dot, by_blk,
                       sub.edges["bm"], sub.discs["m"], sub.node_letters[2],
                       sub.edges["mmy"], my_dot, my_blk)
        old_u = VGroup(u_dot, u_lab, yedge, uedge, y_sub, ups)   # hand-built subtree, retired
        # every first-guess candidate at {by,my,up,us} as a TIDY _ctree — ONE builder + ONE
        # scale, so the U candidate matches the alternatives (and E/I/O/A later). SOURCED from
        # the cache; the U candidate keeps the Y-first {by,my} spine chosen for the base case.
        node = self._n_miss_node(4)
        opts = {o["letter"]: o for o in node["options"] if o["splits"]}
        specs = {"u": {"g": "u",
                       "hit": self._subtree_spec(opts["u"]["subtree"]["branches"]["u_"], "u"),
                       "miss": {"g": "y", "hit": {"g": "b", "hit": {"leaf": "by"},
                                                   "miss": {"g": "m", "hit": {"leaf": "my"}}}}}}
        for c in ("y", "b", "m", "p", "s"):
            specs[c] = self._subtree_spec(opts[c]["subtree"])
        raws = {c: self._ctree(sp, root_miss=1) for c, sp in specs.items()}
        scale_c = (uc[1] + 4.0) / max(ct.height for ct in raws.values())   # fit deepest below U
        cand = {}
        for c, ct in raws.items():
            ct.scale(scale_c, about_point=ORIGIN).shift(uc - ct.root.get_center())   # root at U
            cand[c] = ct
        tidy_u = cand["u"]
        u_avg = opts["u"]["avg"]                    # 1.0 (== node['avg'])
        uval = ValueTracker(u_avg)
        counter = self._counter_label(uval, tidy_u.root, direction=LEFT)
        # reformat: the hand-built subtree tidies into the uniform auto-layout; the child value
        # goes away; the rolling counter appears on U (we start ON the U candidate)
        self.play(FadeOut(old_u), FadeIn(tidy_u), FadeOut(self.avg_p), FadeIn(counter),
                  run_time=0.8)
        self.avg_p = None
        self._active = tidy_u
        self.wait(0.4)                             # hold on the U candidate before cycling

        def swap_to(tree, val):                    # cross-fade the subtree; counter rolls
            self.play(FadeOut(self._active), FadeIn(tree),
                      uval.animate.set_value(val), run_time=0.7)
            self.wait(0.3)
            self._active = tree

        for c in ("y", "b", "m", "p", "s"):        # U → Y → B → M → P → S
            swap_to(cand[c], opts[c]["avg"])
        swap_to(tidy_u, u_avg)                      # settle back on U (the minimum, 1.0)
        self.remove(*(cand[c] for c in ("y", "b", "m", "p", "s")))
        # choose U: freeze the counter (drop the updater + its closure attr so the scene can
        # still pickle), then lock U's node + both outgoing edges + the value green
        counter.remove_updater(counter._upd)
        del counter._upd
        self.play(VGroup(tidy_u.root, tidy_u.root_edges, counter).animate.set_color(LIGHT_GREEN),
                  run_time=1.0)
        self.u_subtree = tidy_u                     # hand off U's solved subtree to backing up E
        self.ups = None

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
