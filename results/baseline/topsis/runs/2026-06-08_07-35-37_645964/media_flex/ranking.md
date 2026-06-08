# TOPSIS Ranking - Media-Flex (eMBB)

- source_json: `/app/results/storage/baseline/nsga2_low_congestion.json`
- throughput_min: 60.0
- latency_max: 10.0
- cost_max: 200.0
- energy_max: 100.0
- criterion_type: ['max', 'min', 'min', 'min']
- weights: [0.5, 0.2, 0.2, 0.1]
- fallback_to_all_offers: False

 rank  offer_id  topsis_score  throughput  latency       cost    energy  feasible
    1         3      0.953776  595.227105 0.040665  34.478183  9.700573      True
    2         1      0.823392  543.781891 0.044549  68.579362  0.585581      True
    3         6      0.584374  420.881959 0.057717  72.886756 27.077253      True
    4         5      0.529545  420.881959 0.057717 127.870517  0.585581      True
    5         4      0.442807  420.881959 0.057717  95.887270 79.410438      True
    6         2      0.405990  230.971317 0.106260  44.824930  0.585581      True
