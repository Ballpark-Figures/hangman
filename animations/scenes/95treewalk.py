"""PROTOTYPE — walk the optimal-strategy tree down a single real game (BALLPARK).

Concept (a top-anchored descent, one guess per subscene):
  • The CURRENT node sits near TOP-CENTRE. We "fill in" its guess letter, then
    fan ALL of its result-branches out below it as faint lines — only the ONE
    branch this game actually takes is drawn full-opacity, carrying the blanked
    board (and, on a miss, a 'miss' tag + the next hangman body part).
  • The chosen branch's child node appears below; we hold; then the child slides
    UP to top-centre to become the new current node while the node we just left
    SHRINKS into a breadcrumb chip along the top. Repeat until the word solves.

Everything shown is SOURCED from the solver tree JSON (guess letters, word counts,
revealed boards, the leaf word) — nothing is computed here. BALLPARK through the
converged len-8 uniform optimal tree, played to word COMPLETION (guessing does not
stop at unique determination after 'b' — it continues until the word is filled):

    e(miss,5267) → i(miss,1695) → a(454) → l(36) → k(5) → b(4) → p(1) → r(1) → BALLPARK
    branches:  75       31          30      10      2      3      1      1
    → solves in 2 misses; p, r are single-branch completion guesses (all hits).

BEAT MAP (one guess each; a–g via _expand, h is the completion finale)
  a — root guesses 'e' (miss #1); fan 75; descend into the all-blank branch
  b — 'i' (miss #2); fan 31; descend
  c — 'a' HIT (_a___a_); fan 30; board fills; descend
  d — 'l' HIT (__ll___); fan 10; descend
  e — 'k' HIT (______k); fan 2; descend
  f — 'b' HIT (b______); fan 3; word now DETERMINED but not complete; descend
  g — 'p' HIT (____p___); SINGLE branch (completion guess); descend
  h — 'r' HIT (______r_); SINGLE branch RESOLVES the word → reveal gold BALLPARK

Render:  render 95a --fast   (…95h)   /   render 95 sub  for the whole walk
"""
from pathlib import Path
import sys
import json

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.hangman_board import (blanked_board, solved_word, miss_tag,
                                  merge_pattern, hangman_drawing, missed_letters)
from assets.tree_view import guess_node, connect, chip, faint_fan, NODE_R, CHIP_R

# ── sourced data: the converged optimal tree, len-8 uniform ───────────────────
TREE_PATH = (Path(__file__).resolve().parents[2]
             / "math/data/shared/optimal/len08_uniform_cap09.json")
WORD = "ballpark"

# ── layout (frame 16×9 → x-radius 8.0, y-radius 4.5) ──────────────────────────
CUR_Y      = 2.3      # the active node, near top-centre
FAN_END_Y  = -0.7     # faint sibling edges terminate along this row…
FAN_HALF_W = 7.2      # …spread across ±this in x
CHILD_Y    = -2.7     # the chosen branch's child node appears here (centre col)
BOARD_UP   = 1.15     # blanked board offset up the chosen edge from its child

TRAIL_Y    = 3.95     # breadcrumb row of shrunk guess-chips
TRAIL_X0   = -3.4     # first chip x (row grows rightward; 8 chips clear the board)
TRAIL_DX   = 0.72
RUN_BOARD_POS = np.array([4.6, 3.95, 0])   # running revealed board, top-right
HANG_POS   = np.array([-6.2, 2.6, 0])      # hangman figure, top-left
HANG_SCALE = 0.34

