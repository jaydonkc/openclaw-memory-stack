#!/usr/bin/env python3
import argparse
import hashlib
import os
from pathlib import Path
from typing import List, Tuple

from dotenv import load_dotenv
from pymilvus import MilvusClient, DataType
from sentence_transformers import SentenceTransformer


def chunk_text(text: str, size: int = 900, overlap: int = 120) -> List[str]:
    if not text.strip():
        return []
    chunks = []
    i = 0
    n = len(text)
    while i < n:
        chunk = text[i : i + size].strip()
        if chunk:
            chunks.append(chunk)
        i += max(1, size - overlap)
    return chunks


def load_scope_files(scope: str, main_ws: Path, coding_ws: Path, shared_file: Path) -> List[Tuple[str, Path]]:
    files: List[Tuple[str, Path]] = []
    if scope == "shared":
        files.append(("shared", shared_file))
    elif scope == "main":
        files.append(("main", main_ws / "MEMORY.md"))
        files.extend(("main", p) for p in sorted((main_ws / "memory").glob("*.md")))
    elif scope == "coding":
        files.append(("coding", coding_ws / "MEMORY.md"))
        files.extend(("coding", p) for p in sorted((coding_ws / "memory").glob("*.md")))
    return [(ns, p) for ns, p in files if p.exists()]


def ensure_collection(client: MilvusClient, name: str, dim: int):
    if client.has_collection(name):
        return
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=["shared", "main", "coding"], required=True)
    args = parser.parse_args()

    uri = os.getenv("MILVUS_URI", "http://127.0.0.1:19530")
    collection = os.getenv("MILVUS_COLLECTION", "openclaw_memory")
    model_name = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    main_ws = Path(os.getenv("MAIN_WORKSPACE", "~/.openclaw/workspace")).expanduser()
    coding_ws = Path(os.getenv("CODING_WORKSPACE", "~/.openclaw/workspace-coding")).expanduser()
    shared_file = Path(os.getenv("SHARED_MEMORY_FILE", "~/.openclaw/shared/SHARED_MEMORY.md")).expanduser()

    files = load_scope_files(args.scope, main_ws, coding_ws, shared_file)
    if not files:
        print(f"No files found for scope={args.scope}")
        return

    model = SentenceTransformer(model_name)
    dim = model.get_sentence_embedding_dimension()

    client = MilvusClient(uri=uri)
    ensure_collection(client, collection, dim)

    rows = []
    for namespace, path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        chunks = chunk_text(text)
        if not chunks:
            continue
        vectors = model.encode(chunks, normalize_embeddings=True)
        for idx, (chunk, vec) in enumerate(zip(chunks, vectors)):
            rid = hashlib.sha1(f"{namespace}:{path}:{idx}:{chunk[:120]}".encode()).hexdigest()[:40]
            rows.append(
                {
                    "id": rid,
                    "vector": vec.tolist(),
                    "namespace": namespace,
                    "path": str(path),
                    "text": chunk,
                }
            )

    if rows:
        client.upsert(collection_name=collection, data=rows)
    print(f"Indexed {len(rows)} chunks for scope={args.scope}")


if __name__ == "__main__":
    main()
