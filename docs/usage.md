---
toc: false
sql:
    usage_stats: ./data/usage-stats/usage-stats.csv
---

# Usage Data

Currently showing very high level summary of the usage data we collected to guide model and hardware optimizations. The Y-axis is the number of vLLM processes running on a given day.

## By GPU Type

```sql id=usage_stats_by_gpu_type
WITH filtered_usage AS (
  SELECT *
  FROM usage_stats
),
ranked_usage AS (
    SELECT
        gpu_type,
        SUM(total_gpu_hours) / 30 AS total_hours,
        RANK() OVER (ORDER BY SUM(total_gpu_hours) / 30 DESC) AS rank
    FROM
        filtered_usage
    GROUP BY
        gpu_type
),
threshold AS (
    SELECT MIN(total_hours) AS threshold
    FROM (
        SELECT total_hours
        FROM ranked_usage
        ORDER BY total_hours DESC
        LIMIT 10
    ) AS top_10
)
SELECT
    day_stamp,
    gpu_type,
    sum(total_gpu_hours) as total_gpu_hours
FROM
    filtered_usage
WHERE
    total_gpu_hours >= (SELECT threshold FROM threshold)
GROUP BY
    day_stamp, gpu_type
ORDER BY
    day_stamp, gpu_type
```

```js
display(
  resize((width) =>
    Plot.plot({
      y: {grid: true},
      marginLeft: 80,
      width,
      color: {legend: true},
      marks: [
        Plot.rectY(usage_stats_by_gpu_type, {x: "day_stamp", y: "total_gpu_hours", interval: "day", fill: "gpu_type", tip: true}),
        Plot.ruleY([0])
      ],
    })
  ))
```

## By Model Architecture (with TP)

```sql id=usage_stats_by_model_architecture
WITH filtered_usage AS (
  SELECT *
  FROM usage_stats
),
ranked_usage AS (
    SELECT
        model_architecture_tp,
        SUM(total_gpu_hours) / 30 AS total_hours,
        RANK() OVER (ORDER BY SUM(total_gpu_hours) / 30 DESC) AS rank
    FROM
        filtered_usage
    GROUP BY
        model_architecture_tp
),
threshold AS (
    SELECT MIN(total_hours) AS threshold
    FROM (
        SELECT total_hours
        FROM ranked_usage
        ORDER BY total_hours DESC
        LIMIT 20
    ) AS top_10
)
SELECT
    day_stamp,
    model_architecture_tp as model,
    sum(total_gpu_hours) as total_gpu_hours
FROM
    filtered_usage
WHERE
    total_gpu_hours >= (SELECT threshold FROM threshold)
GROUP BY
    day_stamp, model_architecture_tp
ORDER BY
    day_stamp, model_architecture_tp
```

```js
display(
  resize((width) =>
    Plot.plot({
      y: {grid: true},
      marginLeft: 80,
      width,
      color: {legend: true},
      marks: [
        Plot.rectY(usage_stats_by_model_architecture, {x: "day_stamp", y: "total_gpu_hours", interval: "day", fill: "model", tip: true}),
        Plot.ruleY([0])
      ]
    })
  ))
```

## By Usage Context

```sql id=usage_stats_by_usage_context
SELECT day_stamp, context, sum(total_gpu_hours) as total_gpu_hours
FROM usage_stats
GROUP BY day_stamp, context
ORDER BY day_stamp, context
```

```js
display(
  resize((width) =>
    Plot.plot({
      y: {grid: true},
      marginLeft: 80,
      width,
      color: {legend: true},
      marks: [
        Plot.rectY(usage_stats_by_usage_context, {x: "day_stamp", y: "total_gpu_hours", interval: "day", fill: "context", tip: true}),
        Plot.ruleY([0])
      ]
    })
  ))
``` 