class TreeWalk(HangmanScene):
    """Descend the optimal tree along BALLPARK, one guess per subscene.

    Node / edge / fan / chip come from assets.tree_view (shared with 98tree_demo);
    board / word / gallows / missed-letters from assets.hangman_board.

    a–g  _expand(i)  — reveal guess, fan siblings, highlight taken branch, drop
                       into the child, then raise child + shrink self to a chip.
    h    solve       — the last branch resolves to the single word: gold BALLPARK.
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

    # ── the recurring "expand one node" beat (subscenes a–g) ──────────────────
    def _expand(self, i, *, rt_letter, rt_fan, rt_board, rt_child, rt_descend,
                hold):
        s = self.path[i]
        cur_center = self.cur_body[0].get_center()

        # 1. fill in this node's guess letter (the node "acts")
        letter = crisp_text(s["guess"].upper(), font_size=30, color=WHITE,
                            weight=BOLD).move_to(cur_center)
        self.play(FadeIn(letter), run_time=rt_letter)

        # 2. fan ALL branches out — faint, except the one this game takes. Once the
        #    word is determined the node has a SINGLE branch (a completion guess),
        #    so there are no faint siblings — just the one edge, drawn in step 3.
        child_center = np.array([0.0, CHILD_Y, 0.0])
        fan = faint_fan(cur_center, s["nbranches"], end_y=FAN_END_Y,
                        half_w=FAN_HALF_W)
        chosen = connect(cur_center, child_center, NODE_R, NODE_R,
                         stroke_width=3.5)
        if len(fan):
            self.play(LaggedStartMap(Create, fan, lag_ratio=0.02), run_time=rt_fan)

        # 3. the taken branch: its edge + blanked board (+ miss tag, hangman part,
        #    and the running missed-letters tally below the gallows)
        board = blanked_board(s["board_after"]).move_to(
            child_center + UP * BOARD_UP)
        anims = [Create(chosen), FadeIn(board, shift=DOWN * 0.15)]
        tag = new_missed = None
        if not s["hit"]:
            tag = miss_tag([s["guess"]]).next_to(board, UP, buff=0.06)
            anims.append(FadeIn(tag))
            part = self.hang_parts[self.miss_n]
            self.hang.add(part)
            anims.append(Create(part))
            self.miss_n += 1
            self.missed.append(s["guess"])              # red tally below the gallows
            new_missed = missed_letters(self.missed).next_to(self.hang, DOWN,
                                                             buff=0.3)
            anims.append(ReplacementTransform(self.missed_row, new_missed)
                         if len(self.missed_row) else FadeIn(new_missed))
        self.play(*anims, run_time=rt_board)
        if new_missed is not None:
            self.missed_row = new_missed

        # 4. the chosen child arrives (its letter stays hidden until it acts)
        nxt = self.path[i + 1]
        child_body, _ = guess_node(nxt["guess"], nxt["n"], child_center)
        self.play(FadeIn(child_body, scale=0.6), run_time=rt_child)

        self.wait(hold)   # "pause for a bit" before we descend

        # 5. descend: child rises to top-centre; we shrink into a breadcrumb chip
        crumb = chip(s["guess"], s["hit"]).move_to(
            [TRAIL_X0 + self.chip_i * TRAIL_DX, TRAIL_Y, 0])
        desc = [ReplacementTransform(VGroup(self.cur_body[0], letter), crumb),
                FadeOut(self.cur_body[1]),          # the count text
                FadeOut(fan), FadeOut(chosen), FadeOut(board),
                child_body.animate.move_to([0.0, CUR_Y, 0.0])]
        if tag is not None:
            desc.append(FadeOut(tag))
        if s["board_after"] != s["board_before"]:    # a hit revealed new letters
            new_run = blanked_board(s["board_after"]).move_to(RUN_BOARD_POS)
            desc.append(ReplacementTransform(self.run_board, new_run))
        self.play(*desc, run_time=rt_descend)

        self.trail.add(crumb)
        self.chip_i += 1
        if s["board_after"] != s["board_before"]:
            self.run_board = new_run
        self.cur_body = child_body

    # ── shared setup for subscene a (root + persistent top furniture) ─────────
    def _setup_root(self):
        self.cur_body, _ = guess_node(     # letter is (re)built inside _expand
            self.path[0]["guess"], self.path[0]["n"], [0.0, CUR_Y, 0.0])
        self.trail = VGroup()
        self.chip_i = 0
        self.run_board = blanked_board("_" * len(WORD)).move_to(RUN_BOARD_POS)
        # hangman: build full, scale/position, then detach parts to reveal 1/miss
        full = hangman_drawing(6).scale(HANG_SCALE).move_to(HANG_POS)
        self.hang_parts = list(full.parts)
        for p in self.hang_parts:
            full.remove(p)
        self.hang = full                   # gallows only, on screen from the start
        self.miss_n = 0
        self.missed = []                   # wrong-guess letters, red, below gallows
        self.missed_row = VGroup()         # grown in _expand as misses land

    # a : root guesses 'e' (miss #1); fan 75; descend into the all-blank branch
    @subscene
    def guess_e(self):
        self._setup_root()
        self.play(FadeIn(self.cur_body, scale=0.6), FadeIn(self.hang),
                  FadeIn(self.run_board), run_time=0.7)
        self._expand(0, rt_letter=0.4, rt_fan=1.1, rt_board=0.8, rt_child=0.5,
                     rt_descend=1.0, hold=0.7)

    # b : 'i' (miss #2); fan 31; descend
    @subscene
    def guess_i(self):
        self._expand(1, rt_letter=0.4, rt_fan=1.0, rt_board=0.8, rt_child=0.5,
                     rt_descend=1.0, hold=0.7)

    # c : 'a' HIT (_a___a_); fan 30; board fills; descend
    @subscene
    def guess_a(self):
        self._expand(2, rt_letter=0.4, rt_fan=1.0, rt_board=0.8, rt_child=0.5,
                     rt_descend=1.0, hold=0.7)

    # d : 'l' HIT (__ll___); fan 10; descend
    @subscene
    def guess_l(self):
        self._expand(3, rt_letter=0.4, rt_fan=0.9, rt_board=0.8, rt_child=0.5,
                     rt_descend=1.0, hold=0.7)

    # e : 'k' HIT (______k); fan 2; descend
    @subscene
    def guess_k(self):
        self._expand(4, rt_letter=0.4, rt_fan=0.7, rt_board=0.8, rt_child=0.5,
                     rt_descend=1.0, hold=0.7)

    # f : 'b' HIT (b______); word now DETERMINED but not complete; descend
    @subscene
    def guess_b(self):
        self._expand(5, rt_letter=0.4, rt_fan=0.6, rt_board=0.8, rt_child=0.5,
                     rt_descend=1.0, hold=0.7)

    # g : 'p' HIT (____p___); SINGLE branch (a completion guess); descend
    @subscene
    def guess_p(self):
        self._expand(6, rt_letter=0.4, rt_fan=0.5, rt_board=0.8, rt_child=0.5,
                     rt_descend=1.0, hold=0.7)

    # h : 'r' HIT (______r_); the SINGLE branch RESOLVES → reveal gold BALLPARK
    @subscene
    def solve(self):
        s = self.path[7]
        cur_center = self.cur_body[0].get_center()

        letter = crisp_text(s["guess"].upper(), font_size=30, color=WHITE,
                            weight=BOLD).move_to(cur_center)
        self.play(FadeIn(letter), run_time=0.4)

        child_center = np.array([0.0, CHILD_Y, 0.0])
        chosen = connect(cur_center, child_center, NODE_R, NODE_R)   # single branch
        board = blanked_board(s["board_after"]).move_to(child_center + UP * BOARD_UP)
        self.play(Create(chosen), FadeIn(board, shift=DOWN * 0.15), run_time=0.8)
        self.wait(0.7)

        # the last letter fills in → the word is COMPLETE; it turns gold
        crumb = chip(s["guess"], s["hit"]).move_to(
            [TRAIL_X0 + self.chip_i * TRAIL_DX, TRAIL_Y, 0])
        final = solved_word(s["leaf_word"], font_size=44).move_to([0.0, -0.2, 0.0])
        new_run = blanked_board(s["board_after"]).move_to(RUN_BOARD_POS)  # +the 'r'
        self.play(
            ReplacementTransform(VGroup(self.cur_body[0], letter), crumb),
            FadeOut(self.cur_body[1]),
            FadeOut(chosen),
            ReplacementTransform(self.run_board, new_run),
            ReplacementTransform(board, final),
            run_time=1.1)
        self.run_board = new_run
        self.play(final.animate.scale(1.15), run_time=0.5)
