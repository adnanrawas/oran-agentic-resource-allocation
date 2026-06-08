# TOPSIS Ranking - IoT-Sense (mMTC)

- source_json: `/app/results/storage/baseline/nsga2_low_congestion.json`
- throughput_min: 20.0
- latency_max: 10.0
- cost_max: 50.0
- energy_max: 100.0
- criterion_type: ['max', 'min', 'min', 'min']
- weights: [0.2, 0.2, 0.3, 0.3]
- fallback_to_all_offers: False

 rank  offer_id  topsis_score  throughput  latency      cost    energy  feasible
    1         4      0.699273  312.088437 0.154050 10.385556  5.785675      True
    2         2      0.579799  278.869124 0.172433  1.928151 37.548477      True
    3         1      0.463730  430.241775 0.111695 18.048296 27.036874      True
    4         3      0.399634   60.930885 0.794350  8.978549 19.783154      True
