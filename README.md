# Milvus + OpenMem Integration Scaffold

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

This folder bootstraps the next phase of your memory architecture:

- selective sharing (`SHARED_MEMORY.md`) stays source-of-truth
- Milvus provides namespace-aware vector retrieval
- OpenMem (episodic layer) can write higher-level events on top

## Status

- ✅ Phase 1 (Markdown-first + selective sharing): active
- ✅ Phase 2 (Milvus semantic indexing/query): active
- ✅ Phase 3 (episodic scripts + weekly rollup pipeline): active (script-level)
- 🚧 Native OpenClaw memory plugin replacement (`plugins.slots.memory = custom`) is not enabled yet

## Files

- `docker-compose.milvus.yml` — local Milvus standalone stack
- `.env.example` — env vars for ingestion/query scripts
- `scripts/index_shared_memory.py` — chunks and indexes shared + local memory files
- `scripts/query_memory.py` — namespace-filtered query helper

Embedding backends supported by scripts:
- `sentence-transformers` (default local Python model)
- `openai` (OpenAI-compatible embeddings API; useful for local Ollama at `http://127.0.0.1:11434/v1`)

## Namespace rules

Use explicit prefixes in metadata and IDs:

- `main:*` — assistant/personal context
- `coding:*` — code/system context
- `shared:*` — cross-agent safe context

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

## Agent context pipeline (implemented)

### Coding Agent (deep reconstruction)
1. Core memory (`workspace-coding/MEMORY.md` + latest daily memory note)
2. `SHARED_MEMORY.md`
3. Milvus semantic retrieval (`query_memory.py --scope coding --q <query> --k 5`)
4. Episodic recent events (`episodic/coding.jsonl`)
5. Build context block with `scripts/build_coding_context.py --q "<task>"`

### Main Agent (shallow reconstruction)
1. Core memory (`workspace/MEMORY.md` + latest daily memory note)
2. `SHARED_MEMORY.md`
3. Build summary block with `scripts/build_main_context.py`

## Quick start

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

6. Build agent context blocks:

```bash
python3 scripts/build_coding_context.py --q "review PR #48 conflicts"
python3 scripts/build_main_context.py
```

7. Weekly rollup (uses OpenClaw model, no Ollama required):

```bash
bash scripts/weekly_rollup.sh
```

Optional cron (Sundays 02:00):

```bash
0 2 * * 0 $HOME/openclaw/memory-stack/scripts/weekly_rollup.sh >> /tmp/openclaw_rollup.log 2>&1
```

## Plug into OpenClaw (shared local embedding model)

If you want both OpenClaw built-in `memory_search` and this external stack to use the same local embedding endpoint (recommended):

1. Start your local embedding server (example: Ollama):

```bash
ollama serve
ollama pull nomic-embed-text
```

2. Configure OpenClaw built-in memory search:

```bash
cd /path/to/memory-stack
bash scripts/configure_openclaw_memory.sh
openclaw gateway restart
openclaw memory status --deep --index --agent main
```

3. Configure this stack to use the same endpoint in `.env`:

```bash
EMBED_PROVIDER=openai
EMBED_MODEL=nomic-embed-text
EMBED_BASE_URL=http://127.0.0.1:11434/v1
EMBED_API_KEY=ollama
```

This keeps one embedding model path for both systems.

## OpenMem episodic layer (implemented scaffold)

Included scripts:

- `scripts/episodic_write.py` — writes namespace-tagged episodic events with secret redaction.
- `scripts/episodic_query.py` — reads episodic events with strict namespace filtering.

Example:

```bash
python scripts/episodic_write.py --namespace coding --title "Deep link decision" --event "Use canonical /l/:id route" --tags deep-linking,architecture
python scripts/episodic_query.py --namespace coding --limit 5
```

## License

MIT (see `LICENSE`).

## Important integration note

This stack is production-usable as an **external memory layer** today.
To replace OpenClaw's built-in `memory_search` implementation directly with Milvus/OpenMem, you'd need a custom OpenClaw memory plugin/adapter (not just config toggles).
