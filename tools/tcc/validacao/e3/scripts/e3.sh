#!/usr/bin/env bash
# e3.sh — E3 (passo 3 da 4.6): execução com controle, W3 a 20,8 dB, semente 1, N trials.
#   1) referência: nr_ulsim B2 em seq, sem cliente;
#   2) controle: o mesmo comando, com e3_roteiro.py conectado (contrato da AALI-C + alternância de configurações);
#   3) compara a linha n_errors … errors_scrambling e o [OAI_SW] summary das duas execuções.
#   Rodar como usuário; pede sudo (DPDK).
set -u
B=/home/murilo/tcc/fork/openairinterface5g/build
SC=/home/murilo/tcc/logs/scripts
SOCK=/tmp/aal_ext.sock
N=${N:-3000}; SNR=${SNR:-20.8}; SEED=${SEED:-1}
TROCAS=${TROCAS:-40}; INTERVALO=${INTERVALO:-0.3}
OUT=${OUT:-/home/murilo/tcc/logs/saidas/e3_$(date +%Y%m%d-%H%M%S)}
mkdir -p "$OUT"; L0=$OUT/limits_inicial.txt
echo "oai_sw.workers 1 4" > "$L0"; chmod 644 "$L0"
CMD=(./nr_ulsim -n $N -m 27 -r 273 -R 273 -s $SNR -S $SNR
     --loader.ldpc.shlibpath $B --loader.ldpc.shlibversion _aal
     --nrLDPC_coding_aal.dpdk_dev baseband_oai_sw --nrLDPC_coding_aal.dpdk_core_list 0-1)
res() { grep -oE 'n_errors \([^)]*\).*errors_scrambling \([^)]*\)' "$1"; }
sumry() { grep -oE 'summary: DEC [0-9]+ calls / [0-9]+ ops' "$1"; }
echo "# $(date '+%F %T') e3.sh HEAD=$(git -C $B/.. rev-parse --short HEAD) N=$N SNR=$SNR SEED=$SEED TROCAS=$TROCAS -> $OUT"
[[ -e $SOCK ]] && { echo "socket velho em $SOCK; apague antes (sudo rm $SOCK)"; exit 1; }
sudo -v || exit 1
cd $B || exit 1

echo "== 1. referência (seq, sem cliente)"
sudo OAI_RNGSEED=$SEED "${CMD[@]}" >"$OUT/ref.log" 2>&1
echo "ref: $(res "$OUT/ref.log")"; echo "ref: $(sumry "$OUT/ref.log")"
for i in $(seq 1 20); do [[ -e $SOCK ]] || break; sleep 0.5; done

echo "== 2. controle (roteiro + alternância)"
sudo OAI_RNGSEED=$SEED "${CMD[@]}" >"$OUT/ctl.log" 2>&1 &
for i in $(seq 1 60); do [[ -S $SOCK ]] && break; sleep 0.5; done
[[ -S $SOCK ]] || { echo "socket não apareceu"; tail -20 "$OUT/ctl.log"; exit 1; }
P=$(pgrep -n nr_ulsim)
python3 $SC/e3_roteiro.py --sock $SOCK --pid "$P" --dir "$OUT" --limits0 "$L0" \
  --trocas $TROCAS --intervalo $INTERVALO --cbs 24 | tee "$OUT/roteiro.txt"
rc=${PIPESTATUS[0]}
echo "# esperando o nr_ulsim terminar (pid $P)"
while [[ -d /proc/$P ]]; do sleep 2; done
echo "ctl: $(res "$OUT/ctl.log")"; echo "ctl: $(sumry "$OUT/ctl.log")"

echo "== 3. comparação"
ok=1
[[ -n $(res "$OUT/ref.log") && "$(res "$OUT/ref.log")" == "$(res "$OUT/ctl.log")" ]] && echo "linha de resultado: IGUAL" || { echo "linha de resultado: DIFERENTE"; ok=0; }
[[ -n $(sumry "$OUT/ref.log") && "$(sumry "$OUT/ref.log")" == "$(sumry "$OUT/ctl.log")" ]] && echo "summary: IGUAL" || { echo "summary: DIFERENTE"; ok=0; }
grep -q 'false_positive 0/' "$OUT/ctl.log" && echo "false_positive 0" || { echo "false_positive != 0"; ok=0; }
grep -qE 'rejected|failed to start' "$OUT/ctl.log" && { echo "config recusada no log"; ok=0; }
[[ -e $SOCK ]] && { echo "socket AINDA existe"; ok=0; } || echo "socket removido"
sudo chown -R "$USER": "$OUT" 2>/dev/null
(( rc == 0 && ok == 1 )) && echo "E3: OK" || echo "E3: FALHA (roteiro rc=$rc, comparação ok=$ok)"
(( rc == 0 && ok == 1 ))
