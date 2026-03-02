#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path


def tail_text(path: Path, max_chars: int = 6000) -> str:
    if not path.exists():
        return ""
    t = path.read_text(encoding="utf-8", errors="ignore")
    return t[-max_chars:]


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or ""), (p.stderr or "")


def parse_milvus_output(text: str):
    blocks = []
    cur = {}
    for ln in text.splitlines():
        ln = ln.strip()
        if ln.startswith("[") and "score=" in ln:
            if cur:
                blocks.append(cur)
            cur = {"score": ln, "path": "", "text": ""}
        elif ln.startswith("ns=") or ln.startswith("ns:"):
            cur["path"] = ln
        elif ln.startswith("text=") or ln.startswith("text:"):
            cur["text"] = ln.replace("text=", "").replace("text:", "", 1).strip()
    if cur:
        blocks.append(cur)
    return blocks[:5]


def load_recent_episodes(ep_path: Path, limit: int = 8):
    if not ep_path.exists():
        return []
    lines = ep_path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]
    out = []
    for ln in lines:
        try:
            rec = json.loads(ln)
            title = rec.get("title", "untitled")
            event = rec.get("event", "")
            out.append(f"- {title}: {event[:180]}")
        except Exception:
            continue
    return out[:3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", required=True, help="Current user query/task")
    ap.add_argument("--main-workspace", default=os.getenv("MAIN_WORKSPACE", "~/.openclaw/workspace"))
    ap.add_argument("--coding-workspace", default=os.getenv("CODING_WORKSPACE", "~/.openclaw/workspace-coding"))
    ap.add_argument("--shared", default=os.getenv("SHARED_MEMORY_FILE", "~/.openclaw/shared/SHARED_MEMORY.md"))
    ap.add_argument("--memory-stack", default=os.getenv("MEMORY_STACK_DIR", "~/openclaw/memory-stack"))
    ap.add_argument("--max_chars", type=int, default=4000)
    args = ap.parse_args()

    main_ws = Path(args.main_workspace).expanduser()
    coding_ws = Path(args.coding_workspace).expanduser()
    shared = Path(args.shared).expanduser()
    stack = Path(args.memory_stack).expanduser()

    core_parts = []
    core_parts.append(tail_text(coding_ws / "MEMORY.md", 3500))
    # include latest daily note if present
    mem_dir = coding_ws / "memory"
    if mem_dir.exists():
        files = sorted(mem_dir.glob("*.md"))
        if files:
            core_parts.append(tail_text(files[-1], 2500))

    shared_text = tail_text(shared, 2200)

    # Milvus semantic query (coding namespace)
    cmd = ["python", str(stack / "scripts/query_memory.py"), "--scope", "coding", "--q", args.q, "--k", "5"]
    code, out, err = run(cmd)
    semantic = parse_milvus_output(out if code == 0 else "")

    # Episodic bullets
    episodic_path = stack / "episodic" / "coding.jsonl"
    bullets = load_recent_episodes(episodic_path, limit=10)

    semantic_text = "\n".join([f"- {b.get('text','')[:220]}" for b in semantic]) if semantic else "- none"
    epi_text = "\n".join(bullets) if bullets else "- none"

    prompt = f"""Past coding context:\n{semantic_text}\n\nRecent episodes:\n{epi_text}\n\nCore memory tail:\n{''.join(core_parts)[:3500]}\n\nShared essentials:\n{shared_text[:1200]}\n"""

    print(prompt[: args.max_chars])


if __name__ == "__main__":
    main()
