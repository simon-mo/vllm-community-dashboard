---
toc: false
---

# CI Benchmark

<!-- commit,commit_url,build_datetime,Average Latency,10% Percentile Latency,25% Percentile Latency,50% Percentile Latency,75% Percentile Latency,90% Percentile Latency,Throughput,Token Throughput,Successful Requests,Benchmark Duration,Total Input Tokens,Total Generated Tokens,Request Throughput,Input Token Throughput,Output Token Throughput,Mean TTFT,Median TTFT,P99 TTFT,Mean TPOT,Median TPOT,P99 TPOT -->

<!-- commit,commit_url,build_datetime,metric,value -->

```js
const commitData = await FileAttachment(
  "./data/vllm-commits-last-30-days.json"
).json();
const commitShaToValues = commitData.reduce((acc, d) => {
  acc[d.sha] = d;
  return acc;
}, {});

const ciData = (await FileAttachment("./data/ci-perf-benchmark.csv").csv()).map(
  (d) => {
    d["commit_message"] =
      commitShaToValues[d["commit"]]?.message.split("\n")[0];
    d["build_datetime"] = new Date(d["build_datetime"]);
    d["value"] = parseFloat(d["value"]);
    return d;
  }
).sort((a, b) => a.build_datetime - b.build_datetime);
```

## Plots

```js
function createSelector(metricsSubset, defaultMetric) {
  return Inputs.radio(metricsSubset, { label: "Metric", value: defaultMetric });
}

function makePlot(subsetData, { title } = {}) {
  return Plot.plot({
    title: title,
    y: { grid: true },
    width: 1200,
    marks: [
      Plot.dot(subsetData, {
        x: "build_datetime",
        y: "value",
        z: "metric",
        fill: "orange",
        fillOpacity: 0.5,
      }),
      Plot.tip(
        subsetData,
        Plot.pointer({
          x: "build_datetime",
          y: "value",
          title: (d) => [d.commit_message, d.metric, d.value].join("\n\n"),
        })
      ),
      Plot.lineY(
        subsetData,
        Plot.windowY(12, {
          x: "build_datetime",
          y: "value",
          z: "metric",
          stroke: "DarkTurquoise",
        })
      ),
    ],
    legend: { title: "Metric" },
  });
}
```

### Latency Benchmark

```js
const latencyMetrics = [
  "10% Percentile Latency",
  "25% Percentile Latency",
  "50% Percentile Latency",
  "75% Percentile Latency",
  "90% Percentile Latency",
];

let metricSelected = view(
  createSelector(latencyMetrics, "50% Percentile Latency")
);
```

```js
let subsetData = ciData.filter((d) => d.metric === metricSelected);
display(makePlot(subsetData, { title: metricSelected }));
```

### Throughput Benchmark

```js
const throughputMetrics = ["Throughput", "Token Throughput"];

const throughputSelected = view(
  createSelector(throughputMetrics, "Throughput")
);
```

```js
const throughputSubsetData = ciData.filter(
  (d) => d.metric === throughputSelected
);
display(makePlot(throughputSubsetData, { title: throughputSelected }));
```

### Serving Benchmark (on ShareGPT)

```js
const servingMetrics = [
  "Successful Requests",
  "Benchmark Duration",
  "Total Input Tokens",
  "Total Generated Tokens",
  "Request Throughput",
  "Input Token Throughput",
  "Output Token Throughput",
  "Mean TTFT",
  "Median TTFT",
  "P99 TTFT",
  "Mean TPOT",
  "Median TPOT",
  "P99 TPOT",
];

const servingSelected = view(
  Inputs.checkbox(servingMetrics, {
    label: "Metric",
    value: ["Request Throughput", "Median TTFT", "Median TPOT"],
  })
);
```

```js
for (let metric of servingSelected) {
  display(
    makePlot(
      ciData.filter((d) => d.metric === metric),
      { title: metric }
    )
  );
}
```

## Full Data

```js
const search = view(
  Inputs.search(ciData, { placeholder: "Search commit here.." })
);
```

```js
const messageToUrl = search.reduce((acc, d) => {
  acc[d.commit_message] = d.commit_url;
  return acc;
}, {});

// convert this tall table to a wide table by pivoting the metric column
const wideDataMap = ciData.reduce((acc, d) => {
  if (!acc[d.commit_message]) {
    acc[d.commit_message] = { commit_message: d.commit_message, build_datetime: d.build_datetime};
  }
  acc[d.commit_message][d.metric] = d.value;
  return acc;
}, {});
const wideDataArray = Object.values(wideDataMap);

display(
  Inputs.table(wideDataArray, {
    // columns: ["commit_message", "build_datetime", "metric", "value"],
    width: {
      commit_message: 600,
    },
    format: {
      commit_message: (d) => htl.html`<a href="${messageToUrl[d]}">${d}</a>`,
    },
    sort: "build_datetime",
    reverse: true,
  })
);
```
