# Ambiente da validação

**Código validado:** `80983882e22f34e758e5fd4c830060cc6dbd48f9` (branch `tcc/aal-sw`, "fixes", 01/11/2026 18:14:36).

Entre `cfee4c20b4` (base `develop`) e `80983882e2`, só mudam `openair1/PHY/CODING/nrLDPC_coding/nrLDPC_coding_aal/` e `openair1/SIMULATION/NR_PHY/ulsim.c`. O decodificador (`openair1/PHY/CODING/nrLDPC_decoder/`), o `openair3/ocp-gtpu/gtp_itf.cpp` e os outros `CMakeLists.txt` são os mesmos em todos os commits.

## Versão do código de cada pasta de dados

Os commits e as situações abaixo vêm da verificação de 04/11/2026, feita com reconstrução das árvores a partir dos commits e dos patches registrados.

| Pasta | Commit | Situação | O que mudou / afeta a medição? |
|---|---|---|---|
| `b0xb1/dados/20261101-172001` | `d512b6c75c` + correções não commitadas | código equivalente | difere do `80983882e2` só no comentário de licença do `bbdev_oai_sw.c` |
| `b0xb1/dados/prova_caminhos_20261104-024229` | `80983882e2` | 8098388 | B1 = binário `build/b1/` (só o comentário de licença) |
| `e1/contagens/dados/v1_w1_20261101-173004` | `d512b6c75c` + correções | código equivalente | só o comentário de licença |
| `e1/contagens/dados/v1_w3_20261101-173752` | `d512b6c75c` + correções | código equivalente | só o comentário de licença |
| `e1/contagens/dados/v1_w3r_20261101-181908` | `80983882e2` | 8098388 | B1 = binário `build/b1/` (só o comentário de licença) |
| `e1/tempo/dados/e1_tempo_20261102-174826` | `80983882e2` | 8098388 | B1 = binário `build/b1/` (só o comentário de licença) |
| `e2/contagens/dados/w2_queda_20261101-193242` | `80983882e2` | 8098388 | — |
| `e2/contagens/dados/v2_20261101-194211` | `80983882e2` | 8098388 | — |
| `e2/concorrencia/dados/e2_concorrencia_20261102-132244` | `80983882e2` | 8098388 | — |
| `e2/tempo/dados/e2_tempo_20261102-163741` | `80983882e2` | 8098388 | — |
| `e2/tempo/dados/e2_tempo_20261113-003929` | `a944849c52` (código igual ao `80983882e2`: `diff --stat` vazio em `openair1`, `common` e `executables`) | 8098388 | mesmos binários de `build/`; medida em 13/11/2026, após reboot, com kernel `7.0.0-42-generic` e hugepages realocadas |
| `e2/saturacao/dados/e2_saturacao_20261103-215854` | `80983882e2` | 8098388 | — |
| `tsan/dados/tsan_20261102-140909` | `80983882e2` | 8098388 | `build_tsan/` |
| `tsan/dados/tsan_20261102-141629` | `80983882e2` | 8098388 | `build_tsan/` |
| `tsan/dados/sched_20261102-141828` | `80983882e2` | 8098388 | — |
| `e3/dados/e3_20261102-111743` | `80983882e2` | 8098388 | — |
| `e3/dados/primeira_execucao/e3_20261102-111203` | `80983882e2` | 8098388 | — |
| `ambiente_tempo/dados/amb_ruido_antes_20261102-161834` | `80983882e2` | 8098388 | B1 = binário `build/b1/` (só o comentário de licença) |

As execuções a partir de 01/11 às 18:19 conferiram, no passo 0, `rev-parse` = `80983882e2` e `git status --porcelain -- openair1` = 0, e o cabeçalho dos scripts grava `HEAD=`.

## Binários

| Build | Pasta | Configuração | Compilado em | Origem |
|---|---|---|---|---|
| B0 e B2 | `build/` | `ENABLE_LDPC_AAL=ON`, `ENABLE_LDPC_AAL_EXT=ON`, `ENABLE_TESTS=ON`, `RelWithDebInfo` | `libldpc_aal.so` 01/11 18:13:26; `nr_ulsim` 01/11 17:18:47; `libldpc.so` 26/10 22:52 | `libldpc_aal.so` com o conteúdo final do `80983882e2`; `nr_ulsim` e `libldpc.so` de fontes idênticas às do `80983882e2` |
| B1 | `build/b1/` | `ENABLE_LDPC_AAL_EXT=OFF` | 01/11 17:18:10 (cópia de `build/` após o build com a extensão OFF) | `d512b6c75c` + correções: equivalente ao `80983882e2` a menos do comentário de licença do `bbdev_oai_sw.c` (não recompilado após a troca de licença) |
| TSan | `build_tsan/` | `SANITIZE_THREAD=ON`, `ENABLE_LDPC_AAL=ON`, `ENABLE_LDPC_AAL_EXT=ON`, `ENABLE_TESTS=ON`, `ENABLE_PHYSIM_TESTS=ON`, `RelWithDebInfo` | 02/11 13:56 | `80983882e2` sem mudanças |

No B0, o `nr_ulsim` carrega `libldpc.so` (`--loader.ldpc.shlibpath build`). No B1 e no B2, o adaptador carrega `libldpc_aal.so` (`--loader.ldpc.shlibversion _aal --nrLDPC_coding_aal.dpdk_dev baseband_oai_sw --nrLDPC_coding_aal.dpdk_core_list 0-1`), e a LPU carrega, por `dlopen`, o `libldpc.so` da mesma pasta.

## Máquina e versões

Valores lidos com `lscpu`, `uname -r`, `pkg-config --modversion libdpdk`, `bpftrace --version`, `gcc --version`, `gdb --version` e `/sys/devices/system/cpu/`, e conferidos no `amb_info.sh` de 02/11 (`registros/2026-11-02.md`, 16:11:36).

| Item | Valor |
|---|---|
| CPU | Intel Core i5-8300H @ 2,30 GHz; 4 núcleos, 8 threads; pares de hyperthread 0-4, 1-5, 2-6, 3-7; 800 a 4000 MHz |
| Frequência | driver `intel_pstate`, governor `powersave` nas 8 CPUs, `energy_performance_preference` = `balance_performance`, turbo ligado (`no_turbo=0`); frequência livre durante as medições (decisão do passo 6, `ambiente_tempo/`) |
| Energia | na tomada (`power_supply/*/online` = 1 nos passos 0 das medições de tempo) |
| Kernel | `7.0.0-38-generic` (a máquina não reiniciou entre as medições: 10 dias ligada em 02/11, 12 em 03/11); `7.0.0-42-generic` na execução de 15 rodadas do `e2/tempo/` (13/11/2026, após reboot) |
| DPDK | 24.11.2 (`librte_bbdev.so.25`) |
| bpftrace | v0.25.0 |
| gcc | 15.2.0 (Ubuntu 15.2.0-16ubuntu1) |
| gdb | 17.1 (Ubuntu 17.1-2ubuntu1) |
| Python / matplotlib | 3.14.4 / 3.10.7 (só para as análises em `analise/`) |
| Hugepages | 2 MB, 2 GB alocados (`dpdk-hugepages.py -p 2M --setup 2G`) |
| Afinidade | lcores DPDK 0-1 (thread principal na CPU 0); pool da LPU com 16 threads nas CPUs 2 a 7, `SCHED_RR` prioridade 97 |
