#!/usr/bin/env bash
# v2.sh — V2 (invariância funcional): o B2 em cinco configurações de par dá a mesma saída que em seq.
#   Para cada (carga, SNR, semente): roda seq (referência) e as configurações de par com a mesma semente; um par é IGUAL
#   quando a linha n_errors … errors_scrambling e o "[OAI_SW] summary" coincidem com os de seq, com false_positive 0.
#   Sem taskset: os workers ficam nas CPUs 2-7 (fora dos lcores 0-1), o que aumenta a concorrência real entre eles.
#   Rodar como usuário; pede sudo (DPDK). CARGAS, SEEDS e SNRS_W1/W2/W3 podem ser trocados por variável de ambiente.
set -u
B=/home/murilo/tcc/fork/openairinterface5g/build
CARGAS=${CARGAS:-"W1 W2 W3"}
SEEDS=${SEEDS:-"1 2 3 4 5"}
SNRS_W1=${SNRS_W1:-"0 3 5.2 5.4 5.6"}
SNRS_W2=${SNRS_W2:-"10 11.1 11.2 11.3 11.4"}
SNRS_W3=${SNRS_W3:-"20 20.6 20.8 21 30"}
CFGS=(oai_sw.mode=seq
      oai_sw.mode=par,oai_sw.workers=1,oai_sw.batch=1
      oai_sw.mode=par,oai_sw.workers=2,oai_sw.batch=1
      oai_sw.mode=par,oai_sw.workers=3,oai_sw.batch=1
      oai_sw.mode=par,oai_sw.workers=3,oai_sw.batch=2
      oai_sw.mode=par,oai_sw.workers=3,oai_sw.batch=64)
OUT=${OUT:-/home/murilo/tcc/logs/saidas/v2_$(date +%Y%m%d-%H%M%S)}
AAL=(--loader.ldpc.shlibpath $B --loader.ldpc.shlibversion _aal --nrLDPC_coding_aal.dpdk_dev baseband_oai_sw --nrLDPC_coding_aal.dpdk_core_list 0-1)
mkdir -p "$OUT"; cd $B || exit 1
echo "# $(date '+%F %T') v2.sh HEAD=$(git -C $B/.. rev-parse --short HEAD) CARGAS='$CARGAS' SEEDS='$SEEDS' -> $OUT"
res() { grep -oE 'n_errors \([^)]*\).*errors_scrambling \([^)]*\)' "$1"; }
sumry() { grep -oE 'summary: DEC [0-9]+ calls / [0-9]+ ops' "$1"; }
nok=0; nfail=0
for carga in $CARGAS; do
  case $carga in
    W1) MOD=(-n 1000 -m 9 -r 106 -R 106); SNRS=$SNRS_W1 ;;
    W2) MOD=(-n 200 -m 16 -r 273 -R 273); SNRS=$SNRS_W2 ;;
    W3) MOD=(-n 200 -m 27 -r 273 -R 273); SNRS=$SNRS_W3 ;;
  esac
  for snr in $SNRS; do
    for seed in $SEEDS; do
      for k in "${!CFGS[@]}"; do
        sudo OAI_RNGSEED=$seed ./nr_ulsim "${MOD[@]}" -s $snr -S $snr "${AAL[@]}" --nrLDPC_coding_aal.compute "${CFGS[$k]}" \
          >"$OUT/${carga}_snr${snr}_s${seed}_c$k.log" 2>&1
      done
      ref="$OUT/${carga}_snr${snr}_s${seed}_c0.log"; r0=$(res "$ref"); m0=$(sumry "$ref")
      bad=""
      for k in 1 2 3 4 5; do
        f="$OUT/${carga}_snr${snr}_s${seed}_c$k.log"
        [[ -n $r0 && "$(res "$f")" == "$r0" && -n $m0 && "$(sumry "$f")" == "$m0" ]] || bad="$bad c$k"
        grep -qE 'rejected|failed to start' "$f" && bad="$bad c$k(config recusada)"
      done
      grep -q 'false_positive 0/' "$ref" || bad="$bad c0(false_positive)"
      if [[ -z $bad ]]; then v=IGUAL; nok=$((nok + 1)); else v=FALHA; nfail=$((nfail + 1)); fi
      printf '%-5s %s %-5s s%s | %s%s\n' "$v" "$carga" "$snr" "$seed" "$(sed -E 's/, errors_scrambling.*//' <<<"$r0")" "${bad:+ | divergem:$bad}"
    done
  done
done
chown -R "$USER": "$OUT" 2>/dev/null
echo "IGUAL: $nok  FALHA: $nfail  (cada linha = 5 configurações de par comparadas com seq; logs em $OUT)"
exit $((nfail > 0))
