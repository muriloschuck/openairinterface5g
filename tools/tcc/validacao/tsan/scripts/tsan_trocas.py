#!/usr/bin/env python3
"""tsan_trocas.py: com um nr_ulsim B2 rodando, espera o 1º burst e faz N trocas de configuração pelo socket da AALI-C,
uma a cada INTERVALO s, para exercitar ao mesmo tempo a thread de controle e o caminho de dados sob o ThreadSanitizer."""
import json, socket, sys, time, os
SOCK, N, INTERVALO = "/tmp/aal_ext.sock", int(sys.argv[1]), float(sys.argv[2])
def req(line):
    s = socket.socket(socket.AF_UNIX); s.settimeout(30); s.connect(SOCK); s.sendall(line.encode() + b"\n")
    buf = b""
    while not buf.endswith(b"\n"):
        c = s.recv(65536)
        if not c: break
        buf += c
    s.close(); return json.loads(buf.decode())
t = time.monotonic()
while not os.path.exists(SOCK):
    if time.monotonic() - t > 120: print("trocas: socket não apareceu"); sys.exit(2)
    time.sleep(0.2)
v0 = req("getAalLpuComputeConfig")["version"]
while True:
    v1 = next((x for x in req("getAalLpuComputeStats").get("versions", []) if x["version"] == v0), None)
    if v1 and v1["bursts"] > 0: break
    if time.monotonic() - t > 300: print("trocas: nenhum burst"); sys.exit(2)
    time.sleep(0.2)
CICLO = [("seq", 1, 1), ("par", 3, 1), ("par", 3, 2), ("par", 16, 1), ("par", 2, 64)]
v, ok = req("getAalLpuComputeConfig")["version"], 0
for k in range(N):
    m, w, b = CICLO[k % len(CICLO)]
    r = req(f"setAalLpuComputeConfig expected_version={v} oai_sw.mode={m} oai_sw.workers={w} oai_sw.batch={b}")
    if r.get("status") == "OK": ok += 1; v = r["version"]
    else: print("trocas: recusada", r); break
    time.sleep(INTERVALO)
print(f"trocas: {ok} de {N} aceitas, última versão {v}")
