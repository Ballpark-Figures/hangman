"""SCENE 99 — YouTube thumbnails (static title cards, NOT animated).

One `@thumbnail` per thumbnail; each builds a STATIC composition and `add`s it
(no `self.play`). `@thumbnail` (not `@subscene`) renders each frame INDEPENDENTLY
from a clean, empty frame with no carry-over — so keep the video's normal base
(`HangmanScene`, which applies the brand light-blue `BG_COLOR`). Modelled on
yahtzee's `99thumbnails.py` / battleship's `00thumbnail.py`.

Grab the PNG per thumbnail with:
    render 99a                 # 4K PNG (manim -s -qk), the upload asset
    render 99a --fast          # quick low-res PNG to check layout
Scene 99 auto-renders as a still image (no --thumb needed). The PNG lands (and
its path prints) under media/images/99thumbnails/.

Numbers on a thumbnail are still SOURCED, never invented.

BEAT MAP
  tierlist_gallows — tier list (SABCDEF, S-tier rainbow, all 26 letters filled) on
                     the LEFT, gallows on the RIGHT; every letter blurred EXCEPT the
                     three glyphs S, A, C (which happen to sit in the S/A/C tiers).
  split_bg         — same blurred tier list centred on a LIGHT-BLUE left half, a
                     WHITE gallows centred on a NAVY right half (split at x=0).
  split_bg_tree    — split bg; gallows top-middle switching black→white across the
                     split; tier list bottom-left; top of the optimal length-2 tree
                     (sourced, red/white) bottom-right.
  split_bg_flip    — light-blue TOP half + navy BOTTOM half; tier list top-left, tree
                     bottom-left, gallows on the right spanning the y=0 split (black
                     on top / white on bottom). Equal gaps left→tree→gallows→right.
  split_bg_spread  — same split; tier list top-left, gallows top-right (black), the tree
                     spread WIDE across the navy bottom (off the bottom).
  split_bg_spread_len3 — as split_bg_spread, but the LENGTH-3 tree the intro grows
                     (winprob uniform n=5), same red/white styling.
"""
from pathlib import Path
import sys
import json

import numpy as np
from manim import config as MCFG          # real frame is 16x9 (x-radius 8, y 4.5)

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import *
from assets import tier_list as tl
from assets import tree2_data
from assets.hangman_board import hangman_drawing
from bpkfigures.chalkboard import BOARD_NAVY, CHALK

# the intro's LENGTH-3 winprob (uniform, n=5) tree — scene 01's sourced tree
INTRO_TREE_PATH = (Path(__file__).resolve().parents[2]
                   / "math/data/shared/winprob/len03_uniform_n05.json")

# ── tierlist_gallows layout (brand light-blue bg) ─────────────────────────────
TL_SCALE   = 0.92                    # tier-list scale
LETTER_INK = WHITE                   # filled tier letters (pop on the dark panels)
KEEP_SHARP = {"S", "A", "C"}         # the only glyphs left un-blurred

GAL_INK      = BLACK                 # gallows ink — bold + dark on the cyan bg
GAL_STROKE   = 12.0                  # thumbnail-weight strokes (thick + bold)
GAL_HEIGHT   = 6.0                   # target gallows height

# blurred-letter blob (uniform soft gray oval — no letter shape leaks through)
BLOB_INK   = ManimColor("#CFD3D8")   # light gray, reads as a blurred white glyph
BLOB_W     = 0.62                    # oval width  (tier-list units, pre-TL_SCALE)
BLOB_H     = 0.72                    # oval height

# ── split_bg_tree layout (light-blue LEFT half + navy RIGHT half) ──────────────
GAL_SPLIT_SCALE = 1.0                # top-middle gallows scale
GAL_SPLIT_CY    = 2.15              # gallows centre y (top band)
TL_C_HEIGHT     = 4.3               # tier-list height in the bottom-left
TL_C_CENTER     = np.array([-4.0, -2.05, 0])

