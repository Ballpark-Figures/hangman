"""Blanked hangman board — the shared word display for gameplay scenes and the
strategy-tree viz. Promoted from scenes/98tree_demo.py.

A "pattern" is a fixed-length string of revealed letters and underscores:
  "_a_"  middle letter known      "tat"  fully solved
Underscores render as rules; a revealed letter sits above its rule. Colours:
revealed = ACCENT_FILL, a solved word = ACCENT_GOLD, a miss = CRIMSON (the shared
scorebox crimson from style.py — a true red tuned for the cyan BG, not the
orange-leaning ACCENT_RED).

`merge_pattern` overlays a newly-revealed guess onto the pattern known so far
(a guess only fills its own positions, never overwriting an ancestor's letter),
so a tree edge can show the board accumulate down a path.

NOTE: the rule colour is GREY_D — there is no neutral in style.py yet, so the
lint flags it. If a real gameplay scene adopts this, add a NEUTRAL/RULE colour
to style.py (an ASK-first shared change) and swap RULE_COLOR to it.
"""
from config import *

REVEAL_COLOR = ACCENT_FILL
SOLVED_COLOR = ACCENT_GOLD
MISS_COLOR   = CRIMSON
RULE_COLOR   = GREY_D


def merge_pattern(known, key):
    """Overlay branch key `key` onto the pattern `known` revealed so far."""
    return "".join(k if k != "_" else b for b, k in zip(known, key))


def blanked_board(pattern, *, color=REVEAL_COLOR, slot=0.30, gap=0.14,
                  font_size=22, weight="NORMAL"):
    """A row of rules (one per position); revealed letters sit above their rule."""
    slots = VGroup()
    for ch in pattern:
        rule = Line(LEFT * slot / 2, RIGHT * slot / 2,
                    stroke_width=3.5, color=RULE_COLOR)
        cell = VGroup(rule)
        if ch != "_":
            t = crisp_text(ch.upper(), font_size=font_size, color=color,
                           weight=weight)
            t.next_to(rule, UP, buff=0.05)
            cell.add(t)
        slots.add(cell)
    slots.arrange(RIGHT, buff=gap, aligned_edge=DOWN)
    return slots


def solved_word(word, **kw):
    """A fully-revealed word (a leaf), tinted gold by default."""
    kw.setdefault("color", SOLVED_COLOR)
    return blanked_board(word, **kw)


def miss_tag(letters, *, font_size=15):
    """A small red 'miss: …' caption listing letters ruled out on this edge."""
    return crisp_text("miss: " + ", ".join(l.upper() for l in letters),
                      font_size=font_size, color=MISS_COLOR)


def missed_letters(letters, *, font_size=24, color=MISS_COLOR, buff=0.22,
                   weight="NORMAL"):
    """A row of the wrong-guess letters in red, for display below the gallows —
    the classic hangman running tally. Empty ``letters`` -> an empty VGroup (so a
    scene can start it blank and grow it as misses accumulate)."""
    row = VGroup(*[crisp_text(l.upper(), font_size=font_size, color=color,
                              weight=weight)
                   for l in letters])
    if len(row):
        row.arrange(RIGHT, buff=buff)
    return row


# ── the (optional) hangman gallows drawing ────────────────────────────────────
DRAW_COLOR = ACCENT_FILL

# body parts, in the order they are drawn (one per miss, after the gallows)
HANGMAN_PARTS = ("head", "torso", "arm1", "arm2", "leg1", "leg2")


def hangman_drawing(misses=0, *, color=DRAW_COLOR, stroke_width=5.0):
    """The gallows, plus one body part per miss, capped at 6.

    Drawing order (the gallows is always present, at 0 misses):
        head → torso → arm1 → arm2 → leg1 → leg2
    so `misses` parts hang on the gallows (min(misses, 6)).

    Returns a VGroup carrying two handles for incremental animation:
        .gallows          the gallows VGroup (base/post/beam/rope)
        .parts            the 6 body-part mobjects, IN ORDER, all pre-built and
                          positioned (whether or not this call shows them)
    Only the gallows + the first `misses` parts are added to the returned group.
    To reveal the next miss in a scene:  p = draw.parts[k]; draw.add(p);
    self.play(Create(p)).
    """
    def line(a, b):
        return Line(a, b, color=color, stroke_width=stroke_width)

    # gallows (rope end at x=0.6, where the figure hangs)
    base = line([-1.3, -2.2, 0], [1.3, -2.2, 0])
    post = line([-1.0, -2.2, 0], [-1.0, 2.0, 0])
    beam = line([-1.0, 2.0, 0], [0.6, 2.0, 0])
    rope = line([0.6, 2.0, 0], [0.6, 1.55, 0])
    gallows = VGroup(base, post, beam, rope)

    # the hanging figure (head top meets the rope end at y=1.55)
    head = Circle(radius=0.33, color=color, stroke_width=stroke_width,
                  fill_opacity=0).move_to([0.6, 1.22, 0])
    torso = line([0.6, 0.89, 0], [0.6, -0.35, 0])
    arm1 = line([0.6, 0.62, 0], [0.12, 0.18, 0])
    arm2 = line([0.6, 0.62, 0], [1.08, 0.18, 0])
    leg1 = line([0.6, -0.35, 0], [0.18, -1.05, 0])
    leg2 = line([0.6, -0.35, 0], [1.02, -1.05, 0])

    grp = VGroup(gallows)
    grp.gallows = gallows
    grp.parts = [head, torso, arm1, arm2, leg1, leg2]
    grp.add(*grp.parts[:min(misses, 6)])
    return grp
