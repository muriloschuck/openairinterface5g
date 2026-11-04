#!/usr/bin/env python3
"""e1_tempo_estat.py <tempos.csv> [<freq.csv>]: estatística do E1, tempo (V6). Por configuração: n, média, desvio
padrão, IC95 (% da média). Depois: controle A/A (B1bis × B1), custo da extensão (B2 × B1) com diferença, t de Welch,
IC95 da diferença e limite superior do custo, e B2seq × B2 (o --compute com seq não muda o tempo). As diferenças em %
usam como base a média do B1. O IC da diferença usa t com min(n)-1 graus de liberdade (conservador).
Com freq.csv, a mediana da frequência das CPUs ativas (amostras acima de 1500 MHz) por configuração."""
import csv, math, statistics as st, sys
T95 = {1: 12.71, 2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57, 6: 2.45, 7: 2.36, 8: 2.31, 9: 2.26, 10: 2.23}
xs, erros = {}, []
for r in csv.DictReader(open(sys.argv[1])):
    if not r["decod_us"] or "(0/" not in r["n_errors"] or "RECUSADA" in r["n_errors"]: erros.append((r["rodada"], r["config"], r["n_errors"]))
    if r["decod_us"]: xs.setdefault(r["config"], []).append(float(r["decod_us"]))
est = {}
for c, v in xs.items():
    n, m = len(v), st.mean(v); dp = st.stdev(v) if n > 1 else 0.0
    est[c] = (n, m, dp, T95.get(n - 1, 2.0) * dp / math.sqrt(n) / m * 100 if n > 1 else float("nan"))
print("config,n,media_us,dp_us,ic95_pct")
for c in ["B1", "B1bis", "B2", "B2seq"]:
    if c in est: n, m, dp, ic = est[c]; print(f"{c},{n},{m:.1f},{dp:.1f},{ic:.2f}")
print(f"execucoes_com_problema={len(erros)} {erros[:5]}")
def dif(a, b):
    na, ma, da, _ = est[a]; nb, mb, db, _ = est[b]
    ep = math.sqrt(da**2 / na + db**2 / nb); tc = T95.get(min(na, nb) - 1, 2.0)
    t = (ma - mb) / ep if ep > 0 else float("inf")
    base = est["B1"][1]
    return (ma - mb) / base * 100, t, (ma - mb - tc * ep) / base * 100, (ma - mb + tc * ep) / base * 100
d, t, lo, hi = dif("B1bis", "B1"); print(f"A/A B1bis x B1: diferenca={d:+.2f}% t={t:+.2f} ic95=[{lo:+.2f}%, {hi:+.2f}%]")
d, t, lo, hi = dif("B2", "B1"); print(f"custo B2 x B1: diferenca={d:+.2f}% t={t:+.2f} ic95=[{lo:+.2f}%, {hi:+.2f}%] limite_superior={hi:+.2f}%")
d, t, lo, hi = dif("B2seq", "B2"); print(f"B2seq x B2: diferenca={d:+.2f}% t={t:+.2f} ic95=[{lo:+.2f}%, {hi:+.2f}%]")
if len(sys.argv) > 2:
    fr = {}
    for r in csv.DictReader(open(sys.argv[2])):
        k = int(r["khz"]) / 1000
        if k > 1500: fr.setdefault(r["config"], []).append(k)
    for c in ["B1", "B1bis", "B2", "B2seq"]:
        if c in fr: v = sorted(fr[c]); print(f"freq {c}: amostras_ativas={len(v)} mediana={v[len(v)//2]:.0f} MHz min={v[0]:.0f} MHz")
