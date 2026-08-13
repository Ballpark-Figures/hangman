"""Shared base for the frequency-search TABLE scenes (19 short_words, 20 longer_words).

Both present the CHOOSING strategy per word length as TABLES on the brand light-blue
background (a HangmanScene -> BG_COLOR; crisp_text + filled shapes, NOT chalk, NOT navy):
LEFT = letter-combo patterns + their multipliers, RIGHT = the chosen words + their
frequency share, under an "N-Letter Words" title. This base holds the shared table
machinery (title / mono / censor / reveal + number formatting); each scene subclasses it
and defines its OWN @subscene beats (the render tooling AST-scans the SCENE file, so beats
MUST live there — this base holds ONLY plain helpers).

Formatting conventions (routed through these single helpers so they hold everywhere):
  - a MULTIPLIER is ONE DECIMAL PLACE (`_mult`); a word % is 2 SIGNIFICANT FIGURES (`_sig2`).
  - a pattern (blanked word) / a word is BOLD and MONOSPACED (`_mono`) — each letter on a
    fixed CHAR_W slot, so equal-length strings line their letters up into COLUMNS.
  - censoring a word (`_censor`) replaces it wholesale with a transparent-black box so it
    is never shown clear (manim has no native blur).
"""
import math

from config import *

INK = BLACK                        # dark labels on the brand light-blue bg (scene 17/18 convention)
UNIFORM_COLOR = ACCENT_FILL        # equal-weighted bars (scene 19's double plot)
BESTOP_COLOR = CRIMSON             # best-opener (adversarial) weighted bars

TITLE_Y = 3.6                      # the scene title ("N-Letter Words")

# ── table layout (LEFT = patterns, RIGHT = words) ─────────────────────────────
LEFT_X, RIGHT_X = -3.7, 3.7        # each side's centre
LABEL_DX, VALUE_DX = -1.25, 1.15   # column x offsets from a side centre (label left, value right)
CHAR_W = 0.28                      # monospaced letter slot (letters line up into columns)
TABLE_TITLE_W = 5.4                # a wide table title scales down to this
SCENE_TITLE_H = 0.52               # scene-title glyph height (built small, scaled up)
TABLE_TITLE_H = 0.30              # table-title glyph height
HDR_FS = 22
ROW_FS = 22
TITLE_GAP = 0.6                    # table title → header
HDR_GAP = 0.44                     # header → first row
ROW_DY = 0.48                      # row → row
LABEL_MAX_W = 3.4                  # a mono label wider than this scales down so long words
                                   # (length-16 patterns/words) don't crowd the value column


class WordTablesScene(HangmanScene):
    """Frequency-search table machinery shared by scenes 19 and 20."""

    # ── number / cell formatting (one source of truth) ────────────────────────
    def _sig2(self, x):
        """2 significant figures."""
        if x == 0:
            return "0"
        d = 1 - math.floor(math.log10(abs(x)))
        return f"{x:.{max(d, 0)}f}"

    def _mult(self, x):
        """A multiplier, always to ONE decimal place (e.g. 18.0, 510.8)."""
        return f"{x:.1f}"

    def _pat_rows(self, rows):
        return [(r["pattern"], self._mult(r["multiplier"])) for r in rows]

    def _word_rows(self, rows):
        return [(r["word"], self._sig2(r["pct"]) + "%") for r in rows]

    def _mono(self, s, cx, y, color=INK, max_w=LABEL_MAX_W):
        """A bold, MONOSPACED string: each char on a fixed CHAR_W slot centred on cx, so
        equal-length strings line their letters up into columns down the table. A string
        wider than `max_w` scales down uniformly about cx (all rows in a table share a
        length, so they scale identically — per-table column alignment is preserved)."""
        n = len(s)
        g = VGroup()
        for i, ch in enumerate(s):
            x = cx + (i - (n - 1) / 2) * CHAR_W
            g.add(crisp_text(ch, font_size=ROW_FS, color=color, weight=BOLD, baseline_at=(x, y)))
        if max_w and g.width > max_w:
            g.scale(max_w / g.width)
        return g

    # ── censor: replace a word entirely with a transparent black box ──────────
    def _censor(self, mob):
        return RoundedRectangle(width=mob.width + 0.14, height=mob.height + 0.12,
                                corner_radius=0.05, fill_color=INK, fill_opacity=0.55,
                                stroke_width=0).move_to(mob)

    # ── title helpers (build small + scale so long titles don't wrap) ─────────
    def _fit(self, text, height, **kw):
        return crisp_text(text, font_size=10, **kw).scale_to_fit_height(height)

    def _scene_title(self, text):
        return self._fit(text, SCENE_TITLE_H, color=INK, weight=BOLD).move_to([0, TITLE_Y, 0])

    def _table_title(self, text, maxw):
        t = self._fit(text, TABLE_TITLE_H, color=INK, weight=BOLD)
        if t.width > maxw:
            t.scale_to_fit_width(maxw)
        return t

    # ── one titled table (title + column headers + baseline/mono rows) ────────
    def _table(self, title, headers, rows, *, top_y, cx, censor=()):
        lx, vx = cx + LABEL_DX, cx + VALUE_DX
        ttl = self._table_title(title, TABLE_TITLE_W).move_to([cx, top_y, 0])
        hy = top_y - TITLE_GAP
        hdr = VGroup(
            crisp_text(headers[0], font_size=HDR_FS, color=INK, weight=BOLD, baseline_at=(lx, hy)),
            crisp_text(headers[1], font_size=HDR_FS, color=INK, weight=BOLD, baseline_at=(vx, hy)))
        row_group = VGroup()
        for r, (lab, val) in enumerate(rows):
            ry = hy - HDR_GAP - r * ROW_DY
            label_mob = self._mono(lab, lx, ry)
            if lab in censor:
                label_mob = self._censor(label_mob)      # word replaced → never shown
            val_mob = crisp_text(val, font_size=ROW_FS, color=INK, baseline_at=(vx, ry))
            row_group.add(VGroup(label_mob, val_mob))
        tab = VGroup(ttl, hdr, row_group)
        tab.title, tab.header, tab.rows = ttl, hdr, row_group
        return tab

    def _reveal(self, tab, rows_run_time):
        """Fade the title+header in, then rise the rows up (FadeIn+shift keeps each cell's
        own opacity — so a censored cell keeps its transparency)."""
        self.play(FadeIn(tab.title), FadeIn(tab.header), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(row, shift=UP * 0.3) for row in tab.rows],
                              lag_ratio=0.12), run_time=rows_run_time)
