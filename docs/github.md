---
toc: false
---

# Github Activities

Gathered from commits over last 14 days. Look at time to commit, and major features added.

```js
const pulls = await FileAttachment("./data/vllm-commits-pulls.json").json();
const sglPulls = await FileAttachment("./data/sgl-commits-pulls.json").json();

const bothPulls = [
  ...pulls.map((d) => ({ ...d, repo: "vLLM" })),
  ...sglPulls.map((d) => ({ ...d, repo: "SGL" })),
];

// display(Plot.plot({
//   marginLeft: 60,
//   y: {grid: true},
//   marks: [
//     Plot.rectY(bothPulls, Plot.binX({y: "count"}, {x: "durationDays"}, {color: "repo"})),
//     Plot.ruleY([0])
//   ]
// }))

display(
  Plot.plot({
    marginLeft: 60,
    y: { grid: true },
    round: true,
    color: { legend: true },
    marks: [
      Plot.rectY(
        bothPulls,
        Plot.binX(
          { y: "count" },
          {
            filter: (d) => d.repo === "vLLM",
            x: "durationDays",
            fill: "repo",
            insetLeft: 0,
          }
        )
      ),
      Plot.rectY(
        bothPulls,
        Plot.binX(
          { y: "count" },
          {
            filter: (d) => d.repo === "SGL",
            x: "durationDays",
            fill: "repo",
            insetRight: 0,
          }
        )
      ),
      Plot.ruleY([0]),
    ],
  })
);
```

## vLLM

Number of PRs merged: ${ pulls.length }.

### PRs merged

```js
display(Inputs.table(pulls, {
  columns: ["number", "title", "durationDays", "lines", "author"],
  layout: "fixed",
  width: {
    title: 400,
  },
  sort: "lines",
  reverse: true,
}));
```

## SGL

Number of PRs merged: ${ sglPulls.length }.

### PRs merged

```js
display(Inputs.table(sglPulls, {
  columns: ["number", "title", "durationDays", "lines", "author"],
  layout: "fixed",
  width: {
    title: 400,
  },
  sort: "lines",
  reverse: true,
}));
```
