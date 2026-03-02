#!/usr/bin/env python3
import argparse
import os
from pathlib import Path


def tail_text(path: Path, max_chars: int = 5000) -> str:
    if not path.exists():
        return ""
    t = path.read_text(encoding="utf-8", errors="ignore")
    return t[-max_chars:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--main-workspace", default=os.getenv("MAIN_WORKSPACE", "~/.openclaw/workspace"))
    ap.add_argument("--shared", default=os.getenv("SHARED_MEMORY_FILE", "~/.openclaw/shared/SHARED_MEMORY.md"))
    ap.add_argument("--max_chars", type=int, default=3000)
    args = ap.parse_args()

    ws = Path(args.main_workspace).expanduser()
    shared = Path(args.shared).expanduser()

    core = tail_text(ws / "MEMORY.md", 3800)
    mem_dir = ws / "memory"
    recent = ""
    if mem_dir.exists():
        files = sorted(mem_dir.glob("*.md"))
        if files:
            recent = tail_text(files[-1], 2200)

    shared_text = tail_text(shared, 1500)

    out = f"Main context summary:\n\nCore memory:\n{core}\n\nRecent note:\n{recent}\n\nShared essentials:\n{shared_text}\n"
    print(out[: args.max_chars])


if __name__ == "__main__":
    main()
