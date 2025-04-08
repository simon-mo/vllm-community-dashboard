---
toc: false
---

# CI Benchmark

Update [04/08/2025]: We are currently working on reorganizing the compute for performance benchmark. In the meantime, please reference PyTorch Hub's Dashboard for vLLM: https://hud.pytorch.org/benchmark/llms?repoName=vllm-project/vllm

<!-- This is the performance benchmark for [vllm github repo](https://github.com/vllm-project/vllm) This benchmark is facing towards developers.

# Hardware
Please select a hardware. All plots down below will only show results of the selected hardware (more hardware is coming).
```js

const hardware = [
  "A100", "H100", "H200",
];

const hardwareSelected = view(
  createSelector(hardware, "A100", "Hardware")
)
```


# Smoothing
```js
const ROLLING_WINDOW = view(html`<input type=range step=1 min=1 max=20 value=10>`);
```
Taking the average of last ${ROLLING_WINDOW} commits when drawing the curve. (default: 10)

```js
const commitData = await FileAttachment(
  "./data/vllm-commits-last-30-days.json"
).json();
const commitShaToValues = commitData.reduce((acc, d) => {
  acc[d.sha] = d;
  return acc;
}, {});

const zip = FileAttachment("./data/ci-perf-benchmark.zip").zip()
const ciDataFullUnzip = zip.then((zip) => zip.file("ci-perf-benchmark.csv").csv({typed: true}));

let ciDataFull = (await ciDataFullUnzip).map(
  (d) => {
    d["commit_message"] =
      commitShaToValues[d["commit"]]?.message.split("\n")[0];
    d["build_datetime"] = new Date(d["build_datetime"]);
    d["value"] = parseFloat(d["value"]);
    return d;
  }
).sort((a, b) => a.build_datetime - b.build_datetime);

function createSelector(metricsSubset, defaultMetric) {
  return Inputs.radio(metricsSubset, { label: "Test name", value: defaultMetric });
}

function makeCombinedPlot(data, { title } = {}) {
  let minVal = Math.min(...data.map((d) => d.value));
  let maxVal = Math.max(...data.map((d) => d.value));
  let yDomain = [minVal - 0.2 * (maxVal - minVal), maxVal + 0.2 * (maxVal - minVal)];

  return Plot.plot({
    title: title,
    y: { grid: true, domain: yDomain },
    width: 1200,
    marks: [
      Plot.dot(data, {
        x: "build_datetime",
        y: "value",
        z: "metric",
        fill: "orange",
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
        Plot.windowY(ROLLING_WINDOW, {
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

function makeSparkline(data) {
   return Plot.lineY(
         data,
         Plot.windowY(ROLLING_WINDOW, {
          x: "build_datetime",
          y: "value",
          z: "metric",
          stroke: "DarkTurquoise",
        })
    ).plot({axis: null, width: 80, height: 12});
}
```


```js
// Utility functions for calculating moving average and formatting

function calculateAverageValue(data, daysBefore) {
  const latestDatetime = data[data.length - 1].build_datetime;

  const targetDate = new Date(latestDatetime);
  targetDate.setDate(targetDate.getDate() - daysBefore);

  const filteredData = data.filter(
    (d) => d.build_datetime.toDateString() <= targetDate.toDateString()
  );

  const latestCommits = filteredData
    .sort((a, b) => b.build_datetime - a.build_datetime)
    .slice(0, ROLLING_WINDOW);

  const averageValue = latestCommits.reduce((sum, d) => sum + d.value, 0) / latestCommits.length;

  return averageValue;
}


function formatPercentage(value) {
  let sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

function interpolateColorLatency(value) {
  const green = { r: 0, g: 255, b: 0 };
  const red = { r: 255, g: 0, b: 0 };
  const capped_value =  Math.max(-2.5, Math.min(2.5, value));;
  const ratio = (capped_value + 2.5) / 5; // Normalize value to range [0, 1]

  const r = Math.round(green.r * (1 - ratio) + red.r * ratio);
  const g = Math.round(green.g * (1 - ratio) + red.g * ratio);
  const b = Math.round(green.b * (1 - ratio) + red.b * ratio);

  return `rgb(${r},${g},${b})`;
}

function interpolateColorThroughput(value) {
  const green = { r: 0, g: 255, b: 0 };
  const red = { r: 255, g: 0, b: 0 };
  const capped_value =  Math.max(-2.5, Math.min(2.5, value));;
  const ratio = 1 - (capped_value + 2.5) / 5; // Normalize value to range [0, 1]

  const r = Math.round(green.r * (1 - ratio) + red.r * ratio);
  const g = Math.round(green.g * (1 - ratio) + red.g * ratio);
  const b = Math.round(green.b * (1 - ratio) + red.b * ratio);

  return `rgb(${r},${g},${b})`;
}

```


```js
let ciData = ciDataFull.filter((d) => d.GPU.includes(hardwareSelected));
```

-------------


# TL; DR


-------


- Latency of vllm.
  - Metric: median end-to-end latency (ms). We use median as it is more stable than mean when outliers occur.
  - Input length: 32 tokens.
  - Output length: 128 tokens.


```js

const latencyTableData = [];

for (let test of ["latency_llama8B_tp1", "latency_llama70B_tp4", "latency_mixtral8x7B_tp2"]) {


  let data = ciData.filter((d) => d.test_name == test && d.metric == "Median latency (ms)");

  let cur = calculateAverageValue(data, 0);
  let oneday = calculateAverageValue(data, 1);
  let oneweek = calculateAverageValue(data, 7);

  latencyTableData.push({test,
    "current": cur,
    "oneday": 100 * (cur - oneday) / oneday,
    "oneweek": 100 * (cur - oneweek) / oneweek,
    "sparkline": makeSparkline(data)
  });
}



display(
  Inputs.table(latencyTableData,
    {
      columns: ["test", "current", "oneday", "oneweek", "sparkline"],
      header: {
        test: "Test name",
        current: "Latency",
        oneday: "vs 1 day ago",
        oneweek: "vs 1 week ago",
        "sparkline": "Spark line"
      },
      format: {
        current: (d) => d.toFixed(2),
        oneday: (d) => htl.html`<span style="color:${interpolateColorLatency(d)}"><b>${formatPercentage(d)}</b></span>`,
        oneweek: (d) => htl.html`<span style="color:${interpolateColorLatency(d)}"><b>${formatPercentage(d)}</b></span>`,
        sparkline: (d) => htl.html`${d}`,
        },
      layout: "fixed"
    }));
```


------


- Throughput of vllm.
  - Metric: throughput (request per second)
  - Input length: 200 prompts from ShareGPT.
  - Output length: the corresponding output length of these 200 prompts.


```js

const latencyTableData = [];

for (let test of ["throughput_llama8B_tp1", "throughput_llama70B_tp4", "throughput_mixtral8x7B_tp2"]) {


  let data = ciData.filter((d) => d.test_name == test && d.metric == "Tput (req/s)");

  let cur = calculateAverageValue(data, 0);
  let oneday = calculateAverageValue(data, 1);
  let oneweek = calculateAverageValue(data, 7);

  latencyTableData.push({test,
    "current": cur,
    "oneday": 100 * (cur - oneday) / oneday,
    "oneweek": 100 * (cur - oneweek) / oneweek,
    "sparkline": makeSparkline(data)
  });
}



display(
  Inputs.table(latencyTableData,
    {
      columns: ["test", "current", "oneday", "oneweek", "sparkline"],
      header: {
        test: "Test name",
        current: "Throughput",
        oneday: "vs 1day ago",
        oneweek: "vs 1week ago",
        "sparkline": "Spark line"
      },
      format: {
        current: (d) => d.toFixed(2),
        oneday: (d) => htl.html`<span style="color:${interpolateColorThroughput(d)}"><b>${formatPercentage(d)}</b></span>`,
        oneweek: (d) => htl.html`<span style="color:${interpolateColorThroughput(d)}"><b>${formatPercentage(d)}</b></span>`,
        sparkline: (d) => htl.html`${d}`,
        },
        layout: "fixed",
    }));
```

------


- Serving test of vllm
  - Metrics: median TTFT (time-to-first-token, unit: ms) & median ITL (inter-token latency, unit: ms). We use median as it is more stable than mean when outliers occur.
  - Input length: 200 prompts from ShareGPT.
  - Output length: the corresponding output length of these 200 prompts.
  - Average QPS: 1, 4, 16 and inf. QPS = inf means all requests come at once.



```js
const tableData = [];

for (let model of ["llama8B_tp1", "llama70B_tp4", "mixtral8x7B_tp2"]) {
  for (let qps of ["1", "4", "16"]) {
    const test = `serving_${model}_sharegpt_qps_${qps}`;

    const dataTTFT = ciData.filter((d) => d.test_name == test && d.metric == "Median TTFT (ms)");
    const latestTTFT = calculateAverageValue(dataTTFT, 0);
    const oneDayTTFT = calculateAverageValue(dataTTFT, 1);
    const oneWeekTTFT = calculateAverageValue(dataTTFT, 7);

    const dataITL = ciData.filter((d) => d.test_name == test && d.metric == "Median ITL (ms)");
    const latestITL = dataITL[dataITL.length - 1].value.toFixed(2);
    const oneDayITL = calculateAverageValue(dataITL, 1);
    const oneWeekITL = calculateAverageValue(dataITL, 7);

    tableData.push({ model, qps,
      ttftLatest: latestTTFT,
      ttftOneDay: (latestTTFT - oneDayTTFT) / oneDayTTFT,
      ttftOneWeek: (latestTTFT - oneWeekTTFT) / oneWeekTTFT,
      ttftSparkline: makeSparkline(dataTTFT),
      itlLatest: latestITL,
      itlOneDay: (latestITL - oneDayITL) / oneDayITL,
      itlOneWeek: (latestITL - oneWeekITL) / oneWeekITL,
      itlSparkline: makeSparkline(dataITL),
    });

  }
}

display(
  Inputs.table(tableData,
    {
      columns: ["model", "qps", "ttftLatest", "ttftOneDay", "ttftOneWeek", "itlLatest", "itlOneDay", "itlOneWeek", "ttftSparkline", "itlSparkline"],
      header: {
        model: "Model",
        qps: "QPS",
        ttftLatest: "TTFT",
        ttftOneDay: "vs 1day ago",
        ttftOneWeek: "vs 1week ago",
        itlLatest: "ITL",
        itlOneDay: "vs 1day ago",
        itlOneWeek: "vs 1week ago",
        ttftSparkline: "TTFT",
        itlSparkline: "ITL",
      },
      format: {
        ttftOneDay: (d) => htl.html`<span style="color:${interpolateColorLatency(d)}"><b>${formatPercentage(d)}</b></span>`,
        ttftOneWeek: (d) => htl.html`<span style="color:${interpolateColorLatency(d)}"><b>${formatPercentage(d)}</b></span>`,
        itlOneDay: (d) => htl.html`<span style="color:${interpolateColorLatency(d)}"><b>${formatPercentage(d)}</b></span>`,
        itlOneWeek: (d) => htl.html`<span style="color:${interpolateColorLatency(d)}"><b>${formatPercentage(d)}</b></span>`,
        ttftSparkline: (d) => htl.html`${d}`,
        itlSparkline: (d) => htl.html`${d}`,
        },
      layout: "auto"
    }));
```



- We also test speculative decoding in vllm serving test. Concretely:
  - Metrics: median TTFT (time-to-first-token, unit: ms) & median ITL (inter-token latency, unit: ms). We use median as it is more stable than mean when outliers occur.
  - Input length: 200 prompts from ShareGPT.
  - Output length: the corresponding output length of these 200 prompts.
  - Draft model: Qwama-0.5B
  - Number of tokens proposed per step: 4
  - Average QPS: 2.



```js

const spectableData = []

for (let test of ["serving_llama70B_tp4_sharegpt_specdecode_qps_2"]) {

  const qps = 2;
  const model = "llama70B_tp4";

  const dataTTFT = ciData.filter((d) => d.test_name == test && d.metric == "Median TTFT (ms)");
  const latestTTFT = calculateAverageValue(dataTTFT, 0);
  const oneDayTTFT = calculateAverageValue(dataTTFT, 1);
  const oneWeekTTFT = calculateAverageValue(dataTTFT, 7);

  const dataITL = ciData.filter((d) => d.test_name == test && d.metric == "Median ITL (ms)");
  const latestITL = dataITL[dataITL.length - 1].value.toFixed(2);
  const oneDayITL = calculateAverageValue(dataITL, 1);
  const oneWeekITL = calculateAverageValue(dataITL, 7);

  spectableData.push({ model, qps,
    ttftLatest: latestTTFT,
    ttftOneDay: (latestTTFT - oneDayTTFT) / oneDayTTFT,
    ttftOneWeek: (latestTTFT - oneWeekTTFT) / oneWeekTTFT,
    ttftSparkline: makeSparkline(dataTTFT),
    itlLatest: latestITL,
    itlOneDay: (latestITL - oneDayITL) / oneDayITL,
    itlOneWeek: (latestITL - oneWeekITL) / oneWeekITL,
    itlSparkline: makeSparkline(dataITL),
  });

}

display(
  Inputs.table(spectableData,
    {
      columns: ["model", "qps", "ttftLatest", "ttftOneDay", "ttftOneWeek", "itlLatest", "itlOneDay", "itlOneWeek", "ttftSparkline", "itlSparkline"],
      header: {
        model: "Model",
        qps: "QPS",
        ttftLatest: "TTFT",
        ttftOneDay: "vs 1day ago",
        ttftOneWeek: "vs 1week ago",
        itlLatest: "ITL",
        itlOneDay: "vs 1day ago",
        itlOneWeek: "vs 1week ago",
        ttftSparkline: "TTFT",
        itlSparkline: "ITL",
      },
      format: {
        ttftOneDay: (d) => htl.html`<span style="color:${interpolateColorLatency(d)}"><b>${formatPercentage(d)}</b></span>`,
        ttftOneWeek: (d) => htl.html`<span style="color:${interpolateColorLatency(d)}"><b>${formatPercentage(d)}</b></span>`,
        itlOneDay: (d) => htl.html`<span style="color:${interpolateColorLatency(d)}"><b>${formatPercentage(d)}</b></span>`,
        itlOneWeek: (d) => htl.html`<span style="color:${interpolateColorLatency(d)}"><b>${formatPercentage(d)}</b></span>`,
        ttftSparkline: (d) => htl.html`${d}`,
        itlSparkline: (d) => htl.html`${d}`,
        },
      layout: "auto"
    }));

```



-------------


# Latency tests






### Description

This test suite aims to test vLLM's end-to-end latency under a controlled setup.

- Input length: 32 tokens.
- Output length: 128 tokens.
- Batch size: fixed (8).
- Evaluation metrics: end-to-end latency (mean, median, p99).





### Plot

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
    value: ["Median latency (ms)"],
  })
);
```


```js
let combinedData = [];
for (let metric of latencyMetricSelected) {
  let subsetData = ciData.filter((d) => d.metric === metric).filter((d) => d.test_name == latencyTestSelected);
  combinedData = combinedData.concat(subsetData);
}
display(makeCombinedPlot(combinedData, { title: "Latency (ms)" }));
```



--------






# Throughput tests



### Description


This test suite aims to test vLLM's throughput.

- Input length: randomly sample 200 prompts from ShareGPT dataset (with fixed random seed).
- Output length: the corresponding output length of these 200 prompts.
- Batch size: dynamically determined by vllm to achieve maximum throughput.
- Evaluation metrics: throughput.



### Plot


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

------

# Serving Benchmark (on ShareGPT)





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
  "serving_mixtral8x7B_tp2_sharegpt_qps_inf",
  "serving_llama70B_tp4_sharegpt_specdecode_qps_2",
];
```


