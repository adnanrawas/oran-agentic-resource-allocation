# TOPSIS Ranking - Media-Flex (eMBB)

- source_json: `/app/results/storage/baseline/nsga2_low_congestion.json`
- throughput_min: 60.0
- latency_max: 10.0
- cost_max: 200.0
- energy_max: 100.0
- criterion_type: ['max', 'min', 'min', 'min']
- weights: [1, 1, 1, 1]
- fallback_to_all_offers: False

 rank  offer_id  topsis_score  throughput  latency       cost    energy  feasible
    1         4      0.924075  595.227105 0.040665  34.478183  9.700573      True
    2         1      0.859107  543.781891 0.044549  68.579362  0.585581      True
    3        12      0.789686  543.781891 0.044549  90.099056  0.585581      True
    4         5      0.785615  543.781891 0.044549  91.450593  0.585581      True
    5        13      0.679969  420.881959 0.057717  72.886756 27.077253      True
    6         9      0.661820  420.881959 0.057717 127.870517  0.585581      True
    7         2      0.641470  230.971317 0.106260  44.824930  0.585581      True
    8        10      0.375014  543.781891 0.044549  79.781523 92.770674      True
    9         6      0.334570  420.881959 0.057717  95.887270 79.410438      True
