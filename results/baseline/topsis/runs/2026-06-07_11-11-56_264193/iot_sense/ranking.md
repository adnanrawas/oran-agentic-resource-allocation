# TOPSIS Ranking - IoT-Sense (mMTC)

- source_json: `/app/results/storage/baseline/nsga2_result.json`
- throughput_min: 20.0
- latency_max: 10.0
- cost_max: 50.0
- energy_max: 100.0
- criterion_type: ['max', 'min', 'min', 'min']
- weights: [1, 1, 1, 1]
- fallback_to_all_offers: False

 rank  offer_id  topsis_score  throughput  latency     cost    energy  feasible
    1         2      0.739094  372.242504 0.129228 1.230034 35.389501      True
    2         6      0.575548   97.027309 0.498874 0.740648 13.861224      True
    3         5      0.575548   97.027309 0.498874 0.740648 13.861224      True
    4         3      0.515259  152.942682 0.315510 9.243894  6.814949      True
    5         1      0.455163   74.380493 0.652460 4.406503 16.671492      True
    6         4      0.036589   46.839526 1.042991 8.569538 53.277280      True
