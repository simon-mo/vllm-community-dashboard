import { Octokit } from "@octokit/core";

const octokit = new Octokit({ auth: process.env.GITHUB_TOKEN });

export async function getPullDataFromCommit(
  repoOwner,
  repoName,
  startAfterDate
) {
  const commits = [];
  let pageIdx = 1;
  while (true) {
    const fetched = await octokit.request("GET /repos/{owner}/{repo}/commits", {
      owner: repoOwner,
      repo: repoName,
      per_page: 100,
      order: "desc",
      since: startAfterDate.toISOString(),
      page: pageIdx,
    });
    commits.push(...fetched.data);
    if (fetched.data.length < 100) {
      break;
    }

    pageIdx++;
  }

  // parallel fetch the detail of each commit
  const commitData = await Promise.all(
    commits.map(async (commit) => {
      const commitDetail = await octokit.request(
        "GET /repos/{owner}/{repo}/commits/{ref}",
        {
          owner: repoOwner,
          repo: repoName,
          ref: commit.sha,
        }
      );

      const message = commitDetail.data.commit.message;
      //  extract the PR number from the commit message
      const prNumber = message.match(/#(\d+)/)?.[1];

      // fetch the PR
      try {
        const pull = await octokit.request(
          "GET /repos/{owner}/{repo}/pulls/{pull_number}",
          {
            owner: repoOwner,
            repo: repoName,
            pull_number: prNumber,
          }
        );

        return {
          //   msg: commitDetail.data.commit.message,
          sha: commitDetail.data.sha,
          lines: commitDetail.data.stats.total,
          number: pull.data.number.toString(),
          title: pull.data.title,
          created_at: pull.data.created_at,
          closed_at: pull.data.closed_at,
          merged_at: pull.data.merged_at,
          author: pull.data.user?.login,
          durationDays: Math.round(
            (new Date(pull.data.merged_at) - new Date(pull.data.created_at)) /
              (1000 * 60 * 60 * 24)
          ),
        };
      } catch (e) {
        // console.error("Failed to fetch PR", e);
        return;
      }
    })
  );

  // filter out the undefined
  return commitData.filter((x) => x);
}
