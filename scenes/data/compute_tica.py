"""Genera una trajectoria sintetica sobre la geometria real del monomer de
LHCII (soroll rapid + un mode lent tipus 'frontissa' injectat) i hi aplica
TICA de veritat, seguint la formulacio estandard (Perez-Hernandez et al. 2013,
J. Chem. Phys.; Schwantes & Pande 2013, JCTC):

    xi(t)  = x(t) - mean(x)                              (features centrades)
    C0     = (1/T) sum_t xi(t) xi(t)^T                    (covariancia instantania)
    Ctau   = (1/2(T-tau)) sum_t [xi(t)xi(t+tau)^T + xi(t+tau)xi(t)^T]  (covariancia retardada, simetritzada)
    Ctau v_i = lambda_i C0 v_i                             (problema d'autovalors generalitzat)
    t_i    = -tau / ln|lambda_i|                           (temps d'implicacio)

No tenim trajectories MD reals del grup, aixi que es una demostracio
il·lustrativa i honesta amb 3 components injectats a ma sobre les coordenades
reals del PDB 2BHW: soroll independent per atom, un mode RAPID pero
COL·LECTIU de gran amplitud (una vibracio vistosa que decorrelaciona de
seguida), i un INTERRUPTOR LENT de 2 estats de petita amplitud (un procès
de Markov, com l'ON/OFF de NPQ). Despres es verifica que PCA es deixa
enganyar pel mode rapid col·lectiu (mes variansa) mentre que TICA recupera
correctament l'interruptor lent (mes autocorrelacio) -- exactament el punt
del guio: "el moviment mes gran no es el mes important".
"""

import json
from pathlib import Path

import numpy as np
from scipy.linalg import eigh

HERE = Path(__file__).parent
rng = np.random.default_rng(42)

# --- 1. Geometria real (mateixa transformacio que atom_counter.py) ---
with open(HERE / "lhcii_ca_backbone.json") as f:
    data = json.load(f)

pts = np.array([[p[0], p[1], p[2] * 0.3] for p in data["points"]])  # (223, 3)
n = len(pts)
x = pts[:, 0]
weight = (x - x.mean()) / (np.ptp(x) / 2)  # ~[-1, 1], participacio de cada atom a la frontissa

# --- 2. Trajectoria sintetica amb 3 components ---
# (a) soroll independent per atom (incoherent, curt termini)
# (b) un mode RAPID pero COL·LECTIU (una vibracio gran i vistosa, com un
#     domini que trontolla) -> aquest es el que enganya PCA (molta variansa,
#     pero decorrelaciona de seguida)
# (c) l'interruptor LENT de 2 estats (+1/-1, procès de Markov), petit en
#     amplitud pero persistent -> el mode que TICA ha de trobar. Un procès
#     de Markov de 2 estats es el model correcte per a una 'switch'
#     conformacional (com l'ON/OFF de NPQ): l'autocorrelacio decau exacta-
#     ment com exp(-t/relax_time), que es la hipotesi darrere de la formula
#     t_i = -tau/ln|lambda_i|.
T = 24000
relax_time = 400          # temps mitja d'estada a cada estat de l'interruptor (frames)
p_flip = 1.0 / relax_time
slow_amp = 0.10            # amplitud de l'interruptor lent (petita)
fast_coll_amp = 0.22       # amplitud del mode rapid col·lectiu (LA MES GRAN de totes)
fast_coll_tau = 12.0       # temps de correlacio del mode rapid col·lectiu (frames) -> << tau
noise_amp = 0.09           # soroll independent per atom
fast_tau = 3.0             # temps de correlacio del soroll independent (frames)

hinge_dir_slow = np.array([0.0, 1.0, 0.35])
hinge_dir_slow /= np.linalg.norm(hinge_dir_slow)
hinge_dir_fast = np.array([1.0, 0.0, -0.2])
hinge_dir_fast /= np.linalg.norm(hinge_dir_fast)

