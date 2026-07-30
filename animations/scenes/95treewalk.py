"""PROTOTYPE — walk the optimal-strategy tree down a single real game (BALLPARK).

Concept (a top-anchored VERTICAL STACK, one guess per subscene):
  • The active node sits at the bottom of the growing stack, full size and CENTRED.
    We fill in its guess letter and fan ALL of its result-branches out BELOW it as
    faint lines (only the taken branch is full-opacity). Its words-remaining count
    sits to the RIGHT, and the blanked board (as it appeared) to the right of that.
  • When the chosen child appears below, the finished node SHRINKS to a chip
    (blue = hit, crimson = miss — like the old breadcrumb chips) and its fan/edges
    shrink MORE, while the child pulls UP to the next slot to become active. Repeat.
  • End state: a centred vertical stack of chips down the top, each still showing
    its (shrunk) outgoing fan — except the last node, which resolves the word.
  • Two board displays: the per-row board (right of each node) AND a top-right
    running board aligned to the gallows' vertical centre. Misses show on the
    gallows (a body part + the crimson tally below).

Everything shown is SOURCED from the solver tree JSON (guess letters, word counts,
revealed boards, the leaf word) — nothing is computed here. BALLPARK through the
converged len-8 uniform optimal tree, played to word COMPLETION (guessing does not
stop at unique determination after 'b' — it continues until the word is filled):

    e(miss,5267) → i(miss,1695) → a(454) → l(36) → k(5) → b(4) → p(1) → r(1) → BALLPARK
    branches:  75       31          30      10      2      3      1      1
    → solves in 2 misses; p, r are single-branch completion guesses (all hits).

BEAT MAP (one guess each; a–g via _expand, h is the completion finale)
  a — root guesses 'e' (miss #1); fan 75; stack it, drop into the all-blank branch
  b — 'i' (miss #2); fan 31; stack        e — 'k' HIT (______k); fan 2; stack
  c — 'a' HIT (_a___a_); fan 30; stack     f — 'b' HIT (b______); fan 3; stack
  d — 'l' HIT (__ll___); fan 10; stack     g — 'p' HIT (____p___); SINGLE branch
  h — 'r' HIT (______r_); SINGLE branch RESOLVES the word → blue BALLPARK

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
STACK_X      = 0.0     # nodes are CENTRED horizontally; count + board to the right
STACK_TOP_Y  = 3.9     # slot y of the first node; the stack grows DOWNWARD
STACK_DY     = 0.62    # vertical gap between stack slots
EDGE_SHRINK  = 0.25    # the fan/edges shrink MORE than the node (node → chip size)
FAN_HALF_W   = 4.2     # active fan half-width (clears the gallows on the left)
FAN_DROP     = 1.4     # active fan reaches this far below the active node
CHILD_DROP   = 1.9     # the child first appears this far below the active node
INFO_BUFF    = 0.32    # node → count and count → board gaps
COUNT_FS     = 16      # words-remaining count (to the right of the node)
ROW_BOARD_FS = 15      # compact per-row board (leaves room for the top-right one)

RUN_BOARD_X = 5.7     # top-right running board x; its y = the gallows centre
HANG_POS    = np.array([-6.2, 2.6, 0])     # hangman gallows, top-left
HANG_SCALE  = 0.34


class TreeWalk(HangmanScene):
    """Stack the optimal tree along BALLPARK, one guess per subscene.

    Node / edge / fan / chip come from assets.tree_view (shared with 98tree_demo);
    board / gallows / missed-letters from assets.hangman_board.

    a–g  _expand(i)  — reveal guess, fan siblings, count+board to the right, drop
                       into the child, then shrink this node to a chip (blue/crimson)
                       + shrink its edges more, while the child pulls up.
    h    solve       — the last (single) branch resolves the word: blue BALLPARK.
    """

    # nothing on screen at frame 0 — the root + gallows enter in subscene a
    def setup_scene(self):
        self.tree = json.loads(TREE_PATH.read_text())
        self.path = self._build_path()

    # ── sourced path down the tree (data only) ────────────────────────────────
    def _build_path(self):
        steps, node, acc = [], self.tree, "_" * len(WORD)
        while "branches" in node:
            g, n = node["guess"], node["n"]
            key = "".join(g if WORD[p] == g else "_" for p in range(len(WORD)))
            hit = any(c != "_" for c in key)
            after = merge_pattern(acc, key)
            child = node["branches"][key]
            leaf = "branches" not in child
            steps.append(dict(
                guess=g, n=n, nbranches=len(node["branches"]), hit=hit,
                board_before=acc, board_after=after, child_leaf=leaf,
                child_guess=None if leaf else child["guess"],
                child_n=None if leaf else child["n"],
                leaf_word=child.get("word") if leaf else None))
            acc, node = after, child
        return steps

    # ── build a (centred) active node + its persistent count label ────────────
    def _node(self, guess, n, y):
        body, _ = guess_node(guess, n, [STACK_X, y, 0.0], count=False)
        count = crisp_text(str(n), font_size=COUNT_FS, color=GREY_D)
        count.next_to(body, RIGHT, buff=INFO_BUFF)
        return body, count

    def _run_board(self, pattern):
        return blanked_board(pattern).move_to([RUN_BOARD_X, self.run_y, 0])

    # ── the recurring "expand one node" beat (subscenes a–g) ──────────────────
    def _expand(self, i, *, rt_letter, rt_fan, rt_board, rt_child, rt_stack, hold):
        s = self.path[i]
        cur = self.cur_body[0].get_center()          # active node circle centre

        # 1. fill in this node's guess letter (the node "acts")
        letter = crisp_text(s["guess"].upper(), font_size=30, color=WHITE,
                            weight=BOLD).move_to(cur)
        self.play(FadeIn(letter), run_time=rt_letter)

        # 2. fan ALL branches out BELOW (faint) + the chosen edge to the child. A
        #    determined node has one branch (completion guess) -> no faint fan.
        child_center = np.array([STACK_X, cur[1] - CHILD_DROP, 0.0])
        fan = faint_fan(cur, s["nbranches"], end_y=cur[1] - FAN_DROP,
                        half_w=FAN_HALF_W)
        chosen = connect(cur, child_center, NODE_R, NODE_R, stroke_width=3.5)
        if len(fan):
            self.play(LaggedStartMap(Create, fan, lag_ratio=0.02), run_time=rt_fan)

        # 3. the blanked board (as it appeared) to the RIGHT of the count; a miss
        #    draws the next hangman part & the crimson tally below the gallows
        board = blanked_board(s["board_after"], font_size=ROW_BOARD_FS).next_to(
            self.cur_count, RIGHT, buff=INFO_BUFF)
        anims = [Create(chosen), FadeIn(board, shift=RIGHT * 0.1)]
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
        self.play(*anims, run_time=rt_board)
        if new_missed is not None:
            self.missed_row = new_missed

        # 4. the chosen child appears below (full size), letter hidden until it acts
        nxt = self.path[i + 1]
        child_body, child_count = self._node(nxt["guess"], nxt["n"],
                                             child_center[1])
        self.play(FadeIn(child_body, scale=0.6), FadeIn(child_count),
                  run_time=rt_child)

        self.wait(hold)   # pause before we stack

        # 5. this node shrinks to a chip (blue hit / crimson miss); its edges shrink
        #    MORE; count + board stay readable; the child pulls up to its slot.
        crumb = chip(s["guess"], s["hit"]).move_to(cur)
        shift = UP * (CHILD_DROP - STACK_DY)         # child rises to the next slot
        stack = [ReplacementTransform(VGroup(self.cur_body, letter), crumb),
                 VGroup(fan, chosen).animate.scale(EDGE_SHRINK, about_point=cur),
                 child_body.animate.shift(shift),
                 child_count.animate.shift(shift)]
        if s["board_after"] != s["board_before"]:    # a hit revealed new letters
            new_run = self._run_board(s["board_after"])
            stack.append(ReplacementTransform(self.run_board, new_run))
        self.play(*stack, run_time=rt_stack)
        if s["board_after"] != s["board_before"]:
            self.run_board = new_run
        self.cur_body, self.cur_count = child_body, child_count

    # ── setup for subscene a (root node at the top + gallows + running board) ──
    def _setup_root(self):
        self.cur_body, self.cur_count = self._node(
            self.path[0]["guess"], self.path[0]["n"], STACK_TOP_Y)
        # hangman: build full, scale/position, then detach parts to reveal 1/miss
        full = hangman_drawing(6).scale(HANG_SCALE).move_to(HANG_POS)
        self.hang_parts = list(full.parts)
        for p in self.hang_parts:
            full.remove(p)
        self.hang = full                   # gallows only, on screen from the start
        self.miss_n = 0
        self.missed = []                   # wrong-guess letters, crimson, below gallows
        self.missed_row = VGroup()
        # top-right running board, aligned to the gallows' vertical centre
        self.run_y = self.hang.get_center()[1]
        self.run_board = self._run_board("_" * len(WORD))

    # a : root guesses 'e' (miss #1); fan 75; stack; drop into the all-blank branch
    @subscene
    def guess_e(self):
        self._setup_root()
        self.play(FadeIn(self.cur_body), FadeIn(self.cur_count), FadeIn(self.hang),
                  FadeIn(self.run_board), run_time=0.7)
        self._expand(0, rt_letter=0.4, rt_fan=1.1, rt_board=0.8, rt_child=0.5,
                     rt_stack=1.0, hold=0.7)

    # b : 'i' (miss #2); fan 31; stack
    @subscene
    def guess_i(self):
        self._expand(1, rt_letter=0.4, rt_fan=1.0, rt_board=0.8, rt_child=0.5,
                     rt_stack=1.0, hold=0.7)

    # c : 'a' HIT (_a___a_); fan 30; board fills; stack
    @subscene
    def guess_a(self):
        self._expand(2, rt_letter=0.4, rt_fan=1.0, rt_board=0.8, rt_child=0.5,
                     rt_stack=1.0, hold=0.7)

    # d : 'l' HIT (__ll___); fan 10; stack
    @subscene
    def guess_l(self):
        self._expand(3, rt_letter=0.4, rt_fan=0.9, rt_board=0.8, rt_child=0.5,
                     rt_stack=1.0, hold=0.7)

    # e : 'k' HIT (______k); fan 2; stack
    @subscene
    def guess_k(self):
        self._expand(4, rt_letter=0.4, rt_fan=0.7, rt_board=0.8, rt_child=0.5,
                     rt_stack=1.0, hold=0.7)

    # f : 'b' HIT (b______); word now DETERMINED but not complete; stack
    @subscene
    def guess_b(self):
        self._expand(5, rt_letter=0.4, rt_fan=0.6, rt_board=0.8, rt_child=0.5,
                     rt_stack=1.0, hold=0.7)

    # g : 'p' HIT (____p___); SINGLE branch (a completion guess); stack
    @subscene
    def guess_p(self):
        self._expand(6, rt_letter=0.4, rt_fan=0.5, rt_board=0.8, rt_child=0.5,
                     rt_stack=1.0, hold=0.7)

    # h : 'r' HIT (______r_); the last (single) branch RESOLVES → blue BALLPARK
    @subscene
    def solve(self):
        s = self.path[7]
        cur = self.cur_body[0].get_center()

        letter = crisp_text(s["guess"].upper(), font_size=30, color=WHITE,
                            weight=BOLD).move_to(cur)
        self.play(FadeIn(letter), run_time=0.4)

        # the last node has NO outgoing edge; the completed word fills in to its
        # right (blue) and the top-right running board completes too.
        board = blanked_board(s["board_after"], font_size=ROW_BOARD_FS).next_to(
            self.cur_count, RIGHT, buff=INFO_BUFF)
        new_run = self._run_board(s["board_after"])
        self.play(FadeIn(board, shift=RIGHT * 0.1),
                  ReplacementTransform(self.run_board, new_run), run_time=0.8)
        self.run_board = new_run

        # settle the last node into the stack as a chip (a hit → blue), no edges
        crumb = chip(s["guess"], s["hit"]).move_to(cur)
        self.play(ReplacementTransform(VGroup(self.cur_body, letter), crumb),
                  run_time=0.6)
