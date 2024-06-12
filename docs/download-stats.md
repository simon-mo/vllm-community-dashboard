---
toc: false
---

# Download Stats

Over last 30 days. Look at the relative trend, not absolute numbers.

<div class="grid grid-cols-2">
  <div class="card grid-colspan-2">

```js
const downloads = (await FileAttachment("./data/pypi-downloads.json").json())
  .map((d) => ({ ...d, count: parseInt(d.count_), day: new Date(d.day.value) }))
  .sort((a, b) => a.version.localeCompare(b.version) || a.day - b.day);

const vllmDownloads = downloads.filter((d) => d.project == "vllm");
const trtDownloads = downloads.filter((d) => d.project == "tensorrt-llm");

const versionRegex = /^0\.[3456789]\./;
const vllmDownloadsFiltered = vllmDownloads.filter((d) =>
  versionRegex.test(d.version)
);
```

## vLLM Downloads: ${ vllmDownloadsFiltered.reduce((acc, d)=>acc+d.count, 0) }

```js
function stackChart(data, { width } = {}) {
  return Plot.plot({
    y: {
      grid: true,
      label: "↑ PyPI Downloads",
      // percent: true,
    },
    width,
    marginLeft: 100,
    marks: [
      Plot.areaY(data, { x: "day", y: "count", fill: "version" }),
      Plot.ruleY([0]),
      Plot.crosshair(data, { x: "day", y: "count", color: "version" }),
    ],
    color: { legend: true },
  });
}

display(resize((width) => stackChart(vllmDownloadsFiltered, { width })));
```

</div>
  <div class="card">

## TGI Container Downloads: ${ tgiData.reduce((acc, d)=>acc+d.mergeCount, 0) }

```js
const tgiDownloads = await FileAttachment(
  "./data/tgi-docker-pulls.json"
).json();

const tgiData = tgiDownloads
  .map((d) => ({ mergeCount: parseInt(d.mergeCount), date: new Date(d.date) }))
  .sort((a, b) => a.date - b.date);

display(
  resize((width) =>
    Plot.plot({
      y: {
        grid: true,
        label: "↑ TGI Docker Pulls",
        // percent: true,
      },
      width,
      marginLeft: 100,
      marks: [
        Plot.lineY(tgiData, { x: "date", y: "mergeCount" }),
        Plot.ruleY([0]),
        Plot.crosshair(tgiData, { x: "date", y: "mergeCount" }),
      ],
    })
  )
);
```

</div>

<div class="card">

## TRT-LLM Downloads: ${ trtDownloadsNormalized.reduce((acc, d)=>acc+d.count, 0) }.

```js
// normalize the version from 0.9.0.dev2024022000 to 0.9.0
const trtDownloadsNormalized = trtDownloads
  .map((d) => ({ ...d, version: d.version.replace(/\.dev.*/, "") }))
  .reduce((acc, d) => {
    const existing = acc.find(
      (e) => e.version == d.version && e.day.getTime() == d.day.getTime()
    );
    if (existing) {
      existing.count += d.count;
    } else {
      acc.push(d);
    }
    return acc;
  }, [])
  .sort((a, b) => a.version.localeCompare(b.version) || a.day - b.day);

display(resize((width) => stackChart(trtDownloadsNormalized, { width })));
```

</div>

</div>
