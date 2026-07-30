"""PROTOTYPE — walk the optimal-strategy tree down a single real game (BALLPARK).

Concept (a top-anchored VERTICAL STACK, one guess per subscene):
  • Each node is a STATE: its blanked board (as it appeared on ARRIVAL — the result
    of the parent's guess) sits to the LEFT (bold), the accumulated crimson misses
    further LEFT of that, and its "N words" count (bold) to the RIGHT. These appear
    BEFORE the node shrinks. We then fill the node with the guess made at that state
    and fan ALL of its result-branches out BELOW as faint lines (behind the nodes).
  • When the chosen child appears below, the finished node SHRINKS to a chip
    (blue = hit, crimson = miss) and its fan shrinks MORE, while the child pulls UP
    to the next slot — then the child's board (left) and count (right) appear, and
    the next beat fills its guess letter. Repeat.
  • End state: a centred vertical stack down the top, plus a BOTTOM node holding the
    final completed word (BALLPARK). Misses show on the gallows (TOP-RIGHT).

Everything shown is SOURCED from the solver tree JSON (guess letters, word counts,
revealed boards, the leaf word) — nothing is computed here. BALLPARK through the
converged len-8 uniform optimal tree, played to word COMPLETION (guessing does not
stop at unique determination after 'b' — it continues until the word is filled):

    e(miss,5267) → i(miss,1695) → a(454) → l(36) → k(5) → b(4) → p(1) → r(1) → BALLPARK
    branches:  75       31          30      10      2      3      1      1
    → solves in 2 misses; p, r are single-branch completion guesses (all hits).

The board at a node is its board_BEFORE (state on arrival); the last board (the
complete word) lives on the extra bottom node.

BEAT MAP (one guess each; a–h via _expand; h's child is the final-word node)
  a — 'e' (miss #1); fan 75    d — 'l' HIT      g — 'p' HIT (single branch)
  b — 'i' (miss #2); fan 31    e — 'k' HIT      h — 'r' HIT (single) → bottom node
  c — 'a' HIT; fan 30          f — 'b' HIT           holds the finished BALLPARK

Render:  render 95a --fast   (…95h)   /   render 95 sub  for the whole walk
"""
from pathlib import Path
import sys
import json

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.hangman_board import (blanked_board, merge_pattern, hangman_drawing,
                                  missed_letters)
from assets.tree_view import guess_node, connect, chip, faint_fan, NODE_R

# ── sourced data: the converged optimal tree, len-8 uniform ───────────────────
TREE_PATH = (Path(__file__).resolve().parents[2]
             / "math/data/shared/optimal/len08_uniform_cap09.json")
WORD = "ballpark"

# ── layout (frame 16×9 → x-radius 8.0, y-radius 4.5) ──────────────────────────
STACK_X      = 0.0     # nodes are CENTRED; board to the LEFT, word-count to the RIGHT
STACK_TOP_Y  = 3.9     # slot y of the first node; the stack grows DOWNWARD
STACK_DY     = 0.80    # slot gap — roomy enough a full active node clears the chip above
EDGE_SHRINK  = 0.25    # the fan shrinks MORE than the node (node → chip size)
FAN_HALF_W   = 4.2     # active fan half-width
FAN_DROP     = 1.3     # active fan reaches this far below the active node
FAN_STROKE   = 1.8     # faint (unused) edge thickness
CHILD_DROP   = 1.7     # the child first appears this far below the active node
INFO_BUFF    = 0.32    # node → count and node → board gaps
MISS_BUFF    = 0.34    # board → accumulated-misses gap (misses sit further left)
BOARD_FS     = 28      # per-row board letters (bold, ~node-letter size)
BOARD_SLOT   = 0.36    # per-row board rule width (scaled up for the bigger font)
BOARD_GAP    = 0.16
COUNT_FS     = 28      # words-remaining count (bold, to the right of the node)
MISS_FS      = 28      # accumulated crimson misses (bold, left of the board)

HANG_POS    = np.array([6.2, 2.6, 0])      # hangman gallows, TOP-RIGHT
HANG_SCALE  = 0.34


