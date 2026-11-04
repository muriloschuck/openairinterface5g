#!/usr/bin/env bash
# v1_w3_reforco.sh — V1 em W3 na queda da curva (20,2 a 21,8 dB, 5 sementes) sobre o código commitado, e conferência
#   das contagens n_errors, arquivo a arquivo, contra a execução de referência de 31/10 (v1_w3_20261031-214010).
set -u
R=/home/murilo/tcc/fork/openairinterface5g
REF=/home/murilo/tcc/logs/saidas/v1_w3_20261031-214010
echo "HEAD: $(git -C $R rev-parse --short HEAD) | árvore: $(git -C $R status --porcelain -- openair1 | wc -l) arquivos modificados em openair1"
OUT=/home/murilo/tcc/logs/saidas/v1_w3r_$(date +%Y%m%d-%H%M%S)
OUT=$OUT CARGA=W3 SEEDS='1 2 3 4 5' SNRS='20.2 20.4 20.6 20.8 21 21.2 21.4 21.6 21.8' ~/tcc/logs/scripts/v1_b1b2.sh | tail -1
ne() { grep -oE 'n_errors \([^)]*\)' "$1" 2>/dev/null; }
for cfg in b1 b2; do
  n=0 d=0
  for f in "$OUT"/${cfg}_s*_snr*.log; do
    r="$REF/${f##*/}"; n=$((n + 1))
    [[ -n $(ne "$f") && "$(ne "$f")" == "$(ne "$r")" ]] || { d=$((d + 1)); echo "  DIF ${f##*/}: $(ne "$f") vs $(ne "$r")"; }
  done
  echo "$cfg × referência 31/10: $n comparados, $d diferentes"
done
echo "linhas do pool no B2: $(cat "$OUT"/b2_*.log | grep -oE 'worker pool: [0-9]+ threads, CPUs [0-9,]+' | sort | uniq -c)"
