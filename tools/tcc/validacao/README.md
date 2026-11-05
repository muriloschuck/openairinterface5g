# Validação do protótipo AAL (TCC): scripts e dados crus

Esta pasta reúne os scripts e os dados crus da validação do adaptador AAL com a LPU de software `baseband_oai_sw` e a extensão computacional. Ela inclui também as análises que geram cada tabela e cada gráfico do relatório. O código validado é o commit `80983882e2` (`80983882e22f34e758e5fd4c830060cc6dbd48f9`, branch `tcc/aal-sw`). A versão do código de cada pasta de dados está em `AMBIENTE.md`.

Em cada experimento:
- `dados/<nome original>/` guarda a saída crua da execução, com o nome que aparece nos registros diários;
- `scripts/` guarda os scripts que geraram os dados;
- `analise/` guarda as tabelas e os gráficos derivados, com os scripts que os geram;
- `SHA256SUMS` guarda o hash de todos os arquivos de `dados/`, `scripts/` e `analise/` (conferir com `sha256sum -c SHA256SUMS` dentro do experimento).

Os registros diários (`registros/AAAA-MM-DD.md`) trazem cada comando com a saída completa. Neles, as entradas aparecem como `### AAAA-MM-DD hh:mm:ss — <passo>`. Os builds são três: B0 é o OAI nativo, B1 é o AAL com `baseband_oai_sw` sem a extensão (`build/b1/`) e B2 é o AAL com a extensão (`build/`).

## Experimentos

