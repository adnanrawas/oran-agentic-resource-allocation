# TOPSIS Ranking - Factory-Ops (URLLC)

- source_json: `/app/results/storage/baseline/nsga2_low_congestion.json`
- throughput_min: 5.0
- latency_max: 2.0
- cost_max: 200.0
- energy_max: 100.0
- criterion_type: ['max', 'min', 'min', 'min']
- weights: [1, 1, 1, 1]
- fallback_to_all_offers: False

 rank  offer_id  topsis_score  throughput  latency       cost    energy  feasible
    1        10      0.870710  407.625568 0.017885   4.390466  0.980931      True
    2         4      0.827672  590.384229 0.012301  34.393636  4.555847      True
    3         5      0.793860  590.384229 0.012301  57.675584  2.783499      True
    4         9      0.765316  407.625568 0.017885  59.387088  0.980931      True
    5         6      0.650809  407.625568 0.017885 109.063515  0.980931      True
    6         2      0.650199  407.625568 0.017885 109.374618  0.980931      True
    7        12      0.628628  407.625568 0.017885  66.222893  8.021888      True
    8         1      0.548310  161.208076 0.046140  34.393636  4.555847      True
    9        13      0.401224  595.574619 0.012192  84.501497 21.210340      True
