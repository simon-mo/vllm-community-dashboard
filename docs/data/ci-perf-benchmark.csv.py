import io
import os
import re
import asyncio
import aiofiles
import sys
from datetime import datetime, timedelta

import pandas as pd
import requests
import httpx
import json


def log(msg):
    print(msg, file=sys.stderr)


def get_builds(org_slug, branch, token, days=30):
    url = f"https://api.buildkite.com/v2/organizations/{org_slug}/builds"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Calculate the date 30 days ago from today
    date_from = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"

    params = {
        "branch": branch,
        "created_from": date_from,
        "per_page": "100",
    }

    all_builds = []
    while url:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            all_builds.extend(response.json())
            # Parse the Link header and look for a 'next' relation
            link_header = response.headers.get('Link', None)
            url = None
            if link_header:
                links = link_header.split(',')
                next_link = [link for link in links if 'rel="next"' in link]
                if next_link:
                    next_url = next_link[0].split(';')[0].strip('<>')
                    url = next_url
                    params = {
                    }  # Clear params because next URL will have necessary params
        else:
            raise Exception(
                f"Failed to get builds: {response.status_code} - {response.text}"
            )

    return all_builds




async def get_benchmark_results_and_save(org_slug, pipeline_slug, build_number, token, filename, commit, commit_url, build_datetime):
    artifacts_url = f"https://api.buildkite.com/v2/organizations/{org_slug}/pipelines/{pipeline_slug}/builds/{build_number}/artifacts"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(artifacts_url, headers=headers)
        if response.status_code == 200:
            artifacts = response.json()
            for artifact in artifacts:
                if artifact['filename'] == "benchmark_results.json":
                    download_url = f"https://api.buildkite.com/v2/organizations/{org_slug}/pipelines/{pipeline_slug}/builds/{build_number}/jobs/{artifact['job_id']}/artifacts/{artifact['id']}/download"
                    download_response = await client.get(download_url, headers=headers)
                    if download_response.status_code in [200, 302]:
                        benchmark_results_url = download_response.json()['url']
                        async with client.stream("GET", benchmark_results_url) as stream:
                            async with aiofiles.open(filename, "wb") as f:
                                async for chunk in stream.aiter_bytes(chunk_size=32768):
                                    await f.write(chunk)
                        log(f"Downloaded benchmarking results for commit {commit}")
                        return filename, commit, commit_url, build_datetime
        return None

        

    

# def get_benchmark_results_and_save(org_slug, pipeline_slug, build_number, token, filename, commit, commit_url, build_datetime):

    
#     # get artifact list:
#     # curl -H "Authorization: Bearer $TOKEN" \
#     # -X GET "https://api.buildkite.com/v2/organizations/{org.slug}/pipelines/{pipeline.slug}/builds/{build.number}/artifacts"
#     artifacts_url = f"https://api.buildkite.com/v2/organizations/{org_slug}/pipelines/{pipeline_slug}/builds/{build_number}/artifacts"
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Content-Type": "application/json"
#     }
#     response = requests.get(artifacts_url, headers=headers)
#     if response.status_code == 200:
#         artifacts = response.json()
#         for artifact in artifacts:
#             if artifact['filename'] == "benchmark_results.md":
#                 # get download URL:
#                 # curl -H "Authorization: Bearer $TOKEN" \
#                 # -X GET "https://api.buildkite.com/v2/organizations/{org.slug}/pipelines/{pipeline.slug}/builds/{build.number}/jobs/{job.id}/artifacts/{id}/download"
#                 download_url = f"https://api.buildkite.com/v2/organizations/{org_slug}/pipelines/{pipeline_slug}/builds/{build_number}/jobs/{artifact['job_id']}/artifacts/{artifact['id']}/download"
#                 download_response = requests.get(download_url, headers=headers)
#                 if download_response.status_code == 200:
#                     # start the downloading
#                     benchmark_results_url = download_response.url
#                     benchmark_results_response = requests.get(benchmark_results_url, stream=True)
#                     with open(filename, "wb") as f:
#                         for chunk in benchmark_results_response.iter_content(chunk_size=8192):
#                             f.write(chunk)
#                     log(f"Downloaded benchmarking results for commit {commit}")
#                     return filename, commit, commit_url, build_datetime
                
#     raise FileNotFoundError("Benchmarking results not found in the build artifacts")


# Function to process log entries using defined patterns
def extract_data_from_logs(logs):
    pattern = 'The json string for all benchmarking tables:\n```json\n(.*?)\n```'
    match = re.search(pattern, logs, re.DOTALL)
    
    if match:
        benchmarking_results = match.group(1)
        return json.loads(benchmarking_results)
    else:
        return {}


API_TOKEN = os.environ["BUILDKIT_API_TOKEN"]
ORG_SLUG = "vllm"
BRANCH = "main"
cache_dir = "/tmp/buildkite_logs"
os.makedirs(cache_dir, exist_ok=True)

async def download_and_cache(raw_log_url, filepath, commit, commit_url,
                             build_datetime):
    async with httpx.AsyncClient() as client:
        data = await client.get(
            raw_log_url, headers={"Authorization": f"Bearer {API_TOKEN}"})
        data = data.text
    if len(data) <= 100:
        log(f"Skipping processing {filepath} for {commit} because the log is empty"
            )
        return
    with open(filepath, "w") as f:
        f.write(data)
    log(f"Saved {filepath} for commit {commit}")
    return filepath, commit, commit_url, build_datetime


async def main():
    builds = get_builds(ORG_SLUG, BRANCH, API_TOKEN, days=2)
    log(f"Found {len(builds)} builds for {BRANCH} branch")

    values = []

    def insert_row(filepath, commit, commit_url, build_datetime):
        with open(filepath, "r") as f:
            logs = f.read()
            results = json.loads(logs)
            df = pd.DataFrame.from_dict(results)
            df['commit'] = commit
            df['commit_url'] = commit_url
            df['build_datetime'] = build_datetime
            df["test_name"] = df["Test name"]
                
            values.extend(df.to_dict(orient='records'))

    download_tasks = []
    for build in builds:
        
        # skip running builds
        if build['state'] == "running":
            continue
        
        commit = build['commit']
        commit_url = f"{build['pipeline']['repository'].replace('.git', '')}/commit/{build['commit']}"
        
        # find if the build contains the benchmarking data
        contains_benchmark = False
        for job in build.get('jobs', []):
            if 'name' in job and job['name'] == "A100 Benchmark":
                contains_benchmark = True
                break
        if not contains_benchmark:
            continue
        
        build_datetime = build['created_at']
        filename = f"{build_datetime}_{commit}.log"
        filepath = os.path.join(cache_dir, filename)
        if os.path.exists(filepath):
            log(f"Skipping downloading {filepath} for {commit} because it already exists"
                )
            insert_row(filepath, commit, commit_url, build_datetime)
        else:
            download_tasks.append(asyncio.create_task(
                get_benchmark_results_and_save(ORG_SLUG,
                                            build['pipeline']['slug'],
                                            build['number'],
                                            API_TOKEN,
                                            filepath,
                                            commit,
                                            commit_url,
                                            build_datetime)
            ))
        
        
        
    # for task in download_tasks:
    for task in asyncio.as_completed(download_tasks):
        result = await task
        if result is None:
            continue
        insert_row(*result)
        
    df = pd.DataFrame.from_dict(values)
    df = df.melt(
        id_vars = ["commit", "commit_url", "build_datetime", "test_name"],
        var_name="metric",
        value_name="value"
    )
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    print(buf.read())


if __name__ == "__main__":
    asyncio.run(main())
