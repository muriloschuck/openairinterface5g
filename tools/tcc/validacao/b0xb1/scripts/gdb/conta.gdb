# Conta quem chama o decodificador/codificador LDPC, sem alterar nada.
set pagination off
set confirm off
set breakpoint pending on
set print thread-events off
# 1ª chamada de cada: mostra a pilha completa (quem chamou)
break LDPCdecoder
commands
  silent
  if $bpnum_dec_shown == 0
    printf "\n=== PILHA da 1a chamada a LDPCdecoder (thread %d) ===\n", $_thread
    bt 12
    info symbol $pc
    set $bpnum_dec_shown = 1
  end
  continue
end
break LDPCencoder
commands
  silent
  if $bpnum_enc_shown == 0
    printf "\n=== PILHA da 1a chamada a LDPCencoder (thread %d) ===\n", $_thread
    bt 12
    set $bpnum_enc_shown = 1
  end
  continue
end
# Funções que só existem no caminho AAL/vdev (libldpc_aal.so)
break oai_sw_enqueue_ldpc_dec
commands
  silent
  continue
end
break oai_sw_enqueue_ldpc_enc
commands
  silent
  continue
end
set $bpnum_dec_shown = 0
set $bpnum_enc_shown = 0
catch syscall exit_group
commands
  printf "\n=== BIBLIOTECAS LDPC/DPDK carregadas no processo ===\n"
  info sharedlibrary ldpc
  info sharedlibrary rte_bbdev
  printf "\n=== CONTAGENS (coluna 'breakpoint already hit N times') ===\n"
  info breakpoints
  continue
end
run
