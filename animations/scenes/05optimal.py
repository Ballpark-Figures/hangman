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

Script row 05, split on '—' (voiceover ↔ animation zip 1:1) — 13 beats a–m. Each @subscene is
ONE script beat; the two back-up beats (h, i) unroll several sub-steps in-body (plain `_`-prefixed
helpers, called in order — NOT separate subscenes). BEAT MAP:
  a greedy_chart  — recap: greedy avg misses by word length (the scene-04 chart)
  b root_node     — one decision node appears centre (the top of the tree)
  c cycle_letters — cycle every letter A–Z through the node (which opener is best?)
  d grid_spread   — 20 openers into a 4×5 grid; each sprouts its next level (blanks + miss)
  e a_dive        — bring A to centre; walk-highlight children (gold); grid A-miss's options
  f drill         — keep drilling the top-left all-miss leaf down the diagonal (4×4 → 3×4 → 2×3)
                    to the {BY,MY} base; the forced Y resolves into the Y-first spine, 'Avg
                    misses: 0' on M. Sub-step: _resolve (the tail of the drill)
  g solve_base    — we've solved that position: green ONLY the computed part (M→MY, avg 0)
  h backup_b      — back up ONE level (the base leaves up to U): green B (0.5), the Y position
                    (0.5), solve U's other child {up,us} (0.5), then choose U (1.0). Sub-steps:
                    _backup_y / _backup_u / _solve_ups / _choose_u
  i backup_e      — REPEAT the back-up up the tree until the WHOLE tree is green: E (2.00), then
                    I (2.57), then O (3.28), then add A's hit branches (O's siblings). Sub-steps:
                    _solve_e_hit / _choose_e / _backup_i / _solve_i_hit / _choose_i / _backup_o /
                    _solve_o_hit / _choose_o / _backup_a / _solve_a_hit
  j compare_openers — collapse the solved A-tree into the top-left grid corner (strip every letter
                    but the root A, colours back to red-white), fill the rest of the grid with each
                    valid opener's optimal tree (red-white shape, root lettered, 'Avg misses: N.NN'
                    above), GREEN the winner (A = 3.88 min), fade the rest, and grow the green tree
                    back to full screen with its letters + solved colours restored
  k dedup         — DEDUP: two parallel miss-DIAGONAL trees (miss=LEFT child, down-left; LEFT A→O,
                    RIGHT O→A), each guess node fanning its hit branches as BARE dots down-right,
                    ending in a bare position node with '_ _' + misses below; same position → solve once
  l bad_guess     — a BAD guess that can only miss: after a successful A gives '_A' (A in pos 2),
                    guessing U (can't be in any '_A' word) yields a SINGLE miss branch (straight down);
                    show ALL of A's branches, each with its board (SOURCED: U splits=False at _a)
  m paired_chart  — the PAIRED greedy-vs-optimal avg-misses-by-length chart: greedy (left) vs optimal
                    (right); unsolved lengths RED to the lower bound + a lighter band up to the upper
                    (grouped_bar_chart + series_highlight/bands). Every value SOURCED. [LAST beat]

BACK-UP BEAT RECIPE (the E→I→O→A back-ups inside beat i REPEAT this — reuse, don't reinvent; the
sub-steps _backup_u/_solve_ups/_choose_u (beat h) and _backup_e/_solve_e_hit/_choose_e (beat i) are
the worked examples, each level is 3 sub-steps):
  1. backup_X  — build X's tidy subtree as ONE _ctree(tall_level=0); SLIDE the already-solved
     child (the green subtree from below) rigidly onto its slot; REUSE X's bare diagonal hit-dots
     as the other children's roots and REVEAL them with the drill's ride-in (letter starts small+
     transparent AT the bare dot, Restore → rides in; children sprout after — the `_transform_move`
     technique, NOT a fade-in at the destination).
  2. solve_X_hit — solve X's OTHER child(ren): for each, show its number, cycle through ALL the
     tied first-guesses (the user means ALL), settle on the optimal, lock root+edges green.
  3. choose_X  — back up X: roll a counter through ALL of X's candidate first-guesses, choose the
     min, lock node+all-edges+value green.
  TALL GAP follows the VALUE: the tall (GRID_ROOT_DY) edges always lead DOWN INTO the level that
  currently shows the avg-miss number; it CLIMBS one level each back-up via `_gap_up` (the just-
  valued node drops toward its fixed children — in-edge lengthens, out-edges compact). SIBLINGS
  move together: `_gap_up(siblings=…)` drops the parent's OTHER children the same delta so a
  level never splits. Do the climb at the START of the beat that deals with the node (choose_X),
  the new number FADING IN travelling WITH the node; only ONE number on screen at a time.
  NUMBERS: every value routes through `_fmt` (2 dp, half-up) + `_value_label` — worded
  'Avg misses: N.NN' through beats g/h (base + first back-up), then a BARE just-the-number from the
  E-hit solve onward (`_solve_e_hit`, same digit size). Never format at the call site; pass the raw
  SOURCED float.

Render:  render 05a --fast  (…05c)   /   render 05 sub  for the whole scene

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every fade/grow
run_time; the letter-cycle per-step run_time (0.09).
"""
from pathlib import Path
from types import SimpleNamespace
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from bpkfigures.bar_graph import get_bar_chart, grouped_bar_chart, grow_bars
from bpkfigures.chalkboard import CHALK, BOARD_NAVY
from assets import tree2_data
from assets import greedy_data
from assets import scene17_chart_data

DATA = tree2_data.get()
GDATA = greedy_data.get()
ODATA = scene17_chart_data.get()   # optimal avg-misses by length (uniform): {avg, lower, upper, converged}

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
GRID_CHILD_DY    = 0.55   # parent → child vertical drop (natural units, deeper levels)
GRID_ROOT_DY     = 1.00   # TALLER first level for the TRUE ROOT of a backed-up tree that must clear
                          # the drilled-past diagonal's hit-sibling text (E and higher). Passed as
                          # _ctree(root_dy=GRID_ROOT_DY) ONLY there; sub-pieces + reused subtrees keep
                          # the compact GRID_CHILD_DY, so only the top junction is tall (no stacking).
GRID_CHILD_SPR   = 0.72   # child horizontal half-spread (blanks sit under each child)
GRID_BLANK_H     = 0.13   # blank-row height under a child (rule + revealed letter)
GRID_BLANK_DROP  = 0.36   # child centre → blank RULE baseline (fixed → rules line up AND
                          # the written letter above the rule clears the child dot)
GRID_MISS_H      = GRID_BLANK_H    # missed letter (red) — SAME size as the blank letters
# the recapped hit-sibling LEAF TEXT on the shrunk diagonal (beat f's final drill tree)
GRID_LEAF_H      = GRID_BLANK_H * 1.22
GRID_LEAF_DROP   = 0.36            # child centre → its blank baseline
GRID_W, GRID_H   = 15.6, 8.0       # the cells tile this box (full width, small top/bottom margin)
GRID_CENTER      = [0, 0, 0]
PATH_SCALE       = 0.5     # the drilled-past path (A→O→…) is shrunk vs the active subtree
# the diagonal takes a TALLER vertical step than a normal parent→child drop, so each
# guess node has room BELOW it for its hit-siblings' recapped leaf text (avoids the packed
# rows colliding). Only the drilled-past diagonal uses this; grafted subtrees use CHILD_DY.
PATH_DY          = GRID_CHILD_DY * 1.55

# ── avg-miss value labels + per-beat sizing (see _fmt / _value_label) ────────────
# MODULE-level (not class attrs) so the snapshot digest captures their VALUE → tuning them
# invalidates correctly. A bare number is built at a FIXED font size for a target cap-height
# (never scaled to fit its own box) and anchored by its DECIMAL POINT — so digit composition
# can't change its size and it doesn't lurch as it rolls.
VALUE_CAP_H      = 0.26   # bare-number digit cap-height (a FIXED world size → consistent throughout)
WORDED_H         = 0.34   # worded 'Avg misses: N.NN' box height (the static g/h beats)
CYCLE_MAX        = 3      # a root-back-up cycle shows at most this many DISTINCT letters (chosen + others)
OPENER_ROOT_BIG  = 4.5    # beat j: grid-cell ROOT node enlarged so its starting letter reads as a header
OPENER_LABEL_H   = 0.32   # beat j: grid-cell 'Avg misses: N.NN' height — FIXED on-screen size (not tiled)
DEDUP_NODE_R     = 0.42   # beat k: dedup miss-diagonal node radius


class Scene05(HangmanScene):
    """Optimal strategy as a search on the length-2 tree.

    13 script beats a–m (one @subscene each) — see the module docstring's BEAT MAP for the full
    walk. The two back-up beats unroll several sub-steps in-body via plain `_`-prefixed helpers:
      f drill        — drill to the {BY,MY} base (+ _resolve)
      h backup_b     — back up ONE level, base → U (+ _backup_y/_backup_u/_solve_ups/_choose_u)
      i backup_e     — repeat up the tree to the whole green tree (+ _solve_e_hit/_choose_e/
                       _backup_i/_solve_i_hit/_choose_i/_backup_o/_solve_o_hit/_choose_o/
                       _backup_a/_solve_a_hit)
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
        path, anchor, last_dot = self._path_diag(5, leaf_text=True)   # + hit-sibling blanks

        # the {by,my} base case as a TIDY _ctree (UNSOLVED colours — per-miss, greened later),
        # rooted at the U-miss anchor: Y (forced hit on both) → B splits → {BY, M → MY}. This
        # is the SAME tidy builder every candidate uses, so the persistent tree and the
        # candidates match exactly (no wider hand-built spacing).
        spec = {"g": "y", "key": "y",
                "hit": {"g": "b", "key": "b",
                        "hit": {"leaf": "by", "key": "by"},
                        "miss": {"g": "m", "key": "m", "hit": {"leaf": "my", "key": "my"}}}}
        # at g/h the avg-miss value sits on the BASE LEAVES (M=0, BY=0), so the tall edges are the
        # ones INTO that level — out of B (depth 1). backup_b/backup_y climb the gap up as the value
        # backs up (B→leaves → Y→B → U→Y).
        sub = self._ctree(spec, root_miss=1, solved=False, tall_level=1)
        sub.shift(anchor - sub.root.get_center())          # Y (root) sits at the anchor
        dn = normalize(anchor - last_dot.get_center())
        drilled_edge = Line(last_dot.get_center() + dn * (r * PATH_SCALE),
                            anchor - dn * r, color=_miss_color(1), stroke_width=2.0)

        ny, nb, nm = sub.node["y"], sub.node["b"], sub.node["m"]
        lby, lmy = sub.leaf["by"], sub.leaf["my"]
        # _transform_move / grow handles (Y arrives via the transform; the fan grows after)
        sub.gdot, sub.glab, sub.bdot, sub.mdot = ny.dot, ny.lab, nb.dot, nm.dot
        l1 = VGroup(nb.in_edge, nb.dot, nb.lab)                   # Y→B
        l2 = VGroup(lby.in_edge, lby.dot, lby.blk, nm.in_edge, nm.dot, nm.lab)   # B→BY, B→M
        l3 = VGroup(lmy.in_edge, lmy.dot, lmy.blk)               # M→MY
        sub.fan = VGroup(l1, l2, l3)
        sub.fan_levels = [l1, l2, l3]
        # granular handles for the DP back-up (green one section at a time). Leaves carry NO
        # miss tally now (the diagonal shows the misses) → the tally slot is None.
        sub.discs = {"y": ny.dot, "b": nb.dot, "m": nm.dot}
        sub.edges = {"yb": nb.in_edge, "bby": lby.in_edge, "bm": nm.in_edge, "mmy": lmy.in_edge}
        sub.leaves = {"by": (lby.dot, lby.blk, None), "my": (lmy.dot, lmy.blk, None)}
        sub.node_letters = VGroup(ny.lab, nb.lab, nm.lab)
        cell = VGroup(path, drilled_edge, sub)
        cell.path, cell.drilled_edge, cell.sub, cell.mdot = path, drilled_edge, sub, nm.dot
        return cell, nm.dot

    # ── ONE place that formats + builds every avg-miss value on screen (see _fmt / _value_label).
    #    _avg_label (static) and _counter_label (rolling) both route through them, so "2 dp",
    #    "round half up", the bare-vs-worded look, and the shared glyph size live in exactly one
    #    spot each — change the convention once, everywhere follows.
    @staticmethod
    def _fmt(v):
        """The canonical avg-miss value string: 2 decimals, rounded HALF UP (1.245 → 1.25)."""
        return f"{int(v * 100 + 0.5) / 100:.2f}"

    # tunable sizing constants (VALUE_CAP_H / WORDED_H / … / DEDUP_NODE_R) live at MODULE level so the
    # snapshot digest captures their VALUE (tuning them invalidates); a self.-read CLASS attr would NOT
    # be captured. Only the runtime CACHE below stays a class attr (read via self._NUM_REF, never
    # Scene05._NUM_REF — naming the class would make the digest hash the whole class source).
    _NUM_REF = {}          # cached height->font_size reference + decimal-point offsets (runtime cache)

    # NB the cache is read via ``self._NUM_REF``, NOT ``Scene05._NUM_REF``: naming the CLASS in a
    # method makes the snapshot-digest machinery hash the WHOLE class source, so every avg-number beat
    # (g onward) would be invalidated by an edit to ANY method. ``self._NUM_REF`` is the same shared
    # class dict (item-assignment mutates it) but references only an attribute name, not the class.
    def _num_font(self, cap_h):
        """The font_size whose digit cap-height is ``cap_h``, from a cached reference '0'. A number's
        size then comes ONLY from ``cap_h`` (never from measuring its own glyphs)."""
        ref = self._NUM_REF.get("h0")
        if ref is None:
            ref = crisp_text("0", font_size=24, weight=BOLD).height
            self._NUM_REF["h0"] = ref
        return 24 * cap_h / ref

    def _num_dot_offsets(self):
        """(left-edge→'.', '.'→right-edge) of a reference 'N.NN' PER UNIT cap-height (they scale with
        the number's size). Cached — pins a rolling number by its decimal point instead of its box."""
        o = self._NUM_REF.get("dot")
        if o is None:
            ref = crisp_text("0.00", font_size=self._num_font(1.0), weight=BOLD)
            o = (ref[1].get_center()[0] - ref.get_left()[0],
                 ref.get_right()[0] - ref[1].get_center()[0])
            self._NUM_REF["dot"] = o
        return o

    def _place_value(self, lab, node_dot, direction, gap, cap_h):
        """Anchor a bare 'N.NN' number beside ``node_dot`` by its DECIMAL POINT (glyph index 1 — every
        value here is < 10) so it doesn't shift as the digits change; y-centred on the node, hugging
        its left/right edge via the reference decimal offsets. If the requested side would run the
        number off the frame (e.g. A's rightmost hit child sits at the edge), FLIP to the inner side.
        Returns ``lab``."""
        left_to_dot, dot_to_right = (x * cap_h for x in self._num_dot_offsets())
        fx = config.frame_x_radius - 0.15
        if np.array_equal(direction, RIGHT) and \
                node_dot.get_right()[0] + gap + left_to_dot + dot_to_right > fx:
            direction = LEFT                                    # would spill right → put it on the left
        elif np.array_equal(direction, LEFT) and \
                node_dot.get_left()[0] - gap - dot_to_right - left_to_dot < -fx:
            direction = RIGHT                                   # would spill left → put it on the right
        y = node_dot.get_center()[1]
        if np.array_equal(direction, LEFT):
            dot_x = node_dot.get_left()[0] - gap - dot_to_right
        else:
            dot_x = node_dot.get_right()[0] + gap + left_to_dot
        return lab.shift([dot_x - lab[1].get_center()[0], y - lab.get_center()[1], 0])

    def _value_label(self, v, height, bare=False, color=WHITE):
        """The avg value at ``height``: a worded 'Avg misses: N.NN' scaled-to-fit (early, static
        beats), or a BARE number built at a FIXED font size for digit cap-height ``height`` (scene o
        on) — NOT scaled to fit its own box, so digit composition can't change its size. crisp_text
        supersamples to a 240pt cap; the worded phrase is built small to avoid a wrap."""
        if not bare:
            # build at a LOW font_size (→ low underlying supersample pt) so pango never wraps the
            # phrase to 2 lines — at font_size=12 (120pt underlying) most of the grid's labels
            # wrapped, rendering tiny; scale_to_fit_height gives the same final size either way.
            full = crisp_text(f"Avg misses: {self._fmt(v)}", font_size=6, color=color, weight=BOLD)
            return full.scale_to_fit_height(height)
        return crisp_text(self._fmt(v), font_size=self._num_font(height), color=color, weight=BOLD)

    def _avg_label(self, node_dot, value=0.0, direction=LEFT, bare=False):
        """A node's backed-up optimal value beside it — ``value`` is the raw SOURCED number. Beats
        g–n label it worded 'Avg misses: N.NN' (fixed size); from scene o on a bare number sized to
        the node and decimal-anchored so it stays steady."""
        if not bare:
            return self._value_label(value, WORDED_H, False).next_to(
                node_dot, direction, buff=WORDED_H * 0.6)
        cap = VALUE_CAP_H
        return self._place_value(self._value_label(value, cap, True), node_dot, direction, cap * 0.9, cap)

    # ── f : keep drilling ("repeat above process"). Expand the top-left (greedy pick O)
    #        tree's all-miss leaf into the next grid (depth 2, greedy-sorted, drill the
    #        top-left again), and REPEAT down the all-miss diagonal until the surviving set
    #        is {BY, MY} — where the forced Y resolves into the Y-first spine and 'Avg
    #        misses: 0' drops on the forced M. (Absorbs the old drill + resolve steps.) ───
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
        self._resolve()                                   # keep drilling to the {BY,MY} base

    # ── g : keep drilling to the BASE CASE. Repeat f's expand (fade all but the top-left,
    #        transform its all-miss leaf into the next option grid) down the all-miss
    #        diagonal — depth 2 → 3 (after A,O,I) → 4 (after A,O,I,E) — until the surviving
    #        set is {BY, MY}. There we play the forced Y (guaranteed hit both) and resolve
    #        into the Y-first spine, dropping 'Avg misses: 0' on the forced M after the
    #        B-miss (the recursion base case we back up from in h). "Leaf" = the FINAL
    #        GUESS — see hangman CLAUDE.md. (Sub-step of beat f — the tail of the drill.) ─
    def _resolve(self):
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

    # ── g : we've SOLVED that position — turn the ACTUALLY-solved part GREEN. Only the
    #        M-down piece has a computed value (Avg misses: 0): the M node, the M→MY edge and
    #        the MY leaf. Green those + the '0' label; the rest of the tree (B, Y, the
    #        diagonal) stays white and greens as we back the value up in i/j. Greening a
    #        section DROPS its red miss tally. Guess-node letters stay knocked-out navy. ───
    @subscene
    def solve_base(self):
        sub = self.grid.sub
        my_dot, my_blk, _ = sub.leaves["my"]
        by_dot, by_blk, _ = sub.leaves["by"]
        # both done-with-0 leaves green (M node + M→MY edge + MY leaf; and the BY leaf); B, Y
        # and the diagonal stay white until they back up (the misses live on the red diagonal)
        green = VGroup(sub.discs["m"], sub.edges["mmy"], my_dot, my_blk, self.avg0,
                       by_dot, by_blk, self.avg0_by)
        self.play(green.animate.set_color(LIGHT_GREEN), run_time=1.2)

    # ── h : back up ONE level — from the solved base leaves up to the U node. Go through
    #        every node at that level, cycling each choice's optimal subtree, settling on the
    #        min, and turning it green: back up B (0.5), then the Y position (0.5), then solve
    #        U's other child {up,us} (0.5), then choose U (1.0). (Absorbs old backup_b /
    #        backup_y / backup_u / solve_ups / choose_u.) ───────────────────────────────────
    @subscene
    def backup_b(self):
        sub = self.grid.sub
        blab, mlab = sub.node_letters[1], sub.node_letters[2]
        by_dot, by_blk, _ = sub.leaves["by"]
        _, my_blk, _ = sub.leaves["my"]
        b_val = self._n_miss_node(5)["avg"]               # 0.5 — sourced {by,my} position value
        # (a) back up B: the value now sits on B, so the tall gap CLIMBS from B→leaves up to Y→B —
        #     B drops toward its children, its '0.5' fades in travelling WITH it, the base-leaf '0's
        #     fade out (all one motion).
        self.avg_b = self._avg_label(sub.discs["b"], value=b_val, direction=LEFT)
        self._gap_up(sub.discs["b"], sub.node_letters[1], sub.gdot, sub.edges["yb"],
                     [(sub.edges["bby"], by_dot), (sub.edges["bm"], sub.discs["m"])],
                     run_time=0.9, fade_in=[self.avg_b], fade_out=[self.avg0, self.avg0_by])
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
        # the rest of the first-level back-up (Y position, {up,us}, then choose U)
        self._backup_y()
        self._backup_u()
        self._solve_ups()
        self._choose_u()

    def _ctree(self, spec, root_miss=1, solved=True, tall_level=None):
        """A COMPLETE optimal subtree, fully played out. In SOLVED mode (default — a candidate)
        the SUBTREE is GREEN, but the ROOT node and its OUTGOING edges keep their ORIGINAL
        colours (the candidate isn't chosen yet — the caller greens them on lock): root node =
        ``_miss_color(root_miss)``, its hit edge white / miss edge red. In UNSOLVED mode
        (``solved=False`` — the persistent tree being worked) EVERY node/edge is coloured by how
        it's reached (miss = red, hit = white), like the diagonal, and the back-up beats green
        it piece by piece. Recursive: a guess node (letter, knocked-out
        navy) with a HIT child (right) and, if it splits, a MISS child (left); a forced-hit
        guess has one child straight down; a leaf is the fully revealed word. Built at natural
        GRID sizes rooted at ORIGIN. spec = {'g', 'hit', 'miss'?} (binary), {'g', 'kids':
        [(is_miss, spec), …]} (N-ary), or {'leaf': word}; any node may carry a 'key' →
        addressable later via g.node[key] / g.leaf[key] (each a handle: .dot, .lab/.blk,
        .in_edge, .out_edges, .kids, .all). g.root / g.root_edges / g.root_h expose the root."""
        r, cr = GRID_NODE_R, GRID_NODE_R * GRID_CHILD_RF
        DY, COL = GRID_CHILD_DY, GRID_CHILD_SPR   # COL = leaf column width
        # y by depth: every level drops by the compact DY, EXCEPT the ONE edge OUT OF depth
        # ``tall_level`` (down into the level currently showing the backed-up avg-miss value),
        # which drops by GRID_ROOT_DY — the tall gap. tall_level=None → fully compact. The tall gap
        # climbs one level each back-up beat (a `_gap_up` reflow), so only ONE junction is ever tall.
        extra = GRID_ROOT_DY - DY
        y_of = lambda d: -(d * DY + (extra if (tall_level is not None and d > tall_level) else 0.0))
        g = VGroup()
        g.root_edges = VGroup()

        # pass 1 — TIDY layout via CONTOUR PACKING (Reingold-Tilford-style, miss subtree LEFT /
        # hit RIGHT, each node centred over its children). Each subtree is laid out relative to
        # its own root, then each next sibling is slid right JUST enough that its left contour
        # clears the placed siblings' right contour by MIN_SEP at EVERY shared depth. So a deep,
        # narrow branch (e.g. a comb like _E: ME/BE/WE/RE/HE/YE) nests tightly against its
        # neighbour instead of claiming one full column per leaf (which left big gaps and shoved
        # it far right — the user's note). A BALANCED tree still spaces its leaves ~COL apart, so
        # existing subtrees (k's, the candidates) are unchanged. No two subtrees can overlap.
        MIN_SEP, INF = COL, float("inf")

        def kids_of(sp):
            """A node's children as [(is_miss, childspec), …], miss-first (LEFT). Accepts the
            N-ary {'g','kids':[(is_miss,spec),…]} form (a guess can hit at pos 1, pos 2, or
            both → several hit children) OR the binary {'g','hit','miss'?} form."""
            if "kids" in sp:
                return sp["kids"]
            ks = [(True, sp["miss"])] if "miss" in sp else []
            return ks + [(False, sp["hit"])]

        def shift_x(node, dx):
            node["x"] += dx
            for _, c in node["kids"]:
                shift_x(c, dx)

        def layout(sp, depth):
            """Returns (node, left_contour, right_contour): the laid-out subtree and its per-depth
            min/max x (absolute in this subtree's frame). A leaf sits at x=0."""
            node = {"spec": sp, "y": y_of(depth), "kids": []}
            kids = [] if "leaf" in sp else kids_of(sp)
            if not kids:
                node["x"] = 0.0
                return node, {depth: 0.0}, {depth: 0.0}
            lcont, rcont = {}, {}                        # contours of the placed children
            for i, (is_miss, cs) in enumerate(kids):
                cnode, cl, cr = layout(cs, depth + 1)
                off = 0.0                                # slide this child right to clear the rest
                if i:
                    off = max([0.0] + [rcont[d] - x + MIN_SEP for d, x in cl.items() if d in rcont])
                    shift_x(cnode, off)
                node["kids"].append((is_miss, cnode))
                for d, x in cl.items():
                    lcont[d] = min(lcont.get(d, INF), x + off)
                for d, x in cr.items():
                    rcont[d] = max(rcont.get(d, -INF), x + off)
            node["x"] = sum(c["x"] for _, c in node["kids"]) / len(node["kids"])  # centre over children
            lcont[depth] = min(lcont.get(depth, INF), node["x"])
            rcont[depth] = max(rcont.get(depth, -INF), node["x"])
            return node, lcont, rcont

        root, _, _ = layout(spec, 0)
        x0 = root["x"]                             # re-centre the whole tree on x = 0

        # pass 2 — build mobjects at the laid-out positions. Each node returns a HANDLE
        # (SimpleNamespace): .dot, .lab/.blk, .radius, .is_miss, .in_edge (from parent),
        # .out_edges (to children), .kids (child handles), .all (VGroup of this node + its
        # whole subtree — for greening/moving as a block). Handles tagged with 'key' in the
        # spec are collected on g.node[key] / g.leaf[key] so back-up beats can address them.
        g.node, g.leaf = {}, {}

        def build(node, is_root, in_miss):
            # SOLVED mode (candidate): the subtree is GREEN, only the root node + its edges keep
            # their original hit/miss colour. UNSOLVED mode (the persistent tree being worked):
            # EVERY node/edge is coloured by how it's reached (miss = red, hit = white), like the
            # diagonal — the back-up beats then green it piece by piece.
            pos = np.array([node["x"] - x0, node["y"], 0.0])
            sp = node["spec"]
            h = SimpleNamespace(spec=sp, in_edge=None, is_miss=bool(in_miss),
                                out_edges=VGroup(), kids=[])
            leaf_color = LIGHT_GREEN if solved else _miss_color(in_miss)
            if "leaf" in sp:
                dot = Dot(pos, radius=cr, color=leaf_color, z_index=2)
                blk = self._blanks(sp["leaf"]).set_x(pos[0]).set_color(leaf_color)
                blk.shift([0, (pos[1] - GRID_BLANK_DROP) - blk.get_bottom()[1], 0])
                g.add(dot, blk)
                h.dot, h.blk, h.radius, h.is_leaf, h.all = dot, blk, cr, True, VGroup(dot, blk)
                if "key" in sp:
                    g.leaf[sp["key"]] = h
                return h
            node_color = _miss_color(in_miss) if not solved else \
                (_miss_color(root_miss) if is_root else LIGHT_GREEN)
            dot = Dot(pos, radius=r, color=node_color, z_index=2)
            lab = crisp_text(sp["g"].upper(), color=BOARD_NAVY, weight=BOLD)
            lab.scale_to_fit_height(NODE_LETTER_H * r).move_to(dot).set_z_index(3)
            g.add(dot, lab)
            h.dot, h.lab, h.radius, h.is_leaf, h.all = dot, lab, r, False, VGroup(dot, lab)
            for is_miss, child in node["kids"]:
                ch = build(child, False, 1 if is_miss else 0)
                ecolor = _miss_color(1 if is_miss else 0) if (not solved or is_root) else LIGHT_GREEN
                dn = normalize(ch.dot.get_center() - pos)
                edge = Line(pos + dn * r, ch.dot.get_center() - dn * ch.radius,
                            color=ecolor, stroke_width=2.0)
                g.add(edge)
                ch.in_edge, ch.is_miss = edge, bool(is_miss)
                h.out_edges.add(edge)
                h.kids.append(ch)
                h.all.add(edge, ch.all)
                if is_root:
                    g.root_edges.add(edge)                # for the caller to green on lock
            if "key" in sp:
                g.node[sp["key"]] = h
            return h

        g.root_h = build(root, True, root_miss)
        g.root = g.root_h.dot
        return g

    def _edge_line(self, a_dot, b_dot, color):
        """A node→node edge Line from ``a_dot``'s boundary to ``b_dot``'s boundary."""
        ac, bc = a_dot.get_center(), b_dot.get_center()
        dn = normalize(bc - ac)
        return Line(ac + dn * a_dot.width / 2, bc - dn * b_dot.width / 2,
                    color=color, stroke_width=2.0)

    def _width_fit(self, ref, anchor, margin=0.3):
        """The largest uniform scale keeping a rooted `_ctree` ``ref`` (its natural, ORIGIN-rooted root
        pinned at ``anchor``) within the two SIDE edges. Measured on the natural-size ref. Used to
        clamp the backed-up subtree / a wide candidate so it doesn't spill off the left (or right)."""
        fx = config.frame_x_radius - margin
        rx = ref.root.get_center()[0]
        loff, roff = rx - ref.get_left()[0], ref.get_right()[0] - rx
        return min((anchor[0] + fx) / loff if loff > 1e-6 else 1e9,   # left edge stays in frame
                   (fx - anchor[0]) / roff if roff > 1e-6 else 1e9)   # right edge stays in frame

    def _above_diag_mobs(self, path, level):
        """The diagonal mobjects a back-up of the node at ``level`` does NOT otherwise animate: the
        levels ABOVE it (dots, labels, in-edges, hit siblings) + the in-edge INTO it (parent→node) +
        the above levels' hit annotations. A reframe must move these explicitly (everything BELOW the
        node is either the slid subtree or the grown branches, already animated). VMobjects only."""
        mobs = []
        for i in range(level):
            lv = path.levels[i]
            mobs += [lv["dot"], lv["lab"]]
            if lv["in_edge"] is not None:
                mobs.append(lv["in_edge"])
            for e, d in lv["hits"]:
                mobs += [e, d]
        if path.levels[level]["in_edge"] is not None:
            mobs.append(path.levels[level]["in_edge"])           # parent→node (not the node→child edge)
        n_above = sum(len(path.levels[i]["hits"]) for i in range(level))
        mobs += list(path.leaf_text[:n_above])
        return [m for m in mobs if isinstance(m, VMobject)]

    def _reframe(self, ref, above, margin=0.3):
        """The horizontal reframe transform (scale ``s`` about point ``c``, then shift ``dx``) that
        centres the FINAL tree — ``ref`` (the backed-up node's tidy subtree, whose phantom children
        span the full footprint) plus the diagonal ``above`` — and shrinks it about that centre ONLY
        if it's still wider than the frame. Applied to the back-up's OWN targets (ref, hit subtrees,
        the slide) AND, concurrently, to ``above`` — so the tree reframes DURING the growth, drifting
        the root right instead of extending off-screen and resizing afterward."""
        comp = VGroup(ref, *above)
        s = min(1.0, 2 * (config.frame_x_radius - margin) / comp.width) if comp.width > 1e-6 else 1.0
        c = comp.get_center()
        return s, c, np.array([-c[0], 0.0, 0.0])

    def _gap_up(self, node_dot, node_lab, parent_dot, in_edge, child_pairs, run_time,
                also=(), fade_in=(), fade_out=(), siblings=()):
        """Climb the tall gap up one level: the avg-miss value has just backed up INTO ``node``,
        so the tall edge becomes the one COMING IN to it (``in_edge``, parent→node) and the edges
        going OUT of it (``child_pairs`` = [(edge, child_dot), …]) revert to compact. Implemented
        as: ``node`` drops toward its (fixed) children by GRID_ROOT_DY−GRID_CHILD_DY (at the node's
        scale) — its in-edge lengthens, its out-edges shorten; the subtree below stays put. The
        node's SIBLINGS (the parent's OTHER children — ``siblings`` = [(group, dot, in_edge), …])
        drop by the SAME delta WITH their whole subtree/annotation so all of the parent's children
        stay ALIGNED (each sibling's in-edge lengthens too). ``also`` = mobjects that shift down
        WITH the node; ``fade_in`` = the NEW avg label, which fades in WHILE travelling down with
        the node; ``fade_out`` = the old (below) avg labels, which fade out in the same motion."""
        delta = DOWN * (GRID_ROOT_DY - GRID_CHILD_DY) * (node_dot.width / (2 * GRID_NODE_R))
        new_c = node_dot.get_center() + delta
        moved = node_dot.copy().move_to(new_c)
        anims = [node_dot.animate.move_to(new_c), node_lab.animate.move_to(new_c),
                 *[m.animate.shift(delta) for m in also],
                 *[FadeOut(m) for m in fade_out],
                 Transform(in_edge, self._edge_line(parent_dot, moved, in_edge.get_color()))]
        for m in fade_in:                      # travels down with the node AND fades in
            m.set_opacity(0)
            anims.append(m.animate.set_opacity(1).shift(delta))
        for edge, child_dot in child_pairs:
            anims.append(Transform(edge, self._edge_line(moved, child_dot, edge.get_color())))
        for sib_group, sib_dot, sib_in_edge in siblings:   # other children drop the SAME, stay aligned
            anims.append(sib_group.animate.shift(delta))
            anims.append(Transform(sib_in_edge,
                                   self._edge_line(parent_dot, sib_dot.copy().shift(delta),
                                                   sib_in_edge.get_color())))
        self.play(*anims, run_time=run_time)

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

    # ── resolved-play spec builders: the DRAWN optimal-subtree SKELETONS a back-up slides its
    #    already-solved child onto its parent's miss slot. ONE source of truth for "what the
    #    solved subtree below X looks like", reused by backup_e / backup_i / backup_o (see the
    #    BACK-UP BEAT RECIPE) — so the tidy parent tree reserves the matching footprint. ────────
    def _u_position_spec(self, key="u"):
        """The RESOLVED U-position play as DRAWN — the {by,my,up,us} bottom. Hand-composed (NOT
        `_subtree_spec`) because the DRAWN guess ORDER is the Y-first spine tiebreak from
        `_ymy_cell`/`choose_u` (an equally-optimal order the solver's raw output doesn't match);
        expected misses are identical. Structure only — carries no numbers."""
        spec = {"g": "u",
                "hit": {"g": "p", "hit": {"leaf": "up"},
                        "miss": {"g": "s", "hit": {"leaf": "us"}}},
                "miss": {"g": "y", "hit": {"g": "b", "hit": {"leaf": "by"},
                                           "miss": {"g": "m", "hit": {"leaf": "my"}}}}}
        if key:
            spec["key"] = key
        return spec

    def _position_hit_specs(self, depth):
        """The HIT-branch plays (X_ and _X, SOURCED via `_subtree_spec`) of the optimal letter at
        the depth-``depth`` all-miss position — grown as green solved subtrees off the diagonal's
        bare hit-sibling dots when that position is backed up (backup_e / backup_i / backup_o)."""
        node = self._n_miss_node(depth)
        opt = {o["letter"]: o for o in node["options"]}[node["optimal_letter"]]
        full = self._subtree_spec(opt["subtree"])
        return [sp for im, sp in full["kids"] if not im]

    def _resolved_play_spec(self, depth, key=None):
        """The fully-resolved optimal PLAY at the depth-``depth`` all-miss position, as DRAWN — the
        skeleton a HIGHER back-up slides its already-solved subtree onto (so the parent's tidy
        `_ctree` reserves the matching footprint). The optimal letter guessed, its HIT branches
        SOURCED (`_position_hit_specs`), its MISS child = the resolved play ONE LEVEL DEEPER
        (recursion), bottoming at the U-position's drawn Y-first spine (`_u_position_spec`). ``key``
        tags ONLY this root (deeper nodes stay unkeyed) so `_ctree`'s g.node[key] addresses the slot."""
        if depth >= 4:
            return self._u_position_spec(key)
        node = self._n_miss_node(depth)
        spec = {"g": node["optimal_letter"],
                "kids": [(True, self._resolved_play_spec(depth + 1))]
                        + [(False, sp) for sp in self._position_hit_specs(depth)]}
        if key:
            spec["key"] = key
        return spec

    def _counter_label(self, tracker, node_dot, direction=LEFT, bare=False):
        """The ROLLING version of ``_avg_label``: a value label that follows ``tracker`` and is re-placed
        relative to ``node_dot`` each frame (so it follows a moving node during a `_gap_up` reflow).
        Same sizing/anchoring as `_avg_label` — a bare number is node-sized + decimal-anchored, so it
        neither resizes nor lurches as it rolls. The caller removes ``lab._upd`` before greening it."""
        def place():
            v = tracker.get_value()
            if not bare:
                return self._value_label(v, WORDED_H, False).next_to(
                    node_dot, direction, buff=WORDED_H * 0.6)
            cap = VALUE_CAP_H
            return self._place_value(self._value_label(v, cap, True), node_dot, direction, cap * 0.9, cap)
        lab = place()
        lab.add_updater(upd := (lambda m: m.become(place())))
        lab._upd = upd
        return lab

    def _freeze(self, mob):
        """Freeze a rolling counter so the scene can SNAPSHOT (pickle): clear its updater AND drop the
        stale `.animate` ``target`` — a leftover copy of the mob that still references the updater
        lambda, so it survives remove_updater/clear_updaters and is what skipped the choose-beat
        snapshots (PicklingError). Walk the family; also drop the `_upd` closure attr."""
        for m in mob.get_family():
            m.clear_updaters()
            if getattr(m, "target", None) is not None:
                m.target = None
        if hasattr(mob, "_upd"):
            del mob._upd

    # ── back up the Y node (the {by,my} position) — sub-step of beat h. B's value fades out;
    #        a fresh WHITE value appears next to Y. The first guess then cycles Y → B → M, each
    #        shown as its COMPLETE optimal subtree (fully played out, all green) with its own avg
    #        misses; then CHOOSE Y and lock the value green. ──────────────────────────────────
    def _backup_y(self):
        sub = self.grid.sub
        path = self.grid.path
        scale = sub.gdot.width / (2 * GRID_NODE_R)        # match the (fit-scaled) spine nodes
        by_dot, by_blk, _ = sub.leaves["by"]
        my_dot, my_blk, _ = sub.leaves["my"]
        # the Y-first spine subtree WITHOUT the leaf tallies (dropped in h) — this IS the Y
        # candidate; fade it out/in as we compare, so its handles survive for later beats
        cur = VGroup(sub.gdot, sub.glab, sub.edges["yb"],
                     sub.discs["b"], sub.node_letters[1], sub.edges["bby"], by_dot, by_blk,
                     sub.edges["bm"], sub.discs["m"], sub.node_letters[2],
                     sub.edges["mmy"], my_dot, my_blk)
        # 1) the value now sits on Y → the tall gap climbs from Y→B up to U→Y (the diagonal
        #    connection): Y drops below the diagonal's U, Y→B reverts to compact, Y's FRESH '0.5'
        #    fades in travelling WITH Y, and B's '0.5' fades out. U's OTHER child ({up,us}, still a
        #    bare hit-sibling dot + 'U_ AOIE' board) drops WITH Y so U's two children stay aligned.
        ue, ud = path.levels[4]["hits"][0]                # U→{up,us} edge + bare dot
        avg_y = self._avg_label(sub.discs["y"], value=self._n_miss_node(5)["avg"], direction=LEFT)   # 0.5
        self._gap_up(sub.gdot, sub.glab, path.levels[4]["dot"], self.grid.drilled_edge,
                     [(sub.edges["yb"], sub.discs["b"])], run_time=0.7,
                     fade_in=[avg_y], fade_out=[self.avg_b],
                     siblings=[(VGroup(ud, path.leaf_text[-1]), ud, ue)])
        self.avg_b = avg_y
        anchor = sub.gdot.get_center()                    # Y's NEW (dropped) position — candidates hang here
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
            # compact internally — at j the tall edge is U→Y (above the spine), so each candidate
            # is fully compact and hangs the same tall gap below U (set up by the reflow above)
            ct = self._ctree(specs[letter])
            ct.scale(scale, about_point=ORIGIN).shift(anchor)
            return ct

        # cross-fade Y → B → M → back to Y (the value stays 0.5 — all three are equal here)
        self._cycle_candidates(cur, ["b", "m"], ctree, run_time=0.6, hold=0.3)
        # 3) choose Y: lock it — Y node + edge + value turn green
        self.play(VGroup(sub.discs["y"], sub.edges["yb"], avg_y).animate.set_color(LIGHT_GREEN),
                  run_time=0.9)

    # ── start backing up U — sub-step of beat h. Build U's FULL subtree as one tidy _ctree
    #        (the same builder the candidates use): slide the solved green {by,my} spine EXACTLY
    #        onto U's miss slot (identical _ctree layout → exact overlay, just scaled to the
    #        uniform node size), morph the diagonal U into the tidy root, and GROW U's other
    #        child {up,us} (unsolved). No hand spread, no reformat later — tidy from here up. ──
    def _backup_u(self):
        path = self.grid.path
        spine = self.grid.sub                              # the tidy green {by,my} _ctree
        u_dot, u_lab = path.levels[4]["dot"], path.levels[4]["lab"]
        uc = u_dot.get_center()
        # U's full tidy subtree (unsolved): U → {up,us} (hit), {by,my} (miss). Keyed so we can
        # address the root, {up,us}, and its edges; the {by,my} half is drawn by the green
        # spine we slide in, so u_ref's own {by,my} pieces are never added to the scene.
        u_spec = {"g": "u", "key": "u",
                  "hit": {"g": "p", "key": "p", "hit": {"leaf": "up", "key": "up"},
                          "miss": {"g": "s", "key": "s", "hit": {"leaf": "us", "key": "us"}}},
                  "miss": {"g": "y", "key": "y",
                           "hit": {"g": "b", "key": "b", "hit": {"leaf": "by"},
                                   "miss": {"g": "m", "key": "m", "hit": {"leaf": "my"}}}}}
        u_ref = self._ctree(u_spec, root_miss=1, solved=False, tall_level=0)  # LAYOUT + U node +
        # U's edges. The value now sits on U's children (Y solved in j, {up,us} here), so the tall
        # edges are U→Y / U→P (out of U). choose_u climbs the gap up to E→U once U itself backs up.
        scale_c = (uc[1] + 4.0) / u_ref.height             # fit below U (same as the candidates)
        u_ref.scale(scale_c, about_point=ORIGIN).shift(uc - u_ref.root.get_center())
        uh, yh, ph = u_ref.node["u"], u_ref.node["y"], u_ref.node["p"]
        # {up,us} drawn SOLVED (green subtree, white P root — the approved look) at u_ref's hit
        # slot; u_ref's own (unsolved) {up,us}/{by,my} pieces are never added to the scene.
        ups_spec = {"g": "p", "hit": {"leaf": "up"}, "miss": {"g": "s", "hit": {"leaf": "us"}}}
        ups = self._ctree(ups_spec, root_miss=0, solved=True)
        ups.scale(scale_c, about_point=ORIGIN).shift(ph.dot.get_center() - ups.root.get_center())
        # slide the green spine onto u_ref's {by,my} slot (exact overlay — same _ctree layout)
        sfac = yh.dot.width / spine.gdot.width
        y0, ty = spine.gdot.get_center(), yh.dot.get_center()
        # REUSE U's existing bare hit-sibling dot as the {up,us} root (P). TWO phases, mirroring
        # the drill's reveal (`_transform_move`): (1) the bare dot MOVES to P's tidy slot while its
        # letter RIDES in on top (starts small+transparent AT the bare dot, Restores to the node —
        # NOT a fade-in at the destination); (2) the {up,us} children SPROUT out of the settled P.
        be, bd = path.levels[4]["hits"][0]                            # U's bare 'u_' hit edge + dot
        p_lab = ups.root_h.lab
        p_lab.save_state()                                            # ride P in with the node…
        p_lab.scale(bd.width / ups.root.width).move_to(bd.get_center()).set_opacity(0)
        p_kids = VGroup(*[m for k in ups.root_h.kids for m in (k.in_edge, k.all)])  # below P
        # the spine arrives from j already compact AND hanging the tall gap below U (U→Y tall was set
        # up by backup_y's reflow), and u_ref lays out the same (tall_level=0) — so it just slides
        # rigidly onto the Y-slot, no reflow here. choose_u climbs the gap up to E→U later.
        # phase 1 — everything MOVES into place
        self.play(
            spine.animate.scale(sfac, about_point=y0).shift(ty - y0),
            self.avg_b.animate.scale(sfac, about_point=y0).shift(ty - y0).set_opacity(0),  # rides out w/ Y
            ReplacementTransform(VGroup(u_dot, u_lab), VGroup(uh.dot, uh.lab)),  # diagonal U → tidy U
            Transform(self.grid.drilled_edge, yh.in_edge),            # U→Y (miss) redrawn tidy
            ReplacementTransform(bd, ups.root),                       # bare 'u_' dot → P root node
            Transform(be, ph.in_edge),                                # bare 'u_' edge → tidy U→P edge
            Restore(p_lab),                                           # …P develops ON the node as it travels
            FadeOut(path.leaf_text[-1]),                              # old 'U_ AOIE' annotation
            run_time=0.9)
        # phase 2 — the {up,us} children sprout out of the (settled) reused P
        self.play(GrowFromPoint(p_kids, ups.root.get_center()), run_time=0.6)
        up_us_avg = self._n_miss_node(4)["children"]["u_"]["avg"]   # {up,us} value (0.5), sourced
        self.avg_p = self._avg_label(ups.root, value=up_us_avg, direction=RIGHT)
        self.play(FadeIn(self.avg_p), run_time=0.4)
        self.u_ref, self.u_spine, self.ups = u_ref, spine, ups
        self.u_pedge = be              # the ACTUAL on-screen U→P edge is the transformed bare edge
                                       # (NOT ph.in_edge, which was only the transform TARGET) — so
                                       # choose_u greens + backup_e slides the REAL edge, no orphan

    # ── solve U's other child {up,us} — sub-step of beat h. Cycle its candidates P and S
    #        (mirror complete green subtrees, both 0.5), then CHOOSE P and lock it green. ─────
    def _solve_ups(self):
        ups = self.ups
        pc = ups.root.get_center()
        s_scale = ups.root.width / (2 * GRID_NODE_R)       # match the on-screen {up,us} tree
        # the S candidate (mirror of P): S → {US hit, P→UP miss}
        spec_s = {"g": "s", "hit": {"leaf": "us"}, "miss": {"g": "p", "hit": {"leaf": "up"}}}
        s_ct = self._ctree(spec_s, root_miss=0).scale(s_scale, about_point=ORIGIN)
        s_ct.shift(pc - s_ct.root.get_center())
        # cycle P (current) → S → P (the value stays put); the U→P edge stays put
        self.play(FadeOut(ups), FadeIn(s_ct), run_time=0.6)
        self.wait(0.4)
        self.play(FadeOut(s_ct), FadeIn(ups), run_time=0.6)
        self.remove(s_ct)
        # choose P: green its root + outgoing edges (subtree already green) and the value
        self.play(VGroup(ups.root, ups.root_edges, self.avg_p).animate.set_color(LIGHT_GREEN),
                  run_time=0.9)

    # ── back up the U position ({by,my,up,us}) — sub-step of beat h. Both children are solved
    #        and the U-subtree is ALREADY tidy (built as a _ctree above), so it IS the U candidate
    #        — no reformat. The child value goes away and a rolling 'Avg misses' COUNTER appears on
    #        U. Cycle the first-guess candidates U/Y/B/M/P/S, each a COMPLETE optimal subtree (green
    #        subtree, original-colour root — a TIDY _ctree, SOURCED from the cache): U/Y = 1.0,
    #        B/M/P/S = 1.25, the counter rolling. CHOOSE U (the min), lock node+edges+value. ──────
    def _choose_u(self):
        uh = self.u_ref.node["u"]
        u_dot, u_lab = uh.dot, uh.lab
        yedge = self.grid.drilled_edge            # U→Y (miss, red)
        uedge = self.u_pedge                      # U→P (hit, white)
        path = self.grid.path
        # the persistent U-subtree (already tidy from k/l) IS the U candidate — no reformat
        cur = VGroup(u_dot, u_lab, yedge, uedge, self.u_spine, self.ups)
        scale_c = u_dot.width / (2 * GRID_NODE_R)  # match the persistent tree's node size
        node = self._n_miss_node(4)
        opts = {o["letter"]: o for o in node["options"] if o["splits"]}
        u_avg = opts["u"]["avg"]                    # 1.0 (== node['avg'])
        uval = ValueTracker(u_avg)
        counter = self._counter_label(uval, u_dot, direction=LEFT)
        # We are dealing with the U node now → at the START its value backs up, so the tall gap
        # climbs from U→children up to E→U (the diagonal connection): U drops below E, U→Y/P revert
        # to compact, the rolling counter fades in travelling WITH U, {up,us}'s value fades out.
        # E's OTHER children (its hit-sibling bare dots + boards) drop WITH U so E's children align.
        n_before = sum(len(path.levels[i]["hits"]) for i in range(3))
        e_hits, e_anns = path.levels[3]["hits"], path.leaf_text[n_before:]
        e_sibs = [(VGroup(hd, ann), hd, he) for (he, hd), ann in zip(e_hits, e_anns)]
        counter.remove_updater(counter._upd)        # detach so it can fade + travel with U
        self._gap_up(u_dot, u_lab, path.levels[3]["dot"], path.levels[4]["in_edge"],
                     [(yedge, self.u_spine.gdot), (uedge, self.ups.root)],
                     run_time=0.7, fade_in=[counter], fade_out=[self.avg_p], siblings=e_sibs)
        self.avg_p = None
        counter.add_updater(counter._upd)           # re-attach for the rolling cycle (tracks moved U)
        uc = u_dot.get_center()                     # U's NEW (dropped) position — candidates hang here
        self.wait(0.4)                             # hold on the U candidate before cycling

        def make(c):                               # a candidate first-guess subtree hanging below U
            # compact: at m the tall edge is E→U (above), so each candidate hangs the same tall gap
            ct = self._ctree(self._subtree_spec(opts[c]["subtree"]), root_miss=1)
            return ct.scale(min(scale_c, self._width_fit(ct, uc)), about_point=ORIGIN).shift(uc - ct.root.get_center())
        # cross-fade U → Y → B → … (capped at CYCLE_MAX) → back to U, the counter rolling to each avg
        self._cycle_candidates(cur, [c for c in opts if c != "u"], make, run_time=0.7, hold=0.3,
                               extra=lambda c: [uval.animate.set_value(opts[c]["avg"] if c else u_avg)])
        # choose U: freeze the counter (drop the updater + its `.animate` target so the scene can
        # still pickle), then lock U's node + both outgoing edges + the value green
        self._freeze(counter)
        # green the counter as its OWN animation (NOT wrapped in the VGroup) so it stays a TOP-LEVEL
        # mobject — else the next back-up's ride-out (fading it) won't render (a submob's opacity anim
        # is dropped)
        self.play(VGroup(u_dot, yedge, uedge).animate.set_color(LIGHT_GREEN),
                  counter.animate.set_color(LIGHT_GREEN), run_time=1.0)
        self.u_subtree = cur                        # hand off U's solved subtree to backing up E
        self.avg_u = counter                        # U's value label (green 1.0)

    # ── i : REPEAT the back-up one step at a time up the tree until the WHOLE tree is green.
    #        Same move as beat h, one level up each time: back up E (2.00), then I (2.57), then O
    #        (3.28), then add O's siblings (A's hit branches). Each level: build the tidy subtree,
    #        slide the solved child onto the miss slot, grow + solve the hit branches, cycle the
    #        candidates and choose the min. (Absorbs old backup_e … solve_a_hit — 11 sub-steps.)
    #        Starts by backing up E: build E's FULL tidy subtree, slide the solved green U-subtree
    #        onto E's miss slot, morph the diagonal E into the tidy root, grow E's hit branches. ──
    @subscene
    def backup_e(self):
        path = self.grid.path
        e_dot, e_lab = path.levels[3]["dot"], path.levels[3]["lab"]
        ec = e_dot.get_center()
        eu_edge = path.levels[4]["in_edge"]           # the diagonal E→U (miss) edge
        # U-position spec (E's MISS child) — the SAME structure as the on-screen green
        # U-subtree, so it slides on exactly; keyed 'u' to address the slot.
        # E's MISS child = the resolved U-position play as DRAWN; its HIT branches (e_, _e) SOURCED.
        # e_ref lays out the WHOLE E subtree (unsolved); the hit branches are grown as separate green
        # solved subtrees (mirroring {up,us} at the U level), the miss slot filled by the slid
        # U-subtree. Same skeleton helpers backup_i / backup_o reuse one level up.
        u_sub_spec = self._u_position_spec("u")
        e_hit_specs = self._position_hit_specs(3)                     # the E-hit branches
        e_spec = {"g": "e", "key": "e",
                  "kids": [(True, u_sub_spec)] + [(False, sp) for sp in e_hit_specs]}
        e_ref = self._ctree(e_spec, root_miss=1, solved=False, tall_level=0)
        scale_c = (ec[1] + 4.0) / e_ref.height        # fit below E (height), pinned at its diagonal node
        e_ref.scale(scale_c, about_point=ORIGIN).shift(ec - e_ref.root.get_center())
        # reframe the WHOLE final tree (this subtree + the diagonal above) horizontally, folded into
        # phase 1 so the root drifts right AS the tree grows (not a separate resize afterward)
        above = self._above_diag_mobs(path, 3)
        s, c, dx = self._reframe(e_ref, above)
        e_ref.scale(s, about_point=c).shift(dx)
        eh, uh = e_ref.node["e"], e_ref.node["u"]
        hit_handles = [k for k in eh.kids if not k.is_miss]
        # slide the green U-subtree onto e_ref's U (miss) slot — exact overlay, scaled to the reframe
        u_now = self.u_ref.node["u"].dot
        sfac = uh.dot.width / u_now.width
        y0, ty = u_now.get_center(), uh.dot.get_center()
        # E's hit branches don't SPAWN new roots: REUSE each existing bare hit-sibling dot as the
        # branch's root guess node. TWO phases, mirroring the drill's reveal (`_transform_move`):
        # (1) the bare dot MOVES to the tidy root slot while its letter RIDES in on top of it
        # (starts small+transparent AT the bare dot, Restores to the node — NOT a fade-in at the
        # destination); (2) the branch's children SPROUT out of the settled root.
        hits = path.levels[3]["hits"]                # [(bare_edge, bare_dot), …], one per hit branch
        sc = scale_c * s                             # hit branches at the reframed scale
        move, grows, hit_trees = [], [], []
        for (be, bd), h, sp in zip(hits, hit_handles, e_hit_specs):
            ct = self._ctree(sp, root_miss=0, solved=True)
            ct.scale(sc, about_point=ORIGIN).shift(h.dot.get_center() - ct.root.get_center())
            lab = ct.root_h.lab
            lab.save_state()                          # ride the letter in with the node…
            lab.scale(bd.width / ct.root.width).move_to(bd.get_center()).set_opacity(0)
            kids = VGroup(*[m for k in ct.root_h.kids for m in (k.in_edge, k.all)])  # below the root
            move += [ReplacementTransform(bd, ct.root),   # bare dot → tidy branch root (the node moves)
                     Transform(be, h.in_edge),            # bare edge → tidy E→root edge
                     Restore(lab)]                        # …letter develops ON the node as it travels
            grows.append((kids, ct.root))
            hit_trees.append((h, ct))
        # only E's OWN bare-board annotation fades (replaced by the real subtree); the drilled-past
        # A/O/I annotations STAY — they're re-expanded when each of those levels is later backed up
        n_before = sum(len(path.levels[i]["hits"]) for i in range(3))
        e_anns = VGroup(*path.leaf_text[n_before:n_before + len(hits)])
        # phase 1 — slide/morph/reveal to the REFRAMED targets AND reframe the diagonal above, together
        self.play(
            self.u_subtree.animate.scale(sfac, about_point=y0).shift(ty - y0),
            FadeOut(self.avg_u, shift=ty - y0),                      # rides out (fade + move) with U
            ReplacementTransform(VGroup(e_dot, e_lab), VGroup(eh.dot, eh.lab)),  # diagonal E → tidy E
            Transform(eu_edge, uh.in_edge),                          # E→U (miss) redrawn tidy
            FadeOut(e_anns),                                          # E's own bare-board annotation
            *move,
            *[m.animate.scale(s, about_point=c).shift(dx) for m in above],   # reframe the diagonal above
            run_time=0.9)
        # phase 2 — each hit branch's children SPROUT out of the (settled) reused root (reframed)
        self.play(*[GrowFromPoint(kids, dot.get_center()) for kids, dot in grows], run_time=0.6)
        self.e_ref, self.eu_edge = e_ref, eu_edge
        self.e_hit_trees = hit_trees                 # [(handle, green subtree), …] for solving
        self.e_hit_edges = [be for be, bd in hits]   # the ACTUAL on-screen E→M edges (transformed be)
        self.avg_u = None
        # solve/choose E, then repeat the whole move up through I, O, and A's hit branches
        self._solve_e_hit()
        self._choose_e()
        self._backup_i()
        self._solve_i_hit()
        self._choose_i()
        self._backup_o()
        self._solve_o_hit()
        self._choose_o()
        self._backup_a()
        self._solve_a_hit()

    def _cycle_candidates(self, home, letters, make_ct, run_time, hold, extra=None):
        """Cross-fade a node's ``home`` subtree through up to ``CYCLE_MAX``-1 alternative candidate
        subtrees (each built + positioned by ``make_ct(letter)``), then settle back on ``home``.
        ``extra(letter | None)`` -> extra anims played WITH each cross-fade (a candidate letter, then
        None for the settle-back) — e.g. rolling a value counter. THE ONE place the candidate-cycle
        cross-fade AND the ``CYCLE_MAX`` cap live, so the solve cycle and the choose cycles cap and
        animate identically (change it once, everywhere follows)."""
        letters = list(letters)[:CYCLE_MAX - 1]
        if not letters:
            return
        active = home
        for c in letters:
            alt = make_ct(c)
            self.play(FadeOut(active), FadeIn(alt), *(extra(c) if extra else []), run_time=run_time)
            self.wait(hold)
            if active is not home:
                self.remove(active)
            active = alt
        self.play(FadeOut(active), FadeIn(home), *(extra(None) if extra else []), run_time=run_time)
        if active is not home:
            self.remove(active)

    # ── ONE place that solves a position's two HIT children (X_ and _X), shared by solve_e_hit /
    #    solve_i_hit / solve_o_hit — so the reveal, the candidate cycle (via _cycle_candidates), and
    #    (critically) the REVEALED-letter threading live in exactly one spot. ──────────────────────
    def _solve_position_hits(self, depth, hit_trees):
        """Solve the depth-``depth`` all-miss position's HIT children (X_ and _X): for each, show its
        avg (bare 2 dp, ONE number on screen at a time), cycle through ALL its OTHER tied first-
        guesses, settle on the optimal, lock root + edges green. Returns the last avg label (the
        caller hands it to choose_X, which fades it). The position letter X is ALREADY REVEALED in a
        hit child, so candidate subtrees are sourced with ``revealed=X`` — WITHOUT it `_subtree_spec`
        re-guesses X as a spurious forced-hit tail on every determined word (e.g. a T-branch in the
        _o position sprouting a bogus 'O' node under each leaf). Keys + directions derived from the
        SOURCED children so any hit-count works."""
        node = self._n_miss_node(depth)
        revealed = node["optimal_letter"]                       # revealed in BOTH hit patterns (X_, _X)
        children = node["children"]
        hit_keys = [p for p in children if set(p) != {"_"}]     # ['x_', '_x'] — SOURCED order
        dirs = (LEFT, RIGHT, LEFT, RIGHT)                       # each hit's number offset (avoid collisions)
        prev = None
        for (h, ct), key, direction in zip(hit_trees, hit_keys, dirs):
            child = children[key]
            opts = {o["letter"]: o for o in child["options"] if o["splits"]}
            avg = self._avg_label(ct.root, value=child["avg"], direction=direction, bare=True)
            self.play(*([FadeOut(prev)] if prev is not None else []),   # one number at a time
                      FadeIn(avg), run_time=0.4)
            scale = ct.root.width / (2 * GRID_NODE_R)

            def make(c):                                        # a candidate guess subtree at ct's slot
                alt = self._ctree(self._subtree_spec(opts[c]["subtree"], revealed=revealed), root_miss=0)
                return alt.scale(scale, about_point=ORIGIN).shift(ct.root.get_center() - alt.root.get_center())
            self._cycle_candidates(ct, [x for x in opts if x != child["optimal_letter"]], make,
                                   run_time=0.5, hold=0.2)
            self.play(VGroup(ct.root, ct.root_edges, avg).animate.set_color(LIGHT_GREEN), run_time=0.7)
            prev = avg
        return prev

    # ── solve E's HIT children — sub-step of beat i. Each grown green with a WHITE root above. For
    #    each position ({EM,EN,EX}=1.00 ; {ME,BE,WE,RE,HE,YE}=2.50) show its number, cycle ALL other
    #    tied first-guesses, settle on M, lock the root + edges green. Bare 2-dp numbers, one at a time.
    def _solve_e_hit(self):
        self.e_hit_avg = self._solve_position_hits(3, self.e_hit_trees)

    # ── back up E — sub-step of beat i. The value now sits on E. Cycle E's first-guess candidates
    #    (e=2.00 the min; m/y=2.08, b=2.31, h/r/u/w=2.54, p/s=2.69, n/x=2.77 — ALL sourced), the bare
    #    2dp counter rolling on E; choose E, lock node + all edges + value green. Then the value backs
    #    up so the tall gap climbs to I→E: E drops below I and I's OTHER children drop with it. ───────
    def _choose_e(self):
        path = self.grid.path
        eh = self.e_ref.node["e"]
        e_dot, e_lab = eh.dot, eh.lab
        scale_c = e_dot.width / (2 * GRID_NODE_R)
        hit_cts = [ct for h, ct in self.e_hit_trees]
        opts = {o["letter"]: o for o in self._n_miss_node(3)["options"] if o["splits"]}
        e_avg = opts["e"]["avg"]                     # 2.0
        eval_ = ValueTracker(e_avg)
        counter = self._counter_label(eval_, e_dot, direction=LEFT, bare=True)
        # climb the gap to I→E at the START of the beat (the node + its siblings drop at the
        # BEGINNING, per the choose_u rule): E drops below I, E→children revert to compact, the
        # rolling counter fades in travelling WITH E, the last hit number (_e's 2.50) fades out;
        # I's OTHER children (bare hit dots + boards) drop WITH E (sibling rule).
        n_before = sum(len(path.levels[i]["hits"]) for i in range(2))
        i_hits, i_anns = path.levels[2]["hits"], path.leaf_text[n_before:]
        i_sibs = [(VGroup(hd, ann), hd, he) for (he, hd), ann in zip(i_hits, i_anns)]
        child_pairs = [(self.eu_edge, self.u_ref.node["u"].dot)] + \
                      [(e, ct.root) for e, ct in zip(self.e_hit_edges, hit_cts)]
        counter.remove_updater(counter._upd)         # detach so it can fade + travel with E
        self._gap_up(e_dot, e_lab, path.levels[2]["dot"], path.levels[3]["in_edge"],
                     child_pairs, run_time=0.7, fade_in=[counter], fade_out=[self.e_hit_avg],
                     siblings=i_sibs)
        counter.add_updater(counter._upd)            # re-attach for the rolling cycle (tracks moved E)
        # the persistent E-tree (now dropped) IS the E candidate
        cur = VGroup(e_dot, e_lab, self.eu_edge, *self.e_hit_edges, self.u_subtree, *hit_cts)
        ec = e_dot.get_center()                      # E's NEW (dropped) position — candidates hang here
        self.wait(0.4)

        def make(c):                                 # compact (the tall gap is I→E, above)
            ct = self._ctree(self._subtree_spec(opts[c]["subtree"]), root_miss=1)
            return ct.scale(min(scale_c, self._width_fit(ct, ec)), about_point=ORIGIN).shift(ec - ct.root.get_center())
        # cross-fade E → other first guesses (capped) → back to E, the counter rolling to each avg
        self._cycle_candidates(cur, [c for c in opts if c != "e"], make, run_time=0.6, hold=0.25,
                               extra=lambda c: [eval_.animate.set_value(opts[c]["avg"] if c else e_avg)])
        # choose E: freeze the counter, green E node + ALL its outgoing edges + the value
        self._freeze(counter)
        e_edges = VGroup(self.eu_edge, *self.e_hit_edges)
        self.play(VGroup(e_dot, e_edges).animate.set_color(LIGHT_GREEN),
                  counter.animate.set_color(LIGHT_GREEN), run_time=1.0)   # counter TOP-LEVEL (rides out later)
        self.e_subtree = cur                         # hand off E's solved subtree to backing up I
        self.avg_e = counter                         # E's value label (green 2.00)
        self.u_ref = None                            # U's layout scaffolding — last used here; drop it
                                                     #   from every later snapshot (keeps them light)

    # ── start backing up I — sub-step of beat i. SAME move as backing up E, one level up. Build
    #        I's FULL tidy subtree as a _ctree (I → its i_/_i HIT branches + the E-position as the
    #        MISS child), slide the solved green E-subtree onto I's miss slot (scaled to the new,
    #        smaller node size), morph the diagonal I into the tidy root, and GROW I's hit branches
    #        (shown solved-green) — chosen among next. ─────────────────────────────────────────────
    def _backup_i(self):
        path = self.grid.path
        i_dot, i_lab = path.levels[2]["dot"], path.levels[2]["lab"]
        ic = i_dot.get_center()
        ie_edge = path.levels[3]["in_edge"]           # the diagonal I→E (miss) edge
        # I's MISS child = the resolved E-play as DRAWN (same structure as the on-screen green
        # E-subtree, so it slides on exactly). SOURCED via _resolved_play_spec; keyed 'e'.
        e_sub_spec = self._resolved_play_spec(3, key="e")
        i_hit_specs = self._position_hit_specs(2)     # I's HIT branches (i_, _i), SOURCED
        i_spec = {"g": "i", "key": "i",
                  "kids": [(True, e_sub_spec)] + [(False, sp) for sp in i_hit_specs]}
        i_ref = self._ctree(i_spec, root_miss=1, solved=False, tall_level=0)
        scale_c = (ic[1] + 4.0) / i_ref.height        # fit below I (height), pinned at its diagonal node
        i_ref.scale(scale_c, about_point=ORIGIN).shift(ic - i_ref.root.get_center())
        # reframe the WHOLE final tree (this subtree + the diagonal above) horizontally, folded into
        # phase 1 so the root drifts right AS the tree grows (not a separate resize afterward)
        above = self._above_diag_mobs(path, 2)
        s, c, dx = self._reframe(i_ref, above)
        i_ref.scale(s, about_point=c).shift(dx)
        ih, eh = i_ref.node["i"], i_ref.node["e"]
        hit_handles = [k for k in ih.kids if not k.is_miss]
        # slide the green E-subtree onto i_ref's E (miss) slot — exact overlay, scaled to the reframe
        e_now = self.e_ref.node["e"].dot
        sfac = eh.dot.width / e_now.width
        y0, ty = e_now.get_center(), eh.dot.get_center()
        # I's hit branches REUSE each existing bare hit-sibling dot as the branch's root (the
        # drill's ride-in — letter starts small+transparent AT the bare dot, Restores as the node
        # travels), then the branch's children SPROUT out of the settled root. Mirrors backup_e.
        hits = path.levels[2]["hits"]                 # [(bare_edge, bare_dot), …], one per hit branch
        sc = scale_c * s                              # hit branches at the reframed scale
        move, grows, hit_trees = [], [], []
        for (be, bd), h, sp in zip(hits, hit_handles, i_hit_specs):
            ct = self._ctree(sp, root_miss=0, solved=True)
            ct.scale(sc, about_point=ORIGIN).shift(h.dot.get_center() - ct.root.get_center())
            lab = ct.root_h.lab
            lab.save_state()
            lab.scale(bd.width / ct.root.width).move_to(bd.get_center()).set_opacity(0)
            kids = VGroup(*[m for k in ct.root_h.kids for m in (k.in_edge, k.all)])
            move += [ReplacementTransform(bd, ct.root),
                     Transform(be, h.in_edge),
                     Restore(lab)]
            grows.append((kids, ct.root))
            hit_trees.append((h, ct))
        n_before = sum(len(path.levels[i]["hits"]) for i in range(2))
        i_anns = VGroup(*path.leaf_text[n_before:n_before + len(hits)])
        # phase 1 — slide/morph/reveal to the REFRAMED targets AND reframe the diagonal above, together
        self.play(
            self.e_subtree.animate.scale(sfac, about_point=y0).shift(ty - y0),
            FadeOut(self.avg_e, shift=ty - y0),                      # rides out (fade + move) with E
            ReplacementTransform(VGroup(i_dot, i_lab), VGroup(ih.dot, ih.lab)),  # diagonal I → tidy I
            Transform(ie_edge, eh.in_edge),                          # I→E (miss) redrawn tidy
            FadeOut(i_anns),                                          # I's own bare-board annotations
            *move,
            *[m.animate.scale(s, about_point=c).shift(dx) for m in above],   # reframe the diagonal above
            run_time=0.9)
        # phase 2 — each hit branch's children SPROUT out of the (settled) reused root (reframed)
        self.play(*[GrowFromPoint(kids, dot.get_center()) for kids, dot in grows], run_time=0.6)
        self.i_ref, self.ie_edge = i_ref, ie_edge
        self.i_hit_trees = hit_trees                 # [(handle, green subtree), …] for solving
        self.i_hit_edges = [be for be, bd in hits]   # the ACTUAL on-screen I→root edges (transformed be)
        # keep self.e_subtree — it's now the slid miss child of I; choose_i folds it into cur
        self.avg_e = None

    # ── solve I's HIT children (i_ {…}=2.0 ; _i {…}=2.0) — sub-step of beat i. For each show its
    #        number, cycle through ALL the other (tied) first-guesses, settle on the optimal, lock
    #        root + edges green. Bare 2-dp numbers, ONE on screen at a time. Mirror of _solve_e_hit.
    def _solve_i_hit(self):
        self.i_hit_avg = self._solve_position_hits(2, self.i_hit_trees)

    # ── back up I — sub-step of beat i. Cycle I's first-guess candidates (i=2.57 the min, then
    #        e/m/y/b/…, ALL sourced), the bare 2-dp counter rolling on I; choose I, lock node + all
    #        edges + value green. The climb to O→I happens at the START (node + siblings drop first).
    #        Mirror of _choose_e (climb-at-start, per the choose_u rule). ──────────────────────────
    def _choose_i(self):
        path = self.grid.path
        ih = self.i_ref.node["i"]
        i_dot, i_lab = ih.dot, ih.lab
        scale_c = i_dot.width / (2 * GRID_NODE_R)
        hit_cts = [ct for h, ct in self.i_hit_trees]
        opts = {o["letter"]: o for o in self._n_miss_node(2)["options"] if o["splits"]}
        i_avg = opts["i"]["avg"]                     # 2.565…
        ival = ValueTracker(i_avg)
        counter = self._counter_label(ival, i_dot, direction=LEFT, bare=True)
        # climb the gap to O→I at the START: I drops below O, I→children revert to compact, the
        # counter fades in travelling WITH I, the last hit number fades out; O's OTHER children
        # (bare hit dots + boards) drop WITH I (sibling rule).
        n_before = sum(len(path.levels[i]["hits"]) for i in range(1))
        o_hits, o_anns = path.levels[1]["hits"], path.leaf_text[n_before:]
        o_sibs = [(VGroup(hd, ann), hd, he) for (he, hd), ann in zip(o_hits, o_anns)]
        child_pairs = [(self.ie_edge, self.e_ref.node["e"].dot)] + \
                      [(e, ct.root) for e, ct in zip(self.i_hit_edges, hit_cts)]
        counter.remove_updater(counter._upd)
        self._gap_up(i_dot, i_lab, path.levels[1]["dot"], path.levels[2]["in_edge"],
                     child_pairs, run_time=0.7, fade_in=[counter], fade_out=[self.i_hit_avg],
                     siblings=o_sibs)
        counter.add_updater(counter._upd)
        # the persistent I-tree (now dropped) IS the I candidate — includes the slid E-subtree (miss)
        cur = VGroup(i_dot, i_lab, self.ie_edge, *self.i_hit_edges, self.e_subtree, *hit_cts)
        ic = i_dot.get_center()                      # I's NEW (dropped) position — candidates hang here
        self.wait(0.4)

        def make(c):                                 # compact (the tall gap is O→I, above)
            ct = self._ctree(self._subtree_spec(opts[c]["subtree"]), root_miss=1)
            return ct.scale(min(scale_c, self._width_fit(ct, ic)), about_point=ORIGIN).shift(ic - ct.root.get_center())
        # cross-fade I → other first guesses (capped) → back to I, the counter rolling to each avg
        self._cycle_candidates(cur, [c for c in opts if c != "i"], make, run_time=0.6, hold=0.25,
                               extra=lambda c: [ival.animate.set_value(opts[c]["avg"] if c else i_avg)])
        self._freeze(counter)
        i_edges = VGroup(self.ie_edge, *self.i_hit_edges)
        self.play(VGroup(i_dot, i_edges).animate.set_color(LIGHT_GREEN),
                  counter.animate.set_color(LIGHT_GREEN), run_time=1.0)   # counter TOP-LEVEL (rides out later)
        self.i_subtree = cur                         # hand off I's solved subtree to backing up O
        self.avg_i = counter                         # I's value label (green)
        self.e_ref = None                            # E's layout scaffolding — last used here; drop it

    # ── start backing up O — sub-step of beat i. SAME move as backing up I, one level up. Build
    #        O's FULL tidy subtree, slide the solved green I-subtree onto O's miss slot, morph the
    #        diagonal O into the tidy root, and GROW O's hit branches (green). Mirror of _backup_i.
    def _backup_o(self):
        path = self.grid.path
        o_dot, o_lab = path.levels[1]["dot"], path.levels[1]["lab"]
        oc = o_dot.get_center()
        oi_edge = path.levels[2]["in_edge"]           # the diagonal O→I (miss) edge
        # O's MISS child = the resolved I-play as DRAWN (matches the on-screen green I-subtree).
        i_sub_spec = self._resolved_play_spec(2, key="i")
        o_hit_specs = self._position_hit_specs(1)     # O's HIT branches (o_, _o), SOURCED
        o_spec = {"g": "o", "key": "o",
                  "kids": [(True, i_sub_spec)] + [(False, sp) for sp in o_hit_specs]}
        o_ref = self._ctree(o_spec, root_miss=1, solved=False, tall_level=0)
        scale_c = (oc[1] + 4.0) / o_ref.height        # fit below O (height), pinned at its diagonal node
        o_ref.scale(scale_c, about_point=ORIGIN).shift(oc - o_ref.root.get_center())
        # reframe the WHOLE final tree (this subtree + the diagonal above) horizontally, folded into
        # phase 1 so the root drifts right AS the tree grows (not a separate resize afterward)
        above = self._above_diag_mobs(path, 1)
        s, c, dx = self._reframe(o_ref, above)
        o_ref.scale(s, about_point=c).shift(dx)
        oh, ih = o_ref.node["o"], o_ref.node["i"]
        hit_handles = [k for k in oh.kids if not k.is_miss]
        i_now = self.i_ref.node["i"].dot
        sfac = ih.dot.width / i_now.width
        y0, ty = i_now.get_center(), ih.dot.get_center()
        hits = path.levels[1]["hits"]                 # O's bare hit-sibling dots
        sc = scale_c * s                              # hit branches at the reframed scale
        move, grows, hit_trees = [], [], []
        for (be, bd), h, sp in zip(hits, hit_handles, o_hit_specs):
            ct = self._ctree(sp, root_miss=0, solved=True)
            ct.scale(sc, about_point=ORIGIN).shift(h.dot.get_center() - ct.root.get_center())
            lab = ct.root_h.lab
            lab.save_state()
            lab.scale(bd.width / ct.root.width).move_to(bd.get_center()).set_opacity(0)
            kids = VGroup(*[m for k in ct.root_h.kids for m in (k.in_edge, k.all)])
            move += [ReplacementTransform(bd, ct.root),
                     Transform(be, h.in_edge),
                     Restore(lab)]
            grows.append((kids, ct.root))
            hit_trees.append((h, ct))
        n_before = sum(len(path.levels[i]["hits"]) for i in range(1))
        o_anns = VGroup(*path.leaf_text[n_before:n_before + len(hits)])
        # phase 1 — slide/morph/reveal to the REFRAMED targets AND reframe the diagonal above, together
        self.play(
            self.i_subtree.animate.scale(sfac, about_point=y0).shift(ty - y0),
            FadeOut(self.avg_i, shift=ty - y0),                      # rides out (fade + move) with I
            ReplacementTransform(VGroup(o_dot, o_lab), VGroup(oh.dot, oh.lab)),  # diagonal O → tidy O
            Transform(oi_edge, ih.in_edge),                          # O→I (miss) redrawn tidy
            FadeOut(o_anns),                                          # O's own bare-board annotations
            *move,
            *[m.animate.scale(s, about_point=c).shift(dx) for m in above],   # reframe the diagonal above
            run_time=0.9)
        self.play(*[GrowFromPoint(kids, dot.get_center()) for kids, dot in grows], run_time=0.6)
        self.o_ref, self.oi_edge = o_ref, oi_edge
        self.o_hit_trees = hit_trees
        self.o_hit_edges = [be for be, bd in hits]
        # keep self.i_subtree — it's now the slid miss child of O; choose_o folds it into cur
        self.avg_i = None

    # ── solve O's HIT children (o_ {…}=2.5 ; _o {…}=3.0) — sub-step of beat i. Cycle ALL tied
    #        first-guesses, lock each root + edges green. Bare 2-dp numbers, one at a time. ─────────
    def _solve_o_hit(self):
        self.o_hit_avg = self._solve_position_hits(1, self.o_hit_trees)

    # ── back up O — sub-step of beat i. Cycle O's first-guess candidates (o=3.28 the min, then
    #        i/e/m/y/…, ALL sourced), the bare counter rolling on O; choose O, lock node + all edges
    #        + value green. The climb to A→O (the diagonal root) happens at the START. Mirror of
    #        _choose_i. ─────────────────────────────────────────────────────────────────────────────
    def _choose_o(self):
        path = self.grid.path
        oh = self.o_ref.node["o"]
        o_dot, o_lab = oh.dot, oh.lab
        scale_c = o_dot.width / (2 * GRID_NODE_R)
        hit_cts = [ct for h, ct in self.o_hit_trees]
        opts = {o["letter"]: o for o in self._n_miss_node(1)["options"] if o["splits"]}
        o_avg = opts["o"]["avg"]                     # 3.278
        oval = ValueTracker(o_avg)
        counter = self._counter_label(oval, o_dot, direction=LEFT, bare=True)
        # climb the gap to A→O at the START: O drops below A (the diagonal root), O→children revert
        # to compact, the counter fades in travelling WITH O, the last hit number fades out; A's
        # OTHER children (bare hit dots + boards) drop WITH O (sibling rule). A is level 0 → no offset.
        a_hits, a_anns = path.levels[0]["hits"], path.leaf_text
        a_sibs = [(VGroup(hd, ann), hd, he) for (he, hd), ann in zip(a_hits, a_anns)]
        child_pairs = [(self.oi_edge, self.i_ref.node["i"].dot)] + \
                      [(e, ct.root) for e, ct in zip(self.o_hit_edges, hit_cts)]
        counter.remove_updater(counter._upd)
        self._gap_up(o_dot, o_lab, path.levels[0]["dot"], path.levels[1]["in_edge"],
                     child_pairs, run_time=0.7, fade_in=[counter], fade_out=[self.o_hit_avg],
                     siblings=a_sibs)
        counter.add_updater(counter._upd)
        # the persistent O-tree (now dropped) IS the O candidate — includes the slid I-subtree (miss)
        cur = VGroup(o_dot, o_lab, self.oi_edge, *self.o_hit_edges, self.i_subtree, *hit_cts)
        oc = o_dot.get_center()
        self.wait(0.4)

        def make(c):                                 # compact (the tall gap is A→O, above)
            ct = self._ctree(self._subtree_spec(opts[c]["subtree"]), root_miss=1)
            return ct.scale(min(scale_c, self._width_fit(ct, oc)), about_point=ORIGIN).shift(oc - ct.root.get_center())
        # cross-fade O → other first guesses (capped) → back to O, the counter rolling to each avg
        self._cycle_candidates(cur, [c for c in opts if c != "o"], make, run_time=0.6, hold=0.25,
                               extra=lambda c: [oval.animate.set_value(opts[c]["avg"] if c else o_avg)])
        self._freeze(counter)
        o_edges = VGroup(self.oi_edge, *self.o_hit_edges)
        self.play(VGroup(o_dot, o_edges).animate.set_color(LIGHT_GREEN),
                  counter.animate.set_color(LIGHT_GREEN), run_time=1.0)   # counter TOP-LEVEL (rides out later)
        self.o_subtree = cur                         # hand off O's solved subtree to backing up A
        self.avg_o = counter                         # O's value label (green)
        self.i_ref = None                            # I's layout scaffolding — last used here; drop it

    # ── add in O's SIBLINGS — A's two hit branches (a_, _a) — sub-step of beat i. SAME move as
    #        backing up O, but A is the diagonal ROOT (no parent edge / no gap climb): build A's
    #        FULL tidy subtree, slide the solved green O-subtree onto A's miss slot, morph the
    #        diagonal A into the tidy (white) root, and GROW A's hit branches (green). Leaves A
    #        itself UN-chosen (the winner is picked in beat j). Mirror of _backup_o at the root. ────
    def _backup_a(self):
        path = self.grid.path
        a_dot, a_lab = path.levels[0]["dot"], path.levels[0]["lab"]
        ac = a_dot.get_center()
        ao_edge = path.levels[1]["in_edge"]           # the diagonal A→O (miss) edge
        # A's MISS child = the resolved O-play as DRAWN (matches the on-screen green O-subtree).
        o_sub_spec = self._resolved_play_spec(1, key="o")
        a_hit_specs = self._position_hit_specs(0)     # A's HIT branches (a_, _a) = O's siblings, SOURCED
        a_spec = {"g": "a", "key": "a",
                  "kids": [(True, o_sub_spec)] + [(False, sp) for sp in a_hit_specs]}
        self.a_spec = a_spec              # reused by beat y to rebuild a clean single-_ctree replica
        a_ref = self._ctree(a_spec, root_miss=0, solved=False, tall_level=0)  # root reached w/ 0 misses → white
        scale_c = (ac[1] + 4.0) / a_ref.height        # fit below A (height), pinned at its diagonal node
        a_ref.scale(scale_c, about_point=ORIGIN).shift(ac - a_ref.root.get_center())
        # reframe the WHOLE final tree horizontally, folded into phase 1 (A is the root — nothing above,
        # so the reframe rides entirely on this subtree's own targets); drifts right AS it grows
        above = self._above_diag_mobs(path, 0)        # [] at the root
        s, c, dx = self._reframe(a_ref, above)
        a_ref.scale(s, about_point=c).shift(dx)
        ah, oh = a_ref.node["a"], a_ref.node["o"]
        hit_handles = [k for k in ah.kids if not k.is_miss]
        o_now = self.o_ref.node["o"].dot
        sfac = oh.dot.width / o_now.width
        y0, ty = o_now.get_center(), oh.dot.get_center()
        hits = path.levels[0]["hits"]                 # A's bare hit-sibling dots (O's siblings)
        sc = scale_c * s                              # hit branches at the reframed scale
        move, grows, hit_trees = [], [], []
        for (be, bd), h, sp in zip(hits, hit_handles, a_hit_specs):
            ct = self._ctree(sp, root_miss=0, solved=True)
            ct.scale(sc, about_point=ORIGIN).shift(h.dot.get_center() - ct.root.get_center())
            lab = ct.root_h.lab
            lab.save_state()
            lab.scale(bd.width / ct.root.width).move_to(bd.get_center()).set_opacity(0)
            kids = VGroup(*[m for k in ct.root_h.kids for m in (k.in_edge, k.all)])
            move += [ReplacementTransform(bd, ct.root),
                     Transform(be, h.in_edge),
                     Restore(lab)]
            grows.append((kids, ct.root))
            hit_trees.append((h, ct))
        a_anns = VGroup(*path.leaf_text[0:len(hits)])
        # phase 1 — slide/morph/reveal to the REFRAMED targets AND reframe the diagonal above, together
        self.play(
            self.o_subtree.animate.scale(sfac, about_point=y0).shift(ty - y0),
            FadeOut(self.avg_o, shift=ty - y0),                      # rides out (fade + move) with O
            ReplacementTransform(VGroup(a_dot, a_lab), VGroup(ah.dot, ah.lab)),  # diagonal A → tidy A
            Transform(ao_edge, oh.in_edge),                          # A→O (miss) redrawn tidy
            FadeOut(a_anns),                                          # A's own bare-board annotations
            *move,
            *[m.animate.scale(s, about_point=c).shift(dx) for m in above],   # reframe the diagonal above
            run_time=0.9)
        self.play(*[GrowFromPoint(kids, dot.get_center()) for kids, dot in grows], run_time=0.6)
        # beat y's _a_replica needs ONLY the on-screen A node (to align the replica) — keep that dot,
        # not the whole a_ref layout tree, so a_ref (scaffolding) is collected when this beat returns.
        self.a_root, self.ao_edge = ah.dot, ao_edge
        self.a_hit_trees = hit_trees
        self.a_hit_edges = [be for be, bd in hits]
        # keep self.o_subtree — it's now the slid miss child of A (a later choose_a would fold it in)
        self.avg_o = None
        self.o_ref = None                            # O's layout scaffolding — last used here; drop it

    # ── solve O's SIBLINGS — A's HIT children a_ ({…}=3.0) and _a ({…}=2.5) — sub-step of beat i,
    #        grown white-rooted above. Just like every other node: show each one's avg, cycle ALL its
    #        tied first-guesses, settle on the optimal (T for both), lock its root + edges green. The
    #        same _solve_position_hits helper at the root; leaves the whole tree green for beat j. ──
    def _solve_a_hit(self):
        self.a_hit_avg = self._solve_position_hits(0, self.a_hit_trees)

    # ── j : compare EVERY first letter. The leftover '2.50' fades FIRST; then MORPH the solved
    #        A-tree 1:1 into the top-left GRID corner (every node/edge to its counterpart, green
    #        recolouring to red-white, every letter but the root A riding out) and only AFTER it
    #        lands does A's 'Avg misses' label appear. Fill the rest of the grid with each valid
    #        opener's optimal tree (red-white shape, ENLARGED lettered root, a big same-size
    #        'Avg misses: N.NN' above). GREEN the winner (A, min = 3.88) IN its slot, fade the
    #        rest, then MORPH A back to full screen — recolouring BACK to red-white as it travels,
    #        its letters + blanks fading in, its avg label fading out MOVING with the tree.
    #        The on-screen A-tree is a patchwork of many `_ctree`s (no single recursive handle
    #        structure), so we SWAP in a geometrically-identical clean `_ctree` replica (invisible
    #        — same spec via `self.a_spec`, aligned to `a_ref`) and morph THAT. Every value SOURCED.
    def _tree_handles(self, g):
        """Every node/leaf handle of a `_ctree`, walked from the root (`.root_h`) — includes the
        UNkeyed interior nodes `g.node` doesn't collect. Used to strip a grid cell to shape + root."""
        out, stack = [], [g.root_h]
        while stack:
            h = stack.pop()
            out.append(h)
            stack.extend(getattr(h, "kids", []))
        return out

    def _strip_to_shape(self, g):
        """Drop every guess-node LETTER and leaf BLANK except the ROOT's letter — leaving the tree
        SHAPE (dots + edges) with only the starting letter (script: 'removing letters except the one
        in the top node'). The dropped mobjects still EXIST (handles keep them) so a morph can fade
        them out / their counterparts back in."""
        root = g.root_h
        rm = [h.blk if getattr(h, "is_leaf", False) else h.lab
              for h in self._tree_handles(g) if h is not root]
        g.remove(*rm)
        return g

    def _enlarge_root(self, g, factor):
        """Scale a `_ctree`'s ROOT node + its letter about the root centre so a grid cell's TOP node
        reads as a lettered header even when the interior nodes are tiny. Out-edges tuck under the
        bigger dot (z-index)."""
        VGroup(g.root, g.root_h.lab).scale(factor, about_point=g.root.get_center())
        return g

    def _opener_cells(self):
        """The 20 valid (splitting) openers' optimal trees, tiled 4×5, sorted by avg misses so the
        WINNER is the top-left corner. Each cell = a red-white tree shape with an ENLARGED lettered
        root + a worded 'Avg misses: N.NN' (built at a FIXED height AFTER tiling, so it stays big
        regardless of the tree's tile scale). Every subtree + value SOURCED."""
        opts = sorted((o for o in DATA["tree"]["options"] if o["splits"]),
                      key=lambda o: (o["avg"], o["letter"]))
        trees = []
        for o in opts:
            # A's cell uses the SAME spec as the replica/return target (self.a_spec) so the morph is
            # a true 1:1 pairing (a mismatched spec leaves unpaired edges as strays); the other 19 are
            # never morphed, so their raw _subtree_spec is fine.
            spec = self.a_spec if o["letter"] == "a" else self._subtree_spec(o["subtree"])
            g = self._ctree(spec, root_miss=0, solved=False)
            self._strip_to_shape(g)
            self._enlarge_root(g, OPENER_ROOT_BIG)
            g._opt = o
            trees.append(g)
        # the SAME 4×5 grid as beat d — full GRID_W×GRID_H, so the trees use the whole screen
        self._tile(trees, rows=GRID_ROWS, cols=GRID_COLS)
        # each label sits in the TOP-LEFT corner of its grid BOX (not above its tree) — so every
        # label is aligned + left-justified regardless of its tree's height/width
        cw, ch = GRID_W / GRID_COLS, GRID_H / GRID_ROWS
        tlx, tly, inset = GRID_CENTER[0] - GRID_W / 2, GRID_CENTER[1] + GRID_H / 2, 0.12
        cells = []
        for idx, g in enumerate(trees):
            r, c = divmod(idx, GRID_COLS)
            # every label built IDENTICALLY (same string length, same fixed height) → all the SAME
            # size, and NOT part of the tiled tree so it stays big regardless of the tree's scale
            lab = self._value_label(g._opt["avg"], OPENER_LABEL_H, bare=False)
            lab.move_to([tlx + c * cw + inset, tly - r * ch - inset, 0], aligned_edge=UL)
            cells.append(VGroup(g, lab))
        return cells

    def _a_replica(self):
        """A fresh full `_ctree` of the walked A-tree (same `self.a_spec`), coloured to EXACTLY match
        beat x's end state (solved=True → subtree green, root A white, A→O red, A→hit edges white) and
        aligned to OVERLAY the on-screen patchwork A-tree (`a_ref` is a uniform transform of the same
        origin layout, so matching the root pins everything). Swapped in invisibly, then morphed 1:1."""
        a_root = self.a_root
        src = self._ctree(self.a_spec, root_miss=0, solved=True, tall_level=0)
        k = a_root.width / src.root.width
        src.scale(k, about_point=src.root.get_center()).shift(a_root.get_center() - src.root.get_center())
        return src

    def _ctree_pairs(self, sh, dh):
        """Walk two structurally-identical `_ctree` handle trees (same spec) in lockstep, yielding
        ('node'|'leaf', s, d) per node and ('edge', s_kid, d_kid) per child in-edge — the 1:1
        correspondence a morph needs."""
        yield ("leaf" if getattr(sh, "is_leaf", False) else "node", sh, dh)
        for sk, dk in zip(sh.kids, dh.kids):
            yield ("edge", sk, dk)
            yield from self._ctree_pairs(sk, dk)

    def _morph_trees(self, src, dst, run_time, *, src_full, dst_full, extra_in=(), extra_out=()):
        """Piece-by-piece 1:1 morph of `_ctree` ``src`` into ``dst`` (same spec). Every dot + edge
        ReplacementTransforms to its counterpart (moving AND recolouring); the ROOT letter always
        transforms across. A non-root guess letter / leaf blank is 'extra' text, shown only when its
        side is ``*_full``: present both sides → transform; src-only → it rides toward its dst node and
        fades; dst-only → it fades in at its node (restoring stripped letters). ``extra_in`` play
        alongside; ``extra_out`` (e.g. a stale label) fade with the morph."""
        anims = list(extra_out)
        root = src.root_h
        for kind, sh, dh in self._ctree_pairs(src.root_h, dst.root_h):
            if kind == "edge":
                anims.append(ReplacementTransform(sh.in_edge, dh.in_edge))
                continue
            anims.append(ReplacementTransform(sh.dot, dh.dot))
            is_leaf = (kind == "leaf")
            s_txt, d_txt = (sh.blk, dh.blk) if is_leaf else (sh.lab, dh.lab)
            s_show = (sh is root) or src_full
            d_show = (sh is root) or dst_full
            if s_show and d_show:
                anims.append(ReplacementTransform(s_txt, d_txt))
            elif s_show and not d_show:
                # ride OUT: shrink toward the dst node while fading (moves WITH the tree)
                ghost = s_txt.copy().scale(max(1e-3, dh.dot.width / max(sh.dot.width, 1e-6))) \
                    .move_to(dh.dot).set_opacity(0)
                anims.append(Transform(s_txt, ghost))
            elif d_show and not s_show:
                # ride IN: start small + transparent AT the src node (z-index keeps it ABOVE the
                # dot), then Restore to its final pose — so it develops ON TOP of the node and
                # travels WITH the tree, NOT a fade-in-place the arriving dot then covers
                d_txt.save_state()
                d_txt.scale(max(1e-3, sh.dot.width / max(dh.dot.width, 1e-6))) \
                    .move_to(sh.dot).set_opacity(0)
                anims.append(Restore(d_txt))
        self.play(*anims, *extra_in, run_time=run_time)

    @subscene
    def compare_openers(self):
        self.op_cells = self._opener_cells()
        self._co_to_corner(0.4, 1.4, 0.5)  # '2.50' fades first, morph A into the corner, THEN its label
        self._co_fill_grid(1.4)            # the other 19 opener trees fill the rest of the grid
        self._co_pick_winner(1.0)          # green the winning (A) tree IN its grid slot, fade the rest
        self._co_return(1.6)               # morph A back to full screen, greening BACK to red-white

    def _co_to_corner(self, fade_num, morph, label_in):
        cell0, tree0 = self.op_cells[0], self.op_cells[0][0]
        # (1) the leftover position number fades out FIRST, before anything moves
        self.play(FadeOut(self.a_hit_avg), run_time=fade_num)
        self.a_hit_avg = None
        # (2) swap the on-screen patchwork tree for its geometrically-identical clean replica
        #     (invisible — no frame renders between remove and add), then morph it 1:1 to the corner
        src = self._a_replica()
        self.clear()
        self.add(src)
        self._morph_trees(src, tree0, morph, src_full=True, dst_full=False)
        self.clear()
        self.add(tree0)
        # (3) A's avg label appears only AFTER the tree has arrived
        self.play(FadeIn(cell0[1]), run_time=label_in)
        self.clear()
        self.add(cell0)

    def _co_fill_grid(self, run_time):
        # the rest of the grid (a bulk reference set) FADES in as a group (CLAUDE.md: enumerated
        # sets fade, they aren't hand-drawn)
        self.play(FadeIn(VGroup(*self.op_cells[1:])), run_time=run_time)

    def _co_pick_winner(self, run_time):
        # green ONLY the winning tree, IN its grid slot (its label stays as-is; it fades on return)
        cell0, tree0 = self.op_cells[0], self.op_cells[0][0]
        keep = set(tree0.root_h.lab.get_family())      # the navy 'A' stays navy (knocked out)
        greenable = VGroup(*[m for m in tree0.get_family() if m not in keep and m.has_points()])
        self.play(greenable.animate.set_color(LIGHT_GREEN),
                  FadeOut(VGroup(*self.op_cells[1:])), run_time=run_time)
        self.clear()
        self.add(cell0)

    def _co_return(self, run_time):
        cell0, tree0 = self.op_cells[0], self.op_cells[0][0]
        # the destination is the full-screen tree in NEUTRAL red-white — the green "winner" colour
        # changes BACK as the tree travels to the centre
        full = self._ctree(self.a_spec, root_miss=0, solved=False, tall_level=0)
        full.scale_to_fit_height(6.8)
        if full.width > 15.0:
            full.scale_to_fit_width(15.0)
        full.move_to([0, -0.3, 0])
        # the avg label fades out while MOVING (and growing) WITH the tree toward the centre
        lab = cell0[1]
        disp = full.root.get_center() - tree0.root.get_center()
        k = full.root.width / tree0.root.width
        ghost = lab.copy().scale(k).shift(disp).set_opacity(0)
        # morph the winning corner cell 1:1 to the full-screen tree — nodes/edges recolour green to
        # red-white while the stripped letters + leaf blanks fade back in at their nodes
        self._morph_trees(tree0, full, run_time, src_full=False, dst_full=True,
                          extra_out=[Transform(lab, ghost)])
        self.clear()
        self.add(full)
        self.winner = full
        # the whole back-up scaffolding + the 20-cell grid are now off-screen and dead — drop every
        # handle so this (and every later) snapshot pickles only the on-screen winner tree, not ~5
        # reference trees + 20 opener trees (that hoarding ballooned the beat-y snapshot to ~64 MB)
        self.a_root = self.op_cells = None
        self.o_subtree = self.i_subtree = self.e_subtree = self.u_subtree = None
        self.u_spine = self.ups = None
        self.a_hit_trees = self.o_hit_trees = self.i_hit_trees = self.e_hit_trees = None
        self.grid = None

    # ── k : DEDUP — the same letters in a different ORDER reach the same position, so a solved
    #        position isn't re-solved. Two parallel miss-DIAGONAL trees (the MISS branch is the LEFT
    #        child, matching the rest of the scene — spine grows DOWN-LEFT): LEFT guesses A then O,
    #        RIGHT guesses O then A. Each guess node (lettered; first white, then red-via-miss) fans its
    #        OTHER children — the hit branches — as BARE white dots DOWN-RIGHT (no letters, no blanks).
    #        The spine ends in a bare position NODE with the '_ _' board hanging below it (a gap wide
    #        enough that a revealed letter would fit above each rule) and the misses tallied under it.
    #        The hit-child COUNT is SOURCED (`_hit_count`: A and O each hit at pos 1 and pos 2). ───────
    def _hit_count(self, letter):
        """How many HIT branches a first-guess ``letter`` splits into (positions it can occupy) —
        SOURCED from the tree's option branches (A, O → 2 each: pos1, pos2)."""
        opt = {o["letter"]: o for o in DATA["tree"]["options"]}[letter]
        return sum(1 for p in opt["subtree"]["branches"] if set(p) != {"_"})

    def _dedup_tree(self, guesses, cx):
        """One miss-DIAGONAL tree rooted at ``cx`` — matching the rest of the scene, the MISS branch is
        the LEFT child, so the spine grows DOWN-LEFT (guess1 white --miss--> guess2 red --miss-->
        position, a bare red node), while each guess node's hit branches fan DOWN-RIGHT as bare white
        dots. The '_ _' board hangs below the position with the two missed letters (red, guessed order)
        tallied under the blanks. Exposed as per-level handles so it can EXTEND out level by level."""
        r = DEDUP_NODE_R
        cr = r * GRID_CHILD_RF                       # bare hit-child radius
        SPREAD, DY = 1.2, 1.85                       # horizontal step, level drop
        p0 = np.array([cx, 2.6, 0.0])
        p1 = p0 + np.array([-SPREAD, -DY, 0.0])      # guess2 — miss child, DOWN-LEFT
        p2 = p1 + np.array([-SPREAD, -DY, 0.0])      # position — miss child, DOWN-LEFT
        d0 = self._node_dot(p0, r=r, misses=0)       # guess1 — white (0 misses)
        l0 = self._node_letter(guesses[0], d0)
        d1 = self._node_dot(p1, r=r, misses=1)       # guess2 — red (reached via a miss)
        l1 = self._node_letter(guesses[1], d1)
        d2 = self._node_dot(p2, r=r, misses=1)       # position — bare red node (no letter)
        e1 = self._edge_line(d0, d1, LIGHT_RED)
        e2 = self._edge_line(d1, d2, LIGHT_RED)

        def hits(parent, ppos, g):                   # hit branches fan DOWN-RIGHT, bare white dots
            edges, dots = VGroup(), VGroup()
            for j in range(self._hit_count(g)):
                hd = Dot(ppos + np.array([SPREAD * (j + 1), -DY, 0.0]), radius=cr,
                         color=_miss_color(0))
                edges.add(self._edge_line(parent, hd, _miss_color(0)))
                dots.add(hd)
            return edges, dots
        h0e, h0d = hits(d0, p0, guesses[0])
        h1e, h1d = hits(d1, p1, guesses[1])
        # the board hangs WELL below the position node (room for a letter above each rule), with the
        # two missed letters (red, in the order guessed) tallied under the blanks
        blanks = self._blanks("__", h=0.5).next_to(d2, DOWN, buff=0.85).set_x(p2[0])
        tally = self._miss_row([c.upper() for c in guesses], h=0.34)
        tally.next_to(blanks, DOWN, buff=0.28).set_x(p2[0])
        board = VGroup(blanks, tally)
        return SimpleNamespace(
            all=VGroup(d0, l0, e1, h0e, h0d, d1, l1, e2, h1e, h1d, d2, board),
            d0=d0, l0=l0, e1=e1, h0e=h0e, h0d=h0d, d1=d1, l1=l1,
            e2=e2, h1e=h1e, h1d=h1d, d2=d2, board=board)

    def _dedup_level(self, T, lvl):
        """Animations that EXTEND tree ``T`` out by one level — the edges + hit dots + the miss child
        emanate from the level's parent. The guess LETTER is INCLUDED in the grown group (z-index keeps
        it above its dot), so it rides IN on the node as it grows, rather than fading in already placed.
        lvl 1 grows off guess1, lvl 2 off guess2 (down to the bare position node — no letter)."""
        if lvl == 1:
            parent, group = T.d0, VGroup(T.e1, T.h0e, T.h0d, T.d1, T.l1)
        else:
            parent, group = T.d1, VGroup(T.e2, T.h1e, T.h1d, T.d2)
        return [GrowFromPoint(group, parent.get_center())]

    def _setup_dedup(self):
        self.dd_left = self._dedup_tree(["a", "o"], -4.0)    # A missed, then O
        self.dd_right = self._dedup_tree(["o", "a"], 4.0)    # O missed, then A

    @subscene
    def dedup(self):
        self._setup_dedup()
        # clear the full A-tree carried in from beat y, then EXTEND both trees out TOGETHER, level by
        # level: the roots, then each guess's children, then the boards
        self.play(FadeOut(self.winner), run_time=0.6)
        self.winner = None
        L, R = self.dd_left, self.dd_right
        # the root letter grows WITH its node (not a separate fade-in), like every level below
        self.play(GrowFromCenter(VGroup(L.d0, L.l0)),
                  GrowFromCenter(VGroup(R.d0, R.l0)), run_time=0.6)
        self.play(*self._dedup_level(L, 1), *self._dedup_level(R, 1), run_time=0.6)
        self.play(*self._dedup_level(L, 2), *self._dedup_level(R, 2), run_time=0.6)
        self.play(FadeIn(L.board), FadeIn(R.board), run_time=0.6)

    # ── l : a BAD guess that can only miss. After a successful A gives '_A' (A in pos 2 — the words
    #        FA/LA/MA/PA/TA/YA), guessing U — which can't be in any '_A' word — yields a SINGLE (miss)
    #        branch, so it's a wasted check we can skip. Show ALL of A's branches (miss + both hits, the
    #        _a hit is the one we follow) for context. SOURCED: `_a` is A's pos-2 hit; U's option there
    #        has only the '__' branch (splits=False). Miss=LEFT / hits=RIGHT, matching the scene. ───────
    def _bg_board(self, dot, pattern, *, misses=None, direction=DOWN, buff=0.35):
        """A branch's board hung off ``dot``: the revealed-state blanks (``pattern``) + an optional red
        miss tally below them. Below the node by default; ``direction=RIGHT`` beside it (U, whose
        straight-down slot is taken by its miss edge)."""
        b = self._blanks(pattern, h=0.5)
        if np.array_equal(direction, DOWN):
            b.next_to(dot, DOWN, buff=buff).set_x(dot.get_center()[0])
        else:
            b.next_to(dot, direction, buff=buff)
        grp = VGroup(b)
        if misses:
            mr = self._miss_row(misses, h=0.34)
            mr.next_to(b, DOWN, buff=0.2).set_x(b.get_center()[0])
            grp.add(mr)
        return grp

    def _setup_badguess(self):
        r = DEDUP_NODE_R
        cr = r * GRID_CHILD_RF
        SPREAD, DY = 1.7, 1.7
        ax, ay = -1.7, 3.0
        a = self._node_dot([ax, ay, 0], r=r, misses=0)          # guess A (root, white)
        al = self._node_letter("a", a)
        # A's three branches: miss down-LEFT (red), the two hits down-RIGHT (white); the 2nd hit (_a,
        # A in pos 2) leads to the U guess node. EACH branch carries its board (revealed state).
        d_miss = self._node_dot([ax - SPREAD, ay - DY, 0], r=cr, misses=1)   # __  (A missed)
        d_a_ = self._node_dot([ax + SPREAD, ay - DY, 0], r=cr, misses=0)     # a_  (A in pos 1)
        u = self._node_dot([ax + 2 * SPREAD, ay - DY, 0], r=r, misses=0)     # guess U at state '_A'
        ul = self._node_letter("u", u)
        e_miss = self._edge_line(a, d_miss, LIGHT_RED)
        e_a_ = self._edge_line(a, d_a_, _miss_color(0))
        e_ua = self._edge_line(a, u, _miss_color(0))            # the _a hit → U
        b_miss = self._bg_board(d_miss, "__", misses=["A"])     # '_ _' + A missed
        b_a_ = self._bg_board(d_a_, "a_")                       # 'A _'
        b_u = self._bg_board(u, "_a", direction=RIGHT, buff=0.4)  # '_ A' beside U (below = its edge)
        # U's SINGLE branch — a miss, STRAIGHT DOWN (the single-child convention); U can only miss
        d_um = self._node_dot([ax + 2 * SPREAD, ay - 2 * DY, 0], r=cr, misses=1)
        e_um = self._edge_line(u, d_um, LIGHT_RED)
        b_um = self._bg_board(d_um, "_a", misses=["U"])         # '_ A' + U missed
        self.bg = SimpleNamespace(
            a=a, al=al, d_miss=d_miss, d_a_=d_a_, u=u, ul=ul, d_um=d_um,
            e_miss=e_miss, e_a_=e_a_, e_ua=e_ua, e_um=e_um,
            b_miss=b_miss, b_a_=b_a_, b_u=b_u, b_um=b_um)

    @subscene
    def bad_guess(self):
        self._setup_badguess()
        # clear the two dedup trees carried in from beat z
        self.play(FadeOut(VGroup(self.dd_left.all, self.dd_right.all)), run_time=0.6)
        self.dd_left = self.dd_right = None
        bg = self.bg
        # A + all three branches (miss + both hits — 'all of A's branches'); the _a hit reaches U
        self.play(GrowFromCenter(VGroup(bg.a, bg.al)), run_time=0.5)
        self.play(GrowFromPoint(VGroup(bg.e_miss, bg.d_miss, bg.e_a_, bg.d_a_,
                                       bg.e_ua, bg.u, bg.ul), bg.a.get_center()), run_time=0.7)
        self.play(FadeIn(bg.b_miss), FadeIn(bg.b_a_), FadeIn(bg.b_u), run_time=0.5)
        # we're at '_A'; guessing U here can ONLY miss → a single branch straight down
        self.play(GrowFromPoint(VGroup(bg.e_um, bg.d_um), bg.u.get_center()), run_time=0.5)
        self.play(FadeIn(bg.b_um), run_time=0.4)

    # ── m : the PAIRED greedy-vs-optimal chart — avg misses by word length. LEFT bar = greedy
    #        (SOURCED greedy_data), RIGHT = optimal uniform (SOURCED scene17_chart_data). Solved
    #        lengths: solid green right bar. UNSOLVED lengths (converged=False): a RED bar to the
    #        LOWER bound + a lighter red BAND up to the UPPER bound (the un-narrowed range). Uses the
    #        shared grouped_bar_chart (extended with series_highlight + bands). Every value SOURCED. ──
    def _setup_paired_chart(self):
        greedy, opt = GDATA["avg_misses_by_length"], ODATA["uniform"]
        lengths = sorted(int(L) for L in opt if str(L) in greedy)
        cats = [str(L) for L in lengths]
        g_vals = [greedy[str(L)]["avg_misses"] for L in lengths]
        # optimal solid bar → the exact avg (solved) or the LOWER bound (unsolved); unsolved bars go
        # RED with a lighter band up to the UPPER bound
        o_vals, hl, bands = [], {}, []
        for L in lengths:
            o = opt[str(L)]
            o_vals.append(o["avg"] if o["converged"] else o["lower"])
            if not o["converged"]:
                hl[str(L)] = LIGHT_RED
                bands.append((1, str(L), o["upper"], LIGHT_RED, 0.35))
        chart = grouped_bar_chart(
            cats, [("Greedy", CHART_COLOR, g_vals), ("Optimal", LIGHT_GREEN, o_vals)],
            x_title="Word Length", ink_color=WHITE, series_highlight=[None, hl], bands=bands)
        gm = chart.chart_geom
        # long title wraps if passed to grouped_bar_chart (240pt cap) — build it small + scale up
        title = crisp_text("Average Misses by Word Length", font_size=10, color=WHITE, weight=BOLD)
        title.scale_to_fit_width(7.0).move_to([0, gm["cy"] + gm["height"] / 2 + 0.95, 0])
        self.paired = chart
        self.paired_title = title

    @subscene
    def paired_chart(self):
        self._setup_paired_chart()
        # clear beat za's bad-guess tree, then grow the bars while the axes/labels/legend/title fade
        # in; the uncertainty bands rise on top of the unsolved (red) optimal bars after
        self.play(FadeOut(VGroup(*[m for m in self.mobjects if isinstance(m, VMobject)])), run_time=0.6)
        chart = self.paired
        grow_bars(self, chart.bars, run_time=1.6,
                  extra=[FadeIn(chart.rest), FadeIn(self.paired_title)])
        self.play(FadeIn(chart.bands), run_time=0.5)

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
