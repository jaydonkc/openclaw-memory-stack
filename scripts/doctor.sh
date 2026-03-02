#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/6] checking .env"
[[ -f .env ]] || { echo "Missing .env"; exit 1; }

set -a
source .env
set +a

echo "[2/6] checking required env vars"
for v in MILVUS_URI MILVUS_COLLECTION MAIN_WORKSPACE CODING_WORKSPACE SHARED_MEMORY_FILE; do
  [[ -n "${!v:-}" ]] || { echo "Missing $v"; exit 1; }
done

echo "[3/6] checking paths"
for p in "$MAIN_WORKSPACE" "$CODING_WORKSPACE"; do
  [[ -d "$p" ]] || echo "Warn: missing dir $p"
done
[[ -f "$SHARED_MEMORY_FILE" ]] || echo "Warn: missing shared file $SHARED_MEMORY_FILE"

echo "[4/6] checking docker compose file"
docker compose -f docker-compose.milvus.yml config >/dev/null

echo "[5/6] checking milvus service"
if ! docker compose -f docker-compose.milvus.yml ps | grep -q milvus-standalone; then
  echo "Warn: milvus not running (run docker compose ... up -d)"
fi

echo "[6/6] checking python scripts"
source .venv/bin/activate
python -m py_compile scripts/index_shared_memory.py scripts/query_memory.py scripts/build_coding_context.py scripts/build_main_context.py scripts/benchmark.py scripts/migrate_embeddings.py

echo "doctor: OK (warnings possible above)"
