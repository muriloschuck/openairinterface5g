#!/usr/bin/env bash
# ambiente.sh — validação do ambiente (TCC): B0 (OAI nativo, libldpc.so) × B1 (AAL padrão,
# vdev baseband_oai_sw). Varre SNR em W1 com sementes fixas; a mesma semente gera o mesmo
# payload e o mesmo ruído nas duas configurações, o que permite comparar contagem a contagem.
#
#   sudo tools/tcc/ambiente.sh            # tudo
#   SKIP_B1=1 tools/tcc/ambiente.sh       # só B0 (não precisa de root; teste do script)
#
# Variáveis: BUILD (diretório com nr_ulsim/libldpc*.so), OUT, SEEDS, TRIALS, SNRS,
#            CORES (taskset do nr_ulsim), DPDK_CORES (lcores do EAL; 2: fila ENC + fila DEC)
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
BUILD=${BUILD:-$REPO/build}
OUT=${OUT:-$HERE/resultados/$(date +%Y%m%d-%H%M%S)}
SEEDS=${SEEDS:-"1 2 3 4 5"}
TRIALS=${TRIALS:-1000}
SNRS=${SNRS:-"0 1 2 3 4 4.6 4.8 5.0 5.2 5.4 5.6 5.8 6.0 7 8"}
CORES=${CORES:-0-3}
DPDK_CORES=${DPDK_CORES:-0-1}
W1="-m 9 -r 106 -R 106"
AAL="--loader.ldpc.shlibversion _aal --nrLDPC_coding_aal.dpdk_dev baseband_oai_sw --nrLDPC_coding_aal.dpdk_core_list $DPDK_CORES"

[[ -x $BUILD/nr_ulsim && -f $BUILD/libldpc.so ]] || { echo "nr_ulsim/libldpc.so não encontrados em $BUILD"; exit 1; }
if [[ -z ${SKIP_B1:-} ]]; then
  [[ $EUID -eq 0 ]] || { echo "B1 usa DPDK: rode com sudo (ou SKIP_B1=1 para só B0)"; exit 1; }
  [[ -f $BUILD/libldpc_aal.so ]] || { echo "libldpc_aal.so não encontrado em $BUILD"; exit 1; }
  [[ $(awk '/HugePages_Free/ {print $2}' /proc/meminfo) -gt 0 ]] ||
    { echo "sem hugepages livres: sudo dpdk-hugepages.py -p 2M --setup 2G"; exit 1; }
fi

mkdir -p "$OUT"
LOG=$OUT/run.log
{
  echo "# $(date '+%F %T') ambiente.sh"
  echo "# repo: $REPO @ $(git -C "$REPO" rev-parse --short HEAD) ($(git -C "$REPO" status --porcelain | wc -l) arquivos modificados)"
  echo "# BUILD=$BUILD SEEDS='$SEEDS' TRIALS=$TRIALS SNRS='$SNRS' CORES=$CORES DPDK_CORES=$DPDK_CORES"
  echo "# host: $(lscpu | sed -n 's/^Model name: *//p'), $(nproc) CPUs"
} | tee "$LOG"

run() { # tag cfg seed snr [args...]
  local tag=$1 seed=$3 snr=$4; shift 4
  local cmd="OAI_RNGSEED=$seed taskset -c $CORES ./nr_ulsim -n $TRIALS $W1 -s $snr -S $snr --loader.ldpc.shlibpath $BUILD $*"
  echo "$(date '+%T') \$ $cmd > $tag.log" >>"$LOG"
  # o código de saída do nr_ulsim reflete o critério de vazão do próprio teste, não falha de execução;
  # a falha de execução aparece como ausência da linha n_errors (compara.py: SEM DADOS)
  local rc=0
  (cd "$BUILD" && eval "$cmd") >"$OUT/$tag.log" 2>&1 || rc=$?
  grep -q 'n_errors' "$OUT/$tag.log" || echo "$(date '+%T') SEM n_errors (rc=$rc): $tag" | tee -a "$LOG"
}

for seed in $SEEDS; do
  for snr in $SNRS; do
    echo "$(date '+%T') semente $seed SNR $snr" | tee -a "$LOG"
    run "b0_s${seed}_snr${snr}" B0 "$seed" "$snr"
    [[ -n ${SKIP_B1:-} ]] || run "b1_s${seed}_snr${snr}" B1 "$seed" "$snr" "$AAL"
  done
done

rc=0
python3 "$HERE/compara.py" "$OUT" | tee -a "$LOG" || rc=$?
[[ -z ${SUDO_USER:-} ]] || chown -R "$SUDO_USER": "$OUT"
echo "resultados em $OUT"
exit $rc
