#!/usr/bin/env bash
# v1_b1b2.sh — V1 (CARGA=W1 ou W3): B1 (build/b1, sem a extensão) × B2 (build, extensão com valores padrão), mesmo adaptador.
#   Mesma semente → mesmo payload e ruído; critério: linha n_errors/false_positive/errors_scrambling idêntica.
#   Rodar como usuário; pede sudo (DPDK).  SEEDS, TRIALS e SNRS podem ser trocados por variável de ambiente.
set -u
B=/home/murilo/tcc/fork/openairinterface5g/build
CARGA=${CARGA:-W3}
case $CARGA in
  W1) MOD=(-m 9 -r 106 -R 106); DEF_SEEDS="1 2 3 4 5"; DEF_TRIALS=1000; DEF_SNRS="0 1 2 3 4 4.6 4.8 5.0 5.2 5.4 5.6 5.8 6.0 7 8" ;;
  W3) MOD=(-m 27 -r 273 -R 273); DEF_SEEDS="1 2"; DEF_TRIALS=200; DEF_SNRS="16 17 17.5 18 18.5 19 19.5 20 21 22 30" ;;
  *) echo "CARGA deve ser W1 ou W3"; exit 2 ;;
esac
SEEDS=${SEEDS:-$DEF_SEEDS}
TRIALS=${TRIALS:-$DEF_TRIALS}
SNRS=${SNRS:-$DEF_SNRS}
OUT=${OUT:-/home/murilo/tcc/logs/saidas/v1_${CARGA,,}_$(date +%Y%m%d-%H%M%S)}
W=(-n $TRIALS "${MOD[@]}")
AAL=(--loader.ldpc.shlibversion _aal --nrLDPC_coding_aal.dpdk_dev baseband_oai_sw --nrLDPC_coding_aal.dpdk_core_list 0-1)
mkdir -p "$OUT"; cd $B || exit 1
echo "# $(date '+%F %T') v1_b1b2.sh CARGA=$CARGA SEEDS='$SEEDS' TRIALS=$TRIALS SNRS='$SNRS' -> $OUT"
res() { grep -oE 'n_errors \([^)]*\).*errors_scrambling \([^)]*\)' "$1"; }
nok=0; nfail=0
for seed in $SEEDS; do
  for snr in $SNRS; do
    sudo OAI_RNGSEED=$seed taskset -c 0-3 ./nr_ulsim "${W[@]}" -s $snr -S $snr --loader.ldpc.shlibpath $B/b1 "${AAL[@]}" >"$OUT/b1_s${seed}_snr${snr}.log" 2>&1
    sudo OAI_RNGSEED=$seed taskset -c 0-3 ./nr_ulsim "${W[@]}" -s $snr -S $snr --loader.ldpc.shlibpath $B "${AAL[@]}" >"$OUT/b2_s${seed}_snr${snr}.log" 2>&1
    r1=$(res "$OUT/b1_s${seed}_snr${snr}.log"); r2=$(res "$OUT/b2_s${seed}_snr${snr}.log")
    # evidence of which library each run used: B1 loads build/b1, B2 prints the workers line (extension present)
    p1=$(grep -cE '(carregados de|loaded from) .*/b1/libldpc.so' "$OUT/b1_s${seed}_snr${snr}.log"); x1=$(grep -cE '(workers|threads), CPUs' "$OUT/b1_s${seed}_snr${snr}.log")
    x2=$(grep -cE '(workers|threads), CPUs' "$OUT/b2_s${seed}_snr${snr}.log")
    if [[ -n $r1 && "$r1" == "$r2" && $p1 == 1 && $x1 == 0 && $x2 == 1 ]]; then v=IGUAL; nok=$((nok+1)); else v=FALHA; nfail=$((nfail+1)); fi
    printf '%-5s s%s %s | %s\n' "$v" "$seed" "$snr" "$(sed -E 's/errors_scrambling.*//' <<<"$r1")"
    [[ $v == FALHA ]] && printf '      B2: %s\n      libs: b1=%s ext_b1=%s ext_b2=%s\n' "$r2" "$p1" "$x1" "$x2"
  done
done
chown -R "$USER": "$OUT" 2>/dev/null
echo "IGUAL: $nok  FALHA: $nfail  (logs em $OUT)"
exit $(( nfail > 0 ))
