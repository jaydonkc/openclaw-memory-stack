# Benchmark Suite

Evaluate retrieval quality + latency for your configured embedding backend and Milvus collection.

## Dataset format

Use JSONL with fields:
- `id` (string)
- `scope` (`main` | `coding` | `shared`)
- `query` (string)
- `relevant_paths` (array of expected path substrings)

Start from `bench/queries.sample.jsonl`.

## Run benchmark

```bash
scripts/run-python.sh scripts/benchmark.py \
  --dataset bench/queries.sample.jsonl \
  --k 5 \
  --out bench/results/latest.json
```

Outputs:
- `recall_at_k`
- `mrr`
- `latency_ms` (p50/p95/mean)
- per-query details
