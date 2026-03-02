# OpenClaw Memory Stack

A practical, local-first memory layer for OpenClaw agents.

This repo helps you:
- keep Markdown files as source of truth (`MEMORY.md`, `memory/*.md`)
- index and retrieve semantic memory in Milvus with namespace isolation (`main`, `coding`, `shared`)
- share one local embedding endpoint across OpenClaw built-in `memory_search` and external retrieval scripts

Better long-term recall without giving up control of your data.

## 5-command quickstart (OpenClaw + local embeddings)

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

2. Edit `.env` paths for your machine.

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

8. Weekly rollup (uses OpenClaw model, no Ollama required):

```bash
bash scripts/weekly_rollup.sh
```

## Embedding backends

Supported in scripts:
- `sentence-transformers` (default local Python model)
- `openai` (OpenAI-compatible embeddings API; useful for local Ollama at `http://127.0.0.1:11434/v1`)

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

## Roadmap

- Benchmark suite (latency + retrieval quality)
- Optional native OpenClaw memory plugin adapter
- Safer migration tooling for embedding model switches

## License

MIT (see `LICENSE`).
