# TOPSIS Ranking - Media-Flex (eMBB)

- source_json: `/app/results/storage/baseline/nsga2_result.json`
- throughput_min: 60.0
- latency_max: 10.0
- cost_max: 200.0
- energy_max: 100.0
- criterion_type: ['max', 'min', 'min', 'min']
- weights: [1, 1, 1, 1]
- fallback_to_all_offers: False

 rank  offer_id  topsis_score  throughput  latency       cost   energy  feasible
    1         6      0.780128  743.566106 0.032306  28.414100 0.493145      True
    2         3      0.767329  540.806344 0.044433   0.894458 0.493145      True
    3         8      0.767329  540.806344 0.044433   0.894458 0.493145      True
    4         7      0.697186  743.566106 0.032306  48.456733 0.493145      True
    5         5      0.644303  294.988746 0.081545   0.894458 0.493145      True
    6         1      0.500285  579.357278 0.041473  34.394712 3.939422      True
    7         4      0.499780 1096.371554 0.021904 120.965195 0.493145      True
    8         2      0.488452  294.988746 0.081545   6.299905 4.251894      True
