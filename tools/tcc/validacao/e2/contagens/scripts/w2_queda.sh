#!/usr/bin/env bash
# w2_queda.sh — W2 (MCS 16, 273 PRB): onde fica a queda da curva e quantos CBs há por burst.
#   B2 (build, valores padrão), semente 1, 200 trials por SNR. Prepara a escolha dos SNRs de W2 na V2.
set -u
B=/home/murilo/tcc/fork/openairinterface5g/build
SNRS=${SNRS:-"8 9 10 10.5 11 11.5 12 12.5 13 14"}
OUT=/home/murilo/tcc/logs/saidas/w2_queda_$(date +%Y%m%d-%H%M%S)
mkdir -p "$OUT"; cd $B || exit 1
AAL=(--loader.ldpc.shlibpath $B --loader.ldpc.shlibversion _aal --nrLDPC_coding_aal.dpdk_dev baseband_oai_sw --nrLDPC_coding_aal.dpdk_core_list 0-1)
for snr in $SNRS; do
  f=$OUT/b2_s1_snr$snr.log
  sudo OAI_RNGSEED=1 taskset -c 0-3 ./nr_ulsim -n 200 -m 16 -r 273 -R 273 -s $snr -S $snr "${AAL[@]}" >"$f" 2>&1
  ne=$(grep -oE 'n_errors \([^)]*\)' "$f"); fp=$(grep -oE 'false_positive [0-9/]+' "$f")
  read -r calls ops <<<"$(sed -nE 's/.*summary: DEC ([0-9]+) calls \/ ([0-9]+) ops.*/\1 \2/p' "$f")"
  cbs=$( [[ -n ${calls:-} && $calls -gt 0 ]] && echo $((ops / calls)) || echo "?")
  printf '%-5s | %s | %s | CBs por burst: %s\n' "$snr" "$ne" "$fp" "$cbs"
done
grep -h 'MCS:\|TBS' "$OUT"/b2_s1_snr${SNRS%% *}.log | head -3
chown -R "$USER": "$OUT" 2>/dev/null
echo "logs em $OUT"
