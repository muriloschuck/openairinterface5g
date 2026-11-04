#!/usr/bin/env python3
"""e2s_diag_bursts.py <pasta> <cfg>: só leitura. Usa as funções de e2_saturacao_conta.py (mesmo critério de pausa) para
mostrar, por arquivo da configuração: bursts com tamanho != 24 (vizinhança e pausas), o burst com o máximo de abertas e
a distribuição das pausas entre chamadas consecutivas (entre bursts e dentro deles)."""
import sys, glob, os, statistics as st
sys.argv, pasta, cfg = [sys.argv[0], sys.argv[1]], sys.argv[1], sys.argv[2]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "e2_saturacao_conta.py")).read()
ns = {}; exec(compile(src.split("por_cfg = defaultdict(list)")[0], "conta", "exec"), ns)
for f in sorted(glob.glob(os.path.join(pasta, f"r*_{cfg}.probe"))):
    ev, sp = ns["chamadas"](f); B = ns["bursts"](ev)
    print(f"== {os.path.basename(f)}: chamadas={len(ev)} bursts={len(B)}")
    for i, b in enumerate(B):
        if len(b) != 24:
            ant = (b[0][0] - max(e[1] for e in B[i-1])) / 1e3 if i > 0 else None
            pos = (B[i+1][0][0] - max(e[1] for e in b)) / 1e3 if i + 1 < len(B) else None
            print(f"  burst {i}: {len(b)} chamadas, fase={(max(e[1] for e in b)-b[0][0])/1e3:.1f} us, pausa antes={ant} us, pausa depois={pos} us")
    mx = [ns["ate_max"](b)[0] for b in B]
    for i, m in enumerate(mx):
        if m > 6:
            b = B[i]; print(f"  burst {i}: max_abertas={m}, {len(b)} chamadas, threads={len({e[2] for e in b})}, cpus={sorted({e[3] for e in b})}")
            durs = sorted(((e[1]-e[0])/1e3, e[3], e[2]) for e in b)[-3:]
            print(f"    3 chamadas mais longas (us, cpu, tid): {[(round(d,1), c, t) for d, c, t in durs]}")
    entre = [(B[i+1][0][0] - max(e[1] for e in B[i])) / 1e3 for i in range(len(B)-1)]
    print(f"  pausas entre bursts (us): min={min(entre):.1f} mediana={st.median(entre):.1f} max={max(entre):.1f}; abaixo de 1000: {sum(p < 1000 for p in entre)}")
    th = [len({e[2] for e in b}) for b in B]
    print(f"  threads por burst: min={min(th)} mediana={st.median(th)} max={max(th)}; distribuição={ {k: th.count(k) for k in sorted(set(th))} }")
