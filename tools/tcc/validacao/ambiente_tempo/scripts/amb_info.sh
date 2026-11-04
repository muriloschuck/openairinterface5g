#!/usr/bin/env bash
# amb_info.sh — passo 6 da 4.6: só leitura. Topologia da CPU, frequência e energia, para decidir o ambiente de tempo.
set -u
C=/sys/devices/system/cpu
echo "== modelo"; grep -m1 'model name' /proc/cpuinfo
echo "== lscpu -e"; lscpu -e=CPU,CORE,SOCKET,ONLINE,MAXMHZ,MINMHZ
echo "== irmãos de hyperthread (thread_siblings_list)"; cat $C/cpu*/topology/thread_siblings_list | sort -u
echo "== driver de frequência"; cat $C/cpu0/cpufreq/scaling_driver
echo "== governor por CPU"; cat $C/cpu*/cpufreq/scaling_governor | sort | uniq -c
echo "== energy_performance_preference"; cat $C/cpu*/cpufreq/energy_performance_preference 2>/dev/null | sort | uniq -c || echo "(não existe)"
echo "== turbo"; [[ -e $C/intel_pstate/no_turbo ]] && echo "intel_pstate/no_turbo=$(cat $C/intel_pstate/no_turbo)"; [[ -e $C/cpufreq/boost ]] && echo "cpufreq/boost=$(cat $C/cpufreq/boost)"
echo "== frequências (kHz): base, mín, máx"; for f in base_frequency cpuinfo_min_freq cpuinfo_max_freq; do echo "$f=$(cat $C/cpu0/cpufreq/$f 2>/dev/null || echo '-')"; done
echo "== energia (1 = na tomada)"; cat /sys/class/power_supply/*/online 2>/dev/null || echo "(sem informação)"
echo "== linha de comando do kernel"; cat /proc/cmdline
