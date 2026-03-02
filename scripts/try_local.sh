#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

command -v docker >/dev/null || { echo "Missing docker"; exit 1; }
command -v ollama >/dev/null || { echo "Missing ollama"; exit 1; }

[[ -f .env ]] || cp .env.example .env

echo "[1/6] setup python env"
bash scripts/setup.sh

echo "[2/6] ensure embedding model"
ollama pull nomic-embed-text

echo "[3/6] start milvus"
docker compose -f docker-compose.milvus.yml up -d

echo "[4/6] doctor"
bash scripts/doctor.sh

echo "[5/6] index sample scope (coding)"
scripts/run-python.sh scripts/index_shared_memory.py --scope coding || true

echo "[6/6] query smoke test"
scripts/run-python.sh scripts/query_memory.py --scope coding --q "test query" || true

echo "Trial run complete. Optional next step: bash scripts/configure_openclaw_memory.sh"
