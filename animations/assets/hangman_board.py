"""Blanked hangman board — the shared word display for gameplay scenes and the
strategy-tree viz. Promoted from scenes/98tree_demo.py.

A "pattern" is a fixed-length string of revealed letters and underscores:
  "_a_"  middle letter known      "tat"  fully solved
Underscores render as rules; a revealed letter sits above its rule. Colours:
revealed = ACCENT_FILL, a solved word = ACCENT_GOLD, a miss = ACCENT_RED.

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
MISS_COLOR   = ACCENT_RED
RULE_COLOR   = GREY_D


def merge_pattern(known, key):
    """Overlay branch key `key` onto the pattern `known` revealed so far."""
    return "".join(k if k != "_" else b for b, k in zip(known, key))


def blanked_board(pattern, *, color=REVEAL_COLOR, slot=0.30, gap=0.14,
                  font_size=22):
    """A row of rules (one per position); revealed letters sit above their rule."""
    slots = VGroup()
    for ch in pattern:
        rule = Line(LEFT * slot / 2, RIGHT * slot / 2,
                    stroke_width=3.5, color=RULE_COLOR)
        cell = VGroup(rule)
        if ch != "_":
            t = crisp_text(ch.upper(), font_size=font_size, color=color)
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
