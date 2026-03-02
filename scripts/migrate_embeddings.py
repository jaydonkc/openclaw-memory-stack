#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import List
import urllib.request

from dotenv import load_dotenv
from pymilvus import MilvusClient, DataType
from sentence_transformers import SentenceTransformer


def _l2_normalize(v):
    norm = sum(x * x for x in v) ** 0.5
    if norm == 0:
        return v
    return [x / norm for x in v]


def _openai_embed(base_url: str, api_key: str, model: str, inputs: List[str]):
    url = base_url.rstrip("/") + "/embeddings"
    payload = {"model": model, "input": inputs}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    data = body.get("data", [])
    vectors = [item.get("embedding", []) for item in data]
    return [_l2_normalize(v) for v in vectors]


def _probe_dim(provider: str, model_name: str, base_url: str, api_key: str) -> int:
    if provider == "sentence-transformers":
        model = SentenceTransformer(model_name)
        return int(model.get_sentence_embedding_dimension())
    if provider == "openai":
        probe = _openai_embed(base_url, api_key, model_name, ["probe"])
        if not probe or not probe[0]:
            raise RuntimeError("OpenAI-compatible provider returned empty embedding")
        return len(probe[0])
    raise ValueError(f"Unsupported EMBED_PROVIDER={provider}")


def _existing_dim(client: MilvusClient, collection_name: str) -> int:
    schema = client.describe_collection(collection_name=collection_name).get("schema", {})
    fields = schema.get("fields", [])
    for f in fields:
        if f.get("name") == "vector":
            return int((f.get("params") or {}).get("dim", 0))
    return 0


def _ensure_collection(client: MilvusClient, name: str, dim: int):
    schema = client.create_schema(auto_id=False, enable_dynamic_field=True)
    schema.add_field(field_name="id", datatype=DataType.VARCHAR, is_primary=True, max_length=128)
    schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=dim)
    schema.add_field(field_name="namespace", datatype=DataType.VARCHAR, max_length=32)
    schema.add_field(field_name="path", datatype=DataType.VARCHAR, max_length=512)
    schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=65535)

    index_params = client.prepare_index_params()
    index_params.add_index(field_name="vector", index_type="AUTOINDEX", metric_type="COSINE")

    client.create_collection(collection_name=name, schema=schema, index_params=index_params)


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Safely migrate embedding backend/model + reindex")
    parser.add_argument("--yes", action="store_true", help="Confirm destructive actions")
    parser.add_argument("--skip-reindex", action="store_true")
    parser.add_argument("--scopes", default="shared,main,coding")
    args = parser.parse_args()

    uri = os.getenv("MILVUS_URI", "http://127.0.0.1:19530")
    collection = os.getenv("MILVUS_COLLECTION", "openclaw_memory")
    provider = os.getenv("EMBED_PROVIDER", "sentence-transformers")
    model_name = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    embed_base_url = os.getenv("EMBED_BASE_URL", "http://127.0.0.1:11434/v1")
    embed_api_key = os.getenv("EMBED_API_KEY", "ollama")

    state_path = Path(".embedding_state.json")
    old_state = {}
    if state_path.exists():
        old_state = json.loads(state_path.read_text(encoding="utf-8"))

    target_dim = _probe_dim(provider, model_name, embed_base_url, embed_api_key)
    fingerprint = hashlib.sha256(f"{provider}|{model_name}|{embed_base_url}|{target_dim}".encode()).hexdigest()

    print(f"Target embedding provider={provider} model={model_name} dim={target_dim}")

    client = MilvusClient(uri=uri)
    exists = client.has_collection(collection_name=collection)
    existing_dim = _existing_dim(client, collection) if exists else 0

    needs_recreate = (not exists) or (existing_dim != target_dim) or (old_state.get("fingerprint") != fingerprint)

    if not needs_recreate:
        print("No migration needed: collection dimension + embedding fingerprint unchanged.")
        return

    print("Migration required.")
    if exists:
        print(f"- Existing collection dim: {existing_dim}")
    if old_state:
        print(f"- Previous provider/model: {old_state.get('provider')}/{old_state.get('model')}")

    if not args.yes:
        print("Refusing to continue without --yes (destructive collection recreation may occur).")
        return

    if exists:
        client.drop_collection(collection_name=collection)
        print(f"Dropped collection: {collection}")

    _ensure_collection(client, collection, target_dim)
    print(f"Created collection: {collection} (dim={target_dim})")

    state_path.write_text(
        json.dumps(
            {
                "provider": provider,
                "model": model_name,
                "base_url": embed_base_url,
                "dim": target_dim,
                "fingerprint": fingerprint,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    if args.skip_reindex:
        print("Skipped reindex by request (--skip-reindex).")
        return

    scopes = [s.strip() for s in args.scopes.split(",") if s.strip()]
    for scope in scopes:
        cmd = f"scripts/run-python.sh scripts/index_shared_memory.py --scope {scope}"
        code = os.system(cmd)
        if code != 0:
            raise SystemExit(f"Reindex failed for scope={scope}")
    print("Migration + reindex complete.")


if __name__ == "__main__":
    main()
