"""Shared tree-GRAPH primitives for the strategy-tree scenes (95treewalk,
98tree_demo).

The board / word / gallows vocabulary lives in ``hangman_board``; this module
owns the GRAPH layer — decision nodes, the edges between them, the faint fan of
sibling branches, and the breadcrumb chips — so both scenes render the tree with
ONE visual language and can't drift (they used to keep private copies of
``_guess_node`` / ``_connect`` that had already diverged on stroke width).

A decision NODE is a circle (``ACCENT_FILL``) with the words-remaining count
below; its guess LETTER is returned separately and revealed only when the node
"acts" (draws its first edge). EDGES are straight lines trimmed to sit between
two node faces. Scenes own their own LAYOUT (positions, rows); this module owns
how a node / edge / fan / chip LOOKS.
"""
from config import *

NODE_R = 0.42          # decision-node radius
CHIP_R = 0.24          # breadcrumb-chip radius


def guess_node(letter, n, center, *, r=NODE_R):
    """A decision node: ``(body, letter)`` where ``body`` = circle + count (shown
    on creation) and ``letter`` = the guess text (revealed later, on the node's
    first outgoing edge)."""
    circ = Circle(radius=r, color=ACCENT_FILL, fill_opacity=1.0,
                  stroke_width=2.5).move_to(center)
    cnt = crisp_text(str(n), font_size=15, color=GREY_D)      # words still possible
    cnt.next_to(circ, DOWN, buff=0.08)
    lab = crisp_text(letter.upper(), font_size=30, color=WHITE, weight=BOLD)
    lab.move_to(circ)
    return VGroup(circ, cnt), lab


def connect(a, b, r_a, r_b, **kw):
    """A straight edge trimmed to sit between two node faces (radii ``r_a`` at
    ``a``, ``r_b`` at ``b``). Override ``stroke_width`` to emphasise an edge."""
    d = normalize(b - a)
    kw.setdefault("stroke_width", 3.0)
    kw.setdefault("color", BLACK)
    return Line(a + d * r_a, b - d * r_b, **kw)


def chip(letter, hit, *, r=CHIP_R):
    """A shrunk breadcrumb node: small circle + letter, blue on a hit / red on a
    miss — the trail of guesses already made."""
    col = ACCENT_FILL if hit else CRIMSON
    circ = Circle(radius=r, color=col, fill_opacity=1.0, stroke_width=1.5)
    lab = crisp_text(letter.upper(), font_size=16, color=WHITE, weight=BOLD)
    lab.move_to(circ)
    return VGroup(circ, lab)


def faint_fan(center, nbranches, *, end_y, half_w, r=NODE_R,
              stroke_width=1.2, opacity=0.22):
    """The (unchosen) sibling branches as faint lines radiating from ``center``
    down to a row at ``end_y``, spread across ±``half_w`` in x. Returns an empty
    VGroup for a single branch (a determined node's completion guess has no
    siblings), so callers can skip the draw when it's empty."""
    fan = VGroup()
    if nbranches <= 1:
        return fan
    for x in np.linspace(-half_w, half_w, nbranches - 1):
        end = np.array([x, end_y, 0.0])
        d = normalize(end - center)
        fan.add(Line(center + d * r, end, stroke_width=stroke_width,
                     color=BLACK, stroke_opacity=opacity))
    return fan
