#!/usr/bin/env python3
"""v1_bler.py [<pasta dados>]: contagens e BLER da V1 (E1, contagens; seção 5.2 do relatório).

Lê os logs crus de dados/v1_w1_*/, dados/v1_w3_2*/ e dados/v1_w3r_*/ (nomes b1_s<semente>_snr<SNR>.log e
b2_s<semente>_snr<SNR>.log, gerados por v1_b1b2.sh e v1_w3_reforco.sh). Para cada par (semente, SNR), confere que a
linha n_errors … errors_scrambling do B1 é igual à do B2. Soma, por SNR, os erros da 1ª transmissão das sementes.
Em W3, nos SNRs medidos também no reforço (v1_w3r, sementes 1 a 5), vale o reforço; nos demais, a v1_w3 (sementes 1
e 2). Escreve, na pasta deste script: v1_w1_por_semente.csv, v1_w3_por_semente.csv, v1_w1_bler.csv, v1_w3_bler.csv,
v1_w1_bler.png e v1_w3_bler.png. Só lê os logs; não precisa de sudo."""
import csv, glob, os, re, sys
from collections import defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "comum"))
from graf_comum import le_log, grafico  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "..", "dados")
NOME = re.compile(r"b1_s(\d+)_snr([0-9.]+)\.log$")
falhas = []


def pares(pasta):
    """[(snr, semente, linha, erros, trials)] para cada b1 com b2 correspondente; diferenças vão para falhas."""
    out = []
    for f1 in sorted(glob.glob(os.path.join(pasta, "b1_s*_snr*.log"))):
        m = NOME.search(f1)
        seed, snr_txt = int(m.group(1)), m.group(2)
        f2 = f1.replace("/b1_s", "/b2_s")
        r1, r2 = le_log(f1), (le_log(f2) if os.path.exists(f2) else None)
        if not r1 or not r2 or r1[0] != r2[0]:
            falhas.append((os.path.basename(pasta), os.path.basename(f1), r1 and r1[0], r2 and r2[0]))
            continue
        out.append((float(snr_txt), snr_txt, seed, r1[0], r1[1], r1[2], os.path.basename(pasta)))
    return out


def uma(pat):
    ds = sorted(glob.glob(os.path.join(DADOS, pat)))
    if len(ds) != 1:
        sys.exit(f"esperava 1 pasta {pat} em {DADOS}, achei {len(ds)}")
    return ds[0]


def soma(lst):
    agg = defaultdict(lambda: [0, 0, set(), ""])
    for snr, txt, seed, _, e, t, ex in lst:
        a = agg[snr]; a[0] += e; a[1] += t; a[2].add(seed); a[3] = txt
    return agg


def ne(linha):
    return re.search(r"n_errors \(([^)]*)\)", linha).group(1)


# W1
w1 = pares(uma("v1_w1_2*"))
with open(os.path.join(AQUI, "v1_w1_por_semente.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["snr_db", "semente", "erros_1a_tx", "trials", "n_errors_todas_rodadas (B1 = B2)"])
    for snr, txt, seed, l, e, t, _ in sorted(w1):
        w.writerow([txt, seed, e, t, ne(l)])
a1 = soma(w1)
with open(os.path.join(AQUI, "v1_w1_bler.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["snr_db", "erros_1a_tx", "trials", "bler_1a_tx_B1", "bler_1a_tx_B2"])
    for snr in sorted(a1):
        e, t, _, txt = a1[snr]; w.writerow([txt, e, t, f"{e/t:.4f}", f"{e/t:.4f}"])

# W3: base (sementes 1-2) + reforço (sementes 1-5); no SNR do reforço, vale o reforço
w3b, w3r = pares(uma("v1_w3_2*")), pares(uma("v1_w3r_2*"))
snr_r = {p[0] for p in w3r}
w3 = [p for p in w3b if p[0] not in snr_r] + w3r
with open(os.path.join(AQUI, "v1_w3_por_semente.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["execucao", "snr_db", "semente", "erros_1a_tx", "trials", "n_errors (B1 = B2)"])
    for snr, txt, seed, l, e, t, ex in sorted(w3b + w3r, key=lambda p: (p[6], p[0], p[2])):
        w.writerow([ex, txt, seed, e, t, ne(l)])
a3 = soma(w3)
with open(os.path.join(AQUI, "v1_w3_bler.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["snr_db", "erros_1a_tx", "trials", "bler_1a_tx_B1", "bler_1a_tx_B2", "origem"])
    for snr in sorted(a3):
        e, t, seeds, txt = a3[snr]
        w.writerow([txt, e, t, f"{e/t:.4f}", f"{e/t:.4f}", f"sementes {min(seeds)}-{max(seeds)}"])

print(f"W1: {len(w1)} pares iguais; W3: {len(w3b)} (v1_w3) + {len(w3r)} (v1_w3r) pares iguais; "
      f"total {len(w1) + len(w3b) + len(w3r)}; diferentes ou ausentes: {len(falhas)}")
for f in falhas:
    print("  DIF", f)

def g(png, titulo, agg, xlim, nota):
    xs = sorted(agg); ys = [agg[s][0] / agg[s][1] for s in xs]
    grafico(os.path.join(AQUI, png), titulo, xs, ys, ys, "B1 (AAL padrão)", "B2 (extensão, valores padrão)", nota,
            xlim=xlim)

try:
    g("v1_w1_bler.png", "V1 em W1 (MCS 9, 106 PRB): B1 × B2", a1, (4.45, 6.15),
      f"Sementes 1 a 5, 1000 trials cada (5000 TBs por ponto). De 0 a 4,8 dB a BLER é 1 e em 7 e 8 dB é 0,\n"
      f"igual nos dois. {len(w1)} pares (semente, SNR) com contagens idênticas em todas as rodadas HARQ.")
    g("v1_w3_bler.png", "V1 em W3 (MCS 27, 273 PRB): B1 × B2", a3, (19.35, 22.15),
      f"De 20,2 a 21,8 dB: sementes 1 a 5 (1000 TBs por ponto); demais pontos: sementes 1 e 2 (400 TBs).\n"
      f"De 16 a 20 dB a BLER é 1 e em 30 dB é 0, igual nos dois. {len(w3b) + len(w3r)} pares com contagens idênticas.")
except ImportError:
    print("matplotlib ausente: CSVs gerados, PNGs não")
sys.exit(1 if falhas else 0)
