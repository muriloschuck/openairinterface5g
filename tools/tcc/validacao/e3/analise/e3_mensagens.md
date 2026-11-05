# E3: pedidos e respostas da AALI-C

Fonte: `mensagens.jsonl`. 88 pedidos, 35 itens avaliados (35 OK, 0 FALHA). → = pedido enviado pelo cliente; ← = resposta da extensão, com o tempo de ida e volta.

## espera do primeiro burst

```
(3 leituras de getAalLpuComputeStats até a versão 1 ter bursts; a última:)
#3    → getAalLpuComputeStats
      ← {"op":"getAalLpuComputeStats","status":"OK","now_ns":182378338324192,"versions":[{"version":1,"t_applied_ns":182377989929352,"t_first_burst_ns":182378335375141,"bursts":1,"ops":24,"busy_ns":2404279}]}  (137 µs)
```

## estado inicial e limite inicial

```
#4    → getAalLpuComputeCapabilities
      ← {"op":"getAalLpuComputeCapabilities","status":"OK","aal_lpu_handle":"baseband_oai_sw","descriptor_version":1,"params":[{"name":"oai_sw.mode","type":"ENUM","values":["seq","par"],"default":"seq","category":"PARALLELISM","scope":"LPU","description":"seq: code blocks decoded serially; par: code blocks distributed across workers"},{"name":"oai_sw.workers","type":"INT","min":1,"max":16,"step":1,"default":1,"unit":"threads","category":"PARALLELISM","scope":"LPU","description":"number of worker threads used when mode is par"},{"name":"oai_sw.batch","type":"INT","min":1,"max":64,"step":1,"default":1,"unit":"CBs","category":"BATCHING","scope":"LPU","description":"code blocks processed per worker task"}]}  (108 µs)
#5    → setAalAccelConfig limits=/home/murilo/tcc/logs/saidas/e3_20261104-215128/limits_inicial.txt
      ← {"op":"setAalAccelConfig","status":"OK","descriptor_version":2,"version":1,"adjusted":[]}  (123 µs)
```

## itens 1 a 30: contrato da AALI-C (V3)

