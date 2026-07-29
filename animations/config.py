from bpkfigures.scene import *


class HangmanScene(BpkScene):
    def construct(self):
        self.camera.background_color = BG_COLOR
        super().construct()
