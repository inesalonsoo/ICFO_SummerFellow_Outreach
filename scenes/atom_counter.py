import json
import random
from pathlib import Path

import numpy as np
from manim import *

DATA_PATH = Path(__file__).parent / "data" / "lhcii_ca_backbone.json"


class AtomCounter(Scene):
    """Comptador 'milers d'àtoms' basat en la geometria real del monòmer
    de LHCII (PDB 2BHW, cadena A, Standfuss et al. 2005 EMBO J).

    Fase 1: es traça el backbone Cα real (223 residus resolts a la
    cristal·lografia + 11 residus flexibles no resolts, dibuixats en
    discontinu) mentre un comptador puja fins a 234 àtoms Cα.

    Fase 2: explota en connexions entre parells d'àtoms (distàncies
    interatòmiques, tal com s'usen per construir les features del TICA),
    amb el comptador saltant fins a les 27.261 distàncies reals
    (C(234,2)). Sensació de soroll / massa dades per mirar-ho a ull.

    Pensat com a overlay: renderitzar amb fons transparent (-t).
    """

    def construct(self):
        random.seed(7)
        np.random.seed(7)

        with open(DATA_PATH) as f:
            data = json.load(f)

        pts = [np.array([p[0], p[1], p[2] * 0.3]) for p in data["points"]]
        n_real = len(pts)
        n_sim = data["n_atoms_simulation"]
        n_pairs = data["n_pairs_simulation"]
        n_extra = n_sim - n_real  # residus flexibles no resolts (dibuixats discontinus)

        # Encaixem el núvol a la meitat esquerra perquè hi càpiga el comptador a la dreta
        shift = LEFT * 3.0
        pts = [p + np.array([shift[0], shift[1], 0]) for p in pts]

        rainbow = color_gradient([BLUE_D, TEAL, GREEN, YELLOW, ORANGE, RED], n_real)

        dots = VGroup(
            *[Dot(point=p, radius=0.045, color=rainbow[i], fill_opacity=1) for i, p in enumerate(pts)]
        )

        backbone = VMobject(stroke_color=WHITE, stroke_width=1.2, stroke_opacity=0.5)
        backbone.set_points_as_corners(pts)

        # --- Comptador ---
        counter_label = Text("àtoms Cα", font_size=26, color=WHITE, weight=BOLD)
        count_val = ValueTracker(0)
        counter_number = always_redraw(
            lambda: Text(
                f"{int(count_val.get_value()):,}".replace(",", "."),
                font_size=54,
                color=WHITE,
                weight=BOLD,
            ).next_to(counter_label, UP, buff=0.18)
        )
        counter_group = VGroup(counter_label, counter_number)
        counter_group.arrange(UP, buff=0.18).to_edge(RIGHT, buff=1.6)

        # --- Fase 1: es dibuixa el backbone real ---
        self.play(
            LaggedStart(*[Create(d) for d in dots], lag_ratio=0.02, run_time=2.2),
            Create(backbone, run_time=2.2),
            count_val.animate(run_time=2.2).set_value(n_real),
        )
        self.add(counter_group)

        # Cua discontinua: residus N-terminals flexibles, no resolts al cristall
        tail_dir = normalize(pts[0] - pts[3])
        tail_pts = [pts[0] + tail_dir * 0.22 * (i + 1) + np.random.normal(scale=0.05, size=3) for i in range(n_extra)]
        tail_dots = VGroup(
            *[Dot(point=p, radius=0.04, color=BLUE_D, fill_opacity=0.4, stroke_width=0) for p in tail_pts]
        )
        tail_line = DashedVMobject(
            VMobject().set_points_as_corners([pts[0]] + tail_pts), num_dashes=14, color=BLUE_D
        ).set_stroke(opacity=0.5)

        self.play(
            FadeIn(tail_dots, lag_ratio=0.1, run_time=0.7),
            Create(tail_line, run_time=0.7),
            count_val.animate(run_time=0.7).set_value(n_sim),
        )
        self.wait(0.4)

        all_dots = VGroup(*dots, *tail_dots)
        all_pts = pts + tail_pts

        # --- Fase 2: explosió de distàncies entre parells ---
        random.seed(3)
        n_show = 900  # subconjunt representatiu (27.261 parells reals no es poden dibuixar)
        pairs = set()
        while len(pairs) < n_show:
            i, j = random.randrange(len(all_pts)), random.randrange(len(all_pts))
            if i != j:
                pairs.add((min(i, j), max(i, j)))

        edges = VMobject(stroke_color=WHITE, stroke_width=0.6, stroke_opacity=0.25)
        edge_anchors = []
        for i, j in pairs:
            edge_anchors.append((all_pts[i], all_pts[j]))

        def build_edges(vm, anchors):
            vm.clear_points()
            for p, q in anchors:
                vm.start_new_path(p)
                vm.add_line_to(q)
            return vm

        build_edges(edges, edge_anchors)

        new_label = Text("distàncies", font_size=26, color=WHITE, weight=BOLD)
        new_label.move_to(counter_label)

        self.play(
            Create(edges, run_time=1.1, rate_func=linear),
            Transform(counter_label, new_label, run_time=0.4),
            count_val.animate(run_time=1.1).set_value(n_pairs),
        )
        self.wait(0.3)

        # --- Soroll: petit tremolor independent de cada àtom ---
        def jitter(mob, dt):
            for d in mob:
                d.shift(np.random.normal(scale=0.006, size=3))

        all_dots.add_updater(jitter)
        self.wait(2.2)
        all_dots.remove_updater(jitter)
        self.wait(0.3)
