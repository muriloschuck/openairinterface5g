#!/usr/bin/env python3
"""compara.py — lê os logs de ambiente.sh e compara B0 × B1 semente a semente.

    python3 tools/tcc/compara.py <diretório de resultados>

Para cada (semente, SNR), extrai do nr_ulsim:
  n_errors          (erros/trials por rodada HARQ, depois do decodificador)
  errors_scrambling (bits errados por rodada, antes do decodificador)
e marca IGUAL quando as duas listas coincidem em B0 e B1. Gera relatorio.md e resumo.csv
no mesmo diretório. Sai com código 1 se houver alguma diferença.
"""
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

PAIR = re.compile(r"(\d+)/(\d+)")
LINE = re.compile(r"SNR\s+[-\d.]+: n_errors \(([^)]*)\).*errors_scrambling \(([^)]*)\)")
NAME = re.compile(r"(b[01])_s(\d+)_snr([-\d.]+)\.log$")


def pairs(text):
    return [(int(a), int(b)) for a, b in PAIR.findall(text)]


def parse(path):
    for line in path.read_text(errors="replace").splitlines():
        m = LINE.search(line)
        if m:
            return {"n_errors": pairs(m.group(1)), "scrambling": pairs(m.group(2))}
    return None


def fmt(p):
    return ",".join(f"{a}/{b}" for a, b in p if b) or "—"


def main(out):
    out = Path(out)
    runs = defaultdict(dict)  # (seed, snr) -> {"b0": res, "b1": res}
    for f in out.glob("b*_s*_snr*.log"):
        m = NAME.search(f.name)
        if m:
            runs[(int(m.group(2)), float(m.group(3)))][m.group(1)] = parse(f)

    rows, diff, missing = [], 0, 0
    bler = defaultdict(lambda: {"b0": [0, 0], "b1": [0, 0]})  # snr -> cfg -> [erros 1ª rodada, trials]
    for (seed, snr) in sorted(runs, key=lambda k: (k[1], k[0])):
        r = runs[(seed, snr)]
        b0, b1 = r.get("b0"), r.get("b1")
        for cfg, res in (("b0", b0), ("b1", b1)):
            if res and res["n_errors"]:
                e, t = res["n_errors"][0]
                bler[snr][cfg][0] += e
                bler[snr][cfg][1] += t
        if b0 is None or b1 is None:
            verdict = "SEM DADOS"
            missing += 1
        else:
            same = b0["n_errors"] == b1["n_errors"] and b0["scrambling"] == b1["scrambling"]
            verdict = "IGUAL" if same else "DIFERENTE"
            diff += not same
        rows.append({
            "snr": snr, "semente": seed, "veredito": verdict,
            "b0_n_errors": fmt(b0["n_errors"]) if b0 else "—",
            "b1_n_errors": fmt(b1["n_errors"]) if b1 else "—",
            "b0_scrambling": fmt(b0["scrambling"]) if b0 else "—",
            "b1_scrambling": fmt(b1["scrambling"]) if b1 else "—",
        })

    with open(out / "resumo.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["snr"])
        w.writeheader()
        w.writerows(rows)

    md = ["# Validação do ambiente: B0 × B1", ""]
    md.append(f"{len(rows)} pares (semente, SNR): {len(rows) - diff - missing} IGUAL, {diff} DIFERENTE, {missing} SEM DADOS.")
    md.append("IGUAL = mesmas contagens de n_errors e errors_scrambling em todas as rodadas HARQ.\n")
    md.append("## BLER da 1ª transmissão (todas as sementes somadas)\n")
    md.append("| SNR (dB) | B0 | B1 |")
    md.append("|---|---|---|")
    for snr in sorted(bler):
        cells = []
        for cfg in ("b0", "b1"):
            e, t = bler[snr][cfg]
            cells.append(f"{e}/{t} = {e / t:.3f}" if t else "—")
        md.append(f"| {snr:g} | {cells[0]} | {cells[1]} |")
    md.append("\n## Por semente\n")
    md.append("| SNR | semente | veredito | B0 n_errors | B1 n_errors | B0 scrambling | B1 scrambling |")
    md.append("|---|---|---|---|---|---|---|")
    for r in rows:
        md.append(f"| {r['snr']:g} | {r['semente']} | {r['veredito']} | {r['b0_n_errors']} | {r['b1_n_errors']} "
                  f"| {r['b0_scrambling']} | {r['b1_scrambling']} |")
    (out / "relatorio.md").write_text("\n".join(md) + "\n")

    print(f"B0 × B1: {len(rows)} pares, {diff} DIFERENTE, {missing} SEM DADOS -> {out / 'relatorio.md'}")
    return 1 if diff else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
