"""Draw schematic quark annihilation and the leptonic Wprime WZ decay."""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def draw(output):
    output = Path(output).expanduser()
    output.mkdir(parents=True, exist_ok=True)
    if any((output / f"wprime_decay.{ext}").exists() for ext in ("pdf", "png")):
        raise FileExistsError("Decay figures already exist")
    fig, ax = plt.subplots(figsize=(6, 7))
    def wave(start, end, cycles=7):
        start, end = np.array(start, dtype=float), np.array(end, dtype=float)
        delta = end - start
        normal = np.array([-delta[1], delta[0]]) / np.linalg.norm(delta)
        t = np.linspace(0, 1, 400)
        points = start[:, None] + delta[:, None] * t + normal[:, None] * 0.055 * np.sin(2 * np.pi * cycles * t)
        ax.plot(*points, color="black", lw=1.8)
    def fermion(start, end, inward=False):
        ax.plot([start[0], end[0]], [start[1], end[1]], color="black", lw=1.8)
        a, b = np.array(start), np.array(end)
        p, q = a + (b-a)*0.4, a + (b-a)*0.6
        if inward:
            p, q = q, p
        ax.annotate("", xy=q, xytext=p, arrowprops={"arrowstyle": "-|>", "color": "black", "lw": 1.5})
    initial, v, z, w = (0.9,0), (2.4,0), (3.5,1.2), (3.5,-1.2)
    fermion((0.15,-2.25),initial)
    fermion((0.15,2.25),initial,inward=True)
    wave(initial,v); wave(v,z); wave(v,w)
    fermion(z,(5,2.3),inward=True); fermion(z,(5,0.8))
    fermion(w,(5,-0.8)); fermion(w,(5,-2.3),inward=True)
    for x,y,label in [(0.0,2.35,r"$\bar q^{\prime}$"),(0.0,-2.4,r"$q$"),
        (1.4,-0.3,r"$W^{\prime +}$"),(2.6,0.85,r"$Z$"),(3.25,-0.55,r"$W^+$"),
        (5.05,2.3,r"$\ell^+$"),(5.05,0.8,r"$\ell^-$"),
        (5.05,-0.8,r"$\nu_{\ell}$"),(5.05,-2.3,r"$\ell^+$")]:
        ax.text(x,y,label,fontsize=22,ha='left',va='center')
    ax.text(2.8,-2.9,"Esquema de producción y decaimiento\nReferencia Wprime: 1 TeV, anchura estrecha",ha='center',fontsize=10)
    ax.set(xlim=(-0.3,5.9),ylim=(-3.25,2.75)); ax.axis('off')
    for ext in ('pdf','png'):
        fig.savefig(output / f'wprime_decay.{ext}',bbox_inches='tight',dpi=300)
    plt.close(fig)
    print(output / 'wprime_decay.pdf')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=Path.home()/'Open-Data/Processed/results_autoencoder_dyjets_ht_10features/poster_figures_10variables')
    draw(parser.parse_args().output_dir)
