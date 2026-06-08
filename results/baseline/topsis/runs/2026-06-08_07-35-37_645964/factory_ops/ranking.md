# TOPSIS Ranking - Factory-Ops (URLLC)

- source_json: `/app/results/storage/baseline/nsga2_low_congestion.json`
- throughput_min: 5.0
- latency_max: 2.0
- cost_max: 200.0
- energy_max: 100.0
- criterion_type: ['max', 'min', 'min', 'min']
- weights: [0.2, 0.5, 0.2, 0.1]
- fallback_to_all_offers: False

 rank  offer_id  topsis_score  throughput  latency       cost    energy  feasible
    1         3      0.951955  590.384229 0.012301  34.393636  4.555847      True
    2         5      0.804954  407.625568 0.017885  59.387088  0.980931      True
    3         6      0.742883  595.574619 0.012192  84.501497 21.210340      True
    4         4      0.728682  407.625568 0.017885 109.063515  0.980931      True
    5         2      0.728163  407.625568 0.017885 109.374618  0.980931      True
    6         1      0.263537  161.208076 0.046140  34.393636  4.555847      True
