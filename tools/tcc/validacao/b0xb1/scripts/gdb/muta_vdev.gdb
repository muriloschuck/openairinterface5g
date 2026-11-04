# Controle negativo: sabota SÓ a função de entrada do vdev (libldpc_aal.so), limitando o decodificador
# a 1 iteração. Se a configuração passa pelo vdev, a BLER tem que piorar; se não passa, nada muda.
set pagination off
set confirm off
set breakpoint pending on
set print thread-events off
break oai_sw_enqueue_ldpc_dec
commands
  silent
  set $i = 0
  while $i < nb_ops
    set var ops[$i]->ldpc_dec.iter_max = 1
    set $i = $i + 1
  end
  continue
end
catch syscall exit_group
commands
  info breakpoints
  continue
end
run