| Pasta | O que mede | Validação | Seção | Dados | Scripts | Comando e entrada do registro |
|---|---|---|---|---|---|---|
| `b0xb1/` | B0 × B1: contagens `n_errors`/`errors_scrambling` iguais em W1 (5 sementes × 15 SNRs, 1000 trials); prova de caminhos com gdb (pilhas, bibliotecas, contagens por breakpoint, controle negativo) | ambiente (B1 decodifica como o OAI nativo) | 5.1 | `20261101-172001/`, `prova_caminhos_20261104-024229/` | `prova_caminhos.sh`, `gdb/conta.gdb`, `gdb/muta_vdev.gdb`, `gdb/pilhas.sh`; varredura: `../ambiente.sh` e `../compara.py` | `sudo BUILD=…/build/b1 ../tools/tcc/ambiente.sh` (`registros/2026-11-01.md`, 17:19:59, "correções B2 passo 5.1"); `sudo ~/tcc/logs/scripts/prova_caminhos.sh` (`registros/2026-11-04.md`, 02:42:27, "Prova caminhos 8098388 passo 2") |
| `e1/contagens/` | B1 × B2 (extensão com valores padrão): linha `n_errors … errors_scrambling` idêntica, W1 e W3 | V1 | 5.2 | `v1_w1_20261101-173004/`, `v1_w3_20261101-173752/`, `v1_w3r_20261101-181908/` | `v1_b1b2.sh`, `v1_w3_reforco.sh` | `CARGA=W1 v1_b1b2.sh` (`2026-11-01.md`, 17:30:04); `CARGA=W3 v1_b1b2.sh` (17:37:52); `v1_w3_reforco.sh` (18:19:08) |
| `e1/tempo/` | custo da extensão com valores padrão: B2 × B1, A/A B1bis × B1, B2seq × B2 (W3 30 dB, 5 rodadas, N=500) | V6 | 5.7 | `e1_tempo_20261102-174826/` | `e1_tempo.sh`, `e1_tempo_estat.py` | `e1_tempo.sh` (`2026-11-02.md`, 17:48:26, "E1 tempo") |
| `e2/contagens/` | `seq` × `par` (c1 a c5: workers 1/2/3, batch 1/2/64): mesma saída e mesmo resumo da LPU, W1/W2/W3; queda da curva W2 | V2 | 5.3 | `v2_20261101-194211/`, `w2_queda_20261101-193242/` | `v2.sh`, `v2_confere.sh`, `v2_extras.sh`, `w2_queda.sh` | `v2.sh` (`2026-11-01.md`, 19:42:11, "V2 completa"); `w2_queda.sh` (19:32:42) |
| `e2/concorrencia/` | decodificações simultâneas de `LDPCdecoder` (uprobes bpftrace) e duração das chamadas | V2 (concorrência real) | 5.3 | `e2_concorrencia_20261102-132244/` | `e2_concorrencia.sh`, `e2_conta.py`, `e2_duracao.py` | `e2_concorrencia.sh` (`2026-11-02.md`, 13:22:44, "E2 concorrência"); `e2_duracao.py …/*.probe` (14:28:13) |
| `e2/tempo/` | tempo de decodificação de 26 configurações do B2 (W3 30 dB, 5 rodadas, N=500) | V4 | 5.5 | `e2_tempo_20261102-163741/` | `e2_tempo.sh`, `e2_tempo_estat.py` | `e2_tempo.sh` (`2026-11-02.md`, 16:37:41, "E2 tempo") |
| `e2/saturacao/` | por que `w16b1` é mais rápido que `w6b1`: CPUs, concorrência, partida das threads e duração das chamadas por burst (bpftrace) | questão em aberto da V4 | 5.5 | `e2_saturacao_20261103-215854/` | `e2_saturacao.sh`, `e2_saturacao_conta.py`, `e2s_diag_bursts.py`, `e2s_complemento.py` | `e2_saturacao.sh` (`2026-11-03.md`, 21:58:54, "E2 saturação"); análises às 21:59:46, 22:00:06 e 22:02:40 |
| `tsan/` | ThreadSanitizer no B2 (`build_tsan/`), com controle positivo `corrida.c`; classe de escalonamento das threads do pool | V2 (ausência de corridas no nosso código) | 5.3 | `tsan_20261102-140909/` (sem a `W3_troca`), `tsan_20261102-141629/` (a troca), `sched_20261102-141828/` | `tsan.sh`, `tsan_conta.py`, `tsan_trocas.py`, `tsan_sched.sh`, `corrida.c` | `tsan.sh` (`2026-11-02.md`, 14:09:09, "TSan"); `EXECS='W3:troca:30' tsan.sh` (14:16:29); `tsan_sched.sh` (14:18:28) |
| `e3/` | contrato da AALI-C com a aplicação em execução (30 itens) e 40 trocas de configuração em runtime, com a saída comparada à referência | V3, V5 | 5.4, 5.6 | `e3_20261104-215128/` (a execução com registro de mensagens, `mensagens.jsonl` e `e3_mensagens.md`); `e3_20261102-111743/` (a execução de 02/11, antes do registro); `primeira_execucao/e3_20261102-111203/` (item 20 em falha, citada como desvio) | `e3.sh`, `e3_roteiro.py` (com `--registro`), `e3_roteiro.py.orig`; análise: `analise/e3_mensagens.py` | `e3.sh` (`2026-11-04.md`, 21:51:28, "E3 com registro de mensagens"); a de 02/11: `e3.sh` (`2026-11-02.md`, 11:17:43, "E3 (repetição com espera do 1º burst)"); a 1ª execução às 11:12:03 |
| `ambiente_tempo/` | ruído de medição do tempo (B1, B2seq, B2par3; 5 rodadas, N=500), frequência livre | preparação do tempo | 5.0 | `amb_ruido_antes_20261102-161834/` | `amb_info.sh`, `amb_ruido.sh`, `amb_estat.py` | `FASE=antes RODADAS=5 amb_ruido.sh` (`2026-11-02.md`, 16:18:34, "Ambiente ruído antes") |

`comum/` traz o `logcmd.sh`, que registra cada comando no registro do dia, e o `graf_comum.py`, que faz a leitura da linha `n_errors` e define o estilo dos gráficos de BLER.

## Resultados do relatório

Os comandos rodam a partir desta pasta (`tools/tcc/validacao/`), só leem `dados/` e não precisam de sudo. Os gráficos precisam do matplotlib; sem ele, saem só os CSVs.

