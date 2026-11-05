#!/usr/bin/env python3
"""e3_mensagens.py <mensagens.jsonl> [<saida.md>]: transforma o registro de mensagens do E3 (gerado por
e3_roteiro.py --registro) num texto legível, em ordem cronológica: cada pedido enviado à AALI-C (→), a resposta da
extensão (←) com o tempo de ida e volta, os arquivos de limites escritos, as notas e o veredito de cada item.
Os pedidos repetidos da espera pelo primeiro burst são resumidos. Só lê o arquivo; não precisa de sudo."""
import json, os, sys

src = sys.argv[1]
dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "e3_mensagens.md")
regs = [json.loads(l) for l in open(src, encoding="utf-8") if l.strip()]
ped = [r for r in regs if r["tipo"] == "pedido"]
itens = [r for r in regs if r["tipo"] == "item"]
out = [f"# E3: pedidos e respostas da AALI-C", "",
       f"Fonte: `{os.path.basename(src)}`. {len(ped)} pedidos, {len(itens)} itens avaliados "
       f"({sum(r['ok'] for r in itens)} OK, {sum(not r['ok'] for r in itens)} FALHA). "
       "→ = pedido enviado pelo cliente; ← = resposta da extensão, com o tempo de ida e volta.", ""]
fase, bloco, espera = None, [], []

def fecha():
    global bloco
    if bloco: out.extend(["```", *bloco, "```", ""]); bloco = []

def fecha_espera():
    global espera
    if espera:
        p = espera[-1]
        bloco.append(f"({len(espera)} leituras de getAalLpuComputeStats até a versão 1 ter bursts; a última:)")
        bloco.append(f"#{p['seq']:<4} → {p['pedido']}")
        bloco.append(f"      ← {p['resposta']}  ({(p['t_resposta_ns'] - p['t_envio_ns']) / 1000:.0f} µs)")
        espera = []

for r in regs:
    t = r["tipo"]
    if t == "fase":
        fecha_espera(); fecha(); fase = r["texto"]; out.extend([f"## {fase}", ""]); continue
    if t == "pedido":
        if fase == "espera do primeiro burst": espera.append(r); continue
        bloco.append(f"#{r['seq']:<4} → {r['pedido']}")
        bloco.append(f"      ← {r['resposta']}  ({(r['t_resposta_ns'] - r['t_envio_ns']) / 1000:.0f} µs)")
    elif t == "arquivo":
        bloco.append(f"      (arquivo {r['nome']}: {r['conteudo'].rstrip()!r})")
    elif t == "nota":
        bloco.append(f"      (nota: {r['texto']})")
    elif t == "item":
        bloco.append(f"   == item {r['item']}: {'OK' if r['ok'] else 'FALHA'} — {r['desc']}")
        bloco.append("")
fecha_espera(); fecha()
open(dst, "w", encoding="utf-8").write("\n".join(out) + "\n")
print(f"{len(ped)} pedidos, {len(itens)} itens ({sum(r['ok'] for r in itens)} OK) -> {dst}")
