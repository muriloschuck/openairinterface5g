#!/usr/bin/env bash
# amb_ruido.sh — passo 6: mede o ruído do tempo de decodificação. Para cada rodada, roda as configurações em ordem
#   intercalada (B1; B2 seq; B2 par w3 b1), W3 a 30 dB, N trials, semente 1, e extrai a linha
#   "ULSCH total decoding time" do nr_ulsim (média por trial, em us). Durante a primeira configuração de cada rodada,
#   amostra a frequência de cada CPU uma vez por segundo. Grava tudo em $OUT/tempos.csv e $OUT/freq.csv.
#   FASE é só um rótulo (antes ou depois de fixar a frequência). Rodar como usuário; pede sudo (DPDK).
set -u
B=/home/murilo/tcc/fork/openairinterface5g/build
FASE=${FASE:?defina FASE=antes ou FASE=depois}
RODADAS=${RODADAS:-10}
N=${N:-500}
OUT=${OUT:-/home/murilo/tcc/logs/saidas/amb_ruido_${FASE}_$(date +%Y%m%d-%H%M%S)}
mkdir -p "$OUT"
COMUM=(-n $N -m 27 -r 273 -R 273 -s 30 -S 30 -P --loader.ldpc.shlibversion _aal --nrLDPC_coding_aal.dpdk_dev baseband_oai_sw --nrLDPC_coding_aal.dpdk_core_list 0-1)
declare -A EXTRA=([B1]="--loader.ldpc.shlibpath $B/b1"
                  [B2seq]="--loader.ldpc.shlibpath $B --nrLDPC_coding_aal.compute oai_sw.mode=seq"
                  [B2par3]="--loader.ldpc.shlibpath $B --nrLDPC_coding_aal.compute oai_sw.mode=par,oai_sw.workers=3,oai_sw.batch=1")
CFGS=(B1 B2seq B2par3)
echo "fase,rodada,config,decod_us,n_errors,summary" > "$OUT/tempos.csv"
echo "fase,rodada,amostra,cpu,khz" > "$OUT/freq.csv"
echo "# $(date '+%F %T') amb_ruido.sh FASE=$FASE RODADAS=$RODADAS N=$N HEAD=$(git -C $B/.. rev-parse --short HEAD) -> $OUT"
sudo -v || exit 1
cd $B || exit 1
for r in $(seq 1 $RODADAS); do
  for k in "${!CFGS[@]}"; do
    c=${CFGS[$k]}; lf="$OUT/r${r}_${c}.log"
    if (( k == 0 )); then
      ( s=0; while sleep 1; do s=$((s + 1)); for f in /sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_cur_freq; do
          cpu=${f#/sys/devices/system/cpu/cpu}; echo "$FASE,$r,$s,${cpu%%/*},$(cat $f)"; done; done ) >> "$OUT/freq.csv" &
      AM=$!
    fi
    # shellcheck disable=SC2086
    sudo OAI_RNGSEED=1 ./nr_ulsim "${COMUM[@]}" ${EXTRA[$c]} >"$lf" 2>&1
    (( k == 0 )) && { kill $AM 2>/dev/null; wait $AM 2>/dev/null; }
    t=$(grep -oE 'ULSCH total decoding time +[0-9.]+ us' "$lf" | grep -oE '[0-9.]+ us' | grep -oE '[0-9.]+')
    ne=$(grep -oE 'n_errors \([^)]*\)' "$lf"); sm=$(grep -oE 'DEC [0-9]+ calls / [0-9]+ ops' "$lf")
    echo "$FASE,$r,$c,${t:-},\"$ne\",\"$sm\"" >> "$OUT/tempos.csv"
    printf 'rodada %2d %-7s decod=%s us  %s  %s\n' "$r" "$c" "${t:-?}" "$ne" "$sm"
  done
done
sudo chown -R "$USER": "$OUT" 2>/dev/null
echo "# tempos em $OUT/tempos.csv; frequências em $OUT/freq.csv"
