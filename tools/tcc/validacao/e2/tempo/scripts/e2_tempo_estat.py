#!/usr/bin/env python3
"""e2_tempo_estat.py <tempos.csv> [<freq.csv>]: estatística do E2, tempo (V4), W3 com 24 CBs por TB.
Por configuração: tarefas por burst = min(workers, ceil(24/batch)), n, média, desvio padrão, IC95 (% da média) e
tempo relativo a seq. Depois, as conferências da V4: controle A/A (w4b1 × w4b1bis), configurações de tarefa única
(seq fora), efeito por decodificações simultâneas possíveis = min(tarefas, 6 CPUs do pool) e saturação (w16b1 × w6b1).
Depois, as comparações pareadas por rodada (o desenho intercala todas as configurações em cada rodada): diferença média
em %, IC95 da diferença e t. Por fim, as configurações com IC95 acima de 5%. Com freq.csv, a mediana da frequência das
CPUs ativas (amostras acima de 1500 MHz) por configuração.
Versão de 13/11/2026: tabela t completa até 30 graus de liberdade (antes, até 10; acima disso usava 2,0), seção pareada
e lista de IC95 acima de 5%. As linhas anteriores à seção pareada têm o mesmo formato da versão anterior."""
import csv, math, statistics as st, sys
# t de Student bicaudal 95% (0,975), por graus de liberdade
T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
       11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
       21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042}
def t95(gl):
    if gl not in T95: sys.exit(f"t95: {gl} graus de liberdade fora da tabela (1 a 30)")
    return T95[gl]
CBS = 24
CPUS_POOL = 6
def tarefas(c):
    if c == "seq": return 0
    w, b = c.replace("bis", "")[1:].split("b"); return min(int(w), math.ceil(CBS / int(b)))
xs, porrod, erros = {}, {}, []
for r in csv.DictReader(open(sys.argv[1])):
    if not r["decod_us"] or "(0/" not in r["n_errors"] or "RECUSADA" in r["n_errors"]: erros.append((r["rodada"], r["config"], r["n_errors"]))
    if r["decod_us"]:
        xs.setdefault(r["config"], []).append(float(r["decod_us"]))
        porrod.setdefault(r["config"], {})[int(r["rodada"])] = float(r["decod_us"])
est = {}
for c, v in xs.items():
    n, m = len(v), st.mean(v); dp = st.stdev(v) if n > 1 else 0.0
    est[c] = (n, m, dp, t95(n - 1) * dp / math.sqrt(n) / m * 100 if n > 1 else float("nan"))
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
# --- comparações pareadas por rodada: diferença relativa de a sobre b em cada rodada ---
rodadas = sorted(set.intersection(*(set(v) for v in porrod.values())))
def serie(c):
    if c == "TAREFA_UNICA": return {k: st.mean(porrod[u][k] for u in um) for k in rodadas}
    return porrod[c]
def pareada(a, b):
    A, B = serie(a), serie(b); d = [(A[k] - B[k]) / B[k] * 100 for k in rodadas]
    n = len(d); m = st.mean(d); dp = st.stdev(d); h = t95(n - 1) * dp / math.sqrt(n)
    print(f"pareada {a} x {b}: n={n} diferenca={m:+.2f}% ic95=[{m-h:+.2f}%, {m+h:+.2f}%] t={m/(dp/math.sqrt(n)):+.2f}")
print(f"rodadas_completas={len(rodadas)}")
for a, b in [("w4b1bis", "w4b1"), ("w6b1", "w4b1"), ("w16b1", "w6b1"), ("TAREFA_UNICA", "seq"),
             ("w16b1", "TAREFA_UNICA"), ("w6b2", "w4b2"), ("w4b1", "w3b1")]:
    pareada(a, b)
acima = [(c, est[c][3]) for c in ordem if est[c][3] > 5]
print(f"ic95_acima_de_5pct={len(acima)} " + " ".join(f"{c}={ic:.2f}%" for c, ic in acima))
print(f"ic95_max={max(est[c][3] for c in est):.2f}% em {max(est, key=lambda c: est[c][3])}")
if len(sys.argv) > 2:
    fr = {}
    for r in csv.DictReader(open(sys.argv[2])):
        k = int(r["khz"]) / 1000
        if k > 1500: fr.setdefault(r["config"], []).append(k)
    for c in ordem:
        if c in fr: v = sorted(fr[c]); print(f"freq {c}: amostras_ativas={len(v)} mediana={v[len(v)//2]:.0f} MHz min={v[0]:.0f} MHz")
