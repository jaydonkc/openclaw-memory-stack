#!/usr/bin/env python3
"""
OpenMem episodic adapter stub.

Intended behavior:
1) accept event text + namespace
2) redact secrets
3) persist to OpenMem backend (to be implemented)
4) mirror summarized vector to Milvus namespace
"""

import argparse
import re

SECRET_PATTERNS = [
    re.compile(r"(ghp_[A-Za-z0-9]{20,})"),
    re.compile(r"(ntn_[A-Za-z0-9]{20,})"),
    re.compile(r"(sk-[A-Za-z0-9]{20,})"),
]


def redact(text: str) -> str:
    out = text
    for p in SECRET_PATTERNS:
        out = p.sub("[REDACTED_SECRET]", out)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--namespace", choices=["main", "coding", "shared"], required=True)
    parser.add_argument("--event", required=True)
    args = parser.parse_args()

    safe = redact(args.event)
    print("[stub] would write episodic memory")
    print("namespace:", args.namespace)
    print("event:", safe)


if __name__ == "__main__":
    main()
