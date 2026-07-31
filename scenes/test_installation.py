from manim import *


class TestInstallation(Scene):
    def construct(self):
        text = Text("Manim instal·lat correctament!", font_size=36)
        circle = Circle(color=BLUE).shift(DOWN * 1.5)
        self.play(Write(text))
        self.play(Create(circle))
        self.wait()