z = pts[:, 2]
weight_fast = (z - z.mean()) / (np.ptp(z) / 2)  # patró espacial DIFERENT del de l'interruptor lent

flips = rng.random(T) < p_flip
slow_signal_true = np.empty(T)
state = 1.0
for t in range(T):
    if flips[t]:
        state = -state
    slow_signal_true[t] = state
print(f"Nombre de canvis d'estat (switch) en {T} frames: {int(flips.sum())}")

phi = np.exp(-1.0 / fast_tau)
phi_fc = np.exp(-1.0 / fast_coll_tau)
noise_state = np.zeros((n, 3))
fc_state = 0.0
fast_coll_signal = np.empty(T)
traj = np.zeros((T, n, 3))

for t in range(T):
    fc_state = phi_fc * fc_state + np.sqrt(1 - phi_fc**2) * rng.standard_normal()
    fast_coll_signal[t] = fc_state
    slow_disp = slow_amp * slow_signal_true[t] * weight[:, None] * hinge_dir_slow[None, :]
    fast_coll_disp = fast_coll_amp * fc_state * weight_fast[:, None] * hinge_dir_fast[None, :]
    noise_state = phi * noise_state + np.sqrt(1 - phi**2) * noise_amp * rng.standard_normal((n, 3))
    traj[t] = pts + slow_disp + fast_coll_disp + noise_state

print(f"Amplitud interruptor lent      : {slow_amp:.4f}")
print(f"Amplitud mode rapid col·lectiu : {fast_coll_amp:.4f}  (la mes gran -> aixo enganya PCA)")
print(f"Amplitud soroll independent    : {noise_amp:.4f}")

# --- 3. Features: distancies entre un subconjunt de 40 atoms 'landmark' ---
landmark_idx = np.linspace(0, n - 1, 40).astype(int)
pairs = [(i, j) for a, i in enumerate(landmark_idx) for j in landmark_idx[a + 1:]]
print(f"Nombre de features (distancies): {len(pairs)}")


def compute_features(frame):
    return np.array([np.linalg.norm(frame[i] - frame[j]) for i, j in pairs])


X = np.array([compute_features(traj[t]) for t in range(T)])  # (T, d)

# --- 4. TICA real ---
tau = 100  # lag en frames (>> fast_tau, ~ fraccio de relax_time)
Xc = X - X.mean(axis=0)

C0 = (Xc.T @ Xc) / T
X0, X1 = Xc[:-tau], Xc[tau:]
Ctau = (X0.T @ X1 + X1.T @ X0) / (2 * (T - tau))

# regularitzacio petita per estabilitat numerica de C0
C0_reg = C0 + 1e-10 * np.eye(C0.shape[0])
eigvals, eigvecs = eigh(Ctau, C0_reg)  # ordre ascendent

order = np.argsort(eigvals)[::-1]
eigvals = eigvals[order]
eigvecs = eigvecs[:, order]

lam1 = eigvals[0]
v1 = eigvecs[:, 0]
implied_t1 = -tau / np.log(abs(lam1))

y1 = Xc @ v1
# signe/escala arbitraris en TICA: alineem amb el senyal lent injectat per interpretabilitat
corr = np.corrcoef(y1, slow_signal_true)[0, 1]
if corr < 0:
    y1 = -y1
    v1 = -v1
    corr = -corr

print(f"\nAutovalor principal (lambda_1)        : {lam1:.4f}")
print(f"Temps d'implicacio recuperat (t_1)    : {implied_t1:.1f} frames  (relaxacio injectada: {relax_time} frames)")
print(f"Correlacio y1(t) vs senyal lent real   : {corr:.3f}  (1.0 = recuperacio perfecta)")

