---
toc: false
sql:
    usage_stats: ./data/usage-stats.csv
---

# Usage Data

Currently showing very high level summary of the usage data we collected to guide model and hardware optimizations. The Y-axis is the number of vLLM processes running on a given day.

## By GPU Type
```sql id=usage_stats_by_gpu_type
select day_stamp, gpu_type, sum(num_instances) as num_instances
from usage_stats
where num_instances > 500
group by day_stamp, gpu_type
order by day_stamp, gpu_type
```

```js
display(
  resize((width) =>
    Plot.plot({
      y: {grid: true},
      marginLeft: 50,
      width,
      color: {legend: true},
      marks: [
        Plot.rectY(usage_stats_by_gpu_type, {x: "day_stamp", y: "num_instances", interval: "day", fill: "gpu_type", tip: true}),
        Plot.ruleY([0])
      ],
    })
  ))
```

## By Model Architecture

```sql id=usage_stats_by_model_architecture
select day_stamp, model_architecture, sum(num_instances) as num_instances
from usage_stats
where num_instances > 500
group by day_stamp, model_architecture
order by day_stamp, model_architecture
```

```js
display(
  resize((width) =>
    Plot.plot({
      y: {grid: true},
      marginLeft: 50,
      width,
      color: {legend: true},
      marks: [
        Plot.rectY(usage_stats_by_model_architecture, {x: "day_stamp", y: "num_instances", interval: "day", fill: "model_architecture", tip: true}),
        Plot.ruleY([0])
      ]
    })
  ))
```

## By Usage Context

```sql id=usage_stats_by_usage_context
select day_stamp, context, sum(num_instances) as num_instances
from usage_stats
where num_instances > 500
group by day_stamp, context
order by day_stamp, context
```

```js
display(
  resize((width) =>
    Plot.plot({
      y: {grid: true},
      marginLeft: 50,
      width,
      color: {legend: true},
      marks: [
        Plot.rectY(usage_stats_by_usage_context, {x: "day_stamp", y: "num_instances", interval: "day", fill: "context", tip: true}),
        Plot.ruleY([0])
      ]
    })
  ))
```