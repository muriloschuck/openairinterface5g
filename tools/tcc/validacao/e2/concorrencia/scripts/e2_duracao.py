#!/usr/bin/env python3
"""e2_duracao.py <arquivo .probe>...: duração de cada chamada de LDPCdecoder (saída - entrada, mesma thread), a partir dos
.probe do E2, concorrência. Imprime, por arquivo: chamadas, mínimo, mediana, p99 e máximo em microssegundos, e quantas
chamadas passaram de 1 ms e de 100 ms (a fatia de tempo do SCHED_RR neste kernel). Só leitura."""
import sys
for path in sys.argv[1:]:
    abertos, dur = {}, []
    for ln in open(path, errors="replace"):
        p = ln.split()
        if len(p) != 4 or p[0] not in ("E", "X"): continue
        tid, ns = int(p[2]), int(p[3])
        if p[0] == "E": abertos[tid] = ns
        elif tid in abertos: dur.append(ns - abertos.pop(tid))
    dur.sort(); n = len(dur)
    if not n: print(f"{path}: sem chamadas"); continue
    us = lambda q: dur[min(n - 1, int(q * n))] / 1e3
    print(f"{path.split('/')[-1]}: chamadas={n} min={dur[0]/1e3:.1f}us mediana={us(0.5):.1f}us p99={us(0.99):.1f}us "
          f"max={dur[-1]/1e3:.1f}us >1ms={sum(d > 1_000_000 for d in dur)} >100ms={sum(d > 100_000_000 for d in dur)}")
