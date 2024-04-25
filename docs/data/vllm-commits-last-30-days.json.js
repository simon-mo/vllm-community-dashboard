import { getCommitData } from "./gh-historical-pulls-lib.js";

let startAfterDate = new Date();
startAfterDate.setDate(startAfterDate.getDate() - 30);

const commitData = await getCommitData("vllm-project", "vllm", startAfterDate);
const filtered = commitData.map((commit) => ({
  sha: commit.sha,
  url: commit.html_url,
  message: commit.commit.message,
  author_login: commit.author?.login,
  author_avatar: commit.author?.avatar_url,
}));
console.log(JSON.stringify(filtered, null, 2));
