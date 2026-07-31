# Estat del projecte

Aquest document és perquè qualsevol persona (o agent) que continuï aquest
treball tingui el mateix context que hi havia en acabar la sessió que va
crear les tres primeres escenes. El README.md explica *com* renderitzar;
aquest fitxer explica *per què* les coses són com són.

## Mapa guió → escenes (numeració de [`script_extracted.txt`](script_extracted.txt))

| Línies guió | Contingut | Estat |
|---|---|---|
| 3–4 | Plantes = central elèctrica, núvol passa, mesurador de llum | ✅ [`light_meter.py`](scenes/light_meter.py) |
| 5–6 | Interruptor molecular ON/OFF, blanc encegador | ⚠️ **Ja fet per l'Inés, fora d'aquest repo** — no el recreïs, pregunta si cal integrar-lo aquí |
| 7–8 | Persona sortint a la llum, aclucant els ulls | 🎥 metratge real (no Manim) |
| 9–10 | "Non-photochemical Quenching (NPQ)", presentació del grup | 🎥 metratge real |
| 11–12 | Grup Photon Harvesting, lab → ordinadors/MD | 🎥 metratge real |
| 13–15 | Simulacions MD, àtom a àtom, fotograma a fotograma | 🎥 clips de simulació real (no Manim) |
| 16–17 | "El moviment més gran no és el més important"; comptador Manim | ✅ [`atom_counter.py`](scenes/atom_counter.py) |
| 18–19 | TICA: filtra soroll, es queda amb els patrons lents | ✅ [`tica_scene.py`](scenes/tica_scene.py) |
| 20–21 | Tornada a la planta/fulla sana; rètol final + logo ICFO | ❌ pendent (metratge real + gràfic senzill) |

## Decisions preses i per què (no òbvies llegint només el codi)

- **PDB 2BHW, no un altre**: és Standfuss et al. 2005 *EMBO J*, el paper
  que descriu exactament el mecanisme de fotoprotecció/NPQ del guió. Coincidència
  perfecta amb el tema, no arbitrària.
- **Monòmer, no trímer**: primera versió feta amb el trímer sencer (3 cadenes,
  8373 àtoms); l'Inés va corregir que el grup treballa amb monòmers. Totes
  les escenes fan servir només la cadena A.
- **234 àtoms Cα, no 223**: la cristal·lografia (2BHW cadena A) només té
  resolts els residus 10–232 (223 àtoms; el terminal N és flexible i no es
  veu als raigs X). El model de simulació del grup té 234 residus. La
  diferència (11) es dibuixa com una cua discontínua a `atom_counter.py` i
  `tica_scene.py` — són punts *il·lustratius*, no coordenades reals.
- **27.261 distàncies, no "milers d'àtoms × milions de fotogrames" literal**:
  el guió original demanava aquest producte, però l'Inés va explicar que el
  pipeline real del grup és: seleccionar àtoms Cα (234) → distàncies entre
  parells (`C(234,2) = 27.261`) com a *features* per TICA. Es va redissenyar
  l'escena del comptador per reflectir això en lloc del càlcul literal del
  guió. El nombre de "fotogrames" es va deixar estilitzat/sense xifra
  concreta perquè no tenim el nombre real de la vostra trajectòria MD —
  **si el teniu, doneu-lo i es pot posar un valor real**.
- **`tica_scene.py` comença exactament on acaba `atom_counter.py`**: mateixa
  llavor aleatòria (`random.seed(7)`, `np.random.seed(7)` per la cua;
  `random.seed(3)` per les 900 aresta-distàncies), mateixes posicions i
  colors, perquè els dos clips es puguin enganxar sense salt visual.
- **TICA amb dades sintètiques, no MD real**: no teníem trajectòries del
  grup, així que `scenes/data/compute_tica.py` genera una trajectòria
  sintètica sobre la geometria real (2BHW) amb 3 components: soroll
  independent per àtom, un mode **ràpid però col·lectiu** de gran amplitud
  (perquè PCA s'hi confongui), i un **interruptor lent de 2 estats** (procés
  de Markov, petita amplitud). Es demostra numèricament que PCA falla
  (correlació 0.02 amb l'interruptor real) i TICA l'encerta (correlació
  0.88), seguint la formulació estàndard (Pérez-Hernández et al. 2013;
  Schwantes & Pande 2013): `Cτ v = λ C0 v`. Detalls i paràmetres exactes
  (`relax_time=400`, `tau=100`, `T=24000`, etc.) als comentaris del mateix
  script. **Si el grup aporta trajectòries MD reals, aquest script s'hauria
  de substituir per una anàlisi TICA sobre dades reals** (la lògica de
  visualització a `tica_scene.py` no hauria de canviar gaire, només la font
  de `tica_result.json`).
- **Estil del mesurador de llum**: es van oferir 3 opcions (gauge analògic,
  barra vertical VU-meter, glow radial); l'Inés va triar la barra vertical.
  No re-proposis les altres opcions llevat que es demani explícitament un
  canvi d'estil.
- **Render sempre amb `-t` (fons transparent)** per als lliurables finals:
  totes les escenes estan pensades com a *overlays* sobre metratge real, no
  com a vídeos autònoms. `-ql` (baixa qualitat, sense `-t`) només per iterar
  ràpid durant el desenvolupament.
- **Vídeos 1080p NO es pugen al repo** (superen el límit de 100MB de GitHub
  en el cas de TICA — 331MB). Al `.gitignore`. Es regeneren en local amb
  `manim -qh -t`. Només els previews 480p (uns pocs centenars de KB) estan
  versionats.

## Com continuar

1. Si es reben trajectòries MD reals del grup: substituir la generació
   sintètica de `compute_tica.py` per una lectura de la trajectòria real
   (mateix format de sortida a `tica_result.json` perquè `tica_scene.py` no
   s'hagi de tocar).
2. Properes escenes pendents: transició "blanc encegador" (si cal integrar-la
   aquí en lloc de com a fitxer separat de l'Inés) i el rètol final amb
   nom del grup + logo ICFO (escena Manim senzilla, text + logo, sense
   requerir dades científiques).
3. Un cop hi hagi metratge real gravat, comprovar que els overlays
   transparents encaixen bé de mida/posició amb el vídeo real (cap escena
   s'ha provat encara compositada sobre metratge de veritat, només sobre
   fons negre/transparent aïllat).
