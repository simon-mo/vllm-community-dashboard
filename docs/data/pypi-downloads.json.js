import {BigQuery} from '@google-cloud/bigquery';

async function runQuery() {
  const bigqueryClient = new BigQuery();

  const query = `
    SELECT
      TIMESTAMP_TRUNC(timestamp, DAY) AS day,
      file.version,
      COUNT(*) AS count_
    FROM
      bigquery-public-data.pypi.file_downloads
    WHERE
      project = "vllm" AND
      timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 60 DAY)
    GROUP BY
      day,
      file.version
  `;

  const options = {
    query: query,
    location: 'US',
  };

  const [rows] = await bigqueryClient.query(options);

  console.log(JSON.stringify(rows, null, 2));
}

runQuery().catch(console.error);