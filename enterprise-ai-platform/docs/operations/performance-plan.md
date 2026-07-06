# Performance Plan

## Goals

Measure API latency for key demo and production workflows:

- upload and index
- search
- chat
- agent run
- evaluation run

## Local Load Test

Run:

```bash
python scripts/load_test_api.py --base-url http://127.0.0.1:8000 --iterations 10
```

The script bootstraps a tenant, uploads and indexes a document, then measures
search, chat, agent, and evaluation latency. It reports count, status codes,
p50, p95, and max latency per workflow.

## Metrics To Track

- request count by route/status
- latency p50/p95/p99
- upload size and duration
- indexing duration
- retrieval candidate count
- citation count per answer
- evaluation pass/fail rates

## Bottlenecks To Expect

- document parsing for large files
- synchronous indexing
- vector search at high chunk counts
- LLM provider latency when replacing deterministic local generation
- database connection pool saturation

## Production Improvements

- queue indexing and evaluation jobs
- use PostgreSQL pgvector indexes
- add Redis caching for repeated retrieval queries
- add pagination for document and conversation views
- add OpenTelemetry traces around search, chat, agent, and evaluation
- add autoscaling based on request latency and queue depth
