#!/usr/bin/env bash
# e2_saturacao.sh — E2, saturação (passo 9 da 4.6, questão em aberto da V4: por que w16b1 é mais rápido que w6b1).
#   Para cada rodada, roda w4b1, w6b1 e w16b1 em ordem rotacionada, W3 a 30 dB, N trials, semente 1, com o bpftrace preso
#   na entrada e na saída de LDPCdecoder (build/libldpc.so), registrando pid, tid, CPU e instante de cada chamada.
#   O e2_saturacao_conta.py agrupa as chamadas em bursts e mede, por burst, a duração da fase de decodificação, a
#   concorrência média, as CPUs usadas e a duração das chamadas por CPU. Execuções com probe não servem para medir tempo
#   absoluto; só se comparam entre si. Rodar como usuário; pede sudo (DPDK e bpftrace).
set -u
B=/home/murilo/tcc/fork/openairinterface5g/build
LIB=$B/libldpc.so
RODADAS=${RODADAS:-3}
N=${N:-500}
CFGS=(w4b1 w6b1 w16b1)
OUT=${OUT:-/home/murilo/tcc/logs/saidas/e2_saturacao_$(date +%Y%m%d-%H%M%S)}
mkdir -p "$OUT"
AAL=(--loader.ldpc.shlibpath $B --loader.ldpc.shlibversion _aal --nrLDPC_coding_aal.dpdk_dev baseband_oai_sw --nrLDPC_coding_aal.dpdk_core_list 0-1)
PROG="uprobe:$LIB:LDPCdecoder { printf(\"E %d %d %d %llu\n\", pid, tid, cpu, nsecs); } uretprobe:$LIB:LDPCdecoder { printf(\"X %d %d %d %llu\n\", pid, tid, cpu, nsecs); }"
NC=${#CFGS[@]}
echo "# $(date '+%F %T') e2_saturacao.sh RODADAS=$RODADAS N=$N HEAD=$(git -C $B/.. rev-parse --short HEAD) -> $OUT"
sudo -v || exit 1
cd $B || exit 1
for r in $(seq 1 $RODADAS); do
  for i in $(seq 0 $((NC - 1))); do
    c=${CFGS[$(( (r - 1 + i) % NC ))]}; w=${c#w}; w=${w%b*}
    pf="$OUT/r${r}_${c}.probe"; lf="$OUT/r${r}_${c}.log"; ef="$OUT/r${r}_${c}.bpftrace.err"
    sudo bpftrace -o "$pf" -e "$PROG" >/dev/null 2>"$ef" &
    for k in $(seq 1 100); do sudo grep -qs Attach "$pf" "$ef" && break; sleep 0.1; done
    sudo grep -qs Attach "$pf" "$ef" || { echo "r$r $c: bpftrace não anexou"; cat "$ef"; exit 1; }
    sudo OAI_RNGSEED=1 ./nr_ulsim -n $N -m 27 -r 273 -R 273 -s 30 -S 30 "${AAL[@]}" \
      --nrLDPC_coding_aal.compute "oai_sw.mode=par,oai_sw.workers=$w,oai_sw.batch=1" >"$lf" 2>&1
    sleep 0.5; sudo pkill -INT -x bpftrace; wait
    sudo chown "$USER": "$pf" "$lf" "$ef" 2>/dev/null
    ops=$(grep -oE 'summary: DEC [0-9]+ calls / [0-9]+ ops' "$lf" | grep -oE '[0-9]+ ops' | grep -oE '[0-9]+')
    ne=$(grep -oE 'n_errors \([^)]*\)' "$lf"); lost=$(grep -ohE 'Lost [0-9]+' "$pf" "$ef" | head -1)
    printf 'rodada %d %-6s ops=%-6s %s %s\n' "$r" "$c" "${ops:-?}" "$ne" "${lost:-sem_perdas}"
  done
done
echo "# probes e logs em $OUT"
