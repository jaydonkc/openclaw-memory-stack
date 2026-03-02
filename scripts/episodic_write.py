#!/usr/bin/env python3
import argparse, json, os, re, time
from pathlib import Path

RULES = {
    "allowed": {"main", "coding", "shared"},
    "deny_patterns": [
        r"ghp_[A-Za-z0-9]{20,}",
        r"ntn_[A-Za-z0-9]{20,}",
        r"sk-[A-Za-z0-9]{20,}",
        r"AKIA[0-9A-Z]{16}",
    ],
}


def redact(text: str) -> str:
    out = text
    for p in RULES["deny_patterns"]:
        out = re.sub(p, "[REDACTED_SECRET]", out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--namespace", required=True, choices=["main", "coding", "shared"])
    ap.add_argument("--title", required=True)
    ap.add_argument("--event", required=True)
    ap.add_argument("--tags", default="")
    args = ap.parse_args()

    ns = args.namespace
    if ns not in RULES["allowed"]:
        raise SystemExit("namespace not allowed")

    safe_event = redact(args.event)
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    out_dir = Path.home() / "openclaw" / "memory-stack" / "episodic"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{ns}.jsonl"

    rec = {
        "ts": int(time.time()),
        "namespace": ns,
        "title": args.title,
        "event": safe_event,
        "tags": tags,
    }
    with out_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"wrote episodic event to {out_file}")


if __name__ == "__main__":
    main()
