from manim import *


class LightMeter(Scene):
    """Petit mesurador d'intensitat de llum (VU meter) que es dispara
    quan un núvol deixa de tapar el sol de cop.

    Pensat com a overlay: renderitzar amb fons transparent (-t) i
    composar a sobre del metratge real de la fulla / el camp.
    """

    def construct(self):
        n = 10
        seg_w, seg_h, gap = 0.6, 0.35, 0.08

        # --- Segments del mesurador ---
        segments = VGroup(
            *[
                RoundedRectangle(
                    width=seg_w,
                    height=seg_h,
                    corner_radius=0.05,
                    stroke_width=1.5,
                    stroke_color=WHITE,
                    stroke_opacity=0.35,
                    fill_opacity=0,
                )
                for _ in range(n)
            ]
        ).arrange(UP, buff=gap)

        # Groc suau -> ambre -> blanc encegador al capdamunt
        lit_colors = color_gradient([YELLOW_E, YELLOW, "#FDBA74", WHITE], n)

        level = ValueTracker(0)

        def refresh_segments(segs):
            lvl = level.get_value()
            for i, seg in enumerate(segs):
                if i < int(lvl):
                    seg.set_fill(lit_colors[i], opacity=1)
                    seg.set_stroke(lit_colors[i], opacity=1, width=1.5)
                elif i < lvl:
                    frac = lvl - i
                    seg.set_fill(lit_colors[i], opacity=frac)
                    seg.set_stroke(WHITE, opacity=0.6, width=1.5)
                else:
                    seg.set_fill(opacity=0)
                    seg.set_stroke(WHITE, opacity=0.35, width=1.5)

        segments.add_updater(refresh_segments)

        # --- Fons semitransparent perquè es llegeixi sobre metratge clar ---
        backing = RoundedRectangle(
            width=seg_w + 0.35,
            height=segments.height + 0.4,
            corner_radius=0.15,
            fill_color=BLACK,
            fill_opacity=0.35,
            stroke_width=0,
        ).move_to(segments)

        caption = Text("INTENSITAT", font_size=16, color=WHITE, weight=BOLD)
        caption.set_opacity(0.85).next_to(segments, DOWN, buff=0.22)

        meter = VGroup(backing, segments, caption)
        meter.scale(0.75).to_corner(DR, buff=0.5)

        # Número "×N" que segueix el mesurador un cop ja està posicionat
        value_text = always_redraw(
            lambda: Text(
                f"×{level.get_value():.1f}", font_size=26, weight=BOLD, color=WHITE
            ).next_to(segments, UP, buff=0.2)
        )

        # --- Entrada ---
        self.play(FadeIn(backing), FadeIn(segments), FadeIn(caption), run_time=0.5)
        self.add(value_text)
        self.play(level.animate.set_value(2.2), run_time=0.6)

        # --- Sol estable, lleuger tremolor natural ---
        for target in (2.6, 1.9, 2.4, 2.0):
            self.play(level.animate.set_value(target), run_time=0.35)

        # --- El núvol deixa de tapar el sol: dispara de cop ---
        self.play(
            level.animate.set_value(11),
            Flash(meter, color=WHITE, flash_radius=1.3, num_lines=14, run_time=0.35),
            run_time=0.18,
            rate_func=rush_into,
        )
        self.play(level.animate.set_value(10), run_time=0.12, rate_func=rush_from)
        self.wait(0.6)

        # --- El núvol acaba de passar, la llum torna a un nivell normal ---
        self.play(level.animate.set_value(3), run_time=1.0)
        self.wait(0.5)
