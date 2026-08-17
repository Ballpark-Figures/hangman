"""SCENE 06 — introduce the TIER LIST (the alphabet, ranked into 7 tiers).

On the brand light-blue background (NOT the chalkboard): a 7-row tier list —
coloured grade cell on the left (classic S-tier rainbow), dark charcoal content
panel on the right. The list is BLANK here (labels only); letters get filled in
the later letter scenes (13-21). Everything routes through the SHARED
`assets/tier_list.py` builder so those scenes reuse the exact same graphic.

Script row 06, split on '—' → 6 beats a–f (voiceover ↔ animation zip 1:1):
  a establish — show the blank tier list (S,A,B,C,D,E,F, full); pulse S then F
  b top       — emphasise the S tier (dim the rest)
  c next      — emphasise the A tier too, keeping S lit
  d cascade   — un-dim one more tier at a time until all 7 are lit again
  e numbers   — swap every grade for its numerical alphabet position (S→19…) — a joke
  f names     — swap to named tiers: TOP / HIGH↑ / HIGH↓ / MID↑ / MID↓ / LOW↑ / LOW↓

Ends on the named, EMPTY tier list (centred) — scene 07 continues from here, filling
in the top tier's letters one at a time.

Render:  render 06a --fast   (…06f)   /   render 06 sub  for the whole scene

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every fade / pulse /
emphasise / label-morph run_time and the inter-tier cascade pacing.
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import *
from assets import tier_list as tl


class Scene06(HangmanScene):
    """The tier list, introduced. See module docstring for the beat map.

    BEAT MAP
      establish — full tier list; pulse S then F (dim the rest, there-and-back)
      top       — emphasise S (dim the rest)
      next      — emphasise S + A
      cascade   — un-dim one more tier at a time until all lit again
      numbers   — grades → alphabet-position numbers (joke)
      names     — numbers → named tiers with arrows
    """

    def setup_scene(self):
        pass   # nothing on frame 0; the list is owned by `establish`

    def _setup_tiers(self):
        # resting state is FULL opacity; emphasis (b–d) DIMS the other tiers
        self.tl = tl.get_tier_list("letter")

    def _pulse(self, i, run_time):
        """Spotlight tier `i` (dim every other tier) and back — a there-and-back
        peek that returns the whole list to full."""
        self.play(*[self.tl.rows[j].animate.set_opacity(tl.DIM_OPACITY)
                    for j in range(self.tl.n) if j != i],
                  rate_func=there_and_back, run_time=run_time)

    def _swap_labels(self, factory, run_time, extra_anims=()):
        """Crossfade every tier's label into a new one from `factory(i)` (built at
        the cell centre): the old fades out as the new fades in, in place. The new
        label joins its row VGroup (so later emphasis keeps dimming it); the old is
        dropped. No shape-morph — clean for unrelated glyphs (S→19→HIGH▲).
        `extra_anims` play concurrently (e.g. the beat-f cell recolour)."""
        news, anims = [], []
        for i in range(self.tl.n):
            new = factory(i).move_to(self.tl.cells[i]).set_opacity(0)
            self.tl.rows[i].add(new)
            news.append(new)
            anims += [self.tl.labels[i].animate.set_opacity(0),
                      new.animate.set_opacity(1)]
        self.play(*anims, *extra_anims, run_time=run_time)
        for i, new in enumerate(news):
            self.tl.rows[i].remove(self.tl.labels[i])
            self.tl.labels[i] = new

    # a : lagged fade-in (rows rise into place), then peek the S + F tiers
    @subscene
    def establish(self):
        self._setup_tiers()
        self.play(LaggedStart(*[FadeIn(row, shift=0.4 * UP)
                                for row in self.tl.rows], lag_ratio=0.15),
                  run_time=1.4)
        self.wait(0.4)                                   # VO
        self._pulse(0, 0.7)                              # S — most useful
        self._pulse(self.tl.n - 1, 0.7)                 # F — least useful

    # b : emphasise the S tier (dim the rest)
    @subscene
    def top(self):
        self.play(*tl.emphasize(self.tl, 0), run_time=0.6)

    # c : emphasise S + A
    @subscene
    def next(self):
        self.play(*tl.emphasize(self.tl, {0, 1}), run_time=0.6)

    # d : un-dim one more tier at a time until all 7 are lit again
    @subscene
    def cascade(self):
        step = 0.45                                      # lockstep per-tier reveal
        for i in range(2, self.tl.n):
            self.play(*tl.emphasize(self.tl, range(i + 1)), run_time=step)

    # e : swap every grade for its numerical position in the alphabet (S→19, A→1…)
    @subscene
    def numbers(self):
        self._swap_labels(tl.number_label, 0.9)

    # f : swap to named tiers with arrows, recolouring cells into name-groups
    #     (TOP red · HIGH orange · MID yellow · LOW green)
    @subscene
    def names(self):
        recolor = [self.tl.cells[i].animate.set_fill(tl.NAME_TIER_COLORS[i])
                   for i in range(self.tl.n)]
        self._swap_labels(tl.name_label, 1.0, extra_anims=recolor)
