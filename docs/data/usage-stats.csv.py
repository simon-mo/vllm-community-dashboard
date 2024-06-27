import os
import io
import logging
import sys
from databricks import sql
import requests

logging.basicConfig(level=logging.DEBUG)

connection = sql.connect(
    server_hostname="dbc-7a98b378-1bdb.cloud.databricks.com",
    http_path="/sql/1.0/warehouses/85017c9e664c11fc",
    access_token=os.environ["DATABRICKS_TOKEN"],
)

model_registry = requests.get(
    "https://raw.githubusercontent.com/vllm-project/vllm/main/vllm/model_executor/models/__init__.py"
).content.decode("utf-8")

lines = model_registry.split("\n")
# find the line starts with _GENERATION_MODELS, then to line starts with _MODELS inclusive
start = [
    i for i, line in enumerate(lines) if line.startswith("_GENERATION_MODELS")
][0]
end = [i for i, line in enumerate(lines) if line.startswith("_MODELS")][0]
model_registry = "\n".join(lines[start:end + 1])
eval(compile(model_registry, "<string>", "exec"))
models = list(_MODELS.keys())
print("Filtering by models:", models, file=sys.stderr)

cursor = connection.cursor()

cursor.execute(f"""
WITH last_30_days AS
(
  SELECT date_sub(current_date(), d) AS day_stamp
  FROM (SELECT posexplode(sequence(1, 30)) AS (pos, d))
),

daily_usage AS
(
SELECT
  gpu_hour / (datediff(ending_time, starting_time) + 1) as gpu_hour_per_day,
  usage_hour / (datediff(ending_time, starting_time) + 1) as usage_hour_per_day,
  concat(model_architecture, "-", tensor_parallel_size) as model_architecture_tp,
  *
FROM
  vllm.vllm_usage_view
WHERE model_architecture IN {tuple(models)}
),

day_exploded AS
(
SELECT *
FROM last_30_days
  JOIN daily_usage
WHERE last_30_days.day_stamp <= daily_usage.ending_time
  AND  last_30_days.day_stamp >= daily_usage.starting_time
ORDER BY day_stamp
)

SELECT day_stamp, gpu_type, model_architecture_tp, context,
       ip LIKE "221.194.167.%" as is_whale,
       -- count(*) as num_instances,
       sum(gpu_hour_per_day) as total_gpu_hours
       -- sum(usage_hour_per_day) as total_usage_hours
FROM day_exploded
GROUP BY day_stamp, gpu_type, model_architecture_tp, context, ip
""")

df = cursor.fetchall_arrow().to_pandas()

buff = io.StringIO()
df.to_csv(buff, index=False)
buff.seek(0)
print(buff.getvalue())

cursor.close()
connection.close()
