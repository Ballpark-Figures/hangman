"""SCENE 06 — introduce the TIER LIST (the alphabet, ranked into 7 tiers).

On the brand light-blue background (NOT the chalkboard): a 7-row tier list —
coloured grade cell on the left (classic S-tier rainbow), dark charcoal content
panel on the right. The list is BLANK here (labels only); letters get filled in
the later letter scenes (13-21). Everything routes through the SHARED
`assets/tier_list.py` builder so those scenes reuse the exact same graphic.

Script row 06, split on '—' → 6 beats a–f (voiceover ↔ animation zip 1:1):
  a establish — show the blank tier list (S,A,B,C,D,E,F, muted); pulse S then F
  b top       — emphasise (light up + hold) the S tier
  c next      — emphasise the A tier, keeping S lit
  d cascade   — light up one more tier at a time until all 7 are lit
  e numbers   — swap every grade for its numerical alphabet position (S→19…) — a joke
  f names     — swap to named tiers: TOP / HIGH↑ / HIGH↓ / MID↑ / MID↓ / LOW↑ / LOW↓

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
      establish — blank muted tier list; pulse S then F
      top       — light + hold S
      next      — light + hold A (S stays lit)
      cascade   — light the remaining tiers one at a time until all lit
      numbers   — grades → alphabet-position numbers (joke)
      names     — numbers → named tiers with up/down arrows
    """

    def setup_scene(self):
        pass   # nothing on frame 0; the list is owned by `establish`

    def _setup_tiers(self):
        # built MUTED — the emphasis build-up (a–d) lights tiers up from here
        self.tl = tl.get_tier_list("letter", dimmed=True)

    def _pulse(self, i, run_time):
        """Brighten tier `i` to full and back to muted (a there-and-back peek)."""
        self.play(self.tl.rows[i].animate.set_opacity(1.0),
                  rate_func=there_and_back, run_time=run_time)

    # a : show the blank tier list, then pulse the S (top) and F (bottom) tiers
    @subscene
    def establish(self):
        self._setup_tiers()
        self.play(FadeIn(self.tl, shift=0.3 * UP), run_time=1.0)
        self.wait(0.4)                                   # VO
        self._pulse(0, 0.7)                              # S — most useful
        self._pulse(self.tl.n - 1, 0.7)                 # F — least useful

    # b : light up + hold the S tier
    @subscene
    def top(self):
        self.play(tl.emphasize(self.tl, 0), run_time=0.6)

    # c : light up the A tier, keeping S lit
    @subscene
    def next(self):
        self.play(tl.emphasize(self.tl, 1), run_time=0.6)

    # d : cascade — one more tier lit at a time until all 7 are lit
    @subscene
    def cascade(self):
        step = 0.45                                      # lockstep per-tier reveal
        for i in range(2, self.tl.n):
            self.play(tl.emphasize(self.tl, i), run_time=step)

    # e : swap every grade for its numerical position in the alphabet (S→19, A→1…)
    @subscene
    def numbers(self):
        news = []
        for i in range(self.tl.n):
            new = tl.number_label(i).move_to(self.tl.cells[i])
            news.append(new)
        self.play(*[Transform(self.tl.labels[i], news[i])
                    for i in range(self.tl.n)], run_time=0.9)

    # f : swap to named tiers with up/down arrows
    @subscene
    def names(self):
        news = []
        for i in range(self.tl.n):
            new = tl.name_label(i).move_to(self.tl.cells[i])
            news.append(new)
        self.play(*[Transform(self.tl.labels[i], news[i])
                    for i in range(self.tl.n)], run_time=1.0)
