#!/usr/bin/env bash
set -euo pipefail

# Configure OpenClaw built-in memory_search to use a local OpenAI-compatible embeddings endpoint
# Defaults target Ollama + nomic-embed-text.

EMBED_BASE_URL="${EMBED_BASE_URL:-http://127.0.0.1:11434/v1}"
EMBED_MODEL="${EMBED_MODEL:-nomic-embed-text}"
EMBED_API_KEY="${EMBED_API_KEY:-ollama}"

openclaw config set agents.defaults.memorySearch.provider openai
openclaw config set agents.defaults.memorySearch.model "$EMBED_MODEL"
openclaw config set agents.defaults.memorySearch.remote.baseUrl "$EMBED_BASE_URL"
openclaw config set agents.defaults.memorySearch.remote.apiKey "$EMBED_API_KEY"

echo "Configured OpenClaw memory_search for local embeddings endpoint."
echo "Next:"
echo "  1) openclaw gateway restart"
echo "  2) openclaw memory status --deep --index --agent main"
