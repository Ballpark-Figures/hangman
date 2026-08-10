"""Tier list — the alphabet ranked into 7 tiers, the recurring graphic for the
tier-list arc (scenes 06, 13-21, and the re-weighting scenes that shuffle it).

Lives on the BRAND light-blue background (crisp_text labels, dark charcoal
content panels, classic S-tier rainbow label cells) — the same visual world as
the letter heatmap / ngram assets it pairs with in the letter scenes, NOT the
chalkboard.

Stateless builder: `get_tier_list(labels)` returns a VGroup with handles
    .rows[i]      VGroup(cell, panel, label, contents) for tier i, top→bottom
    .cells / .panels / .labels / .contents   parallel lists
plus geometry (`.panel_left_x`, `.row_cy`) so a later scene can drop letters
into a tier's `.contents`. The label is swappable per beat via the module
factories `letter_label` / `number_label` / `name_label` (Transform the old
into the new). Resting state is FULL opacity; `emphasize(tiers)` spotlights by
DIMMING every other tier, `reset` clears it.

Scene 06 shows the list BLANK (labels only); the letter→tier assignments are
SOURCED from the script and filled in the later scenes (never invented here).
"""
import numpy as np
from manim import *

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import *   # crisp_text, style colours, LIGHT_* palette


# ── tier vocabulary ───────────────────────────────────────────────────────────
# Default 7 tier labels (classic S-tier grades) and their eventual NAMES.
LETTER_LABELS = ["S", "A", "B", "C", "D", "E", "F"]
NAME_LABELS   = [("TOP",  None),      # tier 0
                 ("HIGH", "up"),      # tier 1
                 ("HIGH", "down"),    # tier 2
                 ("MID",  "up"),      # tier 3
                 ("MID",  "down"),    # tier 4
                 ("LOW",  "up"),      # tier 5
                 ("LOW",  "down")]    # tier 6

# Classic S-tier rainbow (LIGHT_PALETTE ramp + a neutral grey for the last tier) —
# used while the labels are the S,A,B,… GRADES.
TIER_GREY   = ManimColor("#9AA0A6")
TIER_COLORS = [LIGHT_RED, LIGHT_ORANGE, LIGHT_YELLOW,
               LIGHT_GREEN, LIGHT_BLUE, LIGHT_PURPLE, TIER_GREY]

# Once the tiers are NAMED, each name-group shares a hue: TOP red, HIGH orange,
# MID yellow, LOW green. Within a pair the ↑ tier leans slightly toward the group
# ABOVE and the ↓ tier slightly toward the group BELOW — but only by `_LEAN`, so
# the two tiers of one word stay visibly CLOSER to each other than to the adjacent
# tier (a grouped palette, NOT a continuous gradient).
# Anchors reuse the ORIGINAL rainbow's hues (the S-tier LIGHT_* palette) so the
# named colours match its brightness; only the small ±_LEAN pulls each pair apart.
_TOP_RED    = LIGHT_RED
_ORANGE     = LIGHT_ORANGE
_YELLOW     = LIGHT_YELLOW
_GREEN      = LIGHT_GREEN
_DEEP_GREEN = ManimColor("#2E9E56")   # notional "below LOW" anchor for LOW ↓
_LEAN = 0.1                          # small: keep same-word tiers grouped

NAME_TIER_COLORS = [
    _TOP_RED,                                   # TOP
    _ORANGE.interpolate(_TOP_RED, _LEAN),       # HIGH ↑  → toward red   (above)
    _ORANGE.interpolate(_YELLOW,  _LEAN),       # HIGH ↓  → toward yellow (below)
    _YELLOW.interpolate(_ORANGE,  _LEAN),       # MID  ↑  → toward orange (above)
    _YELLOW.interpolate(_GREEN,   _LEAN),       # MID  ↓  → toward green  (below)
    _GREEN.interpolate(_YELLOW,   _LEAN),       # LOW  ↑  → toward yellow (above)
    _GREEN.interpolate(_DEEP_GREEN, _LEAN),     # LOW  ↓  → toward deep green (below)
]

PANEL_FILL   = ManimColor("#2B2B2B")   # dark charcoal content row (letters pop on it)
PANEL_STROKE = ManimColor("#15151A")
LABEL_COLOR  = BLACK                   # reads on every bright cell + the grey
DIM_OPACITY  = 0.28                    # a tier's muted / un-emphasised look


# ── label factories (Transform one state into the next across beats) ───────────
def letter_label(i, *, height=0.44, color=LABEL_COLOR):
    """The grade label for tier `i` (S, A, B, …)."""
    lab = crisp_text(LETTER_LABELS[i], font_size=FONT_SIZE_LG, color=color,
                     weight=BOLD)
    return lab.set_height(height)


def number_label(i, *, height=0.44, color=LABEL_COLOR):
    """The grade letter's numerical position in the alphabet (S→19, A→1, …) —
    the deliberately-absurd beat before the tiers get real names."""
    n = ord(LETTER_LABELS[i].upper()) - 64
    lab = crisp_text(str(n), font_size=FONT_SIZE_LG, color=color, weight=BOLD)
    return lab.set_height(height)


