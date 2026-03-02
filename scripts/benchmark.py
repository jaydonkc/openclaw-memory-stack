#!/usr/bin/env python3
import argparse
import json
import os
import statistics
import time
from pathlib import Path
from typing import List, Dict, Any
import urllib.request

from dotenv import load_dotenv
from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer


def _l2_normalize(v):
    norm = sum(x * x for x in v) ** 0.5
    if norm == 0:
        return v
    return [x / norm for x in v]


def _embed_query(provider: str, model_name: str, text: str, base_url: str, api_key: str, st_model):
    if provider == "sentence-transformers":
        return st_model.encode([text], normalize_embeddings=True)[0].tolist()
    if provider == "openai":
        url = base_url.rstrip("/") + "/embeddings"
        payload = {"model": model_name, "input": [text]}
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
    raise ValueError(f"Unsupported EMBED_PROVIDER={provider}")


def _percentile(sorted_values: List[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    idx = int(round((p / 100.0) * (len(sorted_values) - 1)))
    idx = max(0, min(idx, len(sorted_values) - 1))
    return sorted_values[idx]


def _load_dataset(path: Path) -> List[Dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    uri = os.getenv("MILVUS_URI", "http://127.0.0.1:19530")
    collection = os.getenv("MILVUS_COLLECTION", "openclaw_memory")
    provider = os.getenv("EMBED_PROVIDER", "sentence-transformers")
    model_name = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    embed_base_url = os.getenv("EMBED_BASE_URL", "http://127.0.0.1:11434/v1")
    embed_api_key = os.getenv("EMBED_API_KEY", "ollama")

    dataset = _load_dataset(Path(args.dataset))
    if not dataset:
        raise SystemExit("Dataset is empty")

    st_model = SentenceTransformer(model_name) if provider == "sentence-transformers" else None
    client = MilvusClient(uri=uri)

    per_query = []
    latencies = []
    reciprocal_ranks = []
    recall_hits = 0

    for item in dataset:
        qid = item.get("id") or "unknown"
        scope = item["scope"]
        query = item["query"]
        relevant_paths = item.get("relevant_paths", [])

        vec = _embed_query(provider, model_name, query, embed_base_url, embed_api_key, st_model)

        t0 = time.perf_counter()
        results = client.search(
            collection_name=collection,
            data=[vec],
            filter=f'namespace == "{scope}"',
            limit=args.k,
            output_fields=["path", "text", "namespace"],
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(elapsed_ms)

        hits = results[0] if results else []
        hit_paths = [((h.get("entity") or {}).get("path") or "") for h in hits]

        first_rank = None
        any_relevant = False
        for i, p in enumerate(hit_paths, start=1):
            if any(rp in p for rp in relevant_paths):
                any_relevant = True
                if first_rank is None:
                    first_rank = i

        recall = 1 if any_relevant else 0
        recall_hits += recall
        rr = (1.0 / first_rank) if first_rank else 0.0
        reciprocal_ranks.append(rr)

        per_query.append(
            {
                "id": qid,
                "scope": scope,
                "query": query,
                "latency_ms": round(elapsed_ms, 2),
                "recall_at_k": recall,
                "reciprocal_rank": rr,
                "top_paths": hit_paths,
            }
        )

    lat_sorted = sorted(latencies)
    report = {
        "dataset": args.dataset,
        "k": args.k,
        "count": len(dataset),
        "embed_provider": provider,
        "embed_model": model_name,
        "metrics": {
            "recall_at_k": recall_hits / len(dataset),
            "mrr": sum(reciprocal_ranks) / len(dataset),
            "latency_ms": {
                "mean": round(statistics.mean(latencies), 2),
                "p50": round(_percentile(lat_sorted, 50), 2),
                "p95": round(_percentile(lat_sorted, 95), 2),
            },
        },
        "queries": per_query,
    }

    print(json.dumps(report, indent=2))
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
