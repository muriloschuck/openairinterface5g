#!/usr/bin/env bash
# pilhas.sh <saida gdb> — imprime só as pilhas capturadas pelo conta.gdb, sem os argumentos das funções
awk '/^=== PILHA/ {p=1; print; next} p && (/^#/ || / in section /) {print; next} {p=0}' "$1" |
  sed -E 's/\(([^()]|\([^()]*\))*\) at /() at /; s#/home/murilo/tcc/fork/openairinterface5g/##g'