def name_label(i, *, height=0.34, color=LABEL_COLOR):
    """The named tier label: a word (TOP/HIGH/MID/LOW) with an optional up/down
    arrow to its RIGHT. `height` is the word's cap height."""
    word, arrow = NAME_LABELS[i]
    txt = crisp_text(word, font_size=FONT_SIZE_LG, color=color, weight=BOLD)
    txt.set_height(height)
    if arrow is None:
        return VGroup(txt).move_to(ORIGIN)
    tri = Triangle(fill_color=color, fill_opacity=1.0, stroke_width=0)
    tri.set_height(height * 0.62)
    if arrow == "down":
        tri.rotate(PI)
    tri.next_to(txt, RIGHT, buff=height * 0.32)
    return VGroup(txt, tri).move_to(ORIGIN)


# ── the tier list ─────────────────────────────────────────────────────────────
def get_tier_list(labels="letter", *, center=ORIGIN, panel_width=10.2,
                  cell_width=1.75, row_height=0.82, row_gap=0.10,
                  cell_gap=0.08, colors=None, dimmed=False):
    """A 7-row tier list: a coloured grade CELL on the left + a dark content
    PANEL on the right, per tier, top (best) → bottom (worst).

    labels : "letter" | "number" | "name" — which label state to build.
    dimmed : start every row muted (for the beat-06 emphasis build-up).
    colors : per-tier cell colours; default = the S-tier rainbow for grade labels,
             the grouped TOP/HIGH/MID/LOW palette once the tiers are NAMED.

    Returns VGroup(*rows) with `.rows` (list of VGroup(cell, panel, label,
    contents)), parallel `.cells/.panels/.labels/.contents`, and geometry
    `.panel_left_x` / `.row_cy(i)` for placing letters later.
    """
    if colors is None:
        colors = NAME_TIER_COLORS if labels == "name" else TIER_COLORS
    n = len(LETTER_LABELS)
    pitch = row_height + row_gap
    total_h = n * row_height + (n - 1) * row_gap
    top_cy = total_h / 2 - row_height / 2
    full_w = cell_width + cell_gap + panel_width
    left = -full_w / 2
    cell_cx = left + cell_width / 2
    panel_cx = left + cell_width + cell_gap + panel_width / 2
    panel_left = left + cell_width + cell_gap

    label_fn = {"letter": letter_label, "number": number_label,
                "name": name_label}[labels]

    rows, cells, panels, labs, contents = [], [], [], [], []
    for i in range(n):
        cy = top_cy - i * pitch
        cell = RoundedRectangle(width=cell_width, height=row_height,
                                corner_radius=0.06)
        cell.set_fill(colors[i], opacity=1.0).set_stroke(PANEL_STROKE, width=2)
        cell.move_to([cell_cx, cy, 0])

        panel = RoundedRectangle(width=panel_width, height=row_height,
                                 corner_radius=0.06)
        panel.set_fill(PANEL_FILL, opacity=1.0).set_stroke(PANEL_STROKE, width=2)
        panel.move_to([panel_cx, cy, 0])

        lab = label_fn(i)
        lab.move_to([cell_cx, cy, 0])

        cont = VGroup()   # letters get dropped in here by later scenes
        row = VGroup(cell, panel, lab, cont)
        if dimmed:
            row.set_opacity(DIM_OPACITY)
        rows.append(row)
        cells.append(cell); panels.append(panel); labs.append(lab)
        contents.append(cont)

    tl = VGroup(*rows).shift(center)
    tl.rows = rows
    tl.cells = cells
    tl.panels = panels
    tl.labels = labs
    tl.contents = contents
    tl.panel_left_x = panel_left + center[0]
    tl.row_cys = [(top_cy - i * pitch) + center[1] for i in range(n)]
    tl.n = n
    return tl


# ── emphasis (resting state is FULL; emphasise by DIMMING THE REST) ────────────
def emphasize(tl, tiers):
    """Animations that emphasise tier(s) `tiers` (an int or an iterable of ints)
    by fading EVERY OTHER tier down to `DIM_OPACITY` while the emphasised ones
    stay at full. Passing all tiers (or the resting call `reset`) clears the dim.
    Returns a flat list — unpack into `self.play(*emphasize(tl, {0, 1}))`. Idempo-
    tent: a tier already in the right state animates in place (no visible change),
    so beats can pass a GROWING set to accumulate emphasis."""
    idx = {tiers} if isinstance(tiers, int) else set(tiers)
    return [tl.rows[i].animate.set_opacity(1.0 if i in idx else DIM_OPACITY)
            for i in range(tl.n)]


def reset(tl):
    """Animations returning every tier to the full (un-dimmed) resting state."""
    return [row.animate.set_opacity(1.0) for row in tl.rows]
