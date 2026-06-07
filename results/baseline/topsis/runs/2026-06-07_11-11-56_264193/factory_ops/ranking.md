# TOPSIS Ranking - Factory-Ops (URLLC)

- source_json: `/app/results/storage/baseline/nsga2_result.json`
- throughput_min: 5.0
- latency_max: 2.0
- cost_max: 200.0
- energy_max: 100.0
- criterion_type: ['max', 'min', 'min', 'min']
- weights: [1, 1, 1, 1]
- fallback_to_all_offers: False

 rank  offer_id  topsis_score  throughput  latency      cost    energy  feasible
    1         5      0.664389  302.420508 0.023838  2.407479  8.433840      True
    2         6      0.659566  324.069279 0.022244  5.339275  8.433840      True
    3         3      0.582239  373.265680 0.019309 15.646736  0.915136      True
    4         1      0.543726  710.477335 0.010139  5.339275 60.152930      True
    5         2      0.452879  334.570062 0.021545  5.339275 53.285052      True
    6         4      0.434697  215.802139 0.033423 22.546288  0.915136      True
