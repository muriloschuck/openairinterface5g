#!/usr/bin/env bash
# prova_caminhos.sh — prova que B0 e B1 executam caminhos de código diferentes (rodar com sudo).
#   E1  pilha de chamadas da 1ª decodificação/codificação LDPC (gdb, sem alterar nada)
#   E2  bibliotecas LDPC/DPDK carregadas no processo
#   E3  contagem de chamadas por breakpoint (independe dos contadores do próprio vdev)
#   E4  controle negativo: sabotar só o vdev (iter_max=1) muda B1 e não muda B0
#   E0  o gdb não altera o resultado: mesmas contagens com e sem gdb
# B0 carrega build/libldpc.so; B1 carrega build/b1/libldpc_aal.so (extensão OFF), com o mesmo nr_ulsim de build/.
set -u
L=/home/murilo/tcc/logs/logcmd.sh
G=/home/murilo/tcc/logs/scripts/gdb
BUILD=/home/murilo/tcc/fork/openairinterface5g/build
S=${S:-/home/murilo/tcc/logs/saidas/prova_caminhos_$(date +%Y%m%d-%H%M%S)}
mkdir -p "$S"
W="-n 20 -m 9 -r 106 -R 106 -s 5.4 -S 5.4"
B0="--loader.ldpc.shlibpath $BUILD"
B1="--loader.ldpc.shlibpath $BUILD/b1 --loader.ldpc.shlibversion _aal --nrLDPC_coding_aal.dpdk_dev baseband_oai_sw --nrLDPC_coding_aal.dpdk_core_list 0-1"
echo "# $(date '+%F %T') prova_caminhos.sh HEAD=$(git -C $BUILD/.. rev-parse --short HEAD) -> $S"
run() { # run <tag> <prefixo gdb ou vazio> <args da configuração>
  local tag=$1 pre=$2 extra=$3
  $L "Prova caminhos — $tag" "cd $BUILD && OAI_RNGSEED=1 timeout 600 $pre ./nr_ulsim $W $extra > $S/$tag.txt 2>&1; echo rc=\$?"
}
GC="gdb -q -batch -x $G/conta.gdb --args"
GM="gdb -q -batch -x $G/muta_vdev.gdb --args"

run b0_sem_gdb   ""    "$B0"
run b1_sem_gdb   ""    "$B1"
run b0_conta     "$GC" "$B0"
run b1_conta     "$GC" "$B1"
run b0_mutado    "$GM" "$B0"
run b1_mutado    "$GM" "$B1"

$L "Prova caminhos — E0/E4: n_errors de cada execução" "cd $S && grep -H 'n_errors' b0_sem_gdb.txt b1_sem_gdb.txt b0_conta.txt b1_conta.txt b0_mutado.txt b1_mutado.txt"
$L "Prova caminhos — E1: pilhas da 1ª chamada (B0 e B1)" "cd $S && for f in b0_conta b1_conta; do echo \"##### \$f\"; $G/pilhas.sh \$f.txt; done"
$L "Prova caminhos — E2/E3: bibliotecas e contagens" "cd $S && for f in b0_conta b1_conta b0_mutado b1_mutado; do echo \"##### \$f\"; sed -n '/=== BIBLIOTECAS/,/=== CONTAGENS/p' \$f.txt | grep -E 'ldpc|rte_bbdev|No shared'; grep -E '^[0-9]+ +(breakpoint|catchpoint)|already hit|PENDING' \$f.txt; done"
$L "Prova caminhos — contadores do próprio vdev (para cruzar com E3)" "cd $S && grep -H 'OAI_SW\\] summary' *.txt"
chown -R "${SUDO_USER:-$USER}": "$S"
