#!/usr/bin/env python3
"""amb_estat.py <tempos.csv>... [--freq <freq.csv>...]: por fase e configuração, n, média, desvio padrão, coeficiente de
variação (CV), meia-largura do intervalo de confiança de 95% em % da média, e quantas repetições dariam ±5% e ±2%
(n >= (t·CV/e)², com t de Student). Com --freq, resume a frequência amostrada por fase (mín, mediana e máx, em MHz)."""
import csv, math, statistics as st, sys
T95 = {1: 12.71, 2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57, 6: 2.45, 7: 2.36, 8: 2.31, 9: 2.26, 10: 2.23, 14: 2.14, 19: 2.09, 29: 2.05}
def t95(df):
    ks = [k for k in sorted(T95) if k <= df]
    return T95[ks[-1]] if ks else 12.71
def n_para(cv, e):
    n = 2
    while n < 1000 and t95(n - 1) * cv / math.sqrt(n) > e: n += 1
    return n
args = sys.argv[1:]
tf = args[:args.index("--freq")] if "--freq" in args else args
ff = args[args.index("--freq") + 1:] if "--freq" in args else []
dados = {}
for p in tf:
    for r in csv.DictReader(open(p)):
        if r["decod_us"]: dados.setdefault((r["fase"], r["config"]), []).append(float(r["decod_us"]))
print("fase,config,n,media_us,dp_us,cv_pct,ic95_pct,n_para_5pct,n_para_2pct")
for (fase, cfg), xs in sorted(dados.items()):
    n, m = len(xs), st.mean(xs); dp = st.stdev(xs) if n > 1 else 0.0; cv = dp / m
    ic = t95(n - 1) * cv / math.sqrt(n) * 100 if n > 1 else float("nan")
    print(f"{fase},{cfg},{n},{m:.1f},{dp:.1f},{cv*100:.2f},{ic:.2f},{n_para(cv,0.05)},{n_para(cv,0.02)}")
fr = {}
for p in ff:
    for r in csv.DictReader(open(p)):
        fr.setdefault(r["fase"], []).append(int(r["khz"]) / 1000)
for fase, xs in sorted(fr.items()):
    xs.sort(); print(f"freq {fase}: amostras={len(xs)} min={xs[0]:.0f} MHz mediana={xs[len(xs)//2]:.0f} MHz max={xs[-1]:.0f} MHz")
