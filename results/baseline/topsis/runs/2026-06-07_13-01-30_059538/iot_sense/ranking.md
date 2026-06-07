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
    1        13      0.779077  312.088437 0.154050 10.385556  5.785675      True
    2         9      0.709070  305.168520 0.157549 16.309427  0.431308      True
    3        10      0.681897  305.168520 0.157549 18.389517  0.431308      True
    4        12      0.663066  229.102806 0.209972 18.389517  0.431308      True
    5         6      0.581294  305.168520 0.157549 19.785896 16.938845      True
    6         1      0.551888  430.241775 0.111695 18.048296 27.036874      True
    7         2      0.550530  278.869124 0.172433  1.928151 37.548477      True
    8         4      0.489434   60.930885 0.794350  8.978549 19.783154      True
    9         5      0.218501   34.492482 1.412382  8.880408 43.929302      True
