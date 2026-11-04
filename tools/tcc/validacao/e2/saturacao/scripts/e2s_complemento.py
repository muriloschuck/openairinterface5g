#!/usr/bin/env python3
"""e2s_complemento.py <pasta>: só leitura. Com as funções de e2_saturacao_conta.py, por configuração: duração média e
percentis das chamadas, soma média das durações por burst, média do tempo até o máximo de abertas, e o intervalo
entre a primeira entrada do burst e a entrada da 6ª thread distinta (partida do pool)."""
import sys, glob, os, statistics as st
pasta = sys.argv[1]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "e2_saturacao_conta.py")).read()
ns = {}; exec(compile(src.split("por_cfg = defaultdict(list)")[0], "conta", "exec"), ns)
q = lambda v, p: sorted(v)[int(p * (len(v) - 1))]
print("config,dur_media_us,dur_p90_us,dur_p99_us,soma_dur_media_us,fase_media_us,ate_max_media_us,partida_6a_thread_med_us,partida_6a_thread_media_us")
for c in ("w4b1", "w6b1", "w16b1"):
    durs, somas, fases, am, part = [], [], [], [], []
    for f in sorted(glob.glob(os.path.join(pasta, f"r*_{c}.probe"))):
        ev, _ = ns["chamadas"](f)
        for b in ns["bursts"](ev):
            d = [e[1] - e[0] for e in b]; durs += d; somas.append(sum(d)); fases.append(max(e[1] for e in b) - b[0][0])
            am.append(ns["ate_max"](b)[1])
            vistos, t6 = [], None
            for e in b:
                if e[2] not in vistos:
                    vistos.append(e[2])
                    if len(vistos) == 6: t6 = e[0] - b[0][0]; break
            if t6 is not None: part.append(t6)
    print(f"{c},{st.mean(durs)/1e3:.1f},{q(durs,.9)/1e3:.1f},{q(durs,.99)/1e3:.1f},{st.mean(somas)/1e3:.1f},{st.mean(fases)/1e3:.1f},"
          f"{st.mean(am)/1e3:.1f},{(st.median(part)/1e3 if part else float('nan')):.1f},{(st.mean(part)/1e3 if part else float('nan')):.1f}")
