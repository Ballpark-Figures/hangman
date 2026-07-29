from bpkfigures.scene import *

# Semantic status colours (NOT accents) — a miss/loss is red, a correct/hit green.
# Deliberately deeper than the categorical ACCENT_RED/GREEN so "bad/good" reads as
# a true red/green, not the orange-leaning warm-trio accent. Matches yahtzee's
# SCORE_RED/SCORE_GREEN (see bpkfigures/style.py header on why these live here).
SCORE_GREEN = "#1A7A1A"
SCORE_RED   = "#A60E00"


class HangmanScene(BpkScene):
    def construct(self):
        self.camera.background_color = BG_COLOR
        super().construct()
