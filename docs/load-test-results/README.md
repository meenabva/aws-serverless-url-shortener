# Load test results

Paste the full k6 summary for each run in this folder (for example `run-1-50vus.txt`).

| Run | Peak users | Throughput (req/s) | p50 | p95 | Error rate | Lambda throttles | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 50 | 372 | 36 ms | 143 ms | 80.05% | Yes (peak on Throttles graph) | Most requests failed fast; cause confirmed as the account limit of 10 concurrent Lambda executions |
| 2 | 10 | 137 | 40 ms | 70 ms | 46.01% | Yes (peak on Throttles graph) | 11,459 of 24,884 redirects returned 503 `Service Unavailable` from API Gateway; successful requests only: p50 55 ms, p95 77 ms, max 877 ms (likely cold start). Cause confirmed: account limit of 10 concurrent Lambda executions; 10 VUs with no sleep keep about 10 requests in flight, so bursts over the limit are throttled. Summary: [run-2-10vus.txt](run-2-10vus.txt) |
| 3 | 100 | 1,596 | 29 ms | 72 ms | 94.86% | Yes (peak on Throttles graph) | 275,136 of 290,015 redirects failed. Successful requests only: about 82 req/s, p50 55 ms, p95 185 ms, max 3.88 s. Successful throughput stayed near Run 2's (about 74 req/s) despite 10x the users, so the 10-execution limit caps capacity; the extra load only adds failures. Summary: [run-3-100vus.txt](run-3-100vus.txt) |

Test machine and location: laptop in Bengaluru, testing against ap-south-2 (Hyderabad) (latency includes the trip from here to the AWS region).
Lambda account concurrency limit: 10 (`ConcurrentExecutions` from `aws lambda get-account-settings`)
