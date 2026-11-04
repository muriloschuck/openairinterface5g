#!/usr/bin/env bash
# v2_confere.sh — passo 4 do PLANO_V2: a linha n_errors de c0 (seq) da V2 é igual à do B2 na V1, nos pontos em comum?
#   V2: <carga>_snr<SNR>_s<semente>_c0.log; V1: b2_s<semente>_snr<SNR>.log. Arquivo ausente conta como diferente.
set -u
S=/home/murilo/tcc/logs/saidas
V2=${V2:-$(ls -dt $S/v2_2* | head -1)}
ne() { grep -oE 'n_errors \([^)]*\)' "$1" 2>/dev/null; }
confere() { # confere <rótulo> <carga> <dir V1> <sementes> <SNRs>
  local n=0 d=0 seed snr a b
  for snr in $5; do
    for seed in $4; do
      a="$V2/$2_snr${snr}_s${seed}_c0.log"; b="$3/b2_s${seed}_snr${snr}.log"; n=$((n + 1))
      [[ -n $(ne "$a") && "$(ne "$a")" == "$(ne "$b")" ]] || { d=$((d + 1)); echo "  DIF $2 $snr s$seed: V2 '$(ne "$a")' V1 '$(ne "$b")'"; }
    done
  done
  echo "$1: $n comparados, $d diferentes"
}
echo "V2: $V2"
confere "W1 × v1_w1_20261101-173004" W1 $S/v1_w1_20261101-173004 "1 2 3 4 5" "0 3 5.2 5.4 5.6"
confere "W3 × v1_w3r_20261101-181908" W3 $S/v1_w3r_20261101-181908 "1 2 3 4 5" "20.6 20.8 21"
confere "W3 × v1_w3_20261101-173752" W3 $S/v1_w3_20261101-173752 "1 2" "20 30"
