"""graf_comum.py: leitura da linha n_errors do nr_ulsim e estilo comum dos gráficos de BLER (V1 e V2)."""
import re

NE = re.compile(r"n_errors \(([^)]*)\)")
LINHA = re.compile(r"n_errors \([^)]*\).*errors_scrambling \([^)]*\)")
AZUL, LARANJA = "#2b7bd8", "#f0683a"


def le_log(caminho):
    """Devolve (linha n_errors … errors_scrambling, erros na 1ª tx, trials) ou None se o log não tem a linha."""
    txt = open(caminho, errors="replace").read()
    m, l = NE.search(txt), LINHA.search(txt)
    if not m or not l:
        return None
    a, b = m.group(1).split(",")[0].split("/")
    return l.group(0), int(a), int(b)



def grafico(png, titulo, xs, ys_ref, ys_cmp, rot_ref, rot_cmp, nota, rotulos=None, categorico=False, xlim=None,
            xlabel="SNR (dB)"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.4, 3.6), dpi=200)
    pos = list(range(len(xs))) if categorico else xs
    ax.plot(pos, ys_ref, "-o", color=AZUL, lw=2, ms=5, label=rot_ref, zorder=3)
    ax.plot(pos, ys_cmp, "o", mfc="none", mec=LARANJA, mew=2, ms=12, label=rot_cmp, zorder=2)
    if rotulos:
        for p, y, t in zip(pos, ys_ref, rotulos):
            ax.annotate(t, (p, y), textcoords="offset points", xytext=(0, -18 if y > 0.5 else 12), ha="center",
                        fontsize=7, color="#555")
    if categorico:
        ax.set_xticks(pos, [f"{x:g}".replace(".", ",") for x in xs])
        ax.set_xlim(-0.4, len(xs) - 0.6)
    elif xlim:
        ax.set_xlim(*xlim)
        ax.set_xticks([x for x in xs if xlim[0] <= x <= xlim[1]])
    ax.set_ylim(-0.03, 1.08)
    ax.set_ylabel("BLER da 1ª transmissão")
    ax.set_xlabel(xlabel)
    ax.set_title(titulo, loc="left", fontsize=11)
    ax.grid(axis="y", color="#ddd")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
    fig.text(0.1, 0.01, nota, fontsize=6.5, color="#555", va="bottom")
    fig.subplots_adjust(bottom=0.27, left=0.12, right=0.97, top=0.9)
    fig.savefig(png)
    plt.close(fig)
