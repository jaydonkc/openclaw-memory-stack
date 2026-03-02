#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example (please edit paths)."
fi

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install pymilvus sentence-transformers python-dotenv

echo "Setup complete. Next:"
echo "1) Edit .env"
echo "2) docker compose -f docker-compose.milvus.yml up -d"
echo "3) ./scripts/doctor.sh"
