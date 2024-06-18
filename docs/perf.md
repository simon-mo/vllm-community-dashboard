---
toc: false
---

# CI Benchmark


```js

function createSelector(metricsSubset, defaultMetric, labelName = "Test name") {
  return Inputs.radio(metricsSubset, { label: labelName, value: defaultMetric });
}


function makeCombinedPlot(data, { title } = {}) {
  return Plot.plot({
    title: title,
    y: { grid: true },
    width: 1200,
    marks: [
      Plot.dot(data, {
        x: "build_datetime",
        y: "value",
        z: "metric",
        fill: "blue",
        fillOpacity: 0.5,
      }),
      Plot.tip(
        data,
        Plot.pointer({
          x: "build_datetime",
          y: "value",
          title: (d) => [d.commit_message, d.metric, d.value, d.test_name].join("\n\n"),
        })
      ),
      Plot.lineY(
        data,
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



```js
const commitData = await FileAttachment(
  "./data/vllm-commits-last-30-days.json"
).json();
const commitShaToValues = commitData.reduce((acc, d) => {
  acc[d.sha] = d;
  return acc;
}, {});

const ciDataFull = (await FileAttachment("./data/ci-perf-benchmark.csv").csv()).map(
  (d) => {
    d["commit_message"] =
      commitShaToValues[d["commit"]]?.message.split("\n")[0];
    d["build_datetime"] = new Date(d["build_datetime"]);
    d["value"] = parseFloat(d["value"]);
    return d;
  }
).sort((a, b) => a.build_datetime - b.build_datetime);
```


## Hardware

Please select a hardware. All plots down below will only show results of the selected hardware.

```js

const hardware = [
  "A100",
];

const hardwareSelected = view(
  createSelector(hardware, "A100", "Hardware")
)

```


```js
const ciData = ciDataFull.filter((d) => d.GPU.includes(hardwareSelected));
```




## Latency tests


This test suite aims to test vllm's end-to-end latency under a controlled setup.

- Input length: 32 tokens.
- Output length: 128 tokens.
- Batch size: fixed (8).
- Models: llama-3 8B, llama-3 70B, mixtral 8x7B.
- Evaluation metrics: end-to-end latency (mean, median, p99).



```js

const latencyTest = [
  "latency_llama8B_tp1",
  "latency_llama70B_tp4",
  "latency_mixtral8x7B_tp2",
];

const latencyTestSelected = view(
  createSelector(latencyTest, "latency_llama8B_tp1")
);


const latencyMetrics = [
  "Mean latency (ms)",
  "Median latency (ms)",
  "P99 latency (ms)",
];

const latencyMetricSelected = view(
  Inputs.checkbox(latencyMetrics, {
    label: "Latency metrics",
    value: ["Mean latency (ms)"],
  })
);
```


```js
let combinedData = [];
for (let metric of latencyMetricSelected) {
  let subsetData = ciData.filter((d) => d.metric === metric).filter((d) => d.test_name == latencyTestSelected);
  combinedData = combinedData.concat(subsetData);
}
display(makeCombinedPlot(combinedData, { title: "Combined Latency Metrics" }));
```

## Throughput tests


This test suite aims to test vllm's throughput.

- Input length: randomly sample 200 prompts from ShareGPT dataset (with fixed random seed).
- Output length: the corresponding output length of these 200 prompts.
- Batch size: dynamically determined by vllm to achieve maximum throughput.
- Models: llama-3 8B, llama-3 70B, mixtral 8x7B.
- Evaluation metrics: throughput.



```js

const throughputTest = [
  "throughput_llama8B_tp1",
  "throughput_llama70B_tp4",
  "throughput_mixtral8x7B_tp2",
];

const throughputTestSelected = view(
  createSelector(throughputTest, "throughput_llama8B_tp1")
);


const throughputMetrics = [
  "Tput (req/s)",
];

const throughputMetricSelected = view(
  Inputs.checkbox(throughputMetrics, {
    label: "Throughput metrics",
    value: ["Tput (req/s)"],
  })
);
```


```js
let combinedData = [];
for (let metric of throughputMetricSelected) {
  let subsetData = ciData.filter((d) => d.metric === metric).filter((d) => d.test_name == throughputTestSelected);
  combinedData = combinedData.concat(subsetData);
}
display(makeCombinedPlot(combinedData, { title: "Throughput" }));
```


## Serving Benchmark (on ShareGPT)


This test suite aims to test vllm's real serving metrics.

- Input length: randomly sample 200 prompts from ShareGPT dataset (with fixed random seed).
- Output length: the corresponding output length of these 200 prompts.
- Batch size: dynamically determined by vllm and the arrival pattern of the requests.
- **Average QPS (query per second)**: 1, 4, 16 and inf. QPS = inf means all requests come at once. For other QPS values, the arrival time of each query is determined using a random Poisson process (with fixed random seed).
- Models: llama-3 8B, llama-3 70B, mixtral 8x7B.
- Evaluation metrics: throughput, TTFT (time to the first token, with mean, median and p99), ITL (inter-token latency, with mean, median and p99).


```js

const servingTest = [
  "serving_llama8B_tp1_sharegpt_qps_1",
  "serving_llama8B_tp1_sharegpt_qps_4",
  "serving_llama8B_tp1_sharegpt_qps_16",
  "serving_llama8B_tp1_sharegpt_qps_inf",
  "serving_llama70B_tp4_sharegpt_qps_1",
  "serving_llama70B_tp4_sharegpt_qps_4",
  "serving_llama70B_tp4_sharegpt_qps_16",
  "serving_llama70B_tp4_sharegpt_qps_inf",
  "serving_mixtral8x7B_tp2_sharegpt_qps_1",
  "serving_mixtral8x7B_tp2_sharegpt_qps_4",
  "serving_mixtral8x7B_tp2_sharegpt_qps_16",
  "serving_mixtral8x7B_tp2_sharegpt_qps_inf"
];

const servingTestSelected = view(
  createSelector(servingTest, "serving_llama8B_tp1_sharegpt_qps_1")
);

const servingLatencyMetrics = [
  "Mean TTFT (ms)",
  "Median TTFT (ms)",
  "P99 TTFT (ms)",
  "Mean ITL (ms)",
  "Median ITL (ms)",
  "P99 ITL (ms)",
];

const servingLatencyMetricsSelected = view(
  Inputs.checkbox(servingLatencyMetrics, {
    label: "Latency metrics",
    value: ["Mean TTFT (ms)"],
  })
);
```


```js
let combinedData = [];
for (let metric of servingLatencyMetricsSelected) {
  let subsetData = ciData.filter((d) => d.metric === metric).filter((d) => d.test_name == servingTestSelected);
  combinedData = combinedData.concat(subsetData);
}
display(makeCombinedPlot(combinedData, { title: "Latency (ms)" }));
```


```js

const servingThroughputMetrics = [
  "Tput (req/s)"
];

const servingThroughputMetricsSelected = view(
  Inputs.checkbox(servingThroughputMetrics, {
    label: "Throughput metrics",
    value: ["Tput (req/s)"],
  })
);
```

```js
let combinedData = [];
for (let metric of servingThroughputMetricsSelected) {
  let subsetData = ciData.filter((d) => d.metric === metric).filter((d) => d.test_name == servingTestSelected);
  combinedData = combinedData.concat(subsetData);
}
display(makeCombinedPlot(combinedData, { title: "Throughput (req/s)" }));
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
