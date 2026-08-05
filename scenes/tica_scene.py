import json
import random
from pathlib import Path

import numpy as np
from manim import *

# Format vertical per a xarxes (reels/stories): 9:16 en lloc del 16:9 per defecte.
config.frame_width = 9
config.frame_height = 16
config.pixel_width = 1080
config.pixel_height = 1920

DATA_DIR = Path(__file__).parent / "data"


class TicaScene(Scene):
    """Continuació directa d'AtomCounter: comença amb la imatge final
    d'aquella escena (el núvol de punts + distàncies, sense el comptador).

    Fase 1: els punts vibren (soroll independent + un mode ràpid col·lectiu
    de gran amplitud, com un domini que trontolla).
    Fase 2: la vibració s'apaga a poc a poc i emergeix un moviment lent,
    col·lectiu i petit: l'interruptor de dos estats.
    Fase 3: aquest moviment lent es tradueix en vectors reals de la
    component TICA 1 (calculats amb TICA de veritat a data/compute_tica.py
    sobre una trajectòria sintètica construïda a posta perquè el soroll
    domini la variança però NO l'autocorrelació -- exactament el que TICA
    ha de poder destriar).
    """

    def construct(self):
        random.seed(7)
        np.random.seed(7)

        with open(DATA_DIR / "lhcii_ca_backbone.json") as f:
            backbone = json.load(f)
        with open(DATA_DIR / "tica_result.json") as f:
            tica = json.load(f)

        raw_pts = [np.array([p[0], p[1], p[2] * 0.3]) for p in backbone["points"]]
        n_real = len(raw_pts)
        # Mateix desplaçament que a AtomCounter (nucli a la meitat superior, en
        # vertical no hi ha amplada per posar-lo al costat del text).
        shift = np.array([0.0, 3.2, 0.0])
        base_pts = [p + shift for p in raw_pts]

        rainbow = color_gradient([BLUE_D, TEAL, GREEN, YELLOW, ORANGE, RED], n_real)
        dots = VGroup(
            *[Dot(point=p, radius=0.045, color=rainbow[i], fill_opacity=1) for i, p in enumerate(base_pts)]
        )

        # cua discontinua (residus flexibles, identica a AtomCounter per continuitat)
        tail_dir = normalize(base_pts[0] - base_pts[3])
        tail_pts = [
            base_pts[0] + tail_dir * 0.22 * (i + 1) + np.random.normal(scale=0.05, size=3) for i in range(11)
        ]
        tail_dots = VGroup(
            *[Dot(point=p, radius=0.04, color=BLUE_D, fill_opacity=0.4, stroke_width=0) for p in tail_pts]
        )

        all_dots = VGroup(*dots, *tail_dots)
        all_base = base_pts + tail_pts
        n_all = len(all_base)

        # malla de distancies (identica a la de AtomCounter: mateixa llavor -> mateixos parells)
        random.seed(3)
        n_show = 900
        pairs = set()
        while len(pairs) < n_show:
            i, j = random.randrange(n_all), random.randrange(n_all)
            if i != j:
                pairs.add((min(i, j), max(i, j)))
        pairs = list(pairs)

        def edges_from(positions):
            vm = VMobject(stroke_color=WHITE, stroke_width=0.6, stroke_opacity=0.25)
            for i, j in pairs:
                vm.start_new_path(positions[i])
                vm.add_line_to(positions[j])
            return vm

        edges_dense = edges_from(all_base)

        # --- Imatge inicial: identica al final d'AtomCounter, sense el comptador ---
        self.add(edges_dense, all_dots)
        self.wait(0.3)

        # --- Preparem els patrons espacials reals (sortida de compute_tica.py) ---
        weight_slow = np.array(tica["weight"] + [tica["weight"][0]] * 11)  # extenem per la cua
        weight_fast = np.array(tica["weight_fast"] + [tica["weight_fast"][0]] * 11)
        dir_slow = np.array(tica["hinge_dir"])
        dir_fast = np.array(tica["hinge_dir_fast"])

        # petit "soroll" independent, determinista (suma de sinusoides amb fase/freq aleatoria per atom)
        rng = np.random.default_rng(11)
        n_terms = 3
        noise_freq = rng.uniform(4.0, 9.0, size=(n_all, n_terms))
        noise_phase = rng.uniform(0, 2 * np.pi, size=(n_all, n_terms))
        noise_dir = rng.normal(size=(n_all, n_terms, 3))
        noise_dir /= np.linalg.norm(noise_dir, axis=2, keepdims=True)

        clock = ValueTracker(0.0)
        fast_env = ValueTracker(1.0)      # amplitud del soroll + mode rapid col·lectiu
        switch_state = ValueTracker(1.0)  # -1..1, l'interruptor lent

        FAST_COLL_AMP_DISP = 0.5
        NOISE_AMP_DISP = 0.16
        SLOW_AMP_DISP = 0.55
        FAST_PERIOD = 0.35  # segons (rapid a la pantalla)

        def positions_at(t, env, switch):
            phase = 2 * np.pi * t / FAST_PERIOD
            fast_coll = FAST_COLL_AMP_DISP * np.sin(phase) * weight_fast[:, None] * dir_fast[None, :]
            noise = (
                NOISE_AMP_DISP
                * np.sum(np.sin(noise_freq * t + noise_phase), axis=1)[:, None]
                / n_terms
            )
            noise_vec = noise * np.mean(noise_dir, axis=1)
            slow = SLOW_AMP_DISP * switch * weight_slow[:, None] * dir_slow[None, :]
            return env * (fast_coll + noise_vec) + slow

        def update_dots(mob, dt):
            clock.increment_value(dt)
            t = clock.get_value()
            offsets = positions_at(t, fast_env.get_value(), switch_state.get_value())
            for dot, base, off in zip(mob, all_base, offsets):
                dot.move_to(base + off)

        # 150 d'aquestes distancies seguiran els punts en moviment (la resta s'esvaeix ara)
        random.seed(5)
        tracked_pairs = random.sample(pairs, 150)

        def edges_live_update(mob):
            positions = [d.get_center() for d in all_dots]
            mob.clear_points()
            for i, j in tracked_pairs:
                mob.start_new_path(positions[i])
                mob.add_line_to(positions[j])

        edges_live = VMobject(stroke_color=WHITE, stroke_width=0.7, stroke_opacity=0.3)
        edges_live_update(edges_live)

        # --- Fase 1: vibracio (soroll + mode rapid col·lectiu, gran amplitud) ---
        self.play(FadeOut(edges_dense), FadeIn(edges_live), run_time=0.5)
        all_dots.add_updater(update_dots)
        edges_live.add_updater(edges_live_update)

        # Zona de text: centrada, sota el núvol de punts, sense baixar de la
        # zona segura inferior (hi pot quedar tapada per la descripció del reel).
        label = Text("distàncies vibrant...", font_size=22, color=WHITE, weight=BOLD)
        label.set_opacity(0.85).move_to(DOWN * 1.0)
        self.play(FadeIn(label, run_time=0.4))
        self.wait(2.0)

        # --- Fase 2: la vibracio s'apaga a poc a poc; emergeix el moviment lent ---
        new_label = Text("...a poc a poc, només queda\nel moviment lent", font_size=22, color=WHITE, weight=BOLD)
        new_label.set_opacity(0.85).move_to(label)
        self.play(
            fast_env.animate.set_value(0.08),
            Transform(label, new_label),
            run_time=3.0,
            rate_func=smooth,
        )
        self.wait(0.3)
        self.play(switch_state.animate.set_value(-1.0), run_time=1.6, rate_func=smooth)
        self.wait(0.8)
        self.play(switch_state.animate.set_value(1.0), run_time=1.6, rate_func=smooth)
        self.wait(0.6)

        all_dots.remove_updater(update_dots)
        edges_live.remove_updater(edges_live_update)

        # --- Fase 3: vectors de la component TICA 1 (reals, calculats amb TICA) ---
        arrows = VGroup()
        vectors = np.array(tica["atom_ic1_vectors"])
        for i in range(n_real):
            start = dots[i].get_center()
            end = start + np.array([vectors[i, 0], vectors[i, 1], 0.0]) * 0.9  # nomes (x,y) per llegibilitat 2D
            if np.linalg.norm(end - start) < 0.03:
                continue
            arrows.add(
                Arrow(
                    start, end, buff=0, stroke_width=2.2, max_tip_length_to_length_ratio=0.35,
                    color=interpolate_color(WHITE, ManimColor("#FDBA74"), min(1.0, np.linalg.norm(vectors[i]) * 1.3)),
                )
            )

        ic_label = Text("Component TICA 1", font_size=26, color=WHITE, weight=BOLD)
        ic_sub = Text("(el mode més lent, extret del soroll)", font_size=17, color=WHITE)
        ic_sub.set_opacity(0.8)
        ic_group = VGroup(ic_label, ic_sub).arrange(DOWN, buff=0.1)
        ic_group.move_to(DOWN * 1.0)

        self.play(
            FadeOut(edges_live),
            FadeOut(tail_dots),
            Transform(label, ic_group),
            run_time=0.6,
        )
        self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.01, run_time=1.2))
        self.wait(0.4)

        # --- Petit grafic: senyal brut (soroll) vs senyal extret per TICA (lent, net) ---
        axes = Axes(
            x_range=[0, 1, 1], y_range=[-1.2, 1.2, 1],
            x_length=3.0, y_length=1.6,
            axis_config={"stroke_width": 1.2, "stroke_opacity": 0.5, "include_ticks": False},
        )
        # Sota el bloc de text, sense entrar a la franja inferior (buff de
        # seguretat pels subtítols/descripció del reel).
        axes.move_to(DOWN * 3.6)

        t_frac = np.array(tica["sample_t_frac"])
        raw = np.array(tica["raw_signal_sample"])
        y1 = np.array(tica["y1_smooth_sample"])
        raw_n = raw / np.max(np.abs(raw))
        y1_n = y1 / np.max(np.abs(y1))

        raw_graph = axes.plot_line_graph(
            t_frac, raw_n, line_color=GRAY, stroke_width=1.2, add_vertex_dots=False
        )
        y1_graph = axes.plot_line_graph(
            t_frac, y1_n, line_color="#FDBA74", stroke_width=3, add_vertex_dots=False
        )
        raw_caption = Text("dades brutes", font_size=14, color=GRAY).next_to(axes, UP, buff=0.1).align_to(axes, LEFT)
        y1_caption = Text("IC1 (TICA)", font_size=14, color="#FDBA74", weight=BOLD).next_to(raw_caption, RIGHT, buff=0.25)

        self.play(
            Create(axes, run_time=0.5),
            Create(raw_graph, run_time=1.0),
            FadeIn(raw_caption, run_time=0.5),
        )
        self.play(Create(y1_graph, run_time=1.2), FadeIn(y1_caption, run_time=0.5))
        self.wait(1.2)
