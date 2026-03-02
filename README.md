# OpenClaw Memory Stack

A practical, long-term memory layer for OpenClaw agents.

## Why this over out-of-the-box OpenClaw memory?

OpenClaw built-in memory is excellent for simple setups. This stack is better when you want to:
- keep Markdown files as source of truth (`MEMORY.md`, `memory/*.md`)
- index and retrieve semantic memory in Milvus with namespace isolation (`main`, `coding`, `shared`)
- preserving high-signal memory with customizable summarization loops
- reduce context drift via repeatable retrieval pipelines per agent
- keep cross-session continuity explicit in versionable files + vector index

## Quickstart (OpenClaw + local embeddings)

```bash
cd /path/to/openclaw-memory-stack
bash scripts/setup.sh
docker compose -f docker-compose.milvus.yml up -d
bash scripts/configure_openclaw_memory.sh
bash scripts/doctor.sh
```

Then verify retrieval:

```bash
scripts/run-python.sh scripts/index_shared_memory.py --scope coding
scripts/run-python.sh scripts/query_memory.py --scope coding --q "test query"
openclaw memory status --deep --index --agent main
```

## Use cases

- Personal memory for one OpenClaw agent
- Split memory for multiple agents (`main`, `coding`, `shared`)
- Local-first retrieval with optional Ollama embeddings

## Who this is for

- Self-hosters who want local control and inspectable scripts
- OpenClaw users who want external vector retrieval today

## Who this is not for

- Teams needing managed SaaS memory out of the box
- Users who want zero-infra setup with no Docker/Python

## Architecture (high level)

```text
                +----------------------------+
                |  Markdown source of truth  |
                | MEMORY.md + memory/*.md    |
                +-------------+--------------+
                              |
                              v
                 +------------+------------+
                 |  sync_all.sh / indexer  |
                 +------------+------------+
                              |
                              v
                    +---------+---------+
                    |      Milvus       |
                    | namespace vectors |
                    | main/coding/shared|
                    +---------+---------+
                              |
              +---------------+----------------+
              |                                |
              v                                v
+-----------------------------+      +-----------------------------+
| build_main_context.py       |      | build_coding_context.py     |
| (shallow reconstruction)    |      | (deep reconstruction)       |
+--------------+--------------+      +--------------+--------------+
               |                                    |
               v                                    v
      Main agent prompt context            Coding agent prompt context
```

## Setup

1. Bootstrap environment:

```bash
bash scripts/setup.sh
```

2. Copy and edit `.env` for your machine (`cp .env.example .env`).

3. Start Milvus:

```bash
docker compose -f docker-compose.milvus.yml up -d
```

4. Validate setup:

```bash
bash scripts/doctor.sh
```

5. Index memories:

```bash
scripts/run-python.sh scripts/index_shared_memory.py --scope shared
scripts/run-python.sh scripts/index_shared_memory.py --scope main
scripts/run-python.sh scripts/index_shared_memory.py --scope coding
```

6. Query (example):

```bash
scripts/run-python.sh scripts/query_memory.py --scope coding --q "deep linking architecture decision"
```

7. Build agent context blocks:

```bash
scripts/run-python.sh scripts/build_coding_context.py --q "review PR #48 conflicts"
scripts/run-python.sh scripts/build_main_context.py
```

8. Rollups (uses OpenClaw model, no Ollama required):

```bash
# Daily: 3 durable facts
bash scripts/daily_rollup.sh

# Weekly: synthesize week-level patterns
bash scripts/weekly_rollup.sh
```

Recommended schedule:

```bash
# configure cadence in .env, then install cron entries
bash scripts/install_cron.sh
```

Default cron cadence (UTC) is set in `.env`:
- `ROLLUP_DAILY_CRON=0 2 * * *`
- `ROLLUP_WEEKLY_CRON=0 3 * * 0`

## Configuration

Copy `.env.example` to `.env` and set values.

### Embeddings (important)

**Default configuration (recommended):** local Ollama + `nomic-embed-text`

```env
EMBED_PROVIDER=openai
EMBED_MODEL=nomic-embed-text
EMBED_BASE_URL=http://127.0.0.1:11434/v1
EMBED_API_KEY=ollama
```

Supported backends:
- `openai` (OpenAI-compatible embeddings API; default path for Ollama/vLLM/proxies)
- `sentence-transformers` (local Python model runtime)

If you switch provider/model, run migration + reindex:

```bash
scripts/run-python.sh scripts/migrate_embeddings.py --yes
```

## Plug into OpenClaw built-in memory search

Use the helper script:

```bash
bash scripts/configure_openclaw_memory.sh
openclaw gateway restart
openclaw memory status --deep --index --agent main
```

Default target:
- model: `nomic-embed-text`
- endpoint: `http://127.0.0.1:11434/v1`

## Limitations

- This is an external memory layer; it does not replace OpenClaw’s memory plugin directly.
- Changing embedding model dimensions requires reindexing Milvus collections.
- Multi-user authz policy is out of scope; deploy behind your own trust boundaries.

## Benchmarking

Run latency + retrieval-quality evaluation:

```bash
scripts/run-python.sh scripts/benchmark.py \
  --dataset bench/queries.sample.jsonl \
  --k 5 \
  --out bench/results/latest.json
```

Metrics produced:
- Recall@k
- MRR
- Query latency (mean/p50/p95)

## Safer embedding migrations

When switching embedding providers/models (especially dimension changes), use:

```bash
scripts/run-python.sh scripts/migrate_embeddings.py --yes
```

What it does:
- probes target embedding dimension from current `.env`
- compares against current Milvus collection + saved embedding fingerprint
- recreates collection when needed
- reindexes scopes (`shared,main,coding` by default)

## License

MIT (see `LICENSE`).
