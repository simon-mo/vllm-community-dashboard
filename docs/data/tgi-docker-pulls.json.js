import { JSDOM } from "jsdom";

// Download HTML from
const URL =
  "https://github.com/huggingface/text-generation-inference/pkgs/container/text-generation-inference";

// Extract data
const page = await (await fetch(URL)).text();
const doc = new JSDOM(page).window.document;
const data = Array.from(
  doc.querySelectorAll('[aria-label="Downloads for the last 30 days"] svg rect')
).map((el) => ({
  date: el.getAttribute("data-date"),
  mergeCount: el.getAttribute("data-merge-count"),
}));

console.log(JSON.stringify(data, null, 2));
