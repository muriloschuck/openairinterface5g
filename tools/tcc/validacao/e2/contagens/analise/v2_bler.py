#!/usr/bin/env python3
"""v2_bler.py [<pasta dados>]: contagens e BLER da V2 (E2, contagens; seção 5.3 do relatório).

Lê os logs crus de dados/v2_2*/ (nomes <carga>_snr<SNR>_s<semente>_c<k>.log, gerados por v2.sh; c0 = seq, c1 a c5 =
par com workers 1, 2, 3 e batch 1, e workers 3 com batch 2 e 64). Para cada grupo (carga, SNR, semente), confere que a
linha n_errors … errors_scrambling e o resumo da LPU ([OAI_SW] summary) de c1 a c5 são iguais aos de c0. Soma, por
carga e SNR, os erros da 1ª transmissão das sementes. Escreve, na pasta deste script: v2_por_grupo.csv,
v2_bler.csv e v2_w1_bler.png, v2_w2_bler.png, v2_w3_bler.png. Só lê os logs; não precisa de sudo."""
import csv, glob, os, re, sys
from collections import defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "comum"))
from graf_comum import le_log, grafico  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "..", "dados")
ds = sorted(glob.glob(os.path.join(DADOS, "v2_2*")))
if len(ds) != 1:
    sys.exit(f"esperava 1 pasta v2_2* em {DADOS}, achei {len(ds)}")
PASTA = ds[0]
NOME = re.compile(r"(W\d)_snr([0-9.]+)_s(\d+)_c0\.log$")
SUM = re.compile(r"\[OAI_SW\] summary.*")
CARGA = {"W1": "W1 (MCS 9, 106 PRB)", "W2": "W2 (MCS 16, 273 PRB)", "W3": "W3 (MCS 27, 273 PRB)"}


def resumo(f):
    m = SUM.search(open(f, errors="replace").read())
    return m.group(0).strip() if m else None


grupos, falhas = [], []
for f0 in sorted(glob.glob(os.path.join(PASTA, "W*_snr*_s*_c0.log"))):
    carga, snr_txt, seed = NOME.search(f0).groups()
    r0, s0 = le_log(f0), resumo(f0)
    ok = bool(r0 and s0) and "false_positive 0/" in open(f0, errors="replace").read()
    for k in range(1, 6):
        fk = f0.replace("_c0.log", f"_c{k}.log")
        rk = le_log(fk) if os.path.exists(fk) else None
        txt = open(fk, errors="replace").read() if os.path.exists(fk) else ""
        if not rk or rk[0] != (r0 and r0[0]) or resumo(fk) != s0 or "rejected" in txt:
            ok = False
    (grupos if ok else falhas).append((carga, float(snr_txt), snr_txt, int(seed), r0))

with open(os.path.join(AQUI, "v2_por_grupo.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["carga", "snr_db", "semente", "erros_1a_tx", "trials", "c1_a_c5_iguais_a_c0"])
    for c, snr, txt, seed, r in sorted(grupos + falhas):
        w.writerow([c, txt, seed, r and r[1], r and r[2], "sim" if (c, snr, txt, seed, r) in grupos else "NAO"])

agg = defaultdict(lambda: [0, 0, ""])
for c, snr, txt, seed, r in grupos:
    a = agg[(c, snr)]; a[0] += r[1]; a[1] += r[2]; a[2] = txt
with open(os.path.join(AQUI, "v2_bler.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["carga", "snr_db", "erros_1a_tx_seq", "erros_1a_tx_par", "trials", "bler_1a_tx"])
    for (c, snr) in sorted(agg):
        e, t, txt = agg[(c, snr)]; w.writerow([c, txt, e, e, t, f"{e/t:.4f}"])

print(f"grupos iguais: {len(grupos)}  diferentes ou incompletos: {len(falhas)}  (cada grupo = c0 + 5 configurações par)")
for f in falhas:
    print("  DIF", f[:4])

try:
    for c in sorted({k[0] for k in agg}):
        xs = sorted(s for cc, s in agg if cc == c)
        ys = [agg[(c, s)][0] / agg[(c, s)][1] for s in xs]
        rot = [f"{agg[(c, s)][0]}/{agg[(c, s)][1]}" for s in xs]
        n = sum(1 for g in grupos if g[0] == c); t1 = agg[(c, xs[0])][1] // 5
        grafico(os.path.join(AQUI, f"v2_{c.lower()}_bler.png"), f"V2 em {CARGA[c]}: seq × par", xs, ys, ys,
                "seq (c0)", "par (c1 a c5)",
                f"Sementes 1 a 5 somadas, {t1} trials cada ({5 * t1} TBs por ponto).\n"
                f"c1 a c5 = par com workers 1, 2, 3 (batch 1) e workers 3 com batch 2 e 64.\n"
                f"{n} grupos com contagens idênticas em todas as rodadas HARQ.",
                rotulos=rot, categorico=True, xlabel="SNR (dB), pontos medidos (eixo não linear)")
except ImportError:
    print("matplotlib ausente: CSVs gerados, PNGs não")
sys.exit(1 if falhas else 0)
