CREATE TABLE oran_metrics (
    id SERIAL PRIMARY KEY,
    timestamp DOUBLE PRECISION,
    num_users INTEGER,
    slicing_enabled BOOLEAN,
    slice_prb INTEGER,
    dl_mcs FLOAT,
    tx_brate_dl FLOAT,
    dl_cqi FLOAT,
    rx_brate_ul FLOAT,
    sum_requested_prbs FLOAT,
    sum_granted_prbs FLOAT
);

COPY oran_metrics(
    timestamp, num_users, slicing_enabled, slice_prb,
    dl_mcs, tx_brate_dl, dl_cqi, rx_brate_ul,
    sum_requested_prbs, sum_granted_prbs
)
FROM '/docker-entrypoint-initdb.d/dataset/ColO-RAN.csv'
DELIMITER ','
CSV HEADER;