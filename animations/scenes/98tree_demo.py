"""PROTOTYPE — a way to visualize the optimal strategy tree (not a content scene).

Concept: a left-to-right decision tree.
  • NODE  = the guess at that point (a letter in a circle; words-remaining below).
  • EDGE  = a RESULT of that guess = the partially-blanked word it produces,
            plus any newly-missed letter (the all-blank branch is a miss).
Missed letters accumulate down a path, and the blanked word carries revealed
letters from ancestors — so an edge fully specifies the state entering its child.

Everything shown is SOURCED from the solver tree JSON (guess letters, word counts,
revealed patterns, leaf words). Nothing is computed here.

BEAT MAP
  fan_out — root guesses 'a' (n=640); its 5 result-branches fan in one at a time,
            each edge drawing its blanked word (+ the miss pile).
  descend — dim the other branches, drop INTO the "_a_" branch (guess 't'), and
            fan out ITS results, showing the board accumulate (_a_ -> ta_/_at/tat).

Reusable pieces to promote to assets once the look is settled: the blanked-word
board (`_board`) and the miss tag (`_miss_tag`) — every gameplay scene wants them.

Render:  render 98a --fast   /   render 98b --fast
"""
from pathlib import Path
import sys
import json

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.hangman_board import (blanked_board, solved_word, miss_tag,
                                  merge_pattern)

# ── sourced data: the converged-as-possible optimal tree, len-3 uniform ───────
TREE_PATH = (Path(__file__).resolve().parents[2]
             / "math/data/shared/optimal/len03_uniform_cap11.json")

# ── layout (frame is 16×9 → x-radius 8.0, y-radius 4.5) ───────────────────────
ROOT_X   = -6.4
BOARD1_X = -3.4          # blanked-word column for level 1
NODE1_X  = -1.4          # guess-node column for level 1
BOARD2_X =  2.0          # …and for level 2 (after descending)
NODE2_X  =  4.3
L1_Y = [3.3, 1.65, 0.0, -1.65, -3.3]   # 5 root branches, top→bottom
L2_Y = [2.4, 0.8, -0.8, -2.4]          # 4 branches of the "_a_" node

NODE_R = 0.42
DESCEND_KEY = "_a_"      # which root branch subscene b drops into


# ── mobject builders (candidates for assets/) ─────────────────────────────────
def _guess_node(letter, n):
    """A decision node: the guessed letter in a filled circle, count below."""
    circ = Circle(radius=NODE_R, color=ACCENT_FILL,
                  fill_opacity=1.0, stroke_width=2.5)
    lab = crisp_text(letter.upper(), font_size=30, color=WHITE, weight=BOLD)
    lab.move_to(circ)
    cnt = crisp_text(str(n), font_size=15, color=GREY_D)   # words still possible
    cnt.next_to(circ, DOWN, buff=0.08)
    return VGroup(circ, lab, cnt)


def _connect(a, b, r_a, r_b):
    """A straight edge trimmed to sit between two node faces."""
    d = normalize(b - a)
    return Line(a + d * r_a, b - d * r_b, stroke_width=3, color=GREY_BROWN)


class TreeDemo(HangmanScene):

    # nothing is on screen at frame 0 — the root enters in subscene a
    def setup_scene(self):
        self.tree = json.loads(TREE_PATH.read_text())

    # ── build helpers ─────────────────────────────────────────────────────────
    def _child_mob(self, node):
        """A guess node, or a leaf word board, from a tree child dict."""
        if "word" in node:
            return solved_word(node["word"])
        return _guess_node(node["guess"], node["n"])

    def _fan(self, parent_node, parent_center, carried_board,
             ys, board_x, node_x):
        """Build (edge, board, miss_tag, node) for each branch of `parent_node`,
        laid out at the given column x's and row y's. Returns a list of dicts."""
        rows = []
        for key, (ys_i,) in zip(parent_node["branches"], [(y,) for y in ys]):
            child = parent_node["branches"][key]
            shown = merge_pattern(carried_board, key)   # blanked word on this edge
            is_miss = key == "_" * len(carried_board)

            board = blanked_board(shown).move_to([board_x, ys_i, 0])
            node = self._child_mob(child).move_to([node_x, ys_i, 0])
            r_child = NODE_R if "word" not in child else 0.55
            edge = _connect(np.array(parent_center),
                            node[0].get_center(), NODE_R, r_child)
            tag = None
            if is_miss:
                tag = miss_tag([parent_node["guess"]]).next_to(
                    board, DOWN, buff=0.07)
            rows.append({"key": key, "edge": edge, "board": board,
                         "node": node, "tag": tag, "board_after": shown})
        return rows

    # a : root guesses 'a'; its result-branches fan in one at a time
    @subscene
    def fan_out(self):
        self.root_g = _guess_node(self.tree["guess"], self.tree["n"])
        self.root_g.move_to([ROOT_X, 0, 0])
        wlen = len(next(iter(self.tree["branches"])))   # word length (=3)
        self.l1 = self._fan(self.tree, self.root_g[0].get_center(),
                             "_" * wlen, L1_Y, BOARD1_X, NODE1_X)

        self.play(FadeIn(self.root_g, scale=0.6), run_time=0.7)
        step = 0.5   # lockstep per-branch reveal (a montage, not distinct beats)
        for br in self.l1:
            self.play(Create(br["edge"]),
                      FadeIn(br["board"], shift=RIGHT * 0.2), run_time=step)
            extra = [FadeIn(br["node"], scale=0.6)]
            if br["tag"]:
                extra.append(FadeIn(br["tag"]))
            self.play(*extra, run_time=step)

    # b : dim the other branches, descend into "_a_", fan out its results
    @subscene
    def descend(self):
        idx = list(self.tree["branches"]).index(DESCEND_KEY)
        chosen = self.l1[idx]
        node2_parent = self.tree["branches"][DESCEND_KEY]
        self.l2 = self._fan(node2_parent, chosen["node"][0].get_center(),
                            chosen["board_after"], L2_Y, BOARD2_X, NODE2_X)

        # fade everything except the chosen root→_a_ branch back
        keep = {id(m) for br in (chosen,) for m in
                (br["edge"], br["board"], *br["node"])}
        keep |= {id(m) for m in self.root_g}
        dim = VGroup(*[m for om in self.mobjects for m in om.get_family()
                       if id(m) not in keep and isinstance(m, VMobject)])
        self.play(dim.animate.set_opacity(0.12), run_time=0.6)

        for br in self.l2:
            self.play(Create(br["edge"]),
                      FadeIn(br["board"], shift=RIGHT * 0.2), run_time=0.45)
            extra = [FadeIn(br["node"], scale=0.6)]
            if br["tag"]:
                extra.append(FadeIn(br["tag"]))
            self.play(*extra, run_time=0.4)
