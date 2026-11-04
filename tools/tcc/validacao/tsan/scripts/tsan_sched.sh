#!/usr/bin/env bash
# tsan_sched.sh — confere a política de escalonamento das threads do pool da LPU (build normal, sem TSan): roda um
#   nr_ulsim W3 com workers=16 e, com ele decodificando, lista as threads com classe (TS = normal, FF = FIFO de tempo
#   real), prioridade e CPU. Explica o máximo de 6 decodificações simultâneas do E2, concorrência.
set -u
B=/home/murilo/tcc/fork/openairinterface5g/build
OUT=${OUT:-/home/murilo/tcc/logs/saidas/sched_$(date +%Y%m%d-%H%M%S)}
mkdir -p "$OUT"; sudo -v || exit 1; cd $B || exit 1
sudo OAI_RNGSEED=1 ./nr_ulsim -n 2000 -m 27 -r 273 -R 273 -s 30 -S 30 --loader.ldpc.shlibpath $B --loader.ldpc.shlibversion _aal \
  --nrLDPC_coding_aal.dpdk_dev baseband_oai_sw --nrLDPC_coding_aal.dpdk_core_list 0-1 \
  --nrLDPC_coding_aal.compute oai_sw.mode=par,oai_sw.workers=16,oai_sw.batch=1 >"$OUT/nr_ulsim.log" 2>&1 &
sleep 8
P=$(pgrep -n nr_ulsim)
ps -L -o tid,cls,rtprio,psr,comm -p "$P" | tee "$OUT/threads.txt"
echo "== classes: $(awk 'NR>1{print $2}' "$OUT/threads.txt" | sort | uniq -c | tr '\n' ' ')"
wait
echo "== $(grep -oE 'n_errors \([^)]*\)' "$OUT/nr_ulsim.log")"
