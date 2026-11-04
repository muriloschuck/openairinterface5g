#!/usr/bin/env python3
"""e2_conta.py: conta a concorrência de LDPCdecoder a partir da saída do bpftrace do e2_concorrencia.sh.
Linhas: 'E <pid> <tid> <ns>' (entrada) e 'X <pid> <tid> <ns>' (saída). Uma chamada = um code block.
Imprime: chamadas, threads distintas, máximo de chamadas abertas ao mesmo tempo, % de chamadas que se sobrepõem a outra,
e o histograma do máximo de abertas no início de cada chamada."""
import sys
from collections import Counter

def ler(path):
    ev, perdidos, sem_par = [], 0, 0
    abertos = {}   # tid -> ns de entrada
    for ln in open(path, errors="replace"):
        p = ln.split()
        if ln.startswith("Lost"):
            perdidos += int(p[1]) if len(p) > 1 and p[1].isdigit() else 1
            continue
        if len(p) != 4 or p[0] not in ("E", "X"):
            continue
        tid, ns = int(p[2]), int(p[3])
        if p[0] == "E":
            if tid in abertos: sem_par += 1
            abertos[tid] = ns
        else:
            t0 = abertos.pop(tid, None)
            if t0 is None: sem_par += 1; continue
            ev.append((t0, ns, tid))
    sem_par += len(abertos)
    return ev, perdidos, sem_par

def conta(ev):
    pontos = []
    for i, (a, b, _) in enumerate(ev):
        pontos.append((a, 1, i)); pontos.append((b, 0, i))   # saída antes de entrada no mesmo ns
    pontos.sort()
    abertas, maximo, sobre, hist = set(), 0, set(), Counter()
    for _, tipo, i in pontos:
        if tipo == 1:
            if abertas: sobre.add(i); sobre.update(abertas)
            abertas.add(i); maximo = max(maximo, len(abertas)); hist[len(abertas)] += 1
        else:
            abertas.discard(i)
    return maximo, len(sobre), hist

ev, perdidos, sem_par = ler(sys.argv[1])
maximo, n_sobre, hist = conta(ev)
tids = len({t for _, _, t in ev})
pct = 100.0 * n_sobre / len(ev) if ev else 0.0
h = " ".join(f"{k}:{hist[k]}" for k in sorted(hist))
print(f"chamadas={len(ev)} threads={tids} max_abertas={maximo} sobrepostas={pct:.1f}% perdidos={perdidos} sem_par={sem_par} hist_inicio=[{h}]")