| Seção | Resultado | De onde vem | Script | Comando para gerar de novo |
|---|---|---|---|---|
| 5.1 | BLER e contagens B0 = B1 (75 pares IGUAL) | `b0xb1/dados/20261101-172001/resumo.csv` e `relatorio.md` | `../compara.py` | `cp -a b0xb1/dados/20261101-172001 /tmp/ && python3 ../compara.py /tmp/20261101-172001` (o `compara.py` grava na pasta que recebe); saída de referência em `b0xb1/analise/compara.txt` e `b0xb1/analise/compara/` |
| 5.1 | tabela "B0 e B1 executam caminhos diferentes" | `b0xb1/dados/prova_caminhos_20261104-024229/` | `prova_caminhos.sh`, `gdb/pilhas.sh` | resumo em `b0xb1/analise/prova_caminhos_resumo.txt` (as 4 conferências do `prova_caminhos.sh`, refeitas sobre `dados/`) |
| 5.2 | contagens da V1 e gráficos de BLER B1 × B2 (W1, W3) | `e1/contagens/analise/v1_w1_bler.csv`, `v1_w3_bler.csv`, `v1_w*_por_semente.csv`, `v1_w1_bler.png`, `v1_w3_bler.png` | `e1/contagens/analise/v1_bler.py` | `cd e1/contagens/analise && python3 v1_bler.py` |
| 5.3 | contagens da V2 e gráficos de BLER seq × par (W1, W2, W3) | `e2/contagens/analise/v2_bler.csv`, `v2_por_grupo.csv`, `v2_w1_bler.png`, `v2_w2_bler.png`, `v2_w3_bler.png` | `e2/contagens/analise/v2_bler.py` | `cd e2/contagens/analise && python3 v2_bler.py` |
| 5.3 | concorrência por execução (máximo de abertas, sobreposição) | `e2/concorrencia/analise/e2_conta.txt` | `e2_conta.py` | `for e in W3_c0 W3_c1 W3_c3 W3_c5 W3_c6 W1_c0 W1_c3; do echo "$e $(python3 e2/concorrencia/scripts/e2_conta.py e2/concorrencia/dados/e2_concorrencia_20261102-132244/$e.probe)"; done` |
| 5.3 | duração das chamadas a `LDPCdecoder` | `e2/concorrencia/analise/e2_duracao.txt` | `e2_duracao.py` | `python3 e2/concorrencia/scripts/e2_duracao.py e2/concorrencia/dados/e2_concorrencia_20261102-132244/*.probe` |
| 5.3 | ThreadSanitizer: relatórios por classe (0 em "nosso", "adaptador" e "decodificador") | `tsan/analise/tsan_conta.txt` | `tsan_conta.py` | `python3 tsan/scripts/tsan_conta.py tsan/dados/tsan_20261102-140909/*_snr*.tsan.*` (e o mesmo para `tsan_20261102-141629/`) |
| 5.3 | trocas durante o TSan | `tsan/analise/tsan_trocas.txt` (cópia de `tsan_20261102-141629/W3_troca_snr30.trocas`) | `tsan_trocas.py` (cliente ao vivo, roda dentro do `tsan.sh`) | — (saída da execução) |
| 5.3 | classe de escalonamento do pool (RR, prioridade 97) | `tsan/dados/sched_20261102-141828/threads.txt` | `tsan_sched.sh` | — (saída da execução) |
| 5.4, 5.6 | contrato (30 itens, `35 OK, 0 FALHA`), latência das trocas e invariância da saída | `e3/dados/e3_20261104-215128/roteiro.txt`, `trocas.csv`; `e3/analise/e3_resumo_e3_20261104-215128.txt`; a execução de 02/11 em `e3/dados/e3_20261102-111743/` e `e3/analise/e3_resumo.txt` | `e3.sh`, `e3_roteiro.py` | — (o resumo do `e3.sh` só existe no registro; os `e3_resumo*.txt` são trechos de `registros/2026-11-04.md`, 21:51:28, e de `registros/2026-11-02.md`, 11:17:43) |
| 5.4, 5.6 | troca de mensagens da AALI-C: cada pedido e cada resposta, com o tempo de ida e volta e o veredito de cada item | `e3/analise/e3_mensagens.md` (de `e3/dados/e3_20261104-215128/mensagens.jsonl`) | `e3/analise/e3_mensagens.py` | `python3 e3/analise/e3_mensagens.py e3/dados/e3_20261104-215128/mensagens.jsonl e3/analise/e3_mensagens.md` |
| 5.5 | tempo por configuração do B2, IC95, comparações | `e2/tempo/analise/e2_tempo_estat.txt` | `e2_tempo_estat.py` | `python3 e2/tempo/scripts/e2_tempo_estat.py e2/tempo/dados/e2_tempo_20261102-163741/{tempos,freq}.csv` |
| 5.5 | saturação: `w6b1` × `w16b1` (`ate_max` 114,5 e 80,9 µs etc.) | `e2/saturacao/analise/e2_saturacao_conta.txt`, `e2s_diag_bursts.txt`, `e2s_complemento.txt` | `e2_saturacao_conta.py`, `e2s_diag_bursts.py`, `e2s_complemento.py` | `python3 e2/saturacao/scripts/e2_saturacao_conta.py e2/saturacao/dados/e2_saturacao_20261103-215854` (idem para `e2s_complemento.py`; `e2s_diag_bursts.py <pasta> w16b1` e `<pasta> w6b1`) |
| 5.7 | custo B2 × B1 = +0,48%, IC95 [−0,94%, +1,89%] | `e1/tempo/analise/e1_tempo_estat.txt` | `e1_tempo_estat.py` | `python3 e1/tempo/scripts/e1_tempo_estat.py e1/tempo/dados/e1_tempo_20261102-174826/{tempos,freq}.csv` |
| 5.0 | ruído do ambiente (CV por configuração, frequência) | `ambiente_tempo/analise/amb_estat.txt` | `amb_estat.py` | `python3 ambiente_tempo/scripts/amb_estat.py ambiente_tempo/dados/amb_ruido_antes_20261102-161834/tempos.csv --freq ambiente_tempo/dados/amb_ruido_antes_20261102-161834/freq.csv` |