```
#6    → getAalLpuComputeCapabilities
      ← {"op":"getAalLpuComputeCapabilities","status":"OK","aal_lpu_handle":"baseband_oai_sw","descriptor_version":2,"params":[{"name":"oai_sw.mode","type":"ENUM","values":["seq","par"],"default":"seq","category":"PARALLELISM","scope":"LPU","description":"seq: code blocks decoded serially; par: code blocks distributed across workers"},{"name":"oai_sw.workers","type":"INT","min":1,"max":4,"step":1,"default":1,"unit":"threads","category":"PARALLELISM","scope":"LPU","description":"number of worker threads used when mode is par"},{"name":"oai_sw.batch","type":"INT","min":1,"max":64,"step":1,"default":1,"unit":"CBs","category":"BATCHING","scope":"LPU","description":"code blocks processed per worker task"}]}  (58 µs)
   == item 1: OK — caps: handle baseband_oai_sw, descriptor_version 2, workers 1..4

#7    → getAalLpuComputeConfig
      ← {"op":"getAalLpuComputeConfig","status":"OK","version":1,"t_applied_ns":182377989929352,"values":{"oai_sw.mode":"seq","oai_sw.workers":1,"oai_sw.batch":1}}  (52 µs)
   == item 2: OK — get: versão 1, seq/1/1

#8    → setAalLpuComputeConfig oai_sw.nada=1
      ← {"op":"setAalLpuComputeConfig","status":"UNKNOWN_PARAM","version":1,"param":"oai_sw.nada"}  (48 µs)
   == item 3: OK — set oai_sw.nada=1 -> UNKNOWN_PARAM

#9    → setAalLpuComputeConfig oai_sw.mode=rapido
      ← {"op":"setAalLpuComputeConfig","status":"INVALID_TYPE","version":1,"param":"oai_sw.mode"}  (31 µs)
   == item 4: OK — set oai_sw.mode=rapido -> INVALID_TYPE

#10   → setAalLpuComputeConfig oai_sw.workers=2x
      ← {"op":"setAalLpuComputeConfig","status":"INVALID_TYPE","version":1,"param":"oai_sw.workers"}  (54 µs)
   == item 5: OK — set oai_sw.workers=2x -> INVALID_TYPE

#11   → setAalLpuComputeConfig oai_sw.batch=65
      ← {"op":"setAalLpuComputeConfig","status":"OUT_OF_RANGE","version":1,"param":"oai_sw.batch"}  (31 µs)
   == item 6: OK — set oai_sw.batch=65 -> OUT_OF_RANGE

#12   → setAalLpuComputeConfig oai_sw.batch=0
      ← {"op":"setAalLpuComputeConfig","status":"OUT_OF_RANGE","version":1,"param":"oai_sw.batch"}  (31 µs)
   == item 7: OK — set oai_sw.batch=0 -> OUT_OF_RANGE

#13   → setAalLpuComputeConfig oai_sw.workers=8
      ← {"op":"setAalLpuComputeConfig","status":"LIMIT_EXCEEDED","version":1,"param":"oai_sw.workers"}  (30 µs)
   == item 8: OK — set oai_sw.workers=8 -> LIMIT_EXCEEDED

#14   → setAalLpuComputeConfig
      ← {"op":"setAalLpuComputeConfig","status":"BAD_REQUEST","version":1,"param":""}  (29 µs)
   == item 9: OK — set (vazio) -> BAD_REQUEST

#15   → setAalLpuComputeConfig oai_sw.workers=2 oai_sw.workers=3
      ← {"op":"setAalLpuComputeConfig","status":"BAD_REQUEST","version":1,"param":"oai_sw.workers"}  (30 µs)
   == item 10: OK — set oai_sw.workers=2 oai_sw.workers=3 -> BAD_REQUEST

#16   → setAalLpuComputeConfig expected_version=abc oai_sw.workers=2
      ← {"op":"setAalLpuComputeConfig","status":"BAD_REQUEST","version":1,"param":"expected_version"}  (46 µs)
   == item 11: OK — set expected_version=abc oai_sw.workers=2 -> BAD_REQUEST

#17   → setAalLpuComputeConfig oai_sw.workers
      ← {"op":"setAalLpuComputeConfig","status":"BAD_REQUEST","version":1,"param":"oai_sw.workers"}  (28 µs)
   == item 12: OK — set oai_sw.workers -> BAD_REQUEST

#18   → setAalLpuComputeConfig oai_sw.mode=par oai_sw.workers=8
      ← {"op":"setAalLpuComputeConfig","status":"LIMIT_EXCEEDED","version":1,"param":"oai_sw.workers"}  (32 µs)
   == item 15: OK — set oai_sw.mode=par oai_sw.workers=8 -> LIMIT_EXCEEDED

#19   → setAalLpuComputeConfig expected_version=7 oai_sw.workers=2
      ← {"op":"setAalLpuComputeConfig","status":"VERSION_CONFLICT","version":1,"param":"expected_version"}  (28 µs)
   == item 16: OK — set expected_version=7 oai_sw.workers=2 -> VERSION_CONFLICT

#20   → opInexistente
      ← {"op":"opInexistente","status":"BAD_REQUEST"}  (28 µs)
   == item 13: OK — op desconhecida -> BAD_REQUEST

#21   → getAalLpuComputeCapabilities extra
      ← {"op":"getAalLpuComputeCapabilities","status":"BAD_REQUEST"}  (46 µs)
   == item 14: OK — caps com token extra -> BAD_REQUEST

#22   → getAalLpuComputeConfig
      ← {"op":"getAalLpuComputeConfig","status":"OK","version":1,"t_applied_ns":182377989929352,"values":{"oai_sw.mode":"seq","oai_sw.workers":1,"oai_sw.batch":1}}  (30 µs)
   == item 17: OK — get após erros: versão 1, seq/1/1

#23   → setAalLpuComputeConfig expected_version=1 oai_sw.mode=par oai_sw.workers=3 oai_sw.batch=2
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":2}  (29 µs)
   == item 18: OK — set par/3/2 -> OK, versão 2

#24   → getAalLpuComputeConfig
      ← {"op":"getAalLpuComputeConfig","status":"OK","version":2,"t_applied_ns":182378340189107,"values":{"oai_sw.mode":"par","oai_sw.workers":3,"oai_sw.batch":2}}  (30 µs)
   == item 19: OK — get: versão 2, par/3/2

#25   → getAalLpuComputeStats
      ← {"op":"getAalLpuComputeStats","status":"OK","now_ns":182379340446617,"versions":[{"version":2,"t_applied_ns":182378340189107,"t_first_burst_ns":182378342830620,"bursts":201,"ops":4824,"busy_ns":208794350},{"version":1,"t_applied_ns":182377989929352,"t_first_burst_ns":182378335375141,"bursts":1,"ops":24,"busy_ns":2404279}]}  (129 µs)
#26   → getAalLpuComputeStats
      ← {"op":"getAalLpuComputeStats","status":"OK","now_ns":182379340614234,"versions":[{"version":2,"t_applied_ns":182378340189107,"t_first_burst_ns":182378342830620,"bursts":201,"ops":4824,"busy_ns":208794350},{"version":1,"t_applied_ns":182377989929352,"t_first_burst_ns":182378335375141,"bursts":1,"ops":24,"busy_ns":2404279}]}  (47 µs)
#27   → getAalLpuComputeStats
      ← {"op":"getAalLpuComputeStats","status":"OK","now_ns":182380340836679,"versions":[{"version":2,"t_applied_ns":182378340189107,"t_first_burst_ns":182378342830620,"bursts":403,"ops":9672,"busy_ns":413648215},{"version":1,"t_applied_ns":182377989929352,"t_first_burst_ns":182378335375141,"bursts":1,"ops":24,"busy_ns":2404279}]}  (138 µs)
#28   → getAalLpuComputeStats
      ← {"op":"getAalLpuComputeStats","status":"OK","now_ns":182380341080565,"versions":[{"version":2,"t_applied_ns":182378340189107,"t_first_burst_ns":182378342830620,"bursts":403,"ops":9672,"busy_ns":413648215},{"version":1,"t_applied_ns":182377989929352,"t_first_burst_ns":182378335375141,"bursts":1,"ops":24,"busy_ns":2404279}]}  (69 µs)
   == item 20: OK — stats: v2 201->403, v1 1->1

      (arquivo lim_1_2.txt: 'oai_sw.workers 1 2')
#29   → setAalAccelConfig limits=/home/murilo/tcc/logs/saidas/e3_20261104-215128/lim_1_2.txt
      ← {"op":"setAalAccelConfig","status":"OK","descriptor_version":3,"version":3,"adjusted":["oai_sw.workers"]}  (116 µs)
   == item 21: OK — limits workers 1 2 -> OK, descriptor 3, versão 3, adjusted workers

#30   → getAalLpuComputeConfig
      ← {"op":"getAalLpuComputeConfig","status":"OK","version":3,"t_applied_ns":182380342455183,"values":{"oai_sw.mode":"par","oai_sw.workers":2,"oai_sw.batch":2}}  (75 µs)
   == item 22: OK — get: versão 3, par/2/2

      (arquivo lim_inv23.txt: 'oai_sw.workers 20 30')
#31   → setAalAccelConfig limits=/home/murilo/tcc/logs/saidas/e3_20261104-215128/lim_inv23.txt
      ← {"op":"setAalAccelConfig","status":"BAD_REQUEST"}  (295 µs)
#32   → getAalLpuComputeCapabilities
      ← {"op":"getAalLpuComputeCapabilities","status":"OK","aal_lpu_handle":"baseband_oai_sw","descriptor_version":3,"params":[{"name":"oai_sw.mode","type":"ENUM","values":["seq","par"],"default":"seq","category":"PARALLELISM","scope":"LPU","description":"seq: code blocks decoded serially; par: code blocks distributed across workers"},{"name":"oai_sw.workers","type":"INT","min":1,"max":2,"step":1,"default":1,"unit":"threads","category":"PARALLELISM","scope":"LPU","description":"number of worker threads used when mode is par"},{"name":"oai_sw.batch","type":"INT","min":1,"max":64,"step":1,"default":1,"unit":"CBs","category":"BATCHING","scope":"LPU","description":"code blocks processed per worker task"}]}  (2916 µs)
   == item 23: OK — limits workers 20 30 -> BAD_REQUEST, descriptor fica 3

      (arquivo lim_inv24.txt: 'oai_sw.mode 5 9')
#33   → setAalAccelConfig limits=/home/murilo/tcc/logs/saidas/e3_20261104-215128/lim_inv24.txt
      ← {"op":"setAalAccelConfig","status":"BAD_REQUEST"}  (139 µs)
#34   → getAalLpuComputeCapabilities
      ← {"op":"getAalLpuComputeCapabilities","status":"OK","aal_lpu_handle":"baseband_oai_sw","descriptor_version":3,"params":[{"name":"oai_sw.mode","type":"ENUM","values":["seq","par"],"default":"seq","category":"PARALLELISM","scope":"LPU","description":"seq: code blocks decoded serially; par: code blocks distributed across workers"},{"name":"oai_sw.workers","type":"INT","min":1,"max":2,"step":1,"default":1,"unit":"threads","category":"PARALLELISM","scope":"LPU","description":"number of worker threads used when mode is par"},{"name":"oai_sw.batch","type":"INT","min":1,"max":64,"step":1,"default":1,"unit":"CBs","category":"BATCHING","scope":"LPU","description":"code blocks processed per worker task"}]}  (74 µs)
   == item 24: OK — limits mode 5 9 -> BAD_REQUEST, descriptor fica 3

      (arquivo lim_inv25.txt: 'oai_sw.batch 0 0')
#35   → setAalAccelConfig limits=/home/murilo/tcc/logs/saidas/e3_20261104-215128/lim_inv25.txt
      ← {"op":"setAalAccelConfig","status":"BAD_REQUEST"}  (67 µs)
#36   → getAalLpuComputeCapabilities
      ← {"op":"getAalLpuComputeCapabilities","status":"OK","aal_lpu_handle":"baseband_oai_sw","descriptor_version":3,"params":[{"name":"oai_sw.mode","type":"ENUM","values":["seq","par"],"default":"seq","category":"PARALLELISM","scope":"LPU","description":"seq: code blocks decoded serially; par: code blocks distributed across workers"},{"name":"oai_sw.workers","type":"INT","min":1,"max":2,"step":1,"default":1,"unit":"threads","category":"PARALLELISM","scope":"LPU","description":"number of worker threads used when mode is par"},{"name":"oai_sw.batch","type":"INT","min":1,"max":64,"step":1,"default":1,"unit":"CBs","category":"BATCHING","scope":"LPU","description":"code blocks processed per worker task"}]}  (54 µs)
   == item 25: OK — limits batch 0 0 -> BAD_REQUEST, descriptor fica 3

      (arquivo lim_inv26.txt: 'oai_sw.workers 1')
#37   → setAalAccelConfig limits=/home/murilo/tcc/logs/saidas/e3_20261104-215128/lim_inv26.txt
      ← {"op":"setAalAccelConfig","status":"BAD_REQUEST"}  (107 µs)
#38   → getAalLpuComputeCapabilities
      ← {"op":"getAalLpuComputeCapabilities","status":"OK","aal_lpu_handle":"baseband_oai_sw","descriptor_version":3,"params":[{"name":"oai_sw.mode","type":"ENUM","values":["seq","par"],"default":"seq","category":"PARALLELISM","scope":"LPU","description":"seq: code blocks decoded serially; par: code blocks distributed across workers"},{"name":"oai_sw.workers","type":"INT","min":1,"max":2,"step":1,"default":1,"unit":"threads","category":"PARALLELISM","scope":"LPU","description":"number of worker threads used when mode is par"},{"name":"oai_sw.batch","type":"INT","min":1,"max":64,"step":1,"default":1,"unit":"CBs","category":"BATCHING","scope":"LPU","description":"code blocks processed per worker task"}]}  (54 µs)
   == item 26: OK — limits linha malformada -> BAD_REQUEST, descriptor fica 3

#39   → setAalAccelConfig limits=/nonexistent/v3.txt
      ← {"op":"setAalAccelConfig","status":"BAD_REQUEST"}  (58 µs)
#40   → getAalLpuComputeCapabilities
      ← {"op":"getAalLpuComputeCapabilities","status":"OK","aal_lpu_handle":"baseband_oai_sw","descriptor_version":3,"params":[{"name":"oai_sw.mode","type":"ENUM","values":["seq","par"],"default":"seq","category":"PARALLELISM","scope":"LPU","description":"seq: code blocks decoded serially; par: code blocks distributed across workers"},{"name":"oai_sw.workers","type":"INT","min":1,"max":2,"step":1,"default":1,"unit":"threads","category":"PARALLELISM","scope":"LPU","description":"number of worker threads used when mode is par"},{"name":"oai_sw.batch","type":"INT","min":1,"max":64,"step":1,"default":1,"unit":"CBs","category":"BATCHING","scope":"LPU","description":"code blocks processed per worker task"}]}  (56 µs)
   == item 27: OK — limits arquivo inexistente -> BAD_REQUEST, descriptor fica 3

      (arquivo lim_inv28.txt: 'oai_sw.nada 1 2')
#41   → setAalAccelConfig limits=/home/murilo/tcc/logs/saidas/e3_20261104-215128/lim_inv28.txt
      ← {"op":"setAalAccelConfig","status":"BAD_REQUEST"}  (69 µs)
#42   → getAalLpuComputeCapabilities
      ← {"op":"getAalLpuComputeCapabilities","status":"OK","aal_lpu_handle":"baseband_oai_sw","descriptor_version":3,"params":[{"name":"oai_sw.mode","type":"ENUM","values":["seq","par"],"default":"seq","category":"PARALLELISM","scope":"LPU","description":"seq: code blocks decoded serially; par: code blocks distributed across workers"},{"name":"oai_sw.workers","type":"INT","min":1,"max":2,"step":1,"default":1,"unit":"threads","category":"PARALLELISM","scope":"LPU","description":"number of worker threads used when mode is par"},{"name":"oai_sw.batch","type":"INT","min":1,"max":64,"step":1,"default":1,"unit":"CBs","category":"BATCHING","scope":"LPU","description":"code blocks processed per worker task"}]}  (53 µs)
   == item 28: OK — limits parâmetro desconhecido -> BAD_REQUEST, descriptor fica 3

      (arquivo lim_1_4.txt: 'oai_sw.workers 1 4')
#43   → setAalAccelConfig limits=/home/murilo/tcc/logs/saidas/e3_20261104-215128/lim_1_4.txt
      ← {"op":"setAalAccelConfig","status":"OK","descriptor_version":4,"version":3,"adjusted":[]}  (97 µs)
#44   → getAalLpuComputeConfig
      ← {"op":"getAalLpuComputeConfig","status":"OK","version":3,"t_applied_ns":182380342455183,"values":{"oai_sw.mode":"par","oai_sw.workers":2,"oai_sw.batch":2}}  (46 µs)
   == item 29: OK — limits workers 1 4 -> OK, descriptor 4, adjusted vazio, versão 3

#45   → setAalLpuComputeConfig oai_sw.fo"o=1
      ← {"op":"setAalLpuComputeConfig","status":"UNKNOWN_PARAM","version":3,"param":"oai_sw.fo\"o"}  (47 µs)
      (nota: cliente bruto: 200 pedidos getAalLpuComputeCapabilities numa conexão, fechada sem ler as respostas)
#46   → getAalLpuComputeConfig
      ← {"op":"getAalLpuComputeConfig","status":"OK","version":3,"t_applied_ns":182380342455183,"values":{"oai_sw.mode":"par","oai_sw.workers":2,"oai_sw.batch":2}}  (146 µs)
   == item 30: OK — JSON válido com aspas; processo vivo e respondendo após cliente que fecha sem ler

#47   → getAalLpuComputeConfig
      ← {"op":"getAalLpuComputeConfig","status":"OK","version":3,"t_applied_ns":182380342455183,"values":{"oai_sw.mode":"par","oai_sw.workers":2,"oai_sw.batch":2}}  (48 µs)
```