# optimal length-2 tree (SOURCED from tree2_data; red/white = scene 05's _miss_color
# scheme: a MISS node/edge is red, a HIT node/edge white, the guess letter knocked out
# navy). Full balanced tree, contour-packed and fit to the navy half's WIDTH (so nothing
# spills sideways into the light-blue half); TALL vertical spacing so the lower levels run
# OFF the bottom, with the root sitting in the upper area.
TREE_NODE_R    = 0.42
TREE_CHILD_RF  = 0.6                 # leaf-dot radius ÷ node radius
TREE_DY        = 3.1                 # parent → child vertical drop (tall → overflows the bottom)
TREE_MIN_SEP   = 0.95               # min horizontal gap between packed subtrees
TREE_EDGE_W    = 4.5
TREE_LETTER_H  = 1.3                # letter cap-height ÷ node radius (mirrors 05's NODE_LETTER_H)
TREE_MAX_DEPTH = None               # None = full tree (deep levels clip off the bottom)
TREE_TARGET_W  = 7.4                # fit width into a half's width (no sideways spill)
TREE_CENTER_X  = 4.0               # scene c: the VISIBLE content is centred here (navy half)
TREE_VISIBLE_ROWS = 4             # how many node rows are on-screen; the bottom edge lands
                                    # exactly between row (N-1) and row N

# ── split_bg_flip (d): light-blue TOP half + navy BOTTOM half ──────────────────
TLD_CENTER      = np.array([-4.2, 2.25, 0])   # tier list, top-left (on the light-blue half)
TLD_HEIGHT      = 3.7
TREE_D_CENTER_X = -4.0                          # tree centred here, bottom-left (on navy)
TREE_D_ROWS     = 4
GAL_D_SCALE     = 1.65                          # gallows on the right, spanning the y=0 split
GAL_D_CENTER_X  = 4.2

# ── split_bg_spread (e): tier list + gallows equally spaced across the top half,
#    the optimal tree spread WIDE across the navy bottom ──────────────────────────
TLE_HEIGHT      = 3.4
GAL_E_HEIGHT    = 3.6
GAL_E_STROKE    = 8.0               # thinner than the big c/d gallows
E_NODE_SCALE    = 0.59            # FIXED tree scale → node SIZE (independent of the spread)
E_TREE_SEP      = 1.33           # horizontal node separation (natural) → the wide spread
E_TREE_DY       = 1.9            # vertical spacing → 4 rows spread down the navy half
E_TREE_ROWS     = 4

# ── split_bg_spread_len3 (f): same layout as e, the intro's LENGTH-3 tree ──────
# The length-3 tree branches far more per node (up to 5 children). Auto-fits the visible
# rows to F_TREE_W: a WIDER target uses the frame margin → more spread AND bigger dots (no
# spill, since the fit clamps width). SEP evens the dense right clusters (relative, so it
# survives the refit); node_rf sizes the dots on top of the fit; DY drops to keep row 1 in
# the navy half now that the wider fit enlarges the row spacing too.
F_TREE_W        = 15.0           # fit the VISIBLE rows to this width (near-full frame → max spread)
F_TREE_SEP      = 1.45          # MIN gap between packed subtrees → evens the dense right clusters
F_TREE_DY       = 5.3            # vertical spacing → taller rows lift the root (bottom edge still bisects)
F_TREE_ROWS     = 3
F_NODE_RF       = 2.0           # node-radius factor (bigger dots, on top of the width fit)


