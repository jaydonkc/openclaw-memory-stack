#!/usr/bin/env python3
import argparse
import os

from dotenv import load_dotenv
from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer
import json
import urllib.request



def _l2_normalize(v):
    norm = sum(x * x for x in v) ** 0.5
    if norm == 0:
        return v
    return [x / norm for x in v]


def _openai_embed(base_url: str, api_key: str, model: str, text: str):
    url = base_url.rstrip("/") + "/embeddings"
    payload = {"model": model, "input": [text]}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    emb = ((body.get("data") or [{}])[0]).get("embedding") or []
    return _l2_normalize(emb)


def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=["main", "coding", "shared"], required=True)
    parser.add_argument("--q", required=True)
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()

    uri = os.getenv("MILVUS_URI", "http://127.0.0.1:19530")
    collection = os.getenv("MILVUS_COLLECTION", "openclaw_memory")
    provider = os.getenv("EMBED_PROVIDER", "sentence-transformers")
    model_name = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    embed_base_url = os.getenv("EMBED_BASE_URL", "http://127.0.0.1:11434/v1")
    embed_api_key = os.getenv("EMBED_API_KEY", "ollama")

    if provider == "sentence-transformers":
        model = SentenceTransformer(model_name)
        vec = model.encode([args.q], normalize_embeddings=True)[0].tolist()
    elif provider == "openai":
        vec = _openai_embed(embed_base_url, embed_api_key, model_name, args.q)
    else:
        raise ValueError(f"Unsupported EMBED_PROVIDER={provider}")

    client = MilvusClient(uri=uri)
    results = client.search(
        collection_name=collection,
        data=[vec],
        filter=f'namespace == "{args.scope}"',
        limit=args.k,
        output_fields=["namespace", "path", "text"],
    )

    for i, hit in enumerate(results[0], 1):
        ent = hit.get("entity", {})
        print(f"[{i}] score={hit.get('distance'):.4f}")
        print(f"    namespace: {ent.get('namespace')}")
        print(f"    path: {ent.get('path')}")
        snippet = (ent.get("text") or "").replace("\n", " ")
        print(f"    text: {snippet[:260]}\n")


if __name__ == "__main__":
    main()