## alternância: 40 trocas a cada 0.3 s

```
#48   → setAalLpuComputeConfig expected_version=3 oai_sw.mode=seq oai_sw.workers=1 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":4}  (41 µs)
#49   → setAalLpuComputeConfig expected_version=4 oai_sw.mode=par oai_sw.workers=1 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":5}  (126 µs)
#50   → setAalLpuComputeConfig expected_version=5 oai_sw.mode=par oai_sw.workers=2 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":6}  (155 µs)
#51   → setAalLpuComputeConfig expected_version=6 oai_sw.mode=par oai_sw.workers=3 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":7}  (129 µs)
#52   → setAalLpuComputeConfig expected_version=7 oai_sw.mode=par oai_sw.workers=3 oai_sw.batch=2
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":8}  (183 µs)
#53   → setAalLpuComputeConfig expected_version=8 oai_sw.mode=par oai_sw.workers=4 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":9}  (134 µs)
#54   → setAalLpuComputeConfig expected_version=9 oai_sw.mode=par oai_sw.workers=3 oai_sw.batch=64
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":10}  (127 µs)
#55   → setAalLpuComputeConfig expected_version=10 oai_sw.mode=par oai_sw.workers=4 oai_sw.batch=2
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":11}  (128 µs)
#56   → setAalLpuComputeConfig expected_version=11 oai_sw.mode=seq oai_sw.workers=1 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":12}  (132 µs)
#57   → setAalLpuComputeConfig expected_version=12 oai_sw.mode=par oai_sw.workers=1 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":13}  (123 µs)
#58   → setAalLpuComputeConfig expected_version=13 oai_sw.mode=par oai_sw.workers=2 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":14}  (86 µs)
#59   → setAalLpuComputeConfig expected_version=14 oai_sw.mode=par oai_sw.workers=3 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":15}  (131 µs)
#60   → setAalLpuComputeConfig expected_version=15 oai_sw.mode=par oai_sw.workers=3 oai_sw.batch=2
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":16}  (158 µs)
#61   → setAalLpuComputeConfig expected_version=16 oai_sw.mode=par oai_sw.workers=4 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":17}  (129 µs)
#62   → setAalLpuComputeConfig expected_version=17 oai_sw.mode=par oai_sw.workers=3 oai_sw.batch=64
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":18}  (136 µs)
#63   → setAalLpuComputeConfig expected_version=18 oai_sw.mode=par oai_sw.workers=4 oai_sw.batch=2
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":19}  (83 µs)
#64   → setAalLpuComputeConfig expected_version=19 oai_sw.mode=seq oai_sw.workers=1 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":20}  (136 µs)
#65   → setAalLpuComputeConfig expected_version=20 oai_sw.mode=par oai_sw.workers=1 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":21}  (87 µs)
#66   → setAalLpuComputeConfig expected_version=21 oai_sw.mode=par oai_sw.workers=2 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":22}  (152 µs)
#67   → setAalLpuComputeConfig expected_version=22 oai_sw.mode=par oai_sw.workers=3 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":23}  (141 µs)
#68   → setAalLpuComputeConfig expected_version=23 oai_sw.mode=par oai_sw.workers=3 oai_sw.batch=2
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":24}  (121 µs)
#69   → setAalLpuComputeConfig expected_version=24 oai_sw.mode=par oai_sw.workers=4 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":25}  (132 µs)
#70   → setAalLpuComputeConfig expected_version=25 oai_sw.mode=par oai_sw.workers=3 oai_sw.batch=64
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":26}  (128 µs)
#71   → setAalLpuComputeConfig expected_version=26 oai_sw.mode=par oai_sw.workers=4 oai_sw.batch=2
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":27}  (152 µs)
#72   → setAalLpuComputeConfig expected_version=27 oai_sw.mode=seq oai_sw.workers=1 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":28}  (127 µs)
#73   → setAalLpuComputeConfig expected_version=28 oai_sw.mode=par oai_sw.workers=1 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":29}  (81 µs)
#74   → setAalLpuComputeConfig expected_version=29 oai_sw.mode=par oai_sw.workers=2 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":30}  (130 µs)
#75   → setAalLpuComputeConfig expected_version=30 oai_sw.mode=par oai_sw.workers=3 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":31}  (132 µs)
#76   → setAalLpuComputeConfig expected_version=31 oai_sw.mode=par oai_sw.workers=3 oai_sw.batch=2
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":32}  (131 µs)
#77   → setAalLpuComputeConfig expected_version=32 oai_sw.mode=par oai_sw.workers=4 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":33}  (138 µs)
#78   → setAalLpuComputeConfig expected_version=33 oai_sw.mode=par oai_sw.workers=3 oai_sw.batch=64
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":34}  (209 µs)
#79   → setAalLpuComputeConfig expected_version=34 oai_sw.mode=par oai_sw.workers=4 oai_sw.batch=2
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":35}  (123 µs)
#80   → setAalLpuComputeConfig expected_version=35 oai_sw.mode=seq oai_sw.workers=1 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":36}  (162 µs)
#81   → setAalLpuComputeConfig expected_version=36 oai_sw.mode=par oai_sw.workers=1 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":37}  (126 µs)
#82   → setAalLpuComputeConfig expected_version=37 oai_sw.mode=par oai_sw.workers=2 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":38}  (127 µs)
#83   → setAalLpuComputeConfig expected_version=38 oai_sw.mode=par oai_sw.workers=3 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":39}  (115 µs)
#84   → setAalLpuComputeConfig expected_version=39 oai_sw.mode=par oai_sw.workers=3 oai_sw.batch=2
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":40}  (125 µs)
#85   → setAalLpuComputeConfig expected_version=40 oai_sw.mode=par oai_sw.workers=4 oai_sw.batch=1
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":41}  (139 µs)
#86   → setAalLpuComputeConfig expected_version=41 oai_sw.mode=par oai_sw.workers=3 oai_sw.batch=64
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":42}  (108 µs)
#87   → setAalLpuComputeConfig expected_version=42 oai_sw.mode=par oai_sw.workers=4 oai_sw.batch=2
      ← {"op":"setAalLpuComputeConfig","status":"OK","version":43}  (151 µs)
   == item 31: OK — 40 trocas aceitas, versões 4..43 consecutivas

#88   → getAalLpuComputeStats
      ← {"op":"getAalLpuComputeStats","status":"OK","now_ns":182393162614987,"versions":[{"version":43,"t_applied_ns":182392562150906,"t_first_burst_ns":182392566313029,"bursts":123,"ops":2952,"busy_ns":106808188},{"version":42,"t_applied_ns":182392261885133,"t_first_burst_ns":182392265890131,"bursts":49,"ops":1176,"busy_ns":109238116},{"version":41,"t_applied_ns":182391961563348,"t_first_burst_ns":182391965773065,"bursts":62,"ops":1488,"busy_ns":54516011},{"version":40,"t_applied_ns":182391661260300,"t_first_burst_ns":182391663010639,"bursts":61,"ops":1464,"busy_ns":62994341},{"version":39,"t_applied_ns":182391361027044,"t_first_burst_ns":182391365015260,"bursts":60,"ops":1440,"busy_ns":59749814},{"version":38,"t_applied_ns":182391060708102,"t_first_burst_ns":182391062257819,"bursts":58,"ops":1392,"busy_ns":75477054},{"version":37,"t_applied_ns":182390760418127,"t_first_burst_ns":182390761457554,"bursts":49,"ops":1176,"busy_ns":105715694},{"version":36,"t_applied_ns":182390460052801,"t_first_burst_ns":182390464721821,"bursts":51,"ops":1224,"busy_ns":100858421},{"version":35,"t_applied_ns":182390159743288,"t_first_burst_ns":182390161669507,"bursts":62,"ops":1488,"busy_ns":55787244},{"version":34,"t_applied_ns":182389859415788,"t_first_burst_ns":182389864273177,"bursts":49,"ops":1176,"busy_ns":104813871},{"version":33,"t_applied_ns":182389559041286,"t_first_burst_ns":182389559788364,"bursts":63,"ops":1512,"busy_ns":55299585},{"version":32,"t_applied_ns":182389258728784,"t_first_burst_ns":182389259051553,"bursts":59,"ops":1416,"busy_ns":60286746},{"version":31,"t_applied_ns":182388958427152,"t_first_burst_ns":182388959797000,"bursts":60,"ops":1440,"busy_ns":62158878},{"version":30,"t_applied_ns":182388658125216,"t_first_burst_ns":182388662269675,"bursts":56,"ops":1344,"busy_ns":77971281},{"version":29,"t_applied_ns":182388357862341,"t_first_burst_ns":182388359718274,"bursts":50,"ops":1200,"busy_ns":106628422},{"version":28,"t_applied_ns":182388057564001,"t_first_burst_ns":182388059676188,"bursts":51,"ops":1224,"busy_ns":101848686},{"version":27,"t_applied_ns":182387757276006,"t_first_burst_ns":182387761694888,"bursts":61,"ops":1464,"busy_ns":54332653},{"version":26,"t_applied_ns":182387456976792,"t_first_burst_ns":182387458688557,"bursts":50,"ops":1200,"busy_ns":106259733},{"version":25,"t_applied_ns":182387156668032,"t_first_burst_ns":182387157903499,"bursts":62,"ops":1488,"busy_ns":53732327},{"version":24,"t_applied_ns":182386856372607,"t_first_burst_ns":182386860067053,"bursts":60,"ops":1440,"busy_ns":60645442},{"version":23,"t_applied_ns":182386556069770,"t_first_burst_ns":182386558703054,"bursts":61,"ops":1464,"busy_ns":60043228},{"version":22,"t_applied_ns":182386255740050,"t_first_burst_ns":182386260583845,"bursts":57,"ops":1368,"busy_ns":73459517},{"version":21,"t_applied_ns":182385955440609,"t_first_burst_ns":182385956263358,"bursts":50,"ops":1200,"busy_ns":107555458},{"version":20,"t_applied_ns":182385655139322,"t_first_burst_ns":182385659480966,"bursts":50,"ops":1200,"busy_ns":98669260},{"version":19,"t_applied_ns":182385354914815,"t_first_burst_ns":182385355347289,"bursts":61,"ops":1464,"busy_ns":54279715},{"version":18,"t_applied_ns":182385054608466,"t_first_burst_ns":182385057546749,"bursts":48,"ops":1152,"busy_ns":104823737},{"version":17,"t_applied_ns":182384754291975,"t_first_burst_ns":182384757888814,"bursts":62,"ops":1488,"busy_ns":54441518},{"version":16,"t_applied_ns":182384453998101,"t_first_burst_ns":182384457416342,"bursts":61,"ops":1464,"busy_ns":60708376},{"version":15,"t_applied_ns":182384153690153,"t_first_burst_ns":182384154193895,"bursts":61,"ops":1464,"busy_ns":60724870},{"version":14,"t_applied_ns":182383853419843,"t_first_burst_ns":182383856434843,"bursts":57,"ops":1368,"busy_ns":72686410},{"version":13,"t_applied_ns":182383553122598,"t_first_burst_ns":182383553583124,"bursts":50,"ops":1200,"busy_ns":107609948},{"version":12,"t_applied_ns":182383252837306,"t_first_burst_ns":182383254039145,"bursts":51,"ops":1224,"busy_ns":101324428},{"version":11,"t_applied_ns":182382952537762,"t_first_burst_ns":182382954295930,"bursts":62,"ops":1488,"busy_ns":52751497},{"version":10,"t_applied_ns":182382652239553,"t_first_burst_ns":182382656061773,"bursts":49,"ops":1176,"busy_ns":105485776},{"version":9,"t_applied_ns":182382351967123,"t_first_burst_ns":182382352851100,"bursts":63,"ops":1512,"busy_ns":54394325},{"version":8,"t_applied_ns":182382051660404,"t_first_burst_ns":182382055440494,"bursts":60,"ops":1440,"busy_ns":61447897},{"version":7,"t_applied_ns":182381751295106,"t_first_burst_ns":182381753526217,"bursts":61,"ops":1464,"busy_ns":61568277},{"version":6,"t_applied_ns":182381451004617,"t_first_burst_ns":182381454098576,"bursts":57,"ops":1368,"busy_ns":71723817},{"version":5,"t_applied_ns":182381150687830,"t_first_burst_ns":182381155952952,"bursts":45,"ops":1080,"busy_ns":102025571},{"version":4,"t_applied_ns":182380850461569,"t_first_burst_ns":182380851907929,"bursts":52,"ops":1248,"busy_ns":103429035},{"version":3,"t_applied_ns":182380342455183,"t_first_burst_ns":182380351350204,"bursts":94,"ops":2256,"busy_ns":129298269},{"version":2,"t_applied_ns":182378340189107,"t_first_burst_ns":182378342830620,"bursts":404,"ops":9696,"busy_ns":414712785},{"version":1,"t_applied_ns":182377989929352,"t_first_burst_ns":182378335375141,"bursts":1,"ops":24,"busy_ns":2404279}]}  (149 µs)
   == item 32: OK — todas as versões com bursts > 0 e ops = 24 × bursts (sem bursts: [], ops: [])

   == item 33: OK — t0 ≤ t1 ≤ t2 em todas as versões

   == item 34: OK — t1 - t0 medido em todas as trocas, todos abaixo de 50 ms

   == item 35: OK — nr_ulsim ainda rodando ao fim da alternância

```