class Thumbnails(HangmanScene):
    """Scene 99 — YouTube thumbnails. See module docstring for the beat map."""

    def setup_scene(self):
        pass

    # a : tier list (left) + gallows (right); all letters blurred but S, A, C
    @thumbnail
    def tierlist_gallows(self):
        tlist = self._blurred_tier_list()
        gallows = hangman_drawing(0, color=GAL_INK, stroke_width=GAL_STROKE)
        gallows.scale_to_fit_height(GAL_HEIGHT)

        # equal horizontal gaps: left edge → tier list → gallows → right edge
        fx = MCFG.frame_x_radius
        gap = (2 * fx - tlist.width - gallows.width) / 3
        tlist.move_to([-fx + gap + tlist.width / 2, 0, 0])
        gallows.move_to([-fx + 2 * gap + tlist.width + gallows.width / 2, 0, 0])

        self.add(tlist, gallows)

    # b : light-blue LEFT half (tier list centred) + navy RIGHT half (white gallows)
    @thumbnail
    def split_bg(self):
        fx, fy = MCFG.frame_x_radius, MCFG.frame_y_radius
        # navy covers the right half; the left half stays the brand light-blue bg.
        navy = Rectangle(width=fx + 0.5, height=2 * fy + 0.5, stroke_width=0,
                         fill_color=BOARD_NAVY, fill_opacity=1.0)
        navy.move_to([0, 0, 0], aligned_edge=LEFT)      # split exactly at x=0

        tlist = self._blurred_tier_list().move_to([-fx / 2, 0, 0])
        gallows = hangman_drawing(0, color=WHITE, stroke_width=GAL_STROKE)
        gallows.scale_to_fit_height(GAL_HEIGHT).move_to([fx / 2, 0, 0])

        self.add(navy, tlist, gallows)

    # c : split bg; gallows top-middle (black→white across the split); tier list
    #     bottom-left; top of the optimal length-2 tree bottom-right
    @thumbnail
    def split_bg_tree(self):
        fx, fy = MCFG.frame_x_radius, MCFG.frame_y_radius
        navy = Rectangle(width=fx + 0.5, height=2 * fy + 0.5, stroke_width=0,
                         fill_color=BOARD_NAVY, fill_opacity=1.0)
        navy.move_to([0, 0, 0], aligned_edge=LEFT)      # split exactly at x=0

        gallows = self._split_gallows(scale=GAL_SPLIT_SCALE, center_y=GAL_SPLIT_CY)

        tlist = self._blurred_tier_list()
        tlist.scale_to_fit_height(TL_C_HEIGHT).move_to(TL_C_CENTER)

        tree, _ = self._scaled_tree(spec=self._spec_len2(), visible_rows=TREE_VISIBLE_ROWS)
        tree.shift([TREE_CENTER_X, 0, 0])                 # centre visible content in the navy half

        self.add(navy, tlist, tree, gallows)

    # d : light-blue TOP half + navy BOTTOM half; tier list top-left, tree bottom-left,
    #     gallows on the right spanning the y=0 split (black on top / white on bottom)
    @thumbnail
    def split_bg_flip(self):
        fx, fy = MCFG.frame_x_radius, MCFG.frame_y_radius
        navy = Rectangle(width=2 * fx + 0.5, height=fy + 0.5, stroke_width=0,
                         fill_color=BOARD_NAVY, fill_opacity=1.0)
        navy.move_to([0, 0, 0], aligned_edge=UP)          # top edge at y=0 → bottom half navy

        tree, tree_w = self._scaled_tree(spec=self._spec_len2(), visible_rows=TREE_D_ROWS)
        gallows = self._hsplit_gallows(scale=GAL_D_SCALE, center_x=0)
        gal_w = gallows.width

        # equal horizontal gaps: left edge → tree → gallows → right edge
        gap = (2 * fx - tree_w - gal_w) / 3
        tree_cx = -fx + gap + tree_w / 2
        gal_cx = fx - gap - gal_w / 2
        tree.shift([tree_cx, 0, 0])
        gallows.move_to([gal_cx, 0, 0])

        # tier list centred between the left edge and the gallows' left edge
        tlist = self._blurred_tier_list()
        tlist.scale_to_fit_height(TLD_HEIGHT)
        tlist.move_to([(-fx + gal_cx - gal_w / 2) / 2, TLD_CENTER[1], 0])

        self.add(navy, tlist, tree, gallows)

    # e : light-blue TOP + navy BOTTOM; tier list top-left, gallows top-right (black on the
    #     light-blue), the optimal LENGTH-2 tree spread WIDE across the navy bottom
    @thumbnail
    def split_bg_spread(self):
        tree, _ = self._scaled_tree(spec=self._spec_len2(), visible_rows=E_TREE_ROWS,
                                    dy=E_TREE_DY, sep=E_TREE_SEP, node_scale=E_NODE_SCALE)
        self._spread_composition(tree, tl_h=TLE_HEIGHT, gal_h=GAL_E_HEIGHT,
                                 gal_stroke=GAL_E_STROKE)

    # f : same layout as e, but the LENGTH-3 tree the INTRO grows (winprob uniform n=5),
    #     rendered in the same red/white thumbnail styling, spread across the navy bottom
    @thumbnail
    def split_bg_spread_len3(self):
        tree, _ = self._scaled_tree(spec=self._spec_intro(), visible_rows=F_TREE_ROWS,
                                    target_w=F_TREE_W, dy=F_TREE_DY, sep=F_TREE_SEP,
                                    fit_visible=True, node_rf=F_NODE_RF,
                                    equalize_bottom=True)
        self._spread_composition(tree, tl_h=TLE_HEIGHT, gal_h=GAL_E_HEIGHT,
                                 gal_stroke=GAL_E_STROKE)

    # ── shared e/f composition: light-blue TOP + navy BOTTOM, tier list + gallows
    #    equally spaced across the top half; `tree` is already placed across the bottom
    def _spread_composition(self, tree, *, tl_h, gal_h, gal_stroke):
        fx, fy = MCFG.frame_x_radius, MCFG.frame_y_radius
        navy = Rectangle(width=2 * fx + 0.5, height=fy + 0.5, stroke_width=0,
                         fill_color=BOARD_NAVY, fill_opacity=1.0)
        navy.move_to([0, 0, 0], aligned_edge=UP)          # top edge at y=0 → bottom half navy

        top_cy = fy / 2                                   # vertical centre of the top half
        tlist = self._blurred_tier_list()
        tlist.scale_to_fit_height(tl_h)
        gallows = hangman_drawing(0, color=GAL_INK, stroke_width=gal_stroke)
        gallows.scale_to_fit_height(gal_h)

        # equal horizontal gaps: left edge → tier list → gallows → right edge
        gap = (2 * fx - tlist.width - gallows.width) / 3
        tlist.move_to([-fx + gap + tlist.width / 2, top_cy, 0])
        gallows.move_to([fx - gap - gallows.width / 2, top_cy, 0])

        self.add(navy, tlist, gallows, tree)

    # ── build + scale + vertically place the optimal tree: fit to `target_w`, N rows
    #    on-screen with the frame bottom bisecting the gap to row N, visible content
    #    (nodes + bottom-edge crossings) centred at x=0. Returns (tree, visible_width).
    def _scaled_tree(self, *, spec, visible_rows, target_w=TREE_TARGET_W, dy=TREE_DY,
                     fit_visible=False, sep=TREE_MIN_SEP, node_scale=None,
                     equal_margins=False, node_rf=1.0, equalize_bottom=False):
        eq_depth = visible_rows - 1 if equalize_bottom else None
        tree, nodes, edges = self._render_spec(spec, dy=dy, sep=sep, node_rf=node_rf,
                                               equalize_depth=eq_depth)
        n = visible_rows
        # natural x-extent of the ON-SCREEN content = visible NODES + where the bottom-
        # crossing edges meet the frame edge (the miss branch reaches further out there).
        nat = [x for x, d in nodes if d <= n - 1]
        nat += [(xp + xc) / 2 for xp, dp, xc in edges if dp == n - 1]
        vis_lo, vis_hi = min(nat), max(nat)
        # node_scale → FIX the overall scale (so node SIZE is independent of the spread,
        # which is then set by `sep`); fit_visible → visible rows span target_w; else fit
        # the FULL tree width (the narrow top rows stay well inside).
        if node_scale is not None:
            scale = node_scale
        elif fit_visible:
            scale = target_w / (vis_hi - vis_lo)
        else:
            scale = target_w / tree.width
        dys = dy * scale                                  # on-screen row spacing
        fy = MCFG.frame_y_radius
        if equal_margins:
            # centre the N visible rows so the root→top-of-navy gap equals the last-row→
            # bottom gap (both = (fy - (n-1)·dys)/2).
            root_y = ((n - 1) * dys - fy) / 2
        else:
            # place row (n-1) at -fy + dys/2 so the bottom edge (-fy) bisects the gap to row n
            root_y = -fy + dys / 2 + (n - 1) * dys
        lo, hi = vis_lo * scale, vis_hi * scale
        tree.scale(scale, about_point=ORIGIN)             # root stays at ORIGIN
        tree.shift([-(lo + hi) / 2, root_y, 0])           # centre visible content at x=0
        return tree, hi - lo

    # ── the split gallows (black left of x=0, white right of x=0) ─────────────
    def _split_gallows(self, *, scale, center_y):
        """The gallows straddling x=0: strokes on the LIGHT-BLUE half (x<0) are
        black, strokes on the NAVY half (x>0) are white. Built as CONTINUOUS
        polylines so the L-corners (post→beam, beam→rope) join cleanly — the same
        reason hangman_drawing uses one polyline; only the base and beam BREAK at
        x=0 to change colour (collinear there, so the black/white halves meet flush,
        no seam). Natural bbox is centred at x=0, so the split maps to screen x=0."""
        def poly(points, col):
            m = VMobject(stroke_color=col, stroke_width=GAL_STROKE,
                         joint_type=LineJointType.ROUND)
            m.set_points_as_corners([np.array([x, y, 0.0]) for x, y in points])
            return m
        g = VGroup(
            poly([(-1.3, -2.2), (0.0, -2.2)], GAL_INK),                 # base (left)
            poly([(-1.0, -2.2), (-1.0, 2.0), (0.0, 2.0)], GAL_INK),     # post + beam-left
            poly([(0.0, -2.2), (1.3, -2.2)], WHITE),                    # base (right)
            poly([(0.0, 2.0), (0.6, 2.0), (0.6, 1.55)], WHITE),         # beam-right + rope
        )
        g.scale(scale).move_to([0, center_y, 0])        # x-centre stays 0 → split at x=0
        for m in g:                                     # scaling can shrink stroke; restore
            m.set_stroke(width=GAL_STROKE)
        return g

    # ── the horizontally-split gallows (black above y=0, white below) ─────────
    def _hsplit_gallows(self, *, scale, center_x):
        """The gallows straddling y=0: strokes ABOVE the split (the LIGHT-BLUE top
        half) are black, strokes BELOW (the NAVY bottom half) are white. Only the
        POST crosses the split; it breaks there (collinear, so the two colours meet
        flush). The split sits at the natural bbox-centre y=-0.1, which maps to screen
        y=0 when the group's y-centre is 0."""
        SY = -0.1                                       # natural bbox-centre y = the split line
        def poly(points, col):
            m = VMobject(stroke_color=col, stroke_width=GAL_STROKE,
                         joint_type=LineJointType.ROUND)
            m.set_points_as_corners([np.array([x, y, 0.0]) for x, y in points])
            return m
        g = VGroup(
            poly([(-1.0, SY), (-1.0, 2.0), (0.6, 2.0), (0.6, 1.55)], GAL_INK),  # upper post+beam+rope
            poly([(-1.0, -2.2), (-1.0, SY)], WHITE),                            # lower post
            poly([(-1.3, -2.2), (1.3, -2.2)], WHITE),                           # base
        )
        g.scale(scale).move_to([center_x, 0, 0])        # y-centre stays 0 → split at y=0
        for m in g:                                     # scaling can shrink stroke; restore
            m.set_stroke(width=GAL_STROKE)
        return g

    # ── decision-tree SPEC builders (source JSON → nested {'g','kids'}/{'leaf'}) ──
    def _tree_spec(self, root, *, guess_key, branch_key, max_depth=TREE_MAX_DEPTH):
        """Turn a solver tree — nodes carry `guess_key` + a `branch_key` dict keyed by
        board pattern (the all-underscore pattern is the MISS); a CHILDLESS node is a
        terminal (a determined 'word', or a winprob LOSS leaf with neither) — into the
        nested spec the renderer walks: {'g': letter, 'kids': [(is_miss, spec), …]} or
        {'leaf': word}. Miss branch first (drawn leftmost / red). Works for any word
        length (miss = a pattern of only '_'). `max_depth` caps the build (deeper rows
        aren't drawn). Sourced structure, nothing invented."""
        def spec_of(node, depth):
            children = node.get(branch_key, {})
            if "word" in node or not children:      # terminal: word leaf OR winprob loss leaf
                return {"leaf": node.get("word")}
            if max_depth is not None and depth >= max_depth:
                return {"g": node.get(guess_key), "kids": []}
            items = sorted(children.items(), key=lambda kv: set(kv[0]) != {"_"})  # miss first
            kids = [(set(pat) == {"_"}, spec_of(ch, depth + 1)) for pat, ch in items]
            return {"g": node.get(guess_key), "kids": kids}
        return spec_of(root, 0)

    def _spec_len2(self):
        """The optimal LENGTH-2 tree (tree2_data / scene 05)."""
        return self._tree_spec(tree2_data.get()["tree"],
                               guess_key="optimal_letter", branch_key="children")

    def _spec_intro(self):
        """The winprob LENGTH-3 uniform n=5 tree the INTRO (scene 01) grows — capped
        at F_TREE_ROWS deep (the deeper rows run off the bottom anyway)."""
        return self._tree_spec(json.loads(INTRO_TREE_PATH.read_text())["tree"],
                               guess_key="guess", branch_key="branches",
                               max_depth=F_TREE_ROWS)

    # ── evenly space one row of a packed tree (post-process the layout node tree) ──
    def _equalize_row(self, root, target_depth):
        """Redistribute the nodes at `target_depth` to EQUAL spacing across the same
        [min,max] x-span the contour packer produced, dragging each node's whole subtree
        along (so off-screen descendants stay attached), then re-center every ancestor
        over its children bottom-up. Mutates the layout node tree in place."""
        row = []
        def collect(node, depth):
            if depth == target_depth:
                row.append(node)
                return
            for _, c in node["kids"]:
                collect(c, depth + 1)
        collect(root, 0)
        if len(row) < 2:
            return
        row.sort(key=lambda nd: nd["x"])
        x_lo, x_hi = row[0]["x"], row[-1]["x"]
        step = (x_hi - x_lo) / (len(row) - 1)
        def shift_sub(node, dx):
            node["x"] += dx
            for _, c in node["kids"]:
                shift_sub(c, dx)
        for i, nd in enumerate(row):
            shift_sub(nd, (x_lo + i * step) - nd["x"])
        def recenter(node, depth):                          # post-order → parents use new child x
            if depth >= target_depth:
                return
            for _, c in node["kids"]:
                recenter(c, depth + 1)
            if node["kids"]:
                node["x"] = sum(c["x"] for _, c in node["kids"]) / len(node["kids"])
        recenter(root, 0)

    # ── render a tree spec (sourced structure; scene-05 red/white styling) ────────
    def _render_spec(self, spec, *, dy, sep, node_rf=1.0, equalize_depth=None):
        """Lay out `spec` (Reingold-Tilford contour packing, lifted from 05's `_ctree`)
        and build the mobjects — miss subtree LEFT (red) / hit RIGHT (white), each guess
        node the letter knocked out in navy. Built at natural sizes rooted at ORIGIN.
        `node_rf` scales the node dot radius only (spacing is unchanged, so bigger dots
        at the same horizontal fit). `equalize_depth` (an int depth) REDISTRIBUTES every
        node at that depth to EQUAL horizontal spacing across the same [min,max] span the
        packer gave them, carries each node's off-screen subtree along, then re-centers all
        ancestors over their children — so the bottom visible row is evenly spaced instead
        of contour-packed (dense clusters spread, sparse ones tighten). Returns
        (group, nodes, edges): nodes=[(x,depth)], edges=[(x_par,depth,x_child)]."""
        r, cr = TREE_NODE_R * node_rf, TREE_NODE_R * node_rf * TREE_CHILD_RF
        DY, SEP, INF = dy, sep, float("inf")

        def kids_of(sp):
            return [] if "leaf" in sp else sp["kids"]

        def shift_x(node, dx):
            node["x"] += dx
            for _, c in node["kids"]:
                shift_x(c, dx)

        def layout(sp, depth):
            node = {"spec": sp, "y": -depth * DY, "kids": []}
            kids = kids_of(sp)
            if not kids:
                node["x"] = 0.0
                return node, {depth: 0.0}, {depth: 0.0}
            lcont, rcont = {}, {}
            for i, (is_miss, cs) in enumerate(kids):
                cnode, cl, crr = layout(cs, depth + 1)
                off = 0.0
                if i:
                    off = max([0.0] + [rcont[d] - x + SEP for d, x in cl.items() if d in rcont])
                    shift_x(cnode, off)
                node["kids"].append((is_miss, cnode))
                for d, x in cl.items():
                    lcont[d] = min(lcont.get(d, INF), x + off)
                for d, x in crr.items():
                    rcont[d] = max(rcont.get(d, -INF), x + off)
            node["x"] = sum(c["x"] for _, c in node["kids"]) / len(node["kids"])  # centre over children
            lcont[depth] = min(lcont.get(depth, INF), node["x"])
            rcont[depth] = max(rcont.get(depth, -INF), node["x"])
            return node, lcont, rcont

        root, _, _ = layout(spec, 0)
        if equalize_depth is not None:
            self._equalize_row(root, equalize_depth)
        x0 = root["x"]
        g = VGroup()
        nodes = []                                      # (x_natural, depth) for every node
        edges = []                                      # (x_parent, depth_parent, x_child) natural

        def _mc(miss):                                  # mirrors 05optimal._miss_color
            return LIGHT_RED if miss else CHALK

        def build(node, in_miss, depth):
            pos = np.array([node["x"] - x0, node["y"], 0.0])
            nodes.append((pos[0], depth))
            sp = node["spec"]
            if "leaf" in sp:
                dot = Dot(pos, radius=cr, color=_mc(in_miss), z_index=2)
                g.add(dot)
                return pos, cr
            dot = Dot(pos, radius=r, color=_mc(in_miss), z_index=2)
            lab = crisp_text(sp["g"].upper(), color=BOARD_NAVY, weight=BOLD)
            lab.scale_to_fit_height(TREE_LETTER_H * r).move_to(dot).set_z_index(3)
            g.add(dot, lab)
            for is_miss, child in node["kids"]:
                cpos, crad = build(child, is_miss, depth + 1)
                edges.append((pos[0], depth, cpos[0]))
                dn = normalize(cpos - pos)
                edge = Line(pos + dn * r, cpos - dn * crad, color=_mc(is_miss),
                            stroke_width=TREE_EDGE_W, z_index=1)  # over navy(0), under dots(2)
                g.add(edge)
            return pos, r

        build(root, False, 0)                           # root guess = white (no miss)
        return g, nodes, edges

    # ── shared tier-list builder ─────────────────────────────────────────────
    def _blurred_tier_list(self):
        """The tier list filled with all 26 letters, every glyph blurred to a soft
        uniform blob EXCEPT S/A/C, scaled to TL_SCALE. Blobs are added INTO the
        returned VGroup so a later move_to(...) carries them along."""
        letters = tl.TIER_LETTERS                       # 26 letters, one string / tier
        tlist = tl.get_tier_list("letter")              # rainbow cells, grade labels
        for i in range(len(letters)):
            tl.fill_tier(tlist, i, height=0.5)
        tmap = tl.tile_map(tlist, letters)              # {glyph: tile}
        for tile in tmap.values():                      # neutral white letters
            tile.set_color(LETTER_INK)
        tlist.scale(TL_SCALE)
        for ch, tile in tmap.items():                   # blur all but S/A/C
            if ch in KEEP_SHARP:
                continue
            tlist.add(self._blob(tile.get_center()))
            tile.set_opacity(0)
        return tlist

    # ── manim-native "blur": a soft gray oval that fades from the centre out ──
    def _blob(self, center, *, layers=16, per_op=0.13):
        """A radial-gradient oval (no native gaussian): concentric ellipses from
        full BLOB_W×BLOB_H down to a point, all centred, each faint — so they
        accumulate opaque in the centre and fade to transparent at the rim. Every
        blob is the SAME size, so no letter shape survives. Sized in TL_SCALE units."""
        w, h = BLOB_W * TL_SCALE, BLOB_H * TL_SCALE
        g = VGroup()
        for i in range(layers):
            t = i / (layers - 1)                        # 0 outer … 1 inner
            g.add(Ellipse(width=w * (1 - t) + 1e-3, height=h * (1 - t) + 1e-3,
                          stroke_width=0, fill_color=BLOB_INK, fill_opacity=per_op)
                  .move_to(center))
        return g
