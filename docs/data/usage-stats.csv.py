from databricks import sql
import os
import pandas as pd
import io

connection = sql.connect(
    server_hostname="dbc-7a98b378-1bdb.cloud.databricks.com",
    http_path="/sql/1.0/warehouses/85017c9e664c11fc",
    access_token=os.environ["DATABRICKS_TOKEN"],
)

cursor = connection.cursor()

cursor.execute("""
CREATE OR REPLACE TEMPORARY VIEW vllm_usage_view AS
SELECT get_json_object(message, "$.uuid") as uuid,
       get_json_object(request_metadata, "$.cf-connecting-ip") as ip,
       get_json_object(request_metadata, "$.cf-ipcountry") as country,
       get_json_object(request_metadata, "$.cf-ipcity") as city,
       get_json_object(request_metadata, "$.cf-region") as region,
       CASE
         WHEN get_json_object(message, "$.gpu_type") LIKE '%A100%' OR get_json_object(message, "$.gpu_type") LIKE '%A800%' THEN 'NVIDIA A100'
         WHEN get_json_object(message, "$.gpu_type") LIKE '%H100%' OR get_json_object(message, "$.gpu_type") LIKE '%H800%' THEN 'NVIDIA H100'
         WHEN get_json_object(message, "$.gpu_type") LIKE '%V100%' THEN 'NVIDIA V100'
         WHEN get_json_object(message, "$.gpu_type") LIKE '%L40%' THEN 'NVIDIA L40'
         ELSE get_json_object(message, "$.gpu_type")
       END AS gpu_type,
       get_json_object(message, "$.model_architecture") as model_architecture,
       get_json_object(message, "$.tensor_parallel_size") as tensor_parallel_size,
       get_json_object(message, "$.provider") as provider,
       get_json_object(message, "$.source") as source,
       get_json_object(message, "$.vllm_version") as vllm_version,
       get_json_object(message, "$.context") as context,
       to_date(timestamp_micros(CAST(CAST(get_json_object(message, "$.log_time") AS BIGINT)/1000 AS BIGINT))) as starting_time,
       to_date(timestamp_micros(CAST(latest_log_time/1000 AS BIGINT))) as ending_time,
       (latest_log_time - CAST(get_json_object(message, "$.log_time") AS BIGINT)) / (1e9*60*60) as usage_hour,
       (get_json_object(message, "$.tensor_parallel_size") * (latest_log_time - CAST(get_json_object(message, "$.log_time") AS BIGINT)) / (1e9*60*60)) as gpu_hour
FROM `vllm`.`usage_stats_wide_table`
WHERE
  get_json_object(message, "$.source") != "ci-test" AND
  latest_log_time IS NOT NULL AND
  (latest_log_time - CAST(get_json_object(message, "$.log_time") AS BIGINT)) / (1e9*60*60) > 1
  """)
cursor.fetchall()

cursor.execute("""
WITH last_90_days AS
(
  SELECT date_sub(current_date(), d) AS day_stamp
  FROM (SELECT posexplode(sequence(1, 90)) AS (pos, d))
),
day_exploded AS
(
SELECT *
FROM last_90_days
  JOIN  vllm_usage_view
WHERE last_90_days.day_stamp <= vllm_usage_view.ending_time
  AND  last_90_days.day_stamp >= vllm_usage_view.starting_time
ORDER BY day_stamp
)

SELECT day_stamp, gpu_type, model_architecture, count(*) as num_instances
FROM day_exploded
GROUP BY day_stamp, gpu_type, model_architecture
HAVING count(*) > 1000
""")

df = cursor.fetchall_arrow().to_pandas()
buff = io.StringIO()
df.to_csv(buff, index=False)
buff.seek(0)
print(buff.getvalue())

cursor.close()
connection.close()
