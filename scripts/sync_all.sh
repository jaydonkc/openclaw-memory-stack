#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
python scripts/index_shared_memory.py --scope shared
python scripts/index_shared_memory.py --scope main
python scripts/index_shared_memory.py --scope coding
echo "sync complete"