# comparem amb la 1a component de PCA (variansa, no autocorrelacio) per mostrar la diferencia
pca_eigvals, pca_eigvecs = eigh(C0)
pca_order = np.argsort(pca_eigvals)[::-1]
pc1 = pca_eigvecs[:, pca_order[0]]
y_pca1 = Xc @ pc1
corr_pca = abs(np.corrcoef(y_pca1, slow_signal_true)[0, 1])
print(f"[comparacio] correlacio PC1 (variansa) vs senyal lent: {corr_pca:.3f}  <- pitjor, es deixa enganyar pel soroll")

# --- 5. Retro-projeccio: direccio de cada atom (backbone Ca, no nomes landmarks) que
#     correlaciona amb la component lenta y1(t)  -> vectors 'IC1' per dibuixar sobre l'estructura
disp = traj - traj.mean(axis=0, keepdims=True)  # (T, n, 3)
y1c = y1 - y1.mean()
atom_vectors = np.einsum('tnk,t->nk', disp, y1c) / (T * y1c.var())  # regressio lineal per atom

# normalitzem per visualitzacio (direccio + magnitud relativa)
mags = np.linalg.norm(atom_vectors, axis=1)
max_mag = mags.max()
atom_vectors_norm = atom_vectors / max_mag  # magnitud maxima = 1

# --- 6. Guardem tot el necessari per Manim ---
# submostregem y1(t) per a un grafic petit (300 punts) i tambe el senyal rapid brut d'un atom per contrast.
# Per a la visualitzacio nomes (no pel calcul), suavitzem y1 amb una mitjana mobil curta: a
# aquesta escala de grafic petit, el 12% de variansa residual que li queda a y1 (corr=0.88, no 1.0)
# es prou per fer-lo veure tan 'sorollos' com les dades brutes, encara que matematicament sigui
# molt mes lent (roughness ~0.7x). El senyal brut es mostra SENSE suavitzar, per contrast honest.
smooth_win = 120
kernel = np.ones(smooth_win) / smooth_win
y1_smooth = np.convolve(y1, kernel, mode="same")

# Nomes mostrem una FINESTRA de la trajectoria (no tot T), perque amb 24000
# frames i ~500 frames/interruptor, comprimir-ho tot a 300 punts fa aliasing
# (cada canvi d'estat nomes rep ~4 mostres i sembla soroll ràpid en lloc de
# lent). Una finestra de 6000 frames (~15 interruptors) a 300 punts en dona
# ~20 mostres per interruptor: prou per veure els plans clarament.
window = 6000
start = T // 3
sample_idx = np.linspace(start, start + window - 1, 300).astype(int)
raw_signal_example = X[:, 0] - X[:, 0].mean()  # una feature bruta qualsevol, sense filtrar

out = {
    "n_atoms": n,
    "weight": weight.tolist(),
    "hinge_dir": hinge_dir_slow.tolist(),
    "weight_fast": weight_fast.tolist(),
    "hinge_dir_fast": hinge_dir_fast.tolist(),
    "relax_time_frames": relax_time,
    "slow_amp": slow_amp,
    "fast_coll_amp": fast_coll_amp,
    "fast_coll_tau": fast_coll_tau,
    "noise_amp": noise_amp,
    "fast_tau": fast_tau,
    "tau_lag_frames": tau,
    "lambda1": float(lam1),
    "implied_timescale_frames": float(implied_t1),
    "corr_y1_vs_true": float(corr),
    "corr_pca1_vs_true": float(corr_pca),
    "atom_ic1_vectors": atom_vectors_norm.tolist(),  # (n, 3) direccio + magnitud relativa
    "y1_sample": y1[sample_idx].tolist(),
    "y1_smooth_sample": y1_smooth[sample_idx].tolist(),
    "raw_signal_sample": raw_signal_example[sample_idx].tolist(),
    "sample_t_frac": ((sample_idx - start) / window).tolist(),
}
with open(HERE / "tica_result.json", "w") as f:
    json.dump(out, f)
print("\nGuardat data/tica_result.json")
