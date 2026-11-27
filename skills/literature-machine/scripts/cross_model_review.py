#!/usr/bin/env python3
"""
Cross-Model Review Wrapper (v1.0)
Optional Layer-2 helper for Literature Machine to break single-model mode collapse
by calling external CLIs (codex / claude) when authenticated and permitted, with
clean fallback instructions to Antigravity invoke_subagent when unavailable.

Pure Python 3.10 stdlib-only.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROLE_PROMPTS = {
    "adversarial": (
        "You are a ruthless Korean fiction editor. Do NOT give numeric scores. "
        "Quote 8-15 exact spans (500-800 chars total) that must be CUT or REWRITTEN, "
        "classifying each as OVER-EXPLAIN, REDUNDANT, STOCK-TELL, PURPLE-PROSE, GENERIC, or FAT. "
        "Preserve scientific reasoning logic and deadpan comedy punchlines. Reply in concise Korean."
    ),
    "continuity": (
        "You are a strict Korean webnovel continuity & epistemology auditor. "
        "Cross-check the draft against the attached bible/canon context for past continuity errors, "
        "character knowledge-boundary violations, premature future-arc leaks, and physical/magic rule breaks. "
        "Reply in concise Korean with exact quotes."
    ),
    "panel": (
        "Simulate 4 Korean fiction readers (1. Commercial Webnovel Reader, 2. Literary Editor, "
        "3. Fellow Fantasy Author, 4. General Reader). Flag momentum drops, AI prose tells, "
        "stability-trap tidy endings, and where the 4 readers disagree. Reply in concise Korean."
    ),
}


def probe_clis() -> dict[str, str | None]:
    return {
        "codex": shutil.which("codex"),
        "claude": shutil.which("claude"),
        "node": shutil.which("node"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe or run cross-model review CLI.")
    parser.add_argument("--probe", action="store_true", help="Check available CLIs on PATH")
    parser.add_argument("--engine", choices=["codex", "claude"], default="codex")
    parser.add_argument("--role", choices=["adversarial", "continuity", "panel"], default="adversarial")
    parser.add_argument("--target", default=None, help="Target draft file path")
    parser.add_argument("--bible-dir", default=None, help="Optional bible directory path")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    found = probe_clis()
    if args.probe:
        print("=== Cross-Model CLI Probe ===")
        for k, v in found.items():
            print(f"  {k}: {v or 'NOT_FOUND'}")
        if not found["codex"] and not found["claude"]:
            print("Fallback: Use Antigravity `invoke_subagent` 4-way parallel audit.")
        sys.exit(0)

    if not args.target:
        parser.error("--target is required unless --probe is set.")

    exe = found.get(args.engine)
    if not exe:
        print(f"[UNAVAILABLE] '{args.engine}' CLI not found on PATH. Use Antigravity `invoke_subagent` instead.")
        sys.exit(1)

    target_text = Path(args.target).read_text(encoding="utf-8")
    canon_snip = ""
    if args.bible_dir:
        bdir = Path(args.bible_dir)
        for fname in ("world.md", "future_arc.md", "ledger.md"):
            fp = bdir / fname
            if fp.exists():
                canon_snip += f"\n\n### {fname}\n" + fp.read_text(encoding="utf-8")[:2500]

    full_prompt = (
        f"{ROLE_PROMPTS[args.role]}\n\n"
        f"=== CANON SUMMARY ==={canon_snip}\n\n"
        f"=== DRAFT TO REVIEW ===\n{target_text}"
    )

    if args.engine == "codex":
        cmd = [exe, "exec", "--skip-git-repo-check", full_prompt]
    else:
        cmd = [exe, "-p", full_prompt]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=args.timeout,
        )
        if proc.returncode != 0:
            print(f"[CLI_ERROR code={proc.returncode}] Fallback to Antigravity `invoke_subagent`.", file=sys.stderr)
            print(proc.stderr[:1000], file=sys.stderr)
            sys.exit(proc.returncode)
        print(proc.stdout)
    except Exception as exc:
        print(f"[CLI_EXCEPTION] {exc}. Fallback to Antigravity `invoke_subagent`.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
