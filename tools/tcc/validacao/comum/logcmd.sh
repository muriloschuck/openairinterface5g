#!/usr/bin/env bash
# logcmd.sh "<passo>" "<comando>" — executa o comando e registra comando + saída no log do dia
LOG=/home/murilo/tcc/logs/$(date +%F).md
step=$1; shift; cmd=$*
{ printf '\n### %s — %s\n\n```bash\n$ %s\n' "$(date '+%F %T')" "$step" "$cmd"; } >>"$LOG"
out=$(bash -c "$cmd" 2>&1); rc=$?
{ printf '%s\n# exit=%d\n```\n' "$out" "$rc"; } >>"$LOG"
printf '%s\n# exit=%d\n' "$out" "$rc"; exit $rc