## Notas

- **Caminhos absolutos:** os scripts de execução usam caminhos de `/home/murilo/tcc/logs/` e do fork em `/home/murilo/tcc/fork/openairinterface5g/`, e chamam o `logcmd.sh`. Eles foram copiados sem alteração. Para repetir uma medição em outra máquina, ajuste as variáveis do começo de cada script.
- **`ambiente.sh` (em `tools/tcc/`):** para o B0 × B1, precisa de `BUILD=…/build/b1`. O padrão `build/` hoje é o B2.
- **`tsan/dados/tsan_20261102-140909/`:** não contém a execução `W3_troca` (`.log`, `.trocas`, `.tsan.<pid>`), que teve *traceback* no `tsan_trocas.py` e foi repetida em `tsan_20261102-141629/`. Por isso, o total do `tsan_conta.py` nessa pasta é 4, e não os 5 do registro.
- **Binário `corrida`:** o controle positivo do TSan é compilado pelo `tsan.sh` a partir de `corrida.c`. O binário não foi copiado; o fonte está em `tsan/scripts/corrida.c` e em cada pasta de dados.
- **`e3_roteiro.py.orig`:** é a versão que gerou a primeira execução do E3, em `primeira_execucao/`. O `e3_roteiro.py` acrescenta a espera do 1º burst.
- **Códigos de saída:** os logs do `nr_ulsim` podem ter terminado com `rc=1` sem falha de execução. O simulador devolve 1 quando o seu critério de vazão não é atingido, e as varreduras medem pontos na queda da curva.
- **`.gitignore`:** reativa `*.log` e `*.out`, que o `.gitignore` do OAI ignora, e ignora `__pycache__/`.
