"""PROTOTYPE — a way to visualize the optimal strategy tree (not a content scene).

Concept: a top-to-bottom decision tree (depth grows downward).
  • NODE  = the guess at that point (a letter in a circle; words-remaining below).
            The circle + count appear when the node is created, but the LETTER
            only fades in when the node draws its FIRST outgoing edge — the letter
            marks the moment the node "acts" (commits to a guess and branches).
  • EDGE  = a RESULT of that guess = the partially-blanked word it produces,
            plus any newly-missed letter (the all-blank branch is a miss).
Missed letters accumulate down a path, and the blanked word carries revealed
letters from ancestors — so an edge fully specifies the state entering its child.

Everything shown is SOURCED from the solver tree JSON (guess letters, word counts,
revealed patterns, leaf words). Nothing is computed here.

BEAT MAP
  fan_out — root guesses 'a' (n=640); its 5 result-branches fan DOWN one at a
            time. Root's letter appears with the first edge; each edge draws its
            blanked word (+ the miss pile). Children arrive as blank circles.
  descend — dim the other branches, drop INTO the "_a_" branch (its letter 't'
            appears as it branches), and fan out ITS results below, showing the
            board accumulate (_a_ -> ta_/_at/tat).

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

# ── layout (frame is 16×9 → x-radius 8.0, y-radius 4.5); depth = y (downward) ──
ROOT_Y = 3.4
L1_Y   = 0.6                          # row of the 5 root branches
L2_Y   = -2.5                         # row of the "_a_" node's branches
L1_X   = [-6.0, -3.0, 0.0, 3.0, 6.0]  # 5 root branches, left→right
L2_X   = [-4.5, -1.5, 1.5, 4.5]       # 4 branches of the "_a_" node
BOARD_UP = 1.05                       # board offset from a node, up its own edge

NODE_R = 0.42
DESCEND_KEY = "_a_"      # which root branch subscene b drops into


# ── mobject builders ──────────────────────────────────────────────────────────
def _guess_node(letter, n, center):
    """A decision node. Returns (body, letter): `body` = circle + count (shown on
    creation); `letter` = the guess text (revealed later, on the first edge)."""
    circ = Circle(radius=NODE_R, color=ACCENT_FILL,
                  fill_opacity=1.0, stroke_width=2.5).move_to(center)
    cnt = crisp_text(str(n), font_size=15, color=GREY_D)   # words still possible
    cnt.next_to(circ, DOWN, buff=0.08)
    lab = crisp_text(letter.upper(), font_size=30, color=WHITE,
                     weight=BOLD).move_to(circ)
    return VGroup(circ, cnt), lab


def _connect(a, b, r_a, r_b):
    """A straight edge trimmed to sit between two node faces."""
    d = normalize(b - a)
    return Line(a + d * r_a, b - d * r_b, stroke_width=3, color=GREY_BROWN)


class TreeDemo(HangmanScene):

    # nothing is on screen at frame 0 — the root enters in subscene a
    def setup_scene(self):
        self.tree = json.loads(TREE_PATH.read_text())

    # ── build a fan of branches below a parent ────────────────────────────────
    def _fan(self, parent_node, parent_center, carried_board, xs, node_y):
        """Build each branch of `parent_node` laid out along row `node_y` at the
        given x's. Each row: edge, board (on the edge), body (circle+count),
        letter (revealed on this child's own first edge — None for a leaf), tag.
        """
        rows = []
        for key, x in zip(parent_node["branches"], xs):
            child = parent_node["branches"][key]
            shown = merge_pattern(carried_board, key)   # blanked word on this edge
            is_miss = key == "_" * len(carried_board)
            center = np.array([x, node_y, 0.0])

            if "word" in child:                          # a solved leaf word
                body, letter, r_child = solved_word(child["word"]).move_to(
                    center), None, 0.55
                circ_center = center
            else:
                body, letter = _guess_node(child["guess"], child["n"], center)
                circ_center, r_child = body[0].get_center(), NODE_R

            edge = _connect(np.array(parent_center), circ_center, NODE_R, r_child)
            up = normalize(np.array(parent_center) - circ_center)
            board = blanked_board(shown).move_to(circ_center + up * BOARD_UP)
            tag = (miss_tag([parent_node["guess"]]).next_to(board, UP, buff=0.06)
                   if is_miss else None)
            rows.append({"key": key, "edge": edge, "board": board, "body": body,
                         "letter": letter, "tag": tag, "board_after": shown})
        return rows

    def _grow(self, br, parent_letter, run_time):
        """Draw one branch: its edge + board (and, on the parent's FIRST edge,
        the parent's letter), then the child body and any miss tag."""
        anims = [Create(br["edge"]), FadeIn(br["board"], shift=DOWN * 0.15)]
        if parent_letter is not None:
            anims.append(FadeIn(parent_letter))     # letter appears with 1st edge
        self.play(*anims, run_time=run_time)
        extra = [FadeIn(br["body"], scale=0.6)]
        if br["tag"]:
            extra.append(FadeIn(br["tag"]))
        self.play(*extra, run_time=run_time)

    # a : root guesses 'a'; its result-branches fan DOWN one at a time
    @subscene
    def fan_out(self):
        wlen = len(next(iter(self.tree["branches"])))   # word length (=3)
        self.root_body, self.root_letter = _guess_node(
            self.tree["guess"], self.tree["n"], [0, ROOT_Y, 0])
        self.l1 = self._fan(self.tree, self.root_body[0].get_center(),
                             "_" * wlen, L1_X, L1_Y)

        self.play(FadeIn(self.root_body, scale=0.6), run_time=0.7)
        for i, br in enumerate(self.l1):
            # reveal the root's letter as its FIRST outgoing edge is drawn
            self._grow(br, self.root_letter if i == 0 else None, run_time=0.5)

    # b : dim the other branches, descend into "_a_", fan out its results
    @subscene
    def descend(self):
        idx = list(self.tree["branches"]).index(DESCEND_KEY)
        chosen = self.l1[idx]
        node2_parent = self.tree["branches"][DESCEND_KEY]
        self.l2 = self._fan(node2_parent, chosen["body"][0].get_center(),
                            chosen["board_after"], L2_X, L2_Y)

        # dim everything except the chosen root→_a_ branch (+ the root)
        keep = set()
        for m in (self.root_body, self.root_letter,
                  chosen["edge"], chosen["board"], chosen["body"]):
            keep |= {id(x) for x in m.get_family()}
        dim = VGroup(*[m for om in self.mobjects for m in om.get_family()
                       if id(m) not in keep and isinstance(m, VMobject)])
        self.play(dim.animate.set_opacity(0.12), run_time=0.6)

        for j, br in enumerate(self.l2):
            # reveal the "_a_" node's letter 't' as it draws its first edge
            self._grow(br, chosen["letter"] if j == 0 else None, run_time=0.45)
