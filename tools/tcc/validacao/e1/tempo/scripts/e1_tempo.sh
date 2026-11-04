#!/usr/bin/env bash
# e1_tempo.sh — E1, tempo (passo 8 da 4.6, V6). Para cada rodada, roda B1 e B2 com os valores padrão uma vez cada, em
#   ordem rotacionada a cada rodada, W3 a 30 dB, N trials, semente 1, com -P, e extrai "ULSCH total decoding time"
#   (média por trial, us). Durante cada execução, amostra a frequência das 8 CPUs a cada 1 s.
#   Configurações: B1 (build/b1); B1bis (a mesma, outro rótulo: controle A/A); B2 (build/, sem --compute: valores
#   padrão); B2seq (build/, --compute mode=seq: liga com o seq do passo 7).
#   Grava $OUT/tempos.csv e $OUT/freq.csv. Rodar como usuário; pede sudo (DPDK).
set -u
B=/home/murilo/tcc/fork/openairinterface5g/build
RODADAS=${RODADAS:-5}
N=${N:-500}
OUT=${OUT:-/home/murilo/tcc/logs/saidas/e1_tempo_$(date +%Y%m%d-%H%M%S)}
mkdir -p "$OUT"
COMUM=(-n $N -m 27 -r 273 -R 273 -s 30 -S 30 -P --loader.ldpc.shlibversion _aal
       --nrLDPC_coding_aal.dpdk_dev baseband_oai_sw --nrLDPC_coding_aal.dpdk_core_list 0-1)
CFGS=(B1 B2 B1bis B2seq)
extra() { case $1 in B1|B1bis) echo "--loader.ldpc.shlibpath $B/b1" ;;
                     B2)       echo "--loader.ldpc.shlibpath $B" ;;
                     B2seq)    echo "--loader.ldpc.shlibpath $B --nrLDPC_coding_aal.compute oai_sw.mode=seq" ;; esac; }
NC=${#CFGS[@]}
echo "rodada,ordem,config,decod_us,n_errors,summary" > "$OUT/tempos.csv"
echo "rodada,config,amostra,cpu,khz" > "$OUT/freq.csv"
echo "# $(date '+%F %T') e1_tempo.sh RODADAS=$RODADAS N=$N configs=$NC HEAD=$(git -C $B/.. rev-parse --short HEAD) -> $OUT"
sudo -v || exit 1
cd $B || exit 1
for r in $(seq 1 $RODADAS); do
  ini=$(( (r - 1) % NC ))
  for i in $(seq 0 $((NC - 1))); do
    c=${CFGS[$(( (ini + i) % NC ))]}; lf="$OUT/r${r}_${c}.log"
    ( s=0; while sleep 1; do s=$((s + 1)); for f in /sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_cur_freq; do
        cpu=${f#/sys/devices/system/cpu/cpu}; echo "$r,$c,$s,${cpu%%/*},$(cat $f)"; done; done ) >> "$OUT/freq.csv" &
    AM=$!
    # shellcheck disable=SC2046
    sudo OAI_RNGSEED=1 ./nr_ulsim "${COMUM[@]}" $(extra $c) >"$lf" 2>&1
    kill $AM 2>/dev/null; wait $AM 2>/dev/null
    t=$(grep -oE 'ULSCH total decoding time +[0-9.]+ us' "$lf" | grep -oE '[0-9.]+ us' | grep -oE '[0-9.]+')
    ne=$(grep -oE 'n_errors \([^)]*\)' "$lf"); sm=$(grep -oE 'DEC [0-9]+ calls / [0-9]+ ops' "$lf")
    grep -qE 'rejected|failed to start' "$lf" && ne="$ne CONFIG_RECUSADA"
    echo "$r,$i,$c,${t:-},\"$ne\",\"$sm\"" >> "$OUT/tempos.csv"
    printf 'rodada %d %d %-6s decod=%-8s %s %s\n' "$r" "$i" "$c" "${t:-?}" "$ne" "$sm"
  done
done
sudo chown -R "$USER": "$OUT" 2>/dev/null
echo "# tempos em $OUT/tempos.csv; frequências em $OUT/freq.csv"
