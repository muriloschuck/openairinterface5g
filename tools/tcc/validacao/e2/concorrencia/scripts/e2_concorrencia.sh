#!/usr/bin/env bash
# e2_concorrencia.sh — E2, concorrência (passo 4 da 4.6). Para cada execução da lista, liga o bpftrace com uprobes na entrada e
#   na saída de LDPCdecoder (build/libldpc.so, carregada pela LPU baseband_oai_sw), roda um nr_ulsim B2 curto a 30 dB
#   (sem erros, então o número de chamadas é exato) e conta, com e2_conta.py, quantas decodificações estiveram abertas
#   ao mesmo tempo. Execuções com probe não servem para medir tempo.
#   Rodar como usuário; pede sudo (DPDK e bpftrace). EXECS pode ser trocado por variável de ambiente.
set -u
B=/home/murilo/tcc/fork/openairinterface5g/build
SC=/home/murilo/tcc/logs/scripts
LIB=$B/libldpc.so
N=${N:-200}
EXECS=${EXECS:-"W3:c0 W3:c1 W3:c3 W3:c5 W3:c6 W1:c0 W1:c3"}
declare -A CFG=([c0]=oai_sw.mode=seq
                [c1]=oai_sw.mode=par,oai_sw.workers=1,oai_sw.batch=1
                [c3]=oai_sw.mode=par,oai_sw.workers=3,oai_sw.batch=1
                [c5]=oai_sw.mode=par,oai_sw.workers=3,oai_sw.batch=64
                [c6]=oai_sw.mode=par,oai_sw.workers=16,oai_sw.batch=1)
OUT=${OUT:-/home/murilo/tcc/logs/saidas/e2_concorrencia_$(date +%Y%m%d-%H%M%S)}
mkdir -p "$OUT"
AAL=(--loader.ldpc.shlibpath $B --loader.ldpc.shlibversion _aal --nrLDPC_coding_aal.dpdk_dev baseband_oai_sw --nrLDPC_coding_aal.dpdk_core_list 0-1)
PROG="uprobe:$LIB:LDPCdecoder { printf(\"E %d %d %llu\n\", pid, tid, nsecs); } uretprobe:$LIB:LDPCdecoder { printf(\"X %d %d %llu\n\", pid, tid, nsecs); }"
echo "# $(date '+%F %T') e2_concorrencia.sh HEAD=$(git -C $B/.. rev-parse --short HEAD) N=$N EXECS='$EXECS' -> $OUT"
sudo -v || exit 1
cd $B || exit 1
for e in $EXECS; do
  carga=${e%%:*}; c=${e##*:}
  case $carga in
    W1) MOD=(-m 9 -r 106 -R 106) ;;
    W3) MOD=(-m 27 -r 273 -R 273) ;;
  esac
  pf="$OUT/${carga}_${c}.probe"; lf="$OUT/${carga}_${c}.log"
  sudo bpftrace -o "$pf" -e "$PROG" >/dev/null 2>"$OUT/${carga}_${c}.bpftrace.err" &
  for i in $(seq 1 100); do grep -q Attach "$OUT/${carga}_${c}.bpftrace.err" 2>/dev/null && break; sleep 0.1; done
  grep -q Attach "$OUT/${carga}_${c}.bpftrace.err" 2>/dev/null || { echo "$e: bpftrace não anexou"; cat "$OUT/${carga}_${c}.bpftrace.err"; sudo pkill -INT -x bpftrace; exit 1; }
  sudo OAI_RNGSEED=1 ./nr_ulsim -n $N "${MOD[@]}" -s 30 -S 30 "${AAL[@]}" --nrLDPC_coding_aal.compute "${CFG[$c]}" >"$lf" 2>&1
  sleep 0.5; sudo pkill -INT -x bpftrace; wait
  sudo chown "$USER": "$pf" "$lf" "$OUT/${carga}_${c}.bpftrace.err" 2>/dev/null
  ops=$(grep -oE 'summary: DEC [0-9]+ calls / [0-9]+ ops' "$lf" | grep -oE '[0-9]+ ops' | grep -oE '[0-9]+')
  ne=$(grep -oE 'n_errors \([^)]*\)' "$lf")
  printf '%-6s %-3s ops=%-6s %s | %s\n' "$carga" "$c" "${ops:-?}" "$(python3 $SC/e2_conta.py "$pf")" "$ne"
done
echo "# logs e saídas do probe em $OUT"
