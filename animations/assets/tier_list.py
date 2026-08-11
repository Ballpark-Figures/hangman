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

# The letter → tier assignments, in within-tier DISPLAY order — SOURCED from the
# user (the product; not derived here). One string per tier, top → bottom.
TIER_LETTERS = ["EIA", "SR", "TNO", "LDC", "PUGMBH", "FYVKW", "XZJQ"]

# Letter layout inside a panel: fixed slot pitch + edge buff. The default panel
# width is sized so the FULLEST tier (most letters) sits with EQUAL left/right
# margins (the letters fill a symmetric block; shorter tiers stay left-aligned).
LETTER_PITCH = 0.82
LETTER_BUFF  = 0.26
_DEFAULT_PANEL_W = 2 * LETTER_BUFF + max(len(t) for t in TIER_LETTERS) * LETTER_PITCH

# Classic S-tier rainbow (LIGHT_PALETTE ramp + a neutral grey for the last tier) —
# used while the labels are the S,A,B,… GRADES.
TIER_GREY   = ManimColor("#9AA0A6")
TIER_COLORS = [LIGHT_RED, LIGHT_ORANGE, LIGHT_YELLOW,
               LIGHT_GREEN, LIGHT_BLUE, LIGHT_PURPLE, TIER_GREY]

# Once the tiers are NAMED, the palette spreads the four name-groups EVENLY across
# the rainbow — TOP red → LOW blue, with HIGH and MID spaced evenly between (the
# LIGHT_* ramp, red…blue). Within a pair the ↑ tier leans slightly toward the group
# ABOVE and the ↓ tier toward the group BELOW (by ±_LEAN), so the two tiers of one
# word stay visibly CLOSER to each other than to the adjacent tier (grouped, NOT a
# gradient).
def _rainbow(t):
    """Colour at fraction `t` along the LIGHT_* rainbow red…blue (0 = red … 1 = blue)."""
    stops = LIGHT_PALETTE[:5]   # red, orange, yellow, green, blue (drop purple)
    t = min(max(t, 0.0), 1.0)
    seg = t * (len(stops) - 1)
    i = min(int(seg), len(stops) - 2)
    return stops[i].interpolate(stops[i + 1], seg - i)

_A_TOP       = _rainbow(0.0)                        # red
_A_HIGH      = _rainbow(1 / 3)                      # evenly between red and blue
_A_MID       = _rainbow(2 / 3)
_A_LOW       = _rainbow(1.0)                        # blue
_A_BELOW_LOW = ManimColor("#2B6CB0")               # deeper blue, notional below LOW
_LEAN = 0.15                                         # small: keep same-word tiers grouped

NAME_TIER_COLORS = [
    _A_TOP,                                     # TOP
    _A_HIGH.interpolate(_A_TOP, _LEAN),         # HIGH ↑  → toward TOP  (above)
    _A_HIGH.interpolate(_A_MID, _LEAN),         # HIGH ↓  → toward MID  (below)
    _A_MID.interpolate(_A_HIGH, _LEAN),         # MID  ↑  → toward HIGH (above)
    _A_MID.interpolate(_A_LOW, _LEAN),          # MID  ↓  → toward LOW  (below)
    _A_LOW.interpolate(_A_MID, _LEAN),          # LOW  ↑  → toward MID  (above)
    _A_LOW.interpolate(_A_BELOW_LOW, _LEAN),    # LOW  ↓  → toward deeper purple (below)
]

PANEL_FILL   = ManimColor("#2B2B2B")   # dark charcoal content row (letters pop on it)
PANEL_STROKE = ManimColor("#15151A")
LABEL_COLOR  = BLACK                   # reads on every bright cell + the grey
LETTER_COLOR = WHITE                   # (legacy) neutral tier letter colour
DIM_OPACITY  = 0.28                    # a tier's muted / un-emphasised look

# Vowel/consonant colouring of the letters (the vowel/consonant arc, scene 08 on):
# BRIGHT on the dark tier panels; DARK on the light bg (the big corner letter + the
# ngram anchor). Consonants keep the existing blue (ACCENT_FILL) on the light bg.
VOWELS = set("aeiouy")                 # Y always a vowel (matches scene 08)
VOWEL_TILE_COLOR = LIGHT_RED           # vowel letter on a dark tier panel
CONS_TILE_COLOR  = LIGHT_BLUE          # consonant letter on a dark tier panel
VOWEL_INK_COLOR  = ACCENT_RED          # vowel big-letter / ngram anchor (light bg)
CONS_INK_COLOR   = ACCENT_FILL         # consonant ditto — the existing blue


def tile_color(ch):
    """Bright tier-panel colour for `ch`: vowel red / consonant blue."""
    return VOWEL_TILE_COLOR if ch.lower() in VOWELS else CONS_TILE_COLOR


def ink_color(ch):
    """Dark light-bg colour for `ch` (the big corner letter + the ngram anchor):
    vowel dark-red / consonant blue."""
    return VOWEL_INK_COLOR if ch.lower() in VOWELS else CONS_INK_COLOR


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
def get_tier_list(labels="letter", *, center=ORIGIN, panel_width=_DEFAULT_PANEL_W,
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


# ── filling a tier with its letters ───────────────────────────────────────────
def letter_tile(ch, *, height=0.5, color=None):
    """One tier letter, drawn on the dark panel — coloured vowel-red / consonant-blue
    by default (`tile_color`); pass `color` to override."""
    if color is None:
        color = tile_color(ch)
    return crisp_text(ch.upper(), font_size=FONT_SIZE_LG, color=color,
                      weight=BOLD).set_height(height)


def fill_tier(tl, i, letters=None, *, height=0.5, buff=LETTER_BUFF,
              pitch=LETTER_PITCH):
    """Lay tier `i`'s `letters` (default: the sourced TIER_LETTERS[i]) left→right
    in its panel — each centred in a fixed `pitch`-wide slot so they stay evenly
    spaced regardless of glyph width — and add them to the tier's `.contents` (so
    later emphasis dims them with the row). Returns the VGroup of new tiles."""
    if letters is None:
        letters = TIER_LETTERS[i]
    cy = tl.row_cys[i]
    x0 = tl.panel_left_x + buff
    tiles = VGroup(*[letter_tile(ch, height=height).move_to(
                        [x0 + pitch / 2 + k * pitch, cy, 0])
                     for k, ch in enumerate(letters)])
    tl.contents[i].add(*tiles)
    return tiles


# ── emphasis (resting state is FULL; emphasise by DIMMING THE REST) ────────────


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