### Description

This test suite aims to test vllm's real serving metrics.

- Input length: randomly sample 200 prompts from ShareGPT dataset (with fixed random seed).
- Output length: the corresponding output length of these 200 prompts.
- Batch size: dynamically determined by vllm and the arrival pattern of the requests.
- Average QPS (query per second): 1, 4, 16 and inf. QPS = inf means all requests come at once. For other QPS values, the arrival time of each query is determined using a random Poisson process (with fixed random seed).
- Models: llama-3 8B, llama-3 70B, mixtral 8x7B.
- Evaluation metrics: throughput, TTFT (time to the first token, with mean, median and p99), ITL (inter-token latency, with mean, median and p99).


### Latency plot


```js
// for (let test of servingTest) {
//   for (let metric of ["Mean ITL (ms)", "Mean ITL (ms)"]) {
//     const data = ciData.filter((d) => d.test_name == test && d.metric == metric);
//     const latest = data[data.length - 1].value.toFixed(2);
//     const chunks = test.split("_");
//     const testName = [chunks[1], chunks[2], chunks[4], chunks[5]].join(" ");
//     display(html`<p>${testName} : ${latest}ms</p>`);
//   }
// }

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
    value: ["Median TTFT (ms)"],
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



### Throughput plot


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
``` -->
