#!/usr/bin/env python3
"""e2_tempo_estat.py <tempos.csv> [<freq.csv>]: estatística do E2, tempo (V4), W3 com 24 CBs por TB.
Por configuração: tarefas por burst = min(workers, ceil(24/batch)), n, média, desvio padrão, IC95 (% da média) e
tempo relativo a seq. Depois, as conferências da V4: controle A/A (w4b1 × w4b1bis), configurações de tarefa única
(seq fora), efeito por decodificações simultâneas possíveis = min(tarefas, 6 CPUs do pool) e saturação (w16b1 × w6b1). Com freq.csv, a mediana da frequência das CPUs
ativas (amostras acima de 1500 MHz) por configuração."""
import csv, math, statistics as st, sys
T95 = {1: 12.71, 2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57, 6: 2.45, 7: 2.36, 8: 2.31, 9: 2.26, 10: 2.23}
CBS = 24
CPUS_POOL = 6
def tarefas(c):
    if c == "seq": return 0
    w, b = c.replace("bis", "")[1:].split("b"); return min(int(w), math.ceil(CBS / int(b)))
xs, erros = {}, []
for r in csv.DictReader(open(sys.argv[1])):
    if not r["decod_us"] or "(0/" not in r["n_errors"] or "RECUSADA" in r["n_errors"]: erros.append((r["rodada"], r["config"], r["n_errors"]))
    if r["decod_us"]: xs.setdefault(r["config"], []).append(float(r["decod_us"]))
est = {}
for c, v in xs.items():
    n, m = len(v), st.mean(v); dp = st.stdev(v) if n > 1 else 0.0
    est[c] = (n, m, dp, T95.get(n - 1, 2.0) * dp / math.sqrt(n) / m * 100 if n > 1 else float("nan"))
seq = est["seq"][1]
print("config,tarefas,n,media_us,dp_us,ic95_pct,relativo_seq")
ordem = sorted(est, key=lambda c: (tarefas(c), c))
for c in ordem:
    n, m, dp, ic = est[c]; print(f"{c},{tarefas(c)},{n},{m:.1f},{dp:.1f},{ic:.2f},{m/seq:.3f}")
print(f"execucoes_com_problema={len(erros)} {erros[:5]}")
def dif(a, b):
    na, ma, da, _ = est[a]; nb, mb, db, _ = est[b]
    t = (ma - mb) / math.sqrt(da**2 / na + db**2 / nb) if da + db > 0 else float("inf")
    return (ma - mb) / mb * 100, t
d, t = dif("w4b1bis", "w4b1"); print(f"A/A w4b1bis x w4b1: diferenca={d:+.2f}% t={t:+.2f}")
um = [c for c in est if tarefas(c) == 1]; ms = [est[c][1] for c in um]
print(f"tarefa unica ({len(um)} configs): media={st.mean(ms):.1f} us amplitude={(max(ms)-min(ms))/st.mean(ms)*100:.2f}% "
      f"min={min(um, key=lambda c: est[c][1])} max={max(um, key=lambda c: est[c][1])}")
print(f"seq x tarefa unica: {(seq/st.mean(ms)-1)*100:+.2f}%")
ef = lambda c: min(tarefas(c), CPUS_POOL)
for k in sorted({ef(c) for c in est if tarefas(c) > 0}):
    g = [est[c][1] for c in est if tarefas(c) > 0 and ef(c) == k]
    print(f"simultaneas={k}: configs={len(g)} media_do_grupo={st.mean(g):.1f} us relativo_seq={st.mean(g)/seq:.3f}")
d, t = dif("w16b1", "w6b1"); print(f"saturacao w16b1 x w6b1: diferenca={d:+.2f}% t={t:+.2f}")
if len(sys.argv) > 2:
    fr = {}
    for r in csv.DictReader(open(sys.argv[2])):
        k = int(r["khz"]) / 1000
        if k > 1500: fr.setdefault(r["config"], []).append(k)
    for c in ordem:
        if c in fr: v = sorted(fr[c]); print(f"freq {c}: amostras_ativas={len(v)} mediana={v[len(v)//2]:.0f} MHz min={v[0]:.0f} MHz")
