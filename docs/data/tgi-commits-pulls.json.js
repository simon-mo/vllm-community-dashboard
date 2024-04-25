import { getPullDataFromCommit } from "./gh-historical-pulls-lib.js";

let startAfterDate = new Date();
startAfterDate.setDate(startAfterDate.getDate() - 14);

const data = await getPullDataFromCommit(
  "huggingface",
  "text-generation-inference",
  startAfterDate
);

console.log(JSON.stringify(data, null, 2));
