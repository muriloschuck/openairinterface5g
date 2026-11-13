#!/usr/bin/env python3
"""e2_tempo_grafico.py [<e2_tempo_estat.txt>]: gráfico do E2, tempo (seção 5.5), a partir da saída do
e2_tempo_estat.py. Tempo médio de decodificação por trial em função de workers, uma linha por batch, com o IC95
de cada configuração e a referência seq. Gera e2_tempo.png ao lado do texto lido. Só lê o texto.
Versão de 13/11/2026: o número de rodadas vem da coluna n do texto (antes, "5 rodadas" fixo na nota)."""
import csv, io, os, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
AQUI = os.path.dirname(os.path.abspath(__file__))
TXT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "e2_tempo_estat.txt")
linhas = open(TXT).read().split("\n")
fim = next(i for i, l in enumerate(linhas) if l.startswith("execucoes_com_problema"))
est = {r["config"]: r for r in csv.DictReader(io.StringIO("\n".join(linhas[:fim])))}
W, B = [1, 2, 3, 4, 6, 16], [1, 2, 6, 64]
cores = {1: "#2b6cc4", 2: "#f0683a", 6: "#2e9e6a", 64: "#8a8f98"}
mk = {1: "o", 2: "s", 6: "^", 64: "D"}
fig, ax = plt.subplots(figsize=(6.4, 3.9), dpi=200)
ns = {r["n"] for r in est.values()}
if len(ns) != 1: sys.exit(f"configurações com n diferentes: {ns}")
NROD = ns.pop()
seq = est["seq"]; ms = float(seq["media_us"]); es = ms * float(seq["ic95_pct"]) / 100
ax.axhspan(ms - es, ms + es, color="#000", alpha=0.06, lw=0)
ax.axhline(ms, color="#333", ls="--", lw=1.2, label=f"seq ({ms:.0f} µs)".replace(".", ","))
x = range(len(W))
for b in B:
    m = [float(est[f"w{w}b{b}"]["media_us"]) for w in W]
    e = [mm * float(est[f"w{w}b{b}"]["ic95_pct"]) / 100 for mm, w in zip(m, W)]
    ax.errorbar(x, m, yerr=e, color=cores[b], marker=mk[b], ms=5, lw=1.8, capsize=3, label=f"batch {b}")
ax.set_xticks(list(x), [str(w) for w in W]); ax.set_xlabel("workers")
ax.set_ylabel("tempo de decodificação por trial (µs)"); ax.set_ylim(500, 1600)
ax.set_title("E2 em W3: tempo de decodificação por configuração", loc="left", fontsize=11)
ax.grid(axis="y", color="#ddd")
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.legend(frameon=False, fontsize=7.5, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.17))
fig.text(0.02, 0.01, f"W3 a 30 dB, 500 trials, semente 1; média de {NROD} rodadas por configuração, com o IC95 (barras; faixa cinza para seq).\n"
         "Batch 64 forma um único lote, e workers 1, uma única tarefa: nos dois casos o tempo não depende do outro parâmetro.",
         fontsize=6.3, color="#555", va="bottom")
fig.subplots_adjust(bottom=0.3, left=0.13, right=0.97, top=0.91)
fig.savefig(os.path.join(os.path.dirname(os.path.abspath(TXT)), "e2_tempo.png"))
