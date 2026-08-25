"""Shared entrances + titles for the "view" graphics (the position-frequency
heatmaps, the n-gram lists, the scene-16 usage-by-tier plot).

Extracted from `tier_letter_scene` so ANY scene — not just `TierLetterScene`
subclasses — brings a titled view on with the SAME established motion, instead of
hand-rolling one:

  - `rise(scene, parent, rows)` — "96's row-by-row rise": preset each row a touch
    low + transparent, add the parent, and return a LaggedStart lifting the rows
    into place. The CALLER plays it (sets run_time) and can fold a title FadeIn into
    the same play. Used by `tier_letter_scene.show_heat/add_ngram/show_common` and
    scene 16 beat d.
  - `view_title` / `view_title2` — the one-/two-line view title (`crisp_text` /
    `crisp_paragraph`, brand font, dark ink), placed at (x, y).

Bring a titled view on with:
    title = views.view_title("Usage by Tier", x, y)
    self.play(FadeIn(title), views.rise(self, parent, rows), run_time=1.6)
"""
from config import *

RISE_SHIFT = 0.28
RISE_LAG   = 0.14


def rise(scene, parent, rows, *, lag_ratio=RISE_LAG, shift=RISE_SHIFT):
    """Add `parent`, preset each row in `rows` a touch low + transparent, and return a
    LaggedStart that lifts each row up into place. The caller plays it (and may add a
    title FadeIn / a fade-out of the outgoing view in the SAME play)."""
    for row in rows:
        row.shift(DOWN * shift).set_opacity(0)
    scene.add(parent)
    return LaggedStart(*[row.animate.shift(UP * shift).set_opacity(1)
                         for row in rows], lag_ratio=lag_ratio)


def view_title(text, x, y, *, font_size=30, color=BLACK):
    """A single-line view title (e.g. 'Usage by Tier', 'Common Uses') at `font_size`.

    A LONGER string WRAPS at `crisp_text`'s 240pt supersample cap. When that happens,
    rebuild it at a small underlying font (no wrap) and scale to the SAME height a
    single line at `font_size` has — so the title stays ONE line at the intended SIZE,
    not shrunk to a width. A short title that doesn't wrap is left exactly as before
    (so existing callers render byte-identically)."""
    ref = crisp_text("Ag", font_size=font_size, color=color)          # one-line height
    t = crisp_text(text, font_size=font_size, color=color)
    if t.height > ref.height * 1.5:                                    # it wrapped
        t = crisp_text(text, font_size=10, color=color).scale_to_fit_height(ref.height)
    return t.move_to([x, y, 0])


def view_title2(l1, l2, x, y, *, font_size=30, color=BLACK):
    """A two-line view title (e.g. 'Before'/'After')."""
    return crisp_paragraph(l1, l2, font_size=font_size, color=color,
                           alignment="center").move_to([x, y, 0])