class TreeWalk(HangmanScene):
    """Stack the optimal tree along BALLPARK, one guess per subscene.

    Node / edge / fan / chip come from assets.tree_view (shared with 98tree_demo);
    board / gallows / missed-letters from assets.hangman_board.

    a–h  _expand(i)  — the active node already shows its board (left) + count
                       (right); reveal its guess letter, fan, drop into the child,
                       shrink this node to a chip, then reveal the child's board +
                       count. h's child is the terminal bottom node (BALLPARK).
    """

    # nothing on screen at frame 0 — the root state + gallows enter in subscene a
    def setup_scene(self):
        self.tree = json.loads(TREE_PATH.read_text())
        self.path = self._build_path()

    # ── sourced path down the tree (data only) ────────────────────────────────
    def _build_path(self):
        steps, node, acc, missed = [], self.tree, "_" * len(WORD), []
        while "branches" in node:
            g, n = node["guess"], node["n"]
            key = "".join(g if WORD[p] == g else "_" for p in range(len(WORD)))
            hit = any(c != "_" for c in key)
            after = merge_pattern(acc, key)
            child = node["branches"][key]
            leaf = "branches" not in child
            missed_after = missed if hit else missed + [g]
            steps.append(dict(
                guess=g, n=n, nbranches=len(node["branches"]), hit=hit,
                board_before=acc, board_after=after, child_leaf=leaf,
                missed_before=list(missed), missed_after=list(missed_after),
                child_guess=None if leaf else child["guess"],
                child_n=None if leaf else child["n"],
                leaf_word=child.get("word") if leaf else None))
            acc, node, missed = after, child, list(missed_after)
        return steps

    # ── small builders (shared look; each label is separate + persistent) ─────
    def _count(self, n):
        return crisp_text(f"{n} word" + ("" if n == 1 else "s"),
                          font_size=COUNT_FS, color=BLACK, weight=BOLD)

    def _board(self, pattern):
        return blanked_board(pattern, font_size=BOARD_FS, slot=BOARD_SLOT,
                             gap=BOARD_GAP, weight=BOLD)

    def _missed(self, letters):
        return missed_letters(letters, font_size=MISS_FS, weight=BOLD)

    # ── the recurring "expand one node" beat (subscenes a–h) ──────────────────
    def _expand(self, i, *, rt_letter, rt_fan, rt_child, rt_stack, rt_board,
                rt_count):
        s = self.path[i]
        cur = self.cur_body[0].get_center()          # active node circle centre

        # 1. fill in THIS node's guess letter (its board + count are already shown)
        letter = crisp_text(s["guess"].upper(), font_size=30, color=WHITE,
                            weight=BOLD).move_to(cur)
        self.play(FadeIn(letter), run_time=rt_letter)

        # 2. fan ALL branches out below (faint) + the chosen edge (centre-to-centre,
        #    behind the nodes so it never gaps). A miss draws the next hangman part
        #    + the crimson tally below the gallows.
        child_center = np.array([STACK_X, cur[1] - CHILD_DROP, 0.0])
        fan = faint_fan(cur, s["nbranches"], end_y=cur[1] - FAN_DROP,
                        half_w=FAN_HALF_W, stroke_width=FAN_STROKE)
        chosen = connect(cur, child_center, 0.0, 0.0, stroke_width=3.5)
        VGroup(fan, chosen).set_z_index(-1)
        anims = [Create(chosen)]
        if len(fan):
            anims.append(LaggedStartMap(Create, fan, lag_ratio=0.02))
        new_missed = None
        if not s["hit"]:
            part = self.hang_parts[self.miss_n]
            self.hang.add(part)
            anims.append(Create(part))
            self.miss_n += 1
            self.missed.append(s["guess"])
            new_missed = missed_letters(self.missed).next_to(self.hang, DOWN,
                                                             buff=0.3)
            anims.append(ReplacementTransform(self.missed_row, new_missed)
                         if len(self.missed_row) else FadeIn(new_missed))
        self.play(*anims, run_time=rt_fan)
        if new_missed is not None:
            self.missed_row = new_missed

        # 3. the child appears as a BLANK node below (its letter, if any, is filled
        #    in the NEXT beat; the terminal bottom node never gets one)
        is_last = i + 1 >= len(self.path)
        child_guess = WORD[0] if is_last else self.path[i + 1]["guess"]
        child_n = 1 if is_last else self.path[i + 1]["n"]
        child_body, _ = guess_node(child_guess, child_n, child_center, count=False)
        self.play(FadeIn(child_body, scale=0.6), run_time=rt_child)

        # 4. the child's blanked board (the state it ARRIVED in = this guess's
        #    result) to the LEFT, with the accumulated crimson misses further left;
        #    then 5. its "N words" count to the RIGHT — all BEFORE the shrink.
        board = self._board(s["board_after"]).next_to(child_body, LEFT,
                                                       buff=INFO_BUFF)
        reveal = [FadeIn(board, shift=LEFT * 0.1)]
        missed = self._missed(s["missed_after"])
        if len(missed):
            missed.next_to(board, LEFT, buff=MISS_BUFF)
            reveal.append(FadeIn(missed))
        self.play(*reveal, run_time=rt_board)
        count = self._count(child_n).next_to(child_body, RIGHT, buff=INFO_BUFF)
        self.play(FadeIn(count), run_time=rt_count)

        # 6. this node shrinks to a chip; its fan shrinks MORE; the child (with its
        #    misses / board / count) pulls UP to its slot (chosen edge retargets to
        #    span chip → child, gapless)
        crumb = chip(s["guess"], s["hit"]).move_to(cur)
        shift = UP * (CHILD_DROP - STACK_DY)
        new_chosen = connect(cur, cur + DOWN * STACK_DY, 0.0, 0.0, stroke_width=3.5)
        new_chosen.set_z_index(-1)
        movers = VGroup(child_body, board, count)
        if len(missed):
            movers.add(missed)
        stack = [ReplacementTransform(VGroup(self.cur_body, letter), crumb),
                 ReplacementTransform(chosen, new_chosen),
                 movers.animate.shift(shift)]
        if len(fan):
            stack.append(fan.animate.scale(EDGE_SHRINK, about_point=cur))
        self.play(*stack, run_time=rt_stack)
        self.cur_body = child_body

    # ── setup for subscene a (root STATE at the top + gallows) ────────────────
    def _setup_root(self):
        self.cur_body, _ = guess_node(     # letter is filled in _expand
            self.path[0]["guess"], self.path[0]["n"], [STACK_X, STACK_TOP_Y, 0.0],
            count=False)
        self.root_board = self._board(self.path[0]["board_before"]).next_to(
            self.cur_body, LEFT, buff=INFO_BUFF)
        self.root_count = self._count(self.path[0]["n"]).next_to(
            self.cur_body, RIGHT, buff=INFO_BUFF)
        # hangman: build full, scale/position, then detach parts to reveal 1/miss
        full = hangman_drawing(6).scale(HANG_SCALE).move_to(HANG_POS)
        self.hang_parts = list(full.parts)
        for p in self.hang_parts:
            full.remove(p)
        self.hang = full                   # gallows only, on screen from the start
        self.miss_n = 0
        self.missed = []                   # wrong-guess letters, crimson, below gallows
        self.missed_row = VGroup()

    # a : root STATE (blank node, 5267 words, blank word) → guess 'e' (miss); fan 75
    @subscene
    def guess_e(self):
        self._setup_root()
        self.play(FadeIn(self.cur_body), FadeIn(self.hang), run_time=0.6)
        self.play(FadeIn(self.root_board, shift=LEFT * 0.1), run_time=0.5)
        self.play(FadeIn(self.root_count), run_time=0.4)
        self._expand(0, rt_letter=0.4, rt_fan=1.1, rt_child=0.5, rt_stack=1.0,
                     rt_board=0.5, rt_count=0.4)

    # b : 'i' (miss #2); fan 31
    @subscene
    def guess_i(self):
        self._expand(1, rt_letter=0.4, rt_fan=1.0, rt_child=0.5, rt_stack=1.0,
                     rt_board=0.5, rt_count=0.4)

    # c : 'a' HIT; fan 30
    @subscene
    def guess_a(self):
        self._expand(2, rt_letter=0.4, rt_fan=1.0, rt_child=0.5, rt_stack=1.0,
                     rt_board=0.5, rt_count=0.4)

    # d : 'l' HIT; fan 10
    @subscene
    def guess_l(self):
        self._expand(3, rt_letter=0.4, rt_fan=0.9, rt_child=0.5, rt_stack=1.0,
                     rt_board=0.5, rt_count=0.4)

    # e : 'k' HIT; fan 2
    @subscene
    def guess_k(self):
        self._expand(4, rt_letter=0.4, rt_fan=0.7, rt_child=0.5, rt_stack=1.0,
                     rt_board=0.5, rt_count=0.4)

    # f : 'b' HIT; fan 3 (word now DETERMINED but not complete)
    @subscene
    def guess_b(self):
        self._expand(5, rt_letter=0.4, rt_fan=0.6, rt_child=0.5, rt_stack=1.0,
                     rt_board=0.5, rt_count=0.4)

    # g : 'p' HIT; SINGLE branch (a completion guess)
    @subscene
    def guess_p(self):
        self._expand(6, rt_letter=0.4, rt_fan=0.5, rt_child=0.5, rt_stack=1.0,
                     rt_board=0.5, rt_count=0.4)

    # h : 'r' HIT; SINGLE branch → the bottom node holds the finished BALLPARK
    @subscene
    def guess_r(self):
        self._expand(7, rt_letter=0.4, rt_fan=0.5, rt_child=0.5, rt_stack=1.0,
                     rt_board=0.6, rt_count=0.4)
