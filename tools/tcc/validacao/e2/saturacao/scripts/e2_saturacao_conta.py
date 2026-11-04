#!/usr/bin/env python3
"""e2_saturacao_conta.py <pasta>: lê os r<k>_<cfg>.probe do e2_saturacao.sh (linhas 'E|X pid tid cpu ns') e, por
configuração (todas as rodadas juntas), agrupa as chamadas de LDPCdecoder em bursts (uma pausa de mais de 500 us entre
a última saída e a próxima entrada abre um burst novo; a 30 dB há um burst de 24 CBs por trial). Por burst: fase de
decodificação = última saída - primeira entrada; concorrência média = soma das durações / fase; threads e CPUs
distintas; tempo até atingir o máximo de abertas. Imprime medianas e médias por configuração, a duração mediana das
chamadas por CPU e a parcela das chamadas em cada CPU. Só leitura."""
import sys, glob, os, re, statistics as st
from collections import defaultdict
PAUSA = 500_000
def chamadas(path):
    ab, ev, sem_par = {}, [], 0
    for ln in open(path, errors="replace"):
        p = ln.split()
        if len(p) != 5 or p[0] not in ("E", "X"): continue
        tid, cpu, ns = int(p[2]), int(p[3]), int(p[4])
        if p[0] == "E":
            if tid in ab: sem_par += 1
            ab[tid] = (ns, cpu)
        else:
            a = ab.pop(tid, None)
            if a is None: sem_par += 1; continue
            ev.append((a[0], ns, tid, a[1]))
    return sorted(ev), sem_par + len(ab)
def bursts(ev):
    bs, cur, fim = [], [], None
    for e in ev:
        if cur and e[0] - fim > PAUSA: bs.append(cur); cur = []
        cur.append(e); fim = e[1] if len(cur) == 1 else max(fim, e[1])
    if cur: bs.append(cur)
    return bs
def ate_max(b):
    pts = sorted([(a, 1) for a, _, _, _ in b] + [(x, 0) for _, x, _, _ in b])
    ab = mx = 0; t_mx = pts[0][0]
    for t, k in pts:
        ab += 1 if k else -1
        if ab > mx: mx, t_mx = ab, t
    return mx, t_mx - b[0][0]
por_cfg = defaultdict(list)
for f in sorted(glob.glob(os.path.join(sys.argv[1], "r*_*.probe"))):
    por_cfg[re.match(r"r\d+_(.+)\.probe", os.path.basename(f)).group(1)].append(f)
print("config,arquivos,chamadas,sem_par,bursts,bursts_24,fase_med_us,fase_media_us,dur_med_us,conc_media,threads_med,cpus_med,bursts_6cpus_pct,max_abertas,ate_max_med_us")
porcpu = {}
for c in sorted(por_cfg, key=lambda c: int(c[1:].split("b")[0])):
    ch = sp = 0; B = []; durs = []; cpu_d = defaultdict(list)
    for f in por_cfg[c]:
        ev, s = chamadas(f); ch += len(ev); sp += s; B += bursts(ev)
        for a, x, _, cpu in ev: durs.append(x - a); cpu_d[cpu].append(x - a)
    fase = [max(e[1] for e in b) - b[0][0] for b in B]
    conc = [sum(e[1] - e[0] for e in b) / f_ for b, f_ in zip(B, fase) if f_ > 0]
    mx = [ate_max(b) for b in B]
    print(f"{c},{len(por_cfg[c])},{ch},{sp},{len(B)},{sum(len(b) == 24 for b in B)},{st.median(fase)/1e3:.1f},"
          f"{st.mean(fase)/1e3:.1f},{st.median(durs)/1e3:.1f},{st.mean(conc):.2f},"
          f"{st.median(len({e[2] for e in b}) for b in B):.0f},{st.median(len({e[3] for e in b}) for b in B):.0f},"
          f"{100*sum(len({e[3] for e in b}) == 6 for b in B)/len(B):.1f},"
          f"{max(m for m, _ in mx)},{st.median(t for _, t in mx)/1e3:.1f}")
    porcpu[c] = cpu_d
print("config,cpu,parcela_pct,dur_med_us")
for c, d in porcpu.items():
    tot = sum(len(v) for v in d.values())
    for cpu in sorted(d): print(f"{c},{cpu},{100*len(d[cpu])/tot:.1f},{st.median(d[cpu])/1e3:.1f}")
