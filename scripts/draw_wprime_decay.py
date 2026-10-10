"""Draw the Wprime WZ leptonic benchmark decay without assuming production."""
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
    fig, ax = plt.subplots(figsize=(9, 5))
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
    v, w, z = (1.5, 0), (3.2, 0.9), (3.2, -0.9)
    wave((0.1,0),v); wave(v,w); wave(v,z)
    fermion(w,(4.8,1.65),inward=True); fermion(w,(4.8,0.35))
    fermion(z,(4.8,-0.35)); fermion(z,(4.8,-1.65),inward=True)
    for point in (v,w,z): ax.plot(*point,'ko',ms=4)
    for x,y,label in [(0.6,0.25,r"$W^{\prime +}$"),(2.25,0.8,r"$W^+$"),(2.25,-0.8,r"$Z$"),
        (4.9,1.65,r"$\ell^+$"),(4.9,0.35,r"$\nu_{\ell}$"),(4.9,-0.35,r"$\ell^- $"),(4.9,-1.65,r"$\ell^+$")]:
        ax.text(x,y,label,fontsize=23,ha='left',va='center')
    ax.text(2.7,2.15,r"$W^{\prime +}\to W^+Z\to\ell^+\nu\,\ell^-\ell^+$",ha='center',fontsize=20)
    ax.text(2.7,-2.2,"Referencia: masa 1 TeV, anchura estrecha\nSe muestra Wprime positivo; el canal conjugado también es posible.",ha='center',fontsize=11)
    ax.set(xlim=(-0.1,5.7),ylim=(-2.5,2.55)); ax.axis('off')
    for ext in ('pdf','png'):
        fig.savefig(output / f'wprime_decay.{ext}',bbox_inches='tight',dpi=300)
    plt.close(fig)
    print(output / 'wprime_decay.pdf')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=Path.home()/'Open-Data/Processed/results_autoencoder_dyjets_ht_10features/poster_figures_10variables')
    draw(parser.parse_args().output_dir)
