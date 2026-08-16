"""SCENE 18 — the CHOOSING strategy (best-opener word choice, length 4).

The chooser's half of the game: how to pick words that are HARD to guess. We start
by naively picking the hardest single words, reject that, then hill-climb a per-word
frequency distribution (via letter-combo multipliers) that maximises the best-opener
guesser's average misses — starting from a UNIFORM (every word equally likely) game.

BEAT MAP (Script.md scene 18; --- delimited, 6 beats a-f + a transition beat g):
  a most_misses  — table "Words with Most Misses" (cols Words / # Misses), the words
                   the OPTIMAL guesser misses most. Words in BLUE; rows rise in with a
                   lagged upward cascade; only the top (14-miss) words are listed.
                   SOURCED scene18_data.most_misses (greedy-completed upper bound at the
                   unconverged short lengths — a NEAR-OPTIMAL number, per the user).
  b greedy_tree  — the GREEDY best-opener tree (uniform state, opener 'a'), LETTERED, built
                   LEVEL-BY-LEVEL from the top (intro-style, no camera): edges draw in from
                   their parents, nodes + guess letters fade in. It IS buckets[0]["tree"] —
                   the SAME tree the c–f mini trees use. SOURCED scene18_data (_greedy_tree,
                   guess per node).
  c strategy     — FIRST the beat-b box slides to the top-left mini slot while its letters
                   fade, morphing into the shape-only mini tree (ReplacementTransform each
                   dot/edge onto its mini twin). THEN "Average Misses: N" (counter, top);
                   LEFT = the most common real 2-letter words (by zipf), RIGHT = the most
                   common letter-combos, each a MULTI-ROW block of bars (3 rows of 10,
                   scene-17 style). Starts UNIFORM (every bar equal). SOURCED scene18_data.
  d try_keep     — a combo bar AND the words exhibiting it rise TOGETHER → the avg counts
                   UP; we KEEP it. Rising bars flash GREEN + the number flashes GREEN.
  e try_undo     — a DIFFERENT change → the avg counts DOWN (a failure, number CRIMSON) →
                   undo (NO number colour) → reset to the uniform start (NO number colour).
                   Rule: the avg number flashes green on a RISE, crimson on a DROP, but an
                   UNDO/reset counts with no colour change. A frequency adjustment moves the
                   combo bars and the word bars at the SAME time (one play).
  f replay       — replay the optimization uniform→final in N_BUCKETS steps: each step
                   morphs the combo bars, then the word bars, then the avg (grow = green,
                   shrink = crimson).
  g clear_all    — TRANSITION (not a script beat): fade bars/avg/tree out → blank, for scene 19

REUSE MAP (styling sources):
  - bars    : bpkfigures.bar_graph get_bar_chart / grow_bars (scene-17 word-frequency bars)
  - text    : crisp_text (non-chalkboard world), ink BLACK, bold bar labels
  - counter : a ValueTracker + become() so the avg number never moves or resizes
  - colours : ACCENT_FILL bars; grow = ACCENT_GREEN, shrink = CRIMSON; blue words

FLAGS (owned by a human — tune/decide in the timing+polish pass):
  - beat b: the lettered greedy tree sits on a navy card (the tree world is navy, scenes
    01/05); GT_BOX / GT_DOT_R / GT_LETTER_H / GT_LEVEL_RT + card sizing are layout guesses.
  - TRACK_N (30) / PER_ROW (10) / row geometry / BAR_LABEL_FS / all run_times = guesses.
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets import scene18_data
from bpkfigures.chalkboard import BOARD_NAVY, CHALK
from bpkfigures.bar_graph import get_bar_chart, grow_bars

INK = BLACK                       # dark labels on the brand light-blue bg (scene-17 convention)
WORD_BLUE = ACCENT_FILL           # the blue words in the beat-a table + the resting bars
GROW_GREEN = ACCENT_GREEN         # a bar flashes green while it GROWS
SHRINK_CRIMSON = CRIMSON          # a bar flashes crimson while it SHRINKS
TITLE_Y = 3.7                     # beat-a table title

# ── beat-c/d/e/f bar composition (length 2 → 3 rows of 10) ────────────────────
WORD_CX, COMBO_CX = -4.0, 4.0     # left = words, right = combos
ROW_W = 7.0                       # each side's row width (a touch wider for 10 bars/row)
PER_ROW = 10                      # bars per row
ROW_H = 1.10                      # bar height at y_max (grown further)
BASE_YS = [-0.48, -2.18, -3.875]  # the 3 row BASELINES (bars grow up), placed so the top
                                  # margin (hypothetical top of the top bars → tree card bottom
                                  # at y 0.80) EQUALS the bottom margin (bottom-row labels →
                                  # frame edge at y -4.5); both ≈ 0.18. Labels bottom out at
                                  # base - 0.444 (label_buff 0.28 + cap_h 0.162 at 16pt).
BAR_LABEL_FS = 16                 # bold, scene-17-word-bar sized (smaller for 10 bars/row)

# ── the best-opener greedy TREE — the shared shape used by beat b (big, LETTERED, on its
#    own card) and the c–f mini trees (small, shape-only, top-left). `_tree_mob` builds
#    both from the same layout so beat b's box can morph into the mini tree. ──────────────
TREE_C = (WORD_CX, 2.35)          # MINI card centre: x over the LEFT bars, y lowered from top
TREE_W, TREE_H = 6.2, 2.4         # the mini plotting box inside the card
AVG_C = (COMBO_CX, 2.35)          # "Average Misses: N" readout — centred over the RIGHT bars
AVG_W = 5.6                       # readout width (fixed, so the number never resizes/jitters)
TREE_DOT_R = 0.03                 # mini node radius (a point)
TREE_EDGE_W = 1.3
TREE_MISS_COL = CRIMSON           # miss edges (the deep "spine")
TREE_HIT_COL = CHALK              # hit edges + nodes (off-white)

# ── beat b : the GREEDY best-opener tree (uniform state, opener 'a'), LETTERED, built
#    level-by-level from the top (intro-style, no camera move). It IS the SAME tree beat c
#    uses (buckets[0]["tree"]); at the START of beat c the whole box slides to the top-left
#    mini slot while the letters fade, morphing into the shape-only mini tree. ────────────
GT_BOX = (14.4, 6.2, 0.0, 0.55)   # big tree plotting box: W, H, centre x, centre y (large)
GT_DOT_R = 0.14                   # letter-holding node radius (big)
GT_LETTER_H = 0.16                # guess-letter height (navy, knocked out of the chalk dot)
GT_EDGE_W = 2.0                   # edge stroke width (big display)
GT_LEVEL_RT = 0.7                 # each level takes the SAME time → constant-rate (continuous)
GT_DOT_APPEAR = 0.9               # child nodes pop at this fraction of the edge growth (intro)
GT_EASE_FRAC = 0.4                # first level only: fraction of its time ramping up to speed


def _appear_at_end(t):
    """Hold at 0 until GT_DOT_APPEAR (the edge has ~reached the node), then ramp to 1 —
    so a level's child nodes pop in as its edges finish growing (mirrors the intro)."""
    return 0.0 if t < GT_DOT_APPEAR else (t - GT_DOT_APPEAR) / (1 - GT_DOT_APPEAR)


