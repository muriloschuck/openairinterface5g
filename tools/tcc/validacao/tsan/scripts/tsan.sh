#!/usr/bin/env bash
# tsan.sh — verificação com ThreadSanitizer (passo 5 da 4.6). Primeiro um controle positivo (programa com corrida
#   conhecida, que o TSan tem de acusar); depois execuções curtas do nr_ulsim do build_tsan (OAI compilado com
#   SANITIZE_THREAD=ON) nas configurações com várias tarefas, incluindo uma com HARQ (W3 a 20,8 dB) e uma com trocas
#   de configuração em runtime. tsan_conta.py classifica os relatórios pelo código das pilhas.
#   Rodar como usuário; pede sudo (DPDK). EXECS e N podem ser trocados por variável de ambiente.
set -u
BT=/home/murilo/tcc/fork/openairinterface5g/build_tsan
SC=/home/murilo/tcc/logs/scripts
N=${N:-100}
EXECS=${EXECS:-"W2:c3:30 W3:c4:30 W3:c6:30 W3:c3:20.8 W3:troca:30"}
declare -A CFG=([c3]=oai_sw.mode=par,oai_sw.workers=3,oai_sw.batch=1
                [c4]=oai_sw.mode=par,oai_sw.workers=3,oai_sw.batch=2
                [c6]=oai_sw.mode=par,oai_sw.workers=16,oai_sw.batch=1
                [troca]=oai_sw.mode=seq)
OUT=${OUT:-/home/murilo/tcc/logs/saidas/tsan_$(date +%Y%m%d-%H%M%S)}
mkdir -p "$OUT"
ARCH=$(uname -m)
AAL=(--loader.ldpc.shlibpath $BT --loader.ldpc.shlibversion _aal --nrLDPC_coding_aal.dpdk_dev baseband_oai_sw --nrLDPC_coding_aal.dpdk_core_list 0-1)
echo "# $(date '+%F %T') tsan.sh HEAD=$(git -C $BT/.. rev-parse --short HEAD) N=$N EXECS='$EXECS' -> $OUT"

echo "== controle positivo"
cat > "$OUT/corrida.c" <<'C'
#include <pthread.h>
int x;
static void *f(void *a) { for (int i = 0; i < 100000; i++) x++; return a; }
int main(void) { pthread_t t1, t2; pthread_create(&t1, 0, f, 0); pthread_create(&t2, 0, f, 0);
                 pthread_join(t1, 0); pthread_join(t2, 0); return 0; }
C
gcc -fsanitize=thread -g -O1 "$OUT/corrida.c" -o "$OUT/corrida" -lpthread || exit 1
setarch "$ARCH" -R "$OUT/corrida" 2>"$OUT/corrida.tsan" >/dev/null
echo "controle positivo: $(grep -c 'WARNING: ThreadSanitizer: data race' "$OUT/corrida.tsan") relatório(s) de corrida"

sudo -v || exit 1
cd $BT || exit 1
for e in $EXECS; do
  IFS=: read -r carga c snr <<<"$e"
  case $carga in
    W2) MOD=(-m 16 -r 273 -R 273) ;;
    W3) MOD=(-m 27 -r 273 -R 273) ;;
  esac
  nome="${carga}_${c}_snr${snr}"; lf="$OUT/$nome.log"; n=$N; [[ $c == troca ]] && n=$((N * 3))
  TS="halt_on_error=0 report_signal_unsafe=0 history_size=4 log_path=$OUT/$nome.tsan"
  if [[ $c == troca ]]; then
    python3 $SC/tsan_trocas.py 20 0.5 >"$OUT/$nome.trocas" 2>&1 &
    CL=$!
  fi
  sudo env OAI_RNGSEED=1 LD_LIBRARY_PATH=$BT TSAN_OPTIONS="$TS" setarch "$ARCH" -R ./nr_ulsim -n $n "${MOD[@]}" -s $snr -S $snr "${AAL[@]}" \
    --nrLDPC_coding_aal.compute "${CFG[$c]}" >"$lf" 2>&1
  [[ $c == troca ]] && { wait $CL; cat "$OUT/$nome.trocas"; }
  sudo chown -R "$USER": "$OUT" 2>/dev/null
  echo "$nome: $(grep -oE 'n_errors \([^)]*\)' "$lf") $(grep -oE 'false_positive [0-9]+/[0-9]+' "$lf") | $(grep -oE 'summary: DEC [0-9]+ calls / [0-9]+ ops' "$lf")"
  echo "$nome: $(python3 $SC/tsan_conta.py "$OUT/$nome".tsan.* 2>/dev/null | head -1)"
done
echo "== total"
python3 $SC/tsan_conta.py "$OUT"/*_snr*.tsan.* 2>/dev/null
echo "# logs em $OUT"
