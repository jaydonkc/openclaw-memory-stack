#!/usr/bin/env python3
import argparse, json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--namespace", required=True, choices=["main", "coding", "shared"])
    ap.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()

    p = Path.home() / "openclaw" / "memory-stack" / "episodic" / f"{args.namespace}.jsonl"
    if not p.exists():
        print("no episodic records")
        return

    lines = p.read_text(encoding="utf-8").splitlines()[-args.limit :]
    for ln in lines:
        rec = json.loads(ln)
        print(f"[{rec['namespace']}] {rec['title']} :: {rec['event'][:180]}")


if __name__ == "__main__":
    main()
