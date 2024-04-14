---
toc: false
---

# vLLM Community Metrics


## PyPI Downloads

```js
const downloads = FileAttachment("./data/pypi-downloads.json").json();
```


```js
// only match 0.4 and 0.3
const versionRegex = /^0\.[34]\./;
const data = downloads.map(
    d=>({...d, count: parseInt(d.count_), day: new Date(d.day)})
).sort((a,b)=>a.version.localeCompare(b.version) || a.day - b.day).filter(
    d=>versionRegex.test(d.version)
)



display(Plot.plot({
  y: {
    grid: true,
    label: "↑ PyPI Downloads",
    percent: true,
  },
  marginLeft: 100,
  marks: [
    Plot.areaY(
        data,
         {x: "day", y: "count", fill: "version"}
        ),
    Plot.ruleY([0])
  ],
  color: {legend: true}
}))
```

## Github

```js
const pulls = FileAttachment("./data/gh-historical-pulls.json").json();
```

Number of PRs merged last week ${ pulls.length }.

Distribution of PRs by duration (days):
```js

display(Plot.plot({
  marginLeft: 60,
  y: {grid: true},
  marks: [
    Plot.rectY(pulls, Plot.binX({y: "count"}, {x: "durationDays"})),
    Plot.ruleY([0])
  ]
}))
```

## PRs merged <= 7 days
```js
Inputs.table(pulls,
{
    columns: [
        "number", "title", "durationDays", "lines", "author"
    ],
    layout: "fixed",
    width:{
        title: 400,

    }

})
```