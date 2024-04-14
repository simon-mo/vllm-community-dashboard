#!/bin/bash

# Run the BigQuery query and output the results to stdout in JSON format
bq query --nouse_legacy_sql --format=prettyjson --max_rows=10000  <<EOF
SELECT
  TIMESTAMP_TRUNC(timestamp, DAY) AS day,
  --country_code,
  file.version,
  COUNT(*) AS count_
FROM
  bigquery-public-data.pypi.file_downloads
WHERE
  project = "vllm" AND
  timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 60 DAY)
GROUP BY
  day,
  --country_code,
  file.version
EOF
