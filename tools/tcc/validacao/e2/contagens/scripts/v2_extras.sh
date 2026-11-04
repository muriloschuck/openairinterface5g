#!/usr/bin/env bash
# v2_extras.sh — conferências de leitura nos 450 logs da V2 (antes feitas fora do logcmd.sh).
#   (a) nenhum log com rejected/failed to start; (b) linha do pool nos 450;
#   (c) nos 75 logs c0, ops = CBs por burst × calls (W1 3, W2 12, W3 24).
set -u
D=${D:-/home/murilo/tcc/logs/saidas/v2_20261101-194211}
echo "# pasta: $D  logs: $(ls "$D"/*.log | wc -l)"
echo "(a) logs com rejected/failed to start: $(grep -lE 'rejected|failed to start' "$D"/*.log | wc -l)"
echo "(b) logs com 'worker pool: 16 threads, CPUs 2,3,4,5,6,7': $(grep -l 'worker pool: 16 threads, CPUs 2,3,4,5,6,7' "$D"/*.log | wc -l)"
ok=0; bad=0
for f in "$D"/*_c0.log; do
  b=${f##*/}
  case $b in W1_*) cb=3 ;; W2_*) cb=12 ;; W3_*) cb=24 ;; esac
  read -r calls ops < <(grep -oE 'summary: DEC [0-9]+ calls / [0-9]+ ops' "$f" | awk '{print $3, $6}')
  if [[ -n ${calls:-} && $ops -eq $((cb * calls)) ]]; then ok=$((ok + 1)); else bad=$((bad + 1)); echo "  DIF $b: calls=${calls:-?} ops=${ops:-?} cb=$cb"; fi
done
echo "(c) logs c0 com ops = CBs × calls: $ok OK, $bad diferentes"