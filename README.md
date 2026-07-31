# ICFO Summer Fellowship — Divulgació científica

Clips i animacions per al vídeo de divulgació sobre fotoprotecció en plantes
(Non-photochemical Quenching, NPQ) i com s'estudia amb dinàmica molecular al
grup Photon Harvesting de l'ICFO. Guió complet a
[`Inés Alonso Divulgació Summer Fellowship.docx`](Inés%20Alonso%20Divulgació%20Summer%20Fellowship.docx)
([text pla](script_extracted.txt)).

Les animacions es fan amb [Manim Community](https://docs.manim.community/),
renderitzades amb fons transparent perquè es puguin superposar sobre
metratge real.

## Instal·lació

Cal Python 3.10+ i [FFmpeg](https://ffmpeg.org/) al PATH.

```bash
python -m venv manim_env
source manim_env/Scripts/activate   # Windows: manim_env\Scripts\activate
pip install -r requirements.txt
```

## Escenes

Totes viuen a [`scenes/`](scenes/). Per renderitzar:

```bash
cd scenes
manim -qh -t <fitxer>.py <NomEscena>   # -qh alta qualitat, -t fons transparent
manim -ql <fitxer>.py <NomEscena>      # -ql baixa qualitat, per iterar rapid
```

| Fitxer | Escena | Descripció |
|---|---|---|
| [`light_meter.py`](scenes/light_meter.py) | `LightMeter` | Mesurador d'intensitat de llum (VU meter) que es dispara quan un núvol deixa de tapar el sol. |
| [`atom_counter.py`](scenes/atom_counter.py) | `AtomCounter` | Comptador d'àtoms basat en l'estructura real del monòmer de LHCII (backbone Cα + explosió de distàncies interatòmiques). |
| [`tica_scene.py`](scenes/tica_scene.py) | `TicaScene` | Continuació directa d'`AtomCounter`: la vibració ràpida es filtra amb TICA real fins a un únic mode lent, visualitzat com a vectors. |
| [`test_installation.py`](scenes/test_installation.py) | `TestInstallation` | Escena mínima per comprovar que Manim + FFmpeg funcionen. |

Previsualitzacions en baixa qualitat (480p) de cada clip estan incloses a
`scenes/media/videos/*/480p15/`. Els renders finals en 1080p no es pugen al
repositori (pesen massa); es regeneren amb la comanda `-qh -t` de dalt.

## Base científica

Les animacions `AtomCounter` i `TicaScene` es basen en l'estructura real del
monòmer de LHCII: **PDB [2BHW](https://www.rcsb.org/structure/2BHW)**
(Standfuss, J., Terwisscha van Scheltinga, A.C., Lamborghini, M. & Kühlbrandt,
W. *Mechanisms of photoprotection and nonphotochemical quenching in pea
light-harvesting complex at 2.5 Å resolution.* EMBO J 24, 919–928, 2005).

- **234 àtoms Cα** al monòmer (223 resolts a la cristal·lografia + 11 residus
  flexibles del terminal N no resolts) i **27.261 distàncies** interatòmiques
  possibles (`C(234,2)`) — dades a
  [`scenes/data/lhcii_ca_backbone.json`](scenes/data/lhcii_ca_backbone.json).
- **TICA** (Time-lagged Independent Component Analysis) calculada de veritat
  a [`scenes/data/compute_tica.py`](scenes/data/compute_tica.py) seguint la
  formulació estàndard (Pérez-Hernández et al. 2013, *J. Chem. Phys.*;
  Schwantes & Pande 2013, *JCTC*): problema d'autovalors generalitzat
  `Cτ v = λ C0 v` sobre una trajectòria sintètica construïda a posta perquè
  el soroll domini la variança però NO l'autocorrelació. Resultats numèrics
  (autovalors, vectors, correlacions) a
  [`scenes/data/tica_result.json`](scenes/data/tica_result.json).

No disposem encara de trajectòries MD reals del grup — la trajectòria de
`compute_tica.py` és sintètica i il·lustrativa, però la geometria de partida
(coordenades atòmiques) i el mètode d'anàlisi (TICA) són reals.