def _ease_then_linear(t):
    """First level only: ramp velocity from 0 over GT_EASE_FRAC, then hold CONSTANT — ending
    at the linear levels' speed so growth hands off with no deceleration (the intro trick that
    makes the tree expand smoothly, never stopping between levels)."""
    s = GT_EASE_FRAC
    vfull = 1.0 / (1.0 - s / 2.0)
    return 0.5 * vfull * t * t / s if t <= s else 0.5 * vfull * s + vfull * (t - s)


class Scene18(HangmanScene):
    """The choosing strategy. See the module docstring for the beat map + flags."""

    def setup_scene(self):
        self.data = scene18_data.get()
        opt = self.data["optimization"]
        self.combos = opt["tracked_combos"]
        self.words = opt["tracked_words"]
        # per-side fixed y_max so every state's bars share one scale
        self.combo_ymax = max(max(b["combo_mult"]) for b in opt["buckets"])
        self.word_ymax = max(max(b["word_freq"]) for b in opt["buckets"])
        self.avg_tracker = ValueTracker(0.0)     # bare tracker pickles fine (updater added in body)
        # carried mobjects / state
        self.table = None
        self.gtree = self.gcard = None           # beat-b big LETTERED greedy tree (+ its card),
                                                 # morphed into the mini tree at the start of beat c
        self.foot = None                         # beat-b "*See blog post…" footnote
        self.mini_card = self.tree_mob = None    # beat-c+ mini greedy tree (+ its navy card)
        self.avg_readout = None                  # single-text "Average Misses: N.NN" counter
        self.word_charts = self.combo_charts = None
        self.word_bars = self.combo_bars = None
        self.word_base = self.combo_base = None
        self.word_vals = self.combo_vals = None

    # ── text helpers ──────────────────────────────────────────────────────────
    def _fit_text(self, text, width, **kw):
        # long crisp_text wraps at the 240pt supersample; build small, scale to width
        return crisp_text(text, font_size=10, **kw).scale_to_fit_width(width)

    def _avg_readout(self, value, color=INK):
        """The WHOLE 'Average Misses: N.NN' as ONE text (label + number inherently share a
        baseline — no two-mobject alignment). Fixed left edge + scale, so counting never
        shifts/resizes it; the fixed prefix keeps its height (and baseline) constant. Only
        the NUMBER flashes ``color`` while it counts (green up / crimson down); the words
        'Average Misses:' stay INK — recolour just the trailing number glyphs."""
        numstr = f"{value:.2f}"
        mob = (crisp_text(f"Average Misses: {numstr}", font_size=10, color=INK,
                          weight=BOLD).scale(self.avg_scale)
               .move_to([0, self.avg_y, 0]).align_to([self.avg_left, 0, 0], LEFT))
        if color != INK:
            mob[-len(numstr):].set_color(color)      # numstr has no spaces → one glyph/char
        return mob

    def _avg_updater(self, v0, v1, flash):
        """The become()-from-tracker updater for a count from ``v0`` to ``v1``. When misses
        go UP the readout flashes green, DOWN crimson, then eases back to INK — UNLESS
        ``flash='none'`` (an UNDO/reset: count with no colour change). Mirrors the bars'
        flash-then-settle (`_grow_anim`)."""
        col = None if flash == "none" else \
            (GROW_GREEN if v1 > v0 + 1e-9 else SHRINK_CRIMSON if v1 < v0 - 1e-9 else None)

        def upd(m):
            v = self.avg_tracker.get_value()
            c = INK
            if col is not None and abs(v1 - v0) > 1e-9:
                a = (v - v0) / (v1 - v0)                       # 0..1 count progress
                t = 0.0 if a < 0.72 else (a - 0.72) / 0.28     # hold flash colour, then ease to INK
                c = interpolate_color(col, INK, t)
            m.become(self._avg_readout(v, color=c))
        return upd

    def _setup_avg(self, value):
        ref = crisp_text("Average Misses: 0.00", font_size=10, color=INK, weight=BOLD)
        self.avg_scale = AVG_W / ref.width                 # fixed scale (readout never resizes)
        ref.scale(self.avg_scale).move_to([AVG_C[0], AVG_C[1], 0])
        self.avg_left, self.avg_y = ref.get_left()[0], ref.get_center()[1]
        self.avg_readout = self._avg_readout(value)
        self.avg_tracker.set_value(value)

    def _count_to(self, value, run_time, flash="auto"):
        """Animate the avg readout to ``value`` with a counter (become() from the tracker);
        flashes green/crimson by direction (``flash='none'`` → no colour, for an undo)."""
        v0 = self.avg_tracker.get_value()
        self.avg_readout.add_updater(self._avg_updater(v0, value, flash))
        self.play(self.avg_tracker.animate.set_value(value), run_time=run_time)
        self.avg_readout.clear_updaters()

    def _count_and_tree(self, state, run_time, flash="auto"):
        """Count the avg AND crossfade the mini tree to ``state``'s tree, together — the
        tree updates every time the avg does. The number flashes green (misses up) / crimson
        (down); ``flash='none'`` counts with NO colour change (an UNDO/reset)."""
        v0 = self.avg_tracker.get_value()
        new_tree = self._tree_mob(state["tree"])
        self.avg_readout.add_updater(self._avg_updater(v0, state["avg_misses"], flash))
        self.play(FadeOut(self.tree_mob), FadeIn(new_tree),
                  self.avg_tracker.animate.set_value(state["avg_misses"]), run_time=run_time)
        self.avg_readout.clear_updaters()
        self.tree_mob = new_tree

    # ── the best-opener greedy tree (beat b big+lettered, c/f mini shape-only) ─────
    def _tree_mob(self, tree, *, box=None, dot_r=TREE_DOT_R, edge_w=TREE_EDGE_W,
                  lettered=False, letter_h=None):
        """Draw the WHOLE greedy tree as dots + hit/miss edges (+ guess LETTERS if
        ``lettered``), fit into ``box`` (default the mini TREE box). Layout: leaves spread
        left→right, an internal node sits above its children, depth increases downward; miss
        edges are crimson, hits off-white; all node dots are chalk (a navy letter is knocked
        out for a lettered node). Returns a VGroup with handles .dots/.edges/.letters and,
        for the level-by-level build, .level_marks[d] (dots+letters at depth d) and
        .level_edges[d] (edges arriving at depth d; empty at d=0). Beats built by the SAME
        layout so a big lettered tree morphs onto its mini shape-only twin (beat b→c)."""
        W, H, CX, CY = box if box is not None else (TREE_W, TREE_H, TREE_C[0], TREE_C[1])
        lh = letter_h if letter_h is not None else dot_r * 1.3
        pos, leaf, dep = {}, [0], {}

        def layout(node, depth):
            dep[id(node)] = depth
            if node.get("leaf"):
                x = leaf[0]; leaf[0] += 1
            else:
                xs = [layout(k["sub"], depth + 1) for k in node["kids"]]
                x = sum(xs) / len(xs)
            pos[id(node)] = (x, depth)
            return x
        layout(tree, 0)

        xs = [p[0] for p in pos.values()]
        x0, x1 = min(xs), max(xs)
        dmax = max(p[1] for p in pos.values())
        sx = W / (x1 - x0 or 1)
        sy = H / (dmax or 1)

        def place(node):
            x, d = pos[id(node)]
            return [CX + (x - (x0 + x1) / 2) * sx, CY + H / 2 - d * sy, 0]

        edges, dots, letters = VGroup(), VGroup(), VGroup()
        lnodes = [[] for _ in range(dmax + 1)]        # per depth: (node marker group, parent centre)
        ledges = [VGroup() for _ in range(dmax + 1)]
        letter_dot_idx = []                           # dots-index of each letter's own node

        def draw(node, parent_c):
            c = place(node)
            d = dep[id(node)]
            dot = Dot(c, radius=dot_r, color=TREE_HIT_COL, z_index=2)
            di = len(dots)
            dots.add(dot)
            ng = VGroup(dot)                          # the whole node marker (dot + its letter)
            if lettered and not node.get("leaf"):
                lab = crisp_text(node["guess"].upper(), color=BOARD_NAVY, weight=BOLD)
                lab.scale_to_fit_height(lh).move_to(c).set_z_index(3)
                letters.add(lab); ng.add(lab); letter_dot_idx.append(di)
            lnodes[d].append((ng, None if parent_c is None else np.array(parent_c)))
            if not node.get("leaf"):
                for k in node["kids"]:
                    e = Line(c, place(k["sub"]), stroke_width=edge_w, z_index=-1,
                             color=(TREE_MISS_COL if k["miss"] else TREE_HIT_COL))
                    edges.add(e); ledges[dep[id(k["sub"])]].add(e)
                    draw(k["sub"], c)
        draw(tree, None)
        g = VGroup(edges, dots, letters)              # edges behind dots, letters on top
        g.dots, g.edges, g.letters = dots, edges, letters
        g.level_nodes, g.level_edges = lnodes, ledges
        g.letter_dot_idx = letter_dot_idx
        return g

    def _tree_card(self):
        return RoundedRectangle(width=TREE_W + 0.7, height=TREE_H + 0.7, corner_radius=0.15,
                                fill_color=BOARD_NAVY, fill_opacity=1.0, stroke_color=WHITE,
                                stroke_width=2, z_index=-5).move_to([*TREE_C, 0])

    # ── bar helpers ───────────────────────────────────────────────────────────
    def _build_side(self, cx, labels, values, y_max):
        """A side's bars as ROWS get_bar_charts; return (charts, flat bars, flat baselines).
        Labels are re-aligned to one line per row (get_bar_chart top-aligns bbox tops, so
        ascender/descender words otherwise sit at different heights)."""
        charts, bars, base = [], [], []
        for r, base_y in enumerate(BASE_YS):
            sl = slice(r * PER_ROW, (r + 1) * PER_ROW)
            items = list(zip(labels[sl], values[sl]))
            chart = get_bar_chart(
                items, center=[cx, base_y + ROW_H / 2, 0], width=ROW_W, height=ROW_H,
                y_max=y_max, n_slots=PER_ROW, bar_color=WORD_BLUE, ink_color=INK,
                baseline_labels=True,                      # sit labels on one baseline
                label_factory=lambda s: crisp_text(s.upper(), font_size=BAR_LABEL_FS,
                                                   color=INK, weight=BOLD))
            charts.append(chart)
            bars += list(chart.bars)
            base += [base_y] * len(chart.bars)
        return charts, bars, base

    def _grow_anim(self, bar, base_y, h0, h1, flash=None):
        """One bar height h0→h1, flashing a colour while it changes then settling to blue.
        flash=None → direction (grow GREEN / shrink CRIMSON); flash=<colour> → force that
        colour for a changing bar (e.g. CRIMSON for a failed change, or WORD_BLUE = no flash)."""
        eps = 1e-6
        changed = abs(h1 - h0) > eps
        if flash is not None:
            dcol = flash if changed else WORD_BLUE
        else:
            dcol = GROW_GREEN if h1 > h0 + eps else SHRINK_CRIMSON if changed else WORD_BLUE

        def upd(m, a):
            m.stretch_to_fit_height(max(interpolate(h0, h1, a), 1e-3), about_edge=DOWN)
            m.set_y(base_y + m.height / 2)                    # keep the base pinned
            t = 0.0 if a < 0.72 else (a - 0.72) / 0.28        # hold flash colour, then ease to blue
            m.set_color(interpolate_color(dcol, WORD_BLUE, t))
        return UpdateFromAlphaFunc(bar, upd)

    def _side_anims(self, bars, base, cur_vals, new_vals, y_max, flash=None):
        """The height-morph anims for ONE side (combos OR words); returns (anims, commit).
        Call commit() AFTER the play to write new_vals into cur_vals. Used to gather BOTH
        sides' anims into a SINGLE self.play so combos and words move together."""
        anims = [self._grow_anim(b, by, ROW_H * v0 / y_max, ROW_H * v1 / y_max, flash)
                 for b, by, v0, v1 in zip(bars, base, cur_vals, new_vals)]
        return anims, lambda: cur_vals.__setitem__(slice(None), list(new_vals))

    def _apply_state(self, state, run_time, flash=None):
        """Morph the combo bars AND the word bars to a {combo_mult, word_freq} state
        TOGETHER (one play) — a single frequency adjustment moves both sides at once."""
        ca, ccommit = self._side_anims(self.combo_bars, self.combo_base, self.combo_vals,
                                       state["combo_mult"], self.combo_ymax, flash)
        wa, wcommit = self._side_anims(self.word_bars, self.word_base, self.word_vals,
                                       state["word_freq"], self.word_ymax, flash)
        self.play(*ca, *wa, run_time=run_time)
        ccommit(); wcommit()

    def _apply_state_at_once(self, state, run_time, flash=None):
        """Morph combos, words AND the avg counter to a state ALL in one play (used for
        the reset — cleanup, not a deliberate combo→word→avg step)."""
        ca, ccommit = self._side_anims(self.combo_bars, self.combo_base, self.combo_vals,
                                       state["combo_mult"], self.combo_ymax, flash)
        wa, wcommit = self._side_anims(self.word_bars, self.word_base, self.word_vals,
                                       state["word_freq"], self.word_ymax, flash)
        anims = [*ca, *wa]
        new_tree = self._tree_mob(state["tree"])
        # reset (an UNDO) → count with NO colour change (flash='none')
        self.avg_readout.add_updater(
            self._avg_updater(self.avg_tracker.get_value(), state["avg_misses"], "none"))
        self.play(*anims, FadeOut(self.tree_mob), FadeIn(new_tree),
                  self.avg_tracker.animate.set_value(state["avg_misses"]), run_time=run_time)
        self.avg_readout.clear_updaters()
        self.tree_mob = new_tree
        ccommit(); wcommit()

    # ── a : "Words with Most Misses" — blue words, lagged upward rise, 14-miss set ──
    @subscene
    def most_misses(self):
        mm = self.data["most_misses"]
        top = [r for r in mm["table"] if r["misses"] == mm["max_misses"]]   # only the 14-miss words

        title = self._fit_text("Words with Most Misses", 7.0, color=INK,
                               weight=BOLD).move_to([0, TITLE_Y, 0])
        hdr = VGroup(crisp_text("Words", font_size=30, color=INK, weight=BOLD).move_to([-1.9, 2.5, 0]),
                     self._fit_text("# Misses", 1.8, color=INK, weight=BOLD).move_to([1.9, 2.5, 0]))
        rows = VGroup()
        for r, row in enumerate(top):
            by = 1.72 - r * 0.5                          # common baseline per row
            rows.add(VGroup(
                crisp_text(row["word"].upper(), font_size=26, color=WORD_BLUE, weight=BOLD,
                           baseline_at=(-1.9, by)),
                crisp_text(str(row["misses"]), font_size=26, color=INK, baseline_at=(1.9, by))))
        for row in rows:
            row.shift(DOWN * 0.4).set_opacity(0)          # start below + hidden → rise in

        self.table = VGroup(title, hdr, rows)
        self.play(FadeIn(title), FadeIn(hdr), run_time=0.6)
        self.play(LaggedStart(*[row.animate.shift(UP * 0.4).set_opacity(1) for row in rows],
                              lag_ratio=0.18), run_time=1.4)

    # ── b : the GREEDY best-opener tree (uniform), LETTERED, built level-by-level ──
    @subscene
    def greedy_tree(self):
        self.play(FadeOut(self.table), run_time=0.5)
        self.table = None

        uni = self.data["optimization"]["buckets"][0]          # bucket 0 = uniform tree
        tree = self._tree_mob(uni["tree"], box=GT_BOX, dot_r=GT_DOT_R, edge_w=GT_EDGE_W,
                              lettered=True, letter_h=GT_LETTER_H)
        card = RoundedRectangle(width=tree.width + 0.8, height=tree.height + 0.8,
                                corner_radius=0.2, fill_color=BOARD_NAVY, fill_opacity=1.0,
                                stroke_color=WHITE, stroke_width=2, z_index=-5)
        card.move_to(tree.get_center())
        # footnote with a RAISED asterisk (a superscript footnote marker), HALFWAY between the
        # card bottom and the frame edge
        body = crisp_text("See blog post for more information", font_size=10, color=INK)
        star = crisp_text("*", font_size=10, color=INK).next_to(body, LEFT, buff=0.04)
        star.set_y(body.get_top()[1])                 # centre it at the cap line → clearly raised
        foot = VGroup(star, body).scale_to_fit_width(6.0)
        foot.move_to([0, (card.get_bottom()[1] - config.frame_y_radius) / 2, 0])
        self.gtree, self.gcard, self.foot = tree, card, foot

        self.play(FadeIn(card), FadeIn(foot), run_time=0.6)
        self.play(GrowFromCenter(tree.level_nodes[0][0][0]), run_time=0.6)   # root grows in
        # grow ONE whole level at a time from the top (intro-style, no camera): each level's
        # edges grow AT ONCE (lag_ratio=0.0) and each child NODE grows out of its PARENT,
        # riding the edge's tip to its spot (GrowFromPoint, same rate) — so nodes emerge with
        # their edges instead of popping. ALL levels play in ONE continuous LaggedStart
        # (lag_ratio=1.0 → each level starts exactly as the previous ends) so there are NO
        # per-`play` boundary frames between levels — a single seamless timeline that never
        # stops (the intro used separate plays but hid the seams under its moving camera).
        levels = []
        for d in range(1, len(tree.level_nodes)):
            first = (d == 1)
            rf = _ease_then_linear if first else linear
            rt = GT_LEVEL_RT / (1 - GT_EASE_FRAC / 2) if first else GT_LEVEL_RT
            grows = [GrowFromPoint(ng, pc, rate_func=rf) for ng, pc in tree.level_nodes[d]]
            levels.append(AnimationGroup(
                Create(tree.level_edges[d], lag_ratio=0.0, rate_func=rf), *grows, run_time=rt))
        self.play(LaggedStart(*levels, lag_ratio=1.0))

    # ── c : the choosing strategy composition — starts UNIFORM (every bar equal) ──
    #     the beat-b box slides to the top-left, letters fading, into the mini tree.
    @subscene
    def strategy(self):
        uni = self.data["optimization"]["buckets"][0]          # bucket 0 = uniform
        self._setup_avg(uni["avg_misses"])
        self.mini_card = self._tree_card()
        self.tree_mob = self._tree_mob(uni["tree"])            # shape-only twin (same layout)

        # move the whole box to the top-left mini slot while the letters fade: morph the big
        # card→mini card and each big dot/edge→its mini twin (same traversal order). Each
        # letter RIDES its own node to that node's mini position, fading as it goes.
        morph = [ReplacementTransform(self.gcard, self.mini_card)]
        morph += [ReplacementTransform(bd, md)
                  for bd, md in zip(self.gtree.dots, self.tree_mob.dots)]
        morph += [ReplacementTransform(be, me)
                  for be, me in zip(self.gtree.edges, self.tree_mob.edges)]
        morph += [lab.animate.move_to(self.tree_mob.dots[di].get_center())
                  .scale(0.2).set_opacity(0)
                  for lab, di in zip(self.gtree.letters, self.gtree.letter_dot_idx)]
        morph.append(FadeOut(self.foot))               # the "*See blog post…" note leaves with the box
        self.play(*morph, run_time=1.2)
        self.remove(self.gtree.letters)
        self.gtree = self.gcard = self.foot = None

        self.word_charts, self.word_bars, self.word_base = self._build_side(
            WORD_CX, self.words, uni["word_freq"], self.word_ymax)
        self.combo_charts, self.combo_bars, self.combo_base = self._build_side(
            COMBO_CX, self.combos, uni["combo_mult"], self.combo_ymax)
        self.word_vals = list(uni["word_freq"])
        self.combo_vals = list(uni["combo_mult"])

        self.play(FadeIn(self.avg_readout), run_time=0.6)
        all_bars, label_fades = [], []
        for chart in (*self.word_charts, *self.combo_charts):
            self.add(chart)
            chart.labels.set_opacity(0)
            all_bars += list(chart.bars)
            label_fades.append(chart.labels.animate.set_opacity(1))
        grow_bars(self, all_bars, 1.3, lag=0.02, extra=label_fades)

    # ── d : a combo + its words rise TOGETHER → avg + tree update → keep ────────
    @subscene
    def try_keep(self):
        after = self.data["example_keep"]["after"]
        self._apply_state(after, 0.9)                          # combo + word bars rise together (green)
        self._count_and_tree(after, 0.8)                       # avg ticks UP + tree updates (kept)

    # ── e : a different change → avg counts DOWN (failure) → undo → reset ──────
    @subscene
    def try_undo(self):
        undo = self.data["example_undo"]
        # try the failing change: RAISE the e combo + its words → GREEN (direction rule); avg drops
        self._apply_state(undo["worse"], 0.9)
        self._count_and_tree(undo["worse"], 0.8)               # DOWN = failure → number CRIMSON
        # undo it: LOWER the e combo + its words back → CRIMSON (direction rule)
        self._apply_state(undo["base"], 0.7)
        self._count_and_tree(undo["base"], 0.6, flash="none")  # UNDO → number stays INK
        # reset the kept beat-d change (lower u) — JUST resetting: bars + avg + tree
        # together in ONE play, kept BLUE
        self._apply_state_at_once(undo["reset"], run_time=0.9, flash=WORD_BLUE)

    # ── f : replay the optimization uniform→final, one step per change ─────────
    @subscene
    def replay(self):
        buckets = self.data["optimization"]["buckets"]         # 0 (uniform) .. final
        step = 0.45                   # lockstep montage (identical steps) — one knob
        for b in buckets[1:]:
            self._apply_state(b, step)                         # combo + word bars move together
            self._count_and_tree(b, step * 0.9)                # avg + tree update together

    # g : TRANSITION to scene 19 — fade everything (bars, avg readout, tree) out to the
    #     blank brand background, which scene 19 opens on. (updaters are already cleared.)
    @subscene
    def clear_all(self):
        self.play(*[FadeOut(m) for m in list(self.mobjects)], run_time=1.0)
