#!/usr/bin/env python3
"""tsan_conta.py <arquivos de log do TSan...>: separa os relatórios do ThreadSanitizer e classifica cada um pelo código
que aparece nas pilhas: 'nosso' (bbdev_oai_sw.c ou aal_compute_ext.c), 'adaptador' (nrLDPC_coding_aal.c), 'decodificador' (libldpc: nrLDPC_*, LDPCdecoder,
rate matching/CRC do OAI chamados pela LPU) ou 'outro' (resto do OAI, DPDK, libc). Imprime a contagem por classe e, para
as classes 'nosso' e 'decodificador', o cabeçalho e as 3 primeiras linhas de cada pilha."""
import sys, re
NOSSO = ("bbdev_oai_sw.c", "aal_compute_ext.c")
ADAPT = ("nrLDPC_coding_aal.c",)
DECOD = ("LDPCdecoder", "nrLDPC_decoder", "nrLDPC_bnProc", "nrLDPC_cnProc", "libldpc.so", "nr_rate_matching", "nr_deinterleaving", "check_crc")
reps = []
for path in sys.argv[1:]:
    txt = open(path, errors="replace").read()
    for bloco in txt.split("=================="):
        if "WARNING: ThreadSanitizer" in bloco:
            reps.append((path, bloco.strip()))
cls = {"nosso": [], "adaptador": [], "decodificador": [], "outro": []}
for path, b in reps:
    if any(s in b for s in NOSSO): cls["nosso"].append(b)
    elif any(s in b for s in ADAPT): cls["adaptador"].append(b)
    elif any(s in b for s in DECOD): cls["decodificador"].append(b)
    else: cls["outro"].append(b)
print(f"relatorios={len(reps)} nosso={len(cls['nosso'])} adaptador={len(cls['adaptador'])} decodificador={len(cls['decodificador'])} outro={len(cls['outro'])}")
for k in ("nosso", "adaptador", "decodificador"):
    for b in cls[k][:10]:
        linhas = [l for l in b.splitlines() if l.strip()]
        print(f"--- {k}:"); print("\n".join(linhas[:4]